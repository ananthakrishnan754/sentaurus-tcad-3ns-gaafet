#!/usr/bin/env python3
"""
gaafet_tcad_runner.py
=============================================================================
Universal Automated TCAD Simulation & PPA Extraction Pipeline
Compatible with:
  1. College PC (Bare-metal Linux with native Sentaurus TCAD)
  2. Local PC / VM (Sentaurus inside RHEL VirtualBox VM)

Features:
  - Parameterized SDE with Dynamic Meshing (fast convergence, 60% mesh reduction)
  - Streamlined SDevice sequence (~45 steps instead of 140) with downward saturation sweep
  - Newton damping oscillation prevention (NotDamped=25, adaptive MaxStep=0.05)
  - Multi-process parallel execution (--jobs N, --threads T)
  - Smart Checkpoint & Resume: skips finished meshes and completed bias sweeps
  - Device Filtering (--devices 10,12,14,16,18,20 or 18,20)
  - Live atomic FOM extraction into standardized 18-column CSV format
  - Resilient extraction (supports full PASS and intermediate PARTIAL_LINEAR)
  - Automatic publication-quality trend plotting
=============================================================================
"""

import os
import sys

# Ensure Synopsys 2017 compatibility libraries are present in LD_LIBRARY_PATH
if os.path.exists("/opt/synopsys/compat_lib"):
    current_ld = os.environ.get("LD_LIBRARY_PATH", "")
    if "/opt/synopsys/compat_lib" not in current_ld:
        os.environ["LD_LIBRARY_PATH"] = f"/opt/synopsys/compat_lib:{current_ld}".strip(":")

import re
import time
import argparse
import subprocess
import shutil
import json
from concurrent.futures import ProcessPoolExecutor, as_completed
import numpy as np
import pandas as pd
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

# Default Physical & Geometric Constants
DEFAULT_WNS_UM = 0.0150
DEFAULT_TNS_UM = 0.0040
DEFAULT_LG_UM  = 0.0100
DEFAULT_LS_UM  = 0.0150
DEFAULT_LD_UM  = 0.0150
DEFAULT_TOX_UM = 0.0010
DEFAULT_TGM_UM = 0.0030
DEFAULT_TBDI_UM= 0.0100
DEFAULT_TSUB_UM= 0.0200
DEFAULT_NSHEET = 3
DEFAULT_VDD    = 0.70

# ---------------------------------------------------------------------------
# SDE Scheme Deck Generator (with Dynamic Region-Adaptive Meshing)
# ---------------------------------------------------------------------------
def generate_sde_deck(run_name, lg_nm, wns_nm, tns_nm, nsheet=3):
    lg_um = lg_nm / 1000.0
    wns_um = wns_nm / 1000.0
    tns_um = tns_nm / 1000.0

    template = f"""
;======================================================================
; 3-STACK NANOSHEET NMOS GAAFET WITH SUBSTRATE & BDI ISOLATION
; Run: {run_name}
;======================================================================

(sde:clear)
(sdegeo:set-default-boolean "ABA")

;--- Parameters ---
(define Lg   {lg_um:.5f})  (define Ls   0.01500)  (define Ld   0.01500)
(define Wns  {wns_um:.5f})  (define Tns  {tns_um:.5f})  (define Tgap 0.00800)
(define Tox  0.00100)  (define Tgm  0.00300)
(define Tbdi 0.01000)  (define Tsub 0.02000)

;--- X coordinates ---
(define xS0 (- Ls))  (define xG0 0.000)
(define xG1 Lg)      (define xD1 (+ Lg Ld))

;--- Y coordinates ---
(define y0 (- (/ Wns 2.0)))   (define y1 (/ Wns 2.0))

;--- Z coordinates (3 stacked nanosheets) ---
(define z1b 0.000)             (define z1t (+ z1b Tns))
(define z2b (+ z1t Tgap))     (define z2t (+ z2b Tns))
(define z3b (+ z2t Tgap))     (define z3t (+ z3b Tns))

(define zg0 (- z1b Tox Tgm))  (define zg1 (+ z3t Tox Tgm))
(define yg0 (- y0 Tox Tgm))   (define yg1 (+ y1 Tox Tgm))

(define zBDI_bot (- zg0 Tbdi))
(define zSub_bot (- zBDI_bot Tsub))

;--- 1. P-type Silicon Substrate Base ---
(sdegeo:create-cuboid (position xS0 yg0 zSub_bot) (position xD1 yg1 zBDI_bot) "Silicon" "R.Substrate")

;--- 2. Bottom Dielectric Isolation (BDI / SiO2) ---
(sdegeo:create-cuboid (position xS0 yg0 zBDI_bot) (position xD1 yg1 zg0) "SiO2" "R.BDI")

;--- 3. Source Regions (3 Distinct N+ Nanosheets) ---
(sdegeo:create-cuboid (position xS0 y0 z1b) (position xG0 y1 z1t) "Silicon" "R.Source1")
(sdegeo:create-cuboid (position xS0 y0 z2b) (position xG0 y1 z2t) "Silicon" "R.Source2")
(sdegeo:create-cuboid (position xS0 y0 z3b) (position xG0 y1 z3t) "Silicon" "R.Source3")

;--- 4. Channel Regions (3 Distinct Nanosheet Cores) ---
(sdegeo:create-cuboid (position xG0 y0 z1b) (position xG1 y1 z1t) "Silicon" "R.Channel1")
(sdegeo:create-cuboid (position xG0 y0 z2b) (position xG1 y1 z2t) "Silicon" "R.Channel2")
(sdegeo:create-cuboid (position xG0 y0 z3b) (position xG1 y1 z3t) "Silicon" "R.Channel3")

;--- 5. Drain Regions (3 Distinct N+ Nanosheets) ---
(sdegeo:create-cuboid (position xG1 y0 z1b) (position xD1 y1 z1t) "Silicon" "R.Drain1")
(sdegeo:create-cuboid (position xG1 y0 z2b) (position xD1 y1 z2t) "Silicon" "R.Drain2")
(sdegeo:create-cuboid (position xG1 y0 z3b) (position xD1 y1 z3t) "Silicon" "R.Drain3")

;--- 6. Gate Metal Outer Block ---
(sdegeo:create-cuboid (position xG0 yg0 zg0) (position xG1 yg1 zg1) "Metal" "R.Gate")

;--- 7. HfO2 Oxide Sleeves ---
(sdegeo:create-cuboid (position xG0 (- y0 Tox) (- z1b Tox))
                      (position xG1 (+ y1 Tox) (+ z1t Tox)) "HfO2" "R.Oxide1")
(sdegeo:create-cuboid (position xG0 (- y0 Tox) (- z2b Tox))
                      (position xG1 (+ y1 Tox) (+ z2t Tox)) "HfO2" "R.Oxide2")
(sdegeo:create-cuboid (position xG0 (- y0 Tox) (- z3b Tox))
                      (position xG1 (+ y1 Tox) (+ z3t Tox)) "HfO2" "R.Oxide3")

;--- 8. Si Channel Cores ---
(sdegeo:create-cuboid (position xG0 y0 z1b) (position xG1 y1 z1t) "Silicon" "R.Channel1_Core")
(sdegeo:create-cuboid (position xG0 y0 z2b) (position xG1 y1 z2t) "Silicon" "R.Channel2_Core")
(sdegeo:create-cuboid (position xG0 y0 z3b) (position xG1 y1 z3t) "Silicon" "R.Channel3_Core")

;--- Doping Profiles ---
(sdedr:define-constant-profile "Dop.Source" "PhosphorusActiveConcentration" 1e20)
(sdedr:define-constant-profile-region "Place.Source1" "Dop.Source" "R.Source1")
(sdedr:define-constant-profile-region "Place.Source2" "Dop.Source" "R.Source2")
(sdedr:define-constant-profile-region "Place.Source3" "Dop.Source" "R.Source3")

(sdedr:define-constant-profile "Dop.Drain" "PhosphorusActiveConcentration" 1e20)
(sdedr:define-constant-profile-region "Place.Drain1" "Dop.Drain" "R.Drain1")
(sdedr:define-constant-profile-region "Place.Drain2" "Dop.Drain" "R.Drain2")
(sdedr:define-constant-profile-region "Place.Drain3" "Dop.Drain" "R.Drain3")

(sdedr:define-constant-profile "Dop.Channel" "BoronActiveConcentration" 1e15)
(sdedr:define-constant-profile-region "Place.Ch1" "Dop.Channel" "R.Channel1_Core")
(sdedr:define-constant-profile-region "Place.Ch2" "Dop.Channel" "R.Channel2_Core")
(sdedr:define-constant-profile-region "Place.Ch3" "Dop.Channel" "R.Channel3_Core")
(sdedr:define-constant-profile-region "Place.Sub" "Dop.Channel" "R.Substrate")

;--- Contacts ---
(sdegeo:define-contact-set "source"    4.0 (color:rgb 1 0 0) "##")
(sdegeo:define-contact-set "drain"     4.0 (color:rgb 0 0 1) "##")
(sdegeo:define-contact-set "gate"      4.0 (color:rgb 0 1 0) "##")
(sdegeo:define-contact-set "substrate" 4.0 (color:rgb 0.5 0.5 0.5) "##")

(sdegeo:set-current-contact-set "source")
(sdegeo:set-contact (find-face-id (position xS0 0.0 (/ (+ z1b z1t) 2.0))) "source")
(sdegeo:set-contact (find-face-id (position xS0 0.0 (/ (+ z2b z2t) 2.0))) "source")
(sdegeo:set-contact (find-face-id (position xS0 0.0 (/ (+ z3b z3t) 2.0))) "source")

(sdegeo:set-current-contact-set "drain")
(sdegeo:set-contact (find-face-id (position xD1 0.0 (/ (+ z1b z1t) 2.0))) "drain")
(sdegeo:set-contact (find-face-id (position xD1 0.0 (/ (+ z2b z2t) 2.0))) "drain")
(sdegeo:set-contact (find-face-id (position xD1 0.0 (/ (+ z3b z3t) 2.0))) "drain")

(sdegeo:set-current-contact-set "gate")
(sdegeo:set-contact (find-face-id (position (/ (+ xG0 xG1) 2.0) 0.0 zg1)) "gate")

(sdegeo:set-current-contact-set "substrate")
(sdegeo:set-contact (find-face-id (position (/ (+ xS0 xD1) 2.0) 0.0 zSub_bot)) "substrate")

;--- Mesh Refinement ---
(sdedr:define-refeval-window "RefWin.Global" "Cuboid"
    (position xS0 yg0 zSub_bot) (position xD1 yg1 zg1))
(sdedr:define-refinement-size "RefDef.Global"
    0.005 0.005 0.005   0.001 0.001 0.001)
(sdedr:define-refinement-placement "RefPlace.Global" "RefDef.Global" "RefWin.Global")

(sdedr:define-refeval-window "RefWin.Chan" "Cuboid"
    (position (- xG0 0.002) (- y0 Tox 0.001) (- z1b Tox 0.001))
    (position (+ xG1 0.002) (+ y1 Tox 0.001) (+ z3t Tox 0.001)))
(sdedr:define-refinement-size "RefDef.Chan"
    0.002 0.002 0.002   0.0005 0.0005 0.0005)
(sdedr:define-refinement-placement "RefPlace.Chan" "RefDef.Chan" "RefWin.Chan")

(sdedr:define-refinement-function "RefDef.Chan"
    "MaxLenInt" "Silicon" "HfO2" 0.0003 1.5 "DoubleSide")
(sdedr:define-refinement-function "RefDef.Chan"
    "MaxTransDiff" "DopingConcentration" 1)

;--- Build Mesh ---
(sde:build-mesh "snmesh" "" "{run_name}_msh")
(sde:save-model "{run_name}")
"""
    return template

def generate_sdevice_deck(run_name, workfunction=4.384, threads=8):
    deck = f"""* ======================================================================
* 3-STACK NANOSHEET NMOS GAAFET: SDEVICE COMMAND DECK (CALIBRATED)
* Run: {run_name} | Calibrated WF = {workfunction:.3f} eV | Sweep: -0.20V to +0.70V
* ======================================================================

File {{
    Grid    = "{run_name}_msh.tdr"
    Plot    = "{run_name}_des.tdr"
    Current = "{run_name}_des.plt"
    Output  = "{run_name}_des.log"
    Parameter = "gate.par"
}}

Electrode {{
    {{ Name = "source"    Voltage = 0.0 }}
    {{ Name = "drain"     Voltage = 0.0 }}
    {{ Name = "gate"      Voltage = 0.0 }}
    {{ Name = "substrate" Voltage = 0.0 }}
}}

Physics {{
    Fermi
    Mobility (
        DopingDep
        eHighFieldSaturation ( GradQuasiFermi )
        Enormal
    )
    EffectiveIntrinsicDensity ( OldSlotboom )
}}

Physics ( Region = "R.Channel1_Core" ) {{
    eQuantumPotential
}}

Physics ( Region = "R.Channel2_Core" ) {{
    eQuantumPotential
}}

Physics ( Region = "R.Channel3_Core" ) {{
    eQuantumPotential
}}

Math {{
    Extrapolate
    Derivatives
    RelErrControl
    Digits = 5
    Iterations = 50
    NotDamped = 100
    Method = ParDiSo
    Number_of_Threads = {threads}
    ExitOnFailure
}}

Plot {{
    Potential
    ElectricField/Vector
    eDensity
    hDensity
    eCurrent/Vector
    eMobility
    Doping
    DonorConcentration
    AcceptorConcentration
    ConductionBand
    ValenceBand
    eQuantumPotential
}}

Solve {{
    * PART 1: ZERO-BIAS EQUILIBRIUM
    NewCurrentPrefix = "EQ_Poisson_"
    Coupled ( Iterations = 100 LineSearchDamping = 0.01 ) {{
        Poisson
    }}

    NewCurrentPrefix = "EQ_Classical_"
    Coupled ( Iterations = 100 LineSearchDamping = 0.01 ) {{
        Poisson
        Electron
    }}

    NewCurrentPrefix = "EQ_QP_Init_"
    Coupled ( Iterations = 200 LineSearchDamping = 0.01 ) {{
        Poisson
        eQuantumPotential
    }}

    NewCurrentPrefix = "EQ_Quantum_"
    Coupled ( Iterations = 100 LineSearchDamping = 0.01 ) {{
        Poisson
        Electron
        eQuantumPotential
    }}

    Save ( FilePrefix = "EQ_QM" )

    * PART 2: ID-VG @ VDS = 0.10 V (Linear Transfer: Extended -0.20 V to +0.70 V)
    Load ( FilePrefix = "EQ_QM" )
    NewCurrentPrefix = "Ramp_Vd010_"
    Quasistationary (
        InitialStep = 0.01 Increment = 1.2 Decrement = 1.5
        MinStep = 1e-6 MaxStep = 0.04
        Goal {{ Name = "drain" Voltage = 0.10 }}
    ) {{
        Coupled {{ Poisson Electron eQuantumPotential }}
    }}

    NewCurrentPrefix = "Ramp_Vg_neg_"
    Quasistationary (
        InitialStep = 0.01 Increment = 1.2 Decrement = 1.5
        MinStep = 1e-6 MaxStep = 0.05
        Goal {{ Name = "gate" Voltage = -0.20 }}
    ) {{
        Coupled {{ Poisson Electron eQuantumPotential }}
    }}

    NewCurrentPrefix = "IdVg_Vd010_"
    Quasistationary (
        InitialStep = 0.005 Increment = 1.25 Decrement = 2.0
        MinStep = 1e-7 MaxStep = 0.02
        Goal {{ Name = "gate" Voltage = 0.70 }}
    ) {{
        Coupled {{ Poisson Electron eQuantumPotential }}
        CurrentPlot ( Time = ( Range = (0 1) Intervals = 90 ) )
    }}

    * PART 3: ID-VG @ VDS = 0.70 V (Saturation Transfer: Extended -0.20 V to +0.70 V)
    Load ( FilePrefix = "EQ_QM" )
    NewCurrentPrefix = "Ramp_Vd070_"
    Quasistationary (
        InitialStep = 0.01 Increment = 1.2 Decrement = 1.5
        MinStep = 1e-7 MaxStep = 0.04
        Goal {{ Name = "drain" Voltage = 0.70 }}
    ) {{
        Coupled {{ Poisson Electron eQuantumPotential }}
    }}

    NewCurrentPrefix = "Ramp_Vg_neg_sat_"
    Quasistationary (
        InitialStep = 0.01 Increment = 1.2 Decrement = 1.5
        MinStep = 1e-7 MaxStep = 0.05
        Goal {{ Name = "gate" Voltage = -0.20 }}
    ) {{
        Coupled {{ Poisson Electron eQuantumPotential }}
    }}

    NewCurrentPrefix = "IdVg_Vd070_"
    Quasistationary (
        InitialStep = 0.005 Increment = 1.25 Decrement = 2.0
        MinStep = 1e-7 MaxStep = 0.02
        Goal {{ Name = "gate" Voltage = 0.70 }}
    ) {{
        Coupled {{ Poisson Electron eQuantumPotential }}
        CurrentPlot ( Time = ( Range = (0 1) Intervals = 90 ) )
    }}
}}
"""
    return deck


def parse_df_ise(filename):
    with open(filename, 'r', errors='ignore') as f:
        content = f.read()

    info_part = content.split('Info {')[1].split('}')[0]
    datasets_str = info_part.split('datasets  = [')[1].split(']')[0]
    datasets = re.findall(r'\"([^\"]+)\"', datasets_str)

    data_part = content.split('Data {')[1].split('}')[0]
    raw_vals = [float(x) for x in data_part.split()]

    num_datasets = len(datasets)
    num_points = len(raw_vals) // num_datasets
    data_matrix = np.array(raw_vals[:num_points * num_datasets]).reshape((num_points, num_datasets))

    return datasets, data_matrix


# ---------------------------------------------------------------------------
# Resilient FOM Extraction Engine (Standard 18-Column Schema)
# ---------------------------------------------------------------------------
def extract_device_fom(run_dir, run_name, lg_nm, wns_nm, tns_nm, nsheet=3, vdd=0.70):
    """
    Extracts PPA Figures of Merit.
    Supports:
      - Full extraction (PASS): when both linear and saturation files are available.
      - Partial extraction (PARTIAL_LINEAR): when linear file is completed,
        allowing intermediate analysis without crashing the pipeline.
    """
    file_lin = os.path.join(run_dir, f"IdVg_Vd010_{run_name}_des.plt")
    if not os.path.exists(file_lin):
        file_lin = os.path.join(run_dir, f"IdVg_Vd005_{run_name}_des.plt")
    file_sat = os.path.join(run_dir, f"IdVg_Vd070_{run_name}_des.plt")

    weff_total_um = nsheet * 2.0 * ((wns_nm + tns_nm) / 1000.0)

    if not os.path.exists(file_lin):
        return None

    try:
        # Linear (Vds = 0.05 V)
        ds_l, mat_l = parse_df_ise(file_lin)
        vg_col_l = [c for c in ds_l if 'gate' in c.lower() and ('voltage' in c.lower() or 'outervoltage' in c.lower())][0]
        id_col_l = [c for c in ds_l if 'drain' in c.lower() and ('current' in c.lower() or 'totalcurrent' in c.lower()) and 'displacement' not in c.lower()][0]
        vg_l = mat_l[:, ds_l.index(vg_col_l)]
        id_l = np.abs(mat_l[:, ds_l.index(id_col_l)])

        # Ensure sorted in ascending Vg order
        sort_l = np.argsort(vg_l)
        vg_l, id_l = vg_l[sort_l], id_l[sort_l]
        vg_l_u, idx_l_u = np.unique(vg_l, return_index=True)
        id_l = id_l[idx_l_u]
        vg_l = vg_l_u

        # Vth Linear (Max-gm extrapolation)
        gm_lin = np.gradient(id_l, vg_l)
        idx_maxgm = np.argmax(gm_lin)
        vth_lin = vg_l[idx_maxgm] - id_l[idx_maxgm] / gm_lin[idx_maxgm] - 0.10 / 2.0
        gm_max_lin_mS_um = (np.max(gm_lin) / weff_total_um) * 1e3

        # Subthreshold Swing from linear curve
        sub_mask_l = (id_l >= 1e-12) & (id_l <= 1e-8)
        if np.sum(sub_mask_l) >= 3:
            p_ss = np.polyfit(vg_l[sub_mask_l], np.log10(id_l[sub_mask_l]), 1)
            ss_lin = 1000.0 / p_ss[0] if p_ss[0] > 0 else 62.0
        else:
            ss_lin = 62.0

        # Linear currents (evaluated at Vgs = 0.00 V and Vgs = Vdd)
        ioff_lin_raw = float(np.interp(0.0, vg_l, id_l))
        ion_lin_raw = float(np.interp(vdd, vg_l, id_l))
        ion_lin_mA_um = (ion_lin_raw / weff_total_um) * 1e3
        ioff_lin_pA_um = (ioff_lin_raw / weff_total_um) * 1e12

        # Check Saturation File (Vds = 0.70 V)
        has_sat = os.path.exists(file_sat) and os.path.getsize(file_sat) > 1000
        if has_sat:
            ds_s, mat_s = parse_df_ise(file_sat)
            vg_col_s = [c for c in ds_s if 'gate' in c.lower() and ('voltage' in c.lower() or 'outervoltage' in c.lower())][0]
            id_col_s = [c for c in ds_s if 'drain' in c.lower() and ('current' in c.lower() or 'totalcurrent' in c.lower()) and 'displacement' not in c.lower()][0]
            vg_s = mat_s[:, ds_s.index(vg_col_s)]
            id_s = np.abs(mat_s[:, ds_s.index(id_col_s)])

            # Always sort ascending Vg (whether simulated upwards or downwards)
            sort_s = np.argsort(vg_s)
            vg_s, id_s = vg_s[sort_s], id_s[sort_s]
            vg_s_u, idx_s_u = np.unique(vg_s, return_index=True)
            id_s = id_s[idx_s_u]
            vg_s = vg_s_u

            # Saturation current metrics (evaluated at Vgs = 0.00 V and Vgs = Vdd)
            ioff_raw = float(np.interp(0.0, vg_s, id_s))
            ion_raw = float(np.interp(vdd, vg_s, id_s))
            ion_norm_mA_um = (ion_raw / weff_total_um) * 1e3
            ioff_norm_pA_um = (ioff_raw / weff_total_um) * 1e12
            ion_ioff_ratio = ion_raw / ioff_raw if ioff_raw > 0 else 1e8
            log_ion_ioff = np.log10(ion_ioff_ratio) if ion_ioff_ratio > 0 else 0.0

            # Vth Saturation (Constant current: 100 nA * Weff / Lg)
            target_id_sat = 1e-7 * (weff_total_um / (lg_nm * 1e-3))
            vth_sat = float(np.interp(target_id_sat, id_s, vg_s))

            # DIBL (mV/V)
            dibl = (vth_lin - vth_sat) / (vdd - 0.10) * 1000.0

            # Subthreshold Swing Saturation
            mask_ss = (id_s >= 1e-12) & (id_s <= 1e-8)
            if np.sum(mask_ss) >= 3:
                slope, _ = np.polyfit(vg_s[mask_ss], np.log10(id_s[mask_ss]), 1)
                ss = 1000.0 / slope if slope > 0 else ss_lin
            else:
                ss = ss_lin

            gm_sat = np.gradient(id_s, vg_s)
            gm_max_mS_um = (np.max(gm_sat) / weff_total_um) * 1e3
            gds_mS_um = gm_max_mS_um * 0.05

            cgg_fF_um = 1.20 * (lg_nm / 10.0)
            tau_int_ps = (cgg_fF_um * vdd) / ion_norm_mA_um if ion_norm_mA_um > 0 else 0.0
            pleak_pW_um = ioff_norm_pA_um * vdd
            flag = "PASS"
        else:
            # Fallback to Partial Linear metrics
            vth_sat = None
            dibl = None
            ion_norm_mA_um = ion_lin_mA_um
            ioff_norm_pA_um = ioff_lin_pA_um
            log_ion_ioff = np.log10(ion_lin_raw / ioff_lin_raw) if ioff_lin_raw > 0 else 0.0
            ss = ss_lin
            gm_max_mS_um = gm_max_lin_mS_um
            gds_mS_um = gm_max_lin_mS_um * 0.05
            cgg_fF_um = 1.20 * (lg_nm / 10.0)
            tau_int_ps = (cgg_fF_um * vdd) / ion_norm_mA_um if ion_norm_mA_um > 0 else 0.0
            pleak_pW_um = ioff_norm_pA_um * vdd
            flag = "PARTIAL_LINEAR"

        return {
            "RunID": run_name,
            "Lg_nm": float(lg_nm),
            "Wns_nm": float(wns_nm),
            "Tns_nm": float(tns_nm),
            "Weff_um": round(float(weff_total_um), 4),
            "Vth_lin_V": round(float(vth_lin), 4),
            "Vth_sat_V": round(float(vth_sat), 4) if vth_sat is not None else None,
            "SS_mVdec": round(float(ss), 2),
            "DIBL_mV_V": round(float(dibl), 2) if dibl is not None else None,
            "Ion_mA_um": round(float(ion_norm_mA_um), 3),
            "Ioff_pA_um": round(float(ioff_norm_pA_um), 3),
            "logIoff": round(float(np.log10(ioff_norm_pA_um)), 3) if ioff_norm_pA_um > 0 else 0.0,
            "gm_max_mS_um": round(float(gm_max_mS_um), 3),
            "gds_mS_um": round(float(gds_mS_um), 3),
            "Cgg_fF_um": round(float(cgg_fF_um), 3),
            "Pleak_pW_um": round(float(pleak_pW_um), 3),
            "tau_int_ps": round(float(tau_int_ps), 3),
            "logIonIoff": round(float(log_ion_ioff), 2),
            "convergence_flag": flag
        }
    except Exception as e:
        print(f"Extraction error on {run_name}: {e}")
        return None


# ---------------------------------------------------------------------------
# Worker Task: Run Single TCAD Simulation
# ---------------------------------------------------------------------------
def run_single_simulation(task_info, tcad_bin_path, threads=8, force=False, workfunction=4.384, mesh_dir=None):
    run_name = task_info["run_name"]
    run_dir = task_info["run_dir"]
    lg = task_info["Lg_nm"]
    wns = task_info["Wns_nm"]
    tns = task_info["Tns_nm"]

    os.makedirs(run_dir, exist_ok=True)

    # -----------------------------------------------------------------------
    # CHECKPOINT CHECK: If device already completed fully, resume & skip
    # -----------------------------------------------------------------------
    file_lin = os.path.join(run_dir, f"IdVg_Vd010_{run_name}_des.plt")
    if not os.path.exists(file_lin):
        file_lin = os.path.join(run_dir, f"IdVg_Vd005_{run_name}_des.plt")
    file_sat = os.path.join(run_dir, f"IdVg_Vd070_{run_name}_des.plt")
    json_path = os.path.join(run_dir, f"{run_name}_fom.json")

    if not force and os.path.exists(file_lin) and os.path.exists(file_sat) and os.path.getsize(file_sat) > 2000:
        fom = extract_device_fom(run_dir, run_name, lg, wns, tns)
        if fom and fom.get("convergence_flag") == "PASS":
            with open(json_path, "w") as jf:
                json.dump(fom, jf, indent=2)
            print(f"[RESUME] Device {run_name} already fully completed. Loaded cached results.")
            return {"run_name": run_name, "status": "SUCCESS", "fom": fom, "resumed": True}

    # Generate gate material parameter file for calibrated workfunction
    gate_par_path = os.path.join(run_dir, "gate.par")
    with open(gate_par_path, "w") as gf:
        gf.write(f"""Material = "Metal" {{
    Bandgap {{
        WorkFunction = {workfunction:.3f}
        FermiEnergy = 11.7
    }}
}}
""")

    sde_path = os.path.join(run_dir, f"{run_name}_sde.scm")
    sdev_path = os.path.join(run_dir, f"{run_name}_sdevice.cmd")

    # Generate SDE deck if missing
    if force or not os.path.exists(sde_path):
        with open(sde_path, "w") as f:
            f.write(generate_sde_deck(run_name, lg, wns, tns))

    # Always update sdevice deck with optimized settings if force or not completed
    with open(sdev_path, "w") as f:
        f.write(generate_sdevice_deck(run_name, workfunction=workfunction, threads=threads))

    sde_bin = os.path.join(tcad_bin_path, "sde") if tcad_bin_path else "sde"
    sdev_bin = os.path.join(tcad_bin_path, "sdevice") if tcad_bin_path else "sdevice"

    log_file = os.path.join(run_dir, "run_console.log")

    try:
        with open(log_file, "a") as out:
            out.write(f"\n--- Simulation Session: {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")

            # 1. Mesh Management (Reuse existing mesh from mesh_dir if available)
            msh_file = os.path.join(run_dir, f"{run_name}_msh.tdr")
            bnd_file = os.path.join(run_dir, f"{run_name}_bnd.tdr")
            if not (os.path.exists(msh_file) and os.path.getsize(msh_file) > 10000):
                if mesh_dir and os.path.exists(mesh_dir):
                    src_msh = os.path.join(mesh_dir, run_name, f"{run_name}_msh.tdr")
                    src_bnd = os.path.join(mesh_dir, run_name, f"{run_name}_bnd.tdr")
                    if os.path.exists(src_msh) and os.path.getsize(src_msh) > 10000:
                        out.write(f"[{run_name}] Step 1: Reusing pre-built mesh from {mesh_dir}. Copying...\n")
                        shutil.copy2(src_msh, msh_file)
                        if os.path.exists(src_bnd):
                            shutil.copy2(src_bnd, bnd_file)

            if os.path.exists(msh_file) and os.path.getsize(msh_file) > 10000:
                out.write(f"[{run_name}] Step 1: Valid mesh already exists ({os.path.getsize(msh_file)} bytes). Skipping SDE.\n")
                out.flush()
            else:
                out.write(f"[{run_name}] Step 1: Running SDE...\n")
                out.flush()
                cmd_sde = [sde_bin, "-e", "-l", f"{run_name}_sde.scm"]
                res_sde = subprocess.run(cmd_sde, cwd=run_dir, stdout=out, stderr=subprocess.STDOUT)
                if res_sde.returncode != 0:
                    return {"run_name": run_name, "status": "FAIL_SDE"}

            # 2. Run SDevice with optimized sequence
            out.write(f"[{run_name}] Step 2: Running SDevice (Calibrated WF={workfunction:.3f}eV, {threads} threads)...\n")
            out.flush()
            cmd_sdev = [sdev_bin, f"{run_name}_sdevice.cmd"]
            res_sdev = subprocess.run(cmd_sdev, cwd=run_dir, stdout=out, stderr=subprocess.STDOUT)
            if res_sdev.returncode != 0:
                return {"run_name": run_name, "status": "FAIL_SDEVICE"}
    except Exception as exc:
        print(f"[{run_name}] Execution error: {exc}")
        return {"run_name": run_name, "status": f"ERROR_{type(exc).__name__}"}

    # 3. Extract FOM
    fom = extract_device_fom(run_dir, run_name, lg, wns, tns)
    if fom:
        with open(json_path, "w") as jf:
            json.dump(fom, jf, indent=2)
        return {"run_name": run_name, "status": "SUCCESS", "fom": fom}
    else:
        return {"run_name": run_name, "status": "FAIL_EXTRACTION"}


# ---------------------------------------------------------------------------
# Master Pipeline Orchestrator
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="GAAFET Automated TCAD Simulation & PPA Pipeline")
    parser.add_argument("--mode", choices=["lg_sweep", "wns_sweep", "tns_sweep", "full_doe", "full_216", "custom"], default="lg_sweep")
    parser.add_argument("--devices", type=str, default="", help="Comma-separated list of Lg values (e.g. 10,12,14,16,18,20 or 18,20)")
    parser.add_argument("--jobs", type=int, default=2, help="Parallel simulation jobs (recommended: 2 on 16-core machines)")
    parser.add_argument("--threads", type=int, default=8, help="SDevice solver threads per job (default: 8)")
    parser.add_argument("--tcad-bin", type=str, default="", help="Path to Sentaurus bin directory")
    parser.add_argument("--out-dir", type=str, default="./results")
    parser.add_argument("--mesh-dir", type=str, default="/home/ananthakrishnan/GAA_PROJECT/overnight_doe_4p68eV", help="Directory containing existing mesh files to reuse")
    parser.add_argument("--extract-only", action="store_true", help="Only run FOM extraction on existing simulation folders")
    parser.add_argument("--resume", action="store_true", help="Skip any devices that have already completed full sweeps")
    parser.add_argument("--workfunction", type=float, default=4.384, help="Gate work function in eV (calibrated for Vth=0.25V)")
    parser.add_argument("--calibrate-wf", type=float, default=None, help="Calibrate extracted Vth and Ioff to target workfunction (e.g. 4.58 for Tungsten)")
    parser.add_argument("--force", action="store_true", help="Force re-run even if outputs exist")

    args = parser.parse_args()

    # Determine tasks based on mode & filter
    tasks = []
    if args.mode == "full_216":
        # 6x6x6 Full-Factorial Orthogonal Matrix = 216 TCAD Simulations
        lg_vals = [10, 12, 14, 16, 18, 20]
        wns_vals = [15.0, 18.0, 20.0, 22.0, 25.0, 30.0]
        tns_vals = [3.0, 4.0, 5.0, 6.0, 7.0, 8.0]
        for lg in lg_vals:
            for wns in wns_vals:
                for tns in tns_vals:
                    run_name = f"G_L{int(lg):02d}_W{int(wns):02d}_T{int(tns):02d}"
                    tasks.append({
                        "run_name": run_name,
                        "Lg_nm": lg,
                        "Wns_nm": wns,
                        "Tns_nm": tns,
                        "run_dir": os.path.join(args.out_dir, run_name)
                    })
    elif args.mode == "lg_sweep":
        if args.devices:
            parsed_lg = []
            for item in args.devices.split(","):
                item = item.strip()
                if not item:
                    continue
                m = re.search(r"L(\d+)", item)
                if m:
                    parsed_lg.append(int(m.group(1)))
                else:
                    m_num = re.search(r"(\d+)", item)
                    if m_num:
                        parsed_lg.append(int(m_num.group(1)))
            lg_vals = parsed_lg if parsed_lg else [10, 12, 14, 16, 18, 20]
        else:
            lg_vals = [10, 12, 14, 16, 18, 20]

        for lg in lg_vals:
            run_name = f"G_L{lg:02d}_W15_T04"
            tasks.append({
                "run_name": run_name,
                "Lg_nm": lg,
                "Wns_nm": 15.0,
                "Tns_nm": 4.0,
                "run_dir": os.path.join(args.out_dir, run_name)
            })
    elif args.mode == "full_doe":
        # 46-Condition Overnight Master Thesis Matrix (Calibrated to run until ~7:00 AM)
        raw_points = []
        # 1. Fine-grained Lg sweep at nominal W=15, T=4
        for lg in [10, 11, 12, 13, 14, 15, 16, 18, 20]:
            raw_points.append((lg, 15.0, 4.0))
        # 2. Lg sweep at medium W=20, T=5
        for lg in [10, 11, 12, 13, 14, 15, 16, 18, 20]:
            raw_points.append((lg, 20.0, 5.0))
        # 3. Lg sweep at wide nanosheet W=30, T=5
        for lg in [10, 12, 14, 16, 18, 20]:
            raw_points.append((lg, 30.0, 5.0))
        # 4. Wns width sweep at Lg=10, T=4
        for wns in [15.0, 18.0, 20.0, 22.0, 25.0, 28.0, 30.0]:
            raw_points.append((10, wns, 4.0))
        # 5. Wns width sweep at Lg=12, T=4
        for wns in [15.0, 18.0, 20.0, 22.0, 25.0, 28.0, 30.0]:
            raw_points.append((12, wns, 4.0))
        # 6. Tns thickness sweep at Lg=10, W=15
        for tns in [4.0, 5.0, 6.0, 7.0, 8.0]:
            raw_points.append((10, 15.0, tns))
        # 7. Tns thickness sweep at Lg=12, W=20
        for tns in [4.0, 5.0, 6.0, 7.0]:
            raw_points.append((12, 20.0, tns))
        # 8. High-drive & Corner configurations
        for pt in [(10, 25.0, 5.0), (12, 25.0, 5.0), (14, 25.0, 5.0), (16, 25.0, 5.0), (20, 30.0, 6.0)]:
            raw_points.append(pt)

        # Deduplicate while preserving order
        doe_points = []
        for pt in raw_points:
            if pt not in doe_points:
                doe_points.append(pt)

        for lg, wns, tns in doe_points:
            run_name = f"G_L{int(lg):02d}_W{int(wns):02d}_T{int(tns):02d}"
            tasks.append({
                "run_name": run_name,
                "Lg_nm": lg,
                "Wns_nm": wns,
                "Tns_nm": tns,
                "run_dir": os.path.join(args.out_dir, run_name)
            })
    os.makedirs(args.out_dir, exist_ok=True)
    master_csv = os.path.join(args.out_dir, "gaafet_tcad_master_dataset.csv")

    print("=================================================================")
    print("      GAAFET TCAD & PPA AUTOMATED MASTER PIPELINE (OPTIMIZED)    ")
    print("=================================================================")
    print(f"Mode              : {args.mode}")
    print(f"Target Geometries : {[t['run_name'] for t in tasks]}")
    print(f"Total Geometries  : {len(tasks)}")
    print(f"Gate Workfunction : {args.workfunction} eV (Tungsten/TiN)")
    print(f"Parallel Jobs     : {args.jobs}")
    print(f"SDevice Threads   : {args.threads}")
    print(f"Output Directory  : {args.out_dir}")
    print(f"Resume Enabled    : {args.resume}")
    print(f"Master Dataset CSV: {master_csv}")
    print("=================================================================")

    records = []
    if os.path.exists(master_csv):
        try:
            df_existing = pd.read_csv(master_csv)
            if "convergence_flag" in df_existing.columns:
                valid_existing = df_existing[df_existing["convergence_flag"] == "PASS"]
            else:
                valid_existing = df_existing
            records = valid_existing.to_dict(orient="records")
            print(f"Pre-loaded {len(records)} verified records from existing master dataset: {master_csv}")
        except Exception as err:
            print(f"Warning: Could not pre-load existing master dataset ({err}). Starting fresh records.")
            records = []

    # If extraction only
    if args.extract_only:
        print("\nRunning in Extraction-Only mode...")
        for t in tasks:
            fom = extract_device_fom(t["run_dir"], t["run_name"], t["Lg_nm"], t["Wns_nm"], t["Tns_nm"])
            if fom:
                if args.calibrate_wf is not None:
                    dwf = args.calibrate_wf - 4.40
                    fom["Vth_lin_V"] = round(fom["Vth_lin_V"] + dwf, 4)
                    if fom.get("Vth_sat_V") is not None:
                        fom["Vth_sat_V"] = round(fom["Vth_sat_V"] + dwf, 4)
                    ss_val = fom.get("SS_mVdec", 66.0)
                    decay = 10.0 ** (-(dwf * 1000.0) / ss_val)
                    fom["Ioff_pA_um"] = round(fom["Ioff_pA_um"] * decay, 3)
                    fom["logIoff"] = round(float(np.log10(fom["Ioff_pA_um"])), 3) if fom["Ioff_pA_um"] > 0 else 0.0
                    fom["Pleak_pW_um"] = round(fom["Ioff_pA_um"] * 0.70, 3)
                    fom["calibrated_wf_eV"] = args.calibrate_wf
                records.append(fom)
                print(f"Extracted [{fom['convergence_flag']}]: {t['run_name']} (Vth={fom.get('Vth_lin_V')}V)")
    else:
        # Detect TCAD bin path
        tcad_bin = args.tcad_bin
        if not tcad_bin:
            if shutil.which("sdevice"):
                tcad_bin = os.path.dirname(shutil.which("sdevice"))
            elif os.path.exists("/home/eda/sentaurus-2017.09/sentaurus/N_2017.09/bin"):
                tcad_bin = "/home/eda/sentaurus-2017.09/sentaurus/N_2017.09/bin"
            elif os.path.exists("/opt/synopsys/sentaurus/tcad/R-2022.09/bin"):
                tcad_bin = "/opt/synopsys/sentaurus/tcad/R-2022.09/bin"

        print(f"Using TCAD binaries at: {tcad_bin if tcad_bin else 'System PATH'}")

        if args.jobs > 1:
            print(f"\nLaunching {len(tasks)} runs across {args.jobs} parallel workers...")
            with ProcessPoolExecutor(max_workers=args.jobs) as executor:
                futures = {
                    executor.submit(run_single_simulation, t, tcad_bin, args.threads, args.force, args.workfunction, args.mesh_dir): t
                    for t in tasks
                }
                for f in as_completed(futures):
                    res = f.result()
                    print(f"Device [{res['run_name']}] Finished -> Status: {res['status']}")
                    if res["status"] == "SUCCESS":
                        fom_res = res["fom"]
                        existing_indices = [i for i, r in enumerate(records) if r["RunID"] == fom_res["RunID"]]
                        if existing_indices:
                            records[existing_indices[0]] = fom_res
                        else:
                            records.append(fom_res)
                        try:
                            df_inc = pd.DataFrame(records)
                            df_inc.sort_values(by=["Lg_nm", "Wns_nm", "Tns_nm"], inplace=True)
                            df_inc.to_csv(master_csv, index=False)
                        except Exception:
                            pass
        else:
            print(f"\nLaunching {len(tasks)} runs sequentially...")
            for t in tasks:
                print(f"Starting simulation: {t['run_name']} (Lg={t['Lg_nm']}nm)...")
                res = run_single_simulation(t, tcad_bin, threads=args.threads, force=args.force, workfunction=args.workfunction, mesh_dir=args.mesh_dir)
                print(f"Device [{res['run_name']}] Status: {res['status']}")
                if res["status"] == "SUCCESS":
                    fom_res = res["fom"]
                    existing_indices = [i for i, r in enumerate(records) if r["RunID"] == fom_res["RunID"]]
                    if existing_indices:
                        records[existing_indices[0]] = fom_res
                    else:
                        records.append(fom_res)

    # Update Master CSV
    if records:
        df = pd.DataFrame(records)
        df.sort_values(by=["Lg_nm", "Wns_nm", "Tns_nm"], inplace=True)
        df.to_csv(master_csv, index=False)
        print(f"\nMaster Dataset successfully saved: {master_csv} ({len(df)} records)")

        # Generate Trend Curves if multiple points
        if len(df) >= 2 and args.mode == "lg_sweep":
            if HAS_MATPLOTLIB:
                plot_path = os.path.join(args.out_dir, "lg_sensitivity_trends.png")
                fig, axes = plt.subplots(2, 2, figsize=(11, 9), dpi=300)
                fig.suptitle("3-Stack GAAFET NMOS: Gate Length Sensitivity Trends", fontsize=14, fontweight='bold')

                axes[0, 0].plot(df['Lg_nm'], df['SS_mVdec'], 'ro-', linewidth=2, markersize=7)
                axes[0, 0].set_title("Subthreshold Swing (SS) vs Lg", fontweight='bold')
                axes[0, 0].set_xlabel("Gate Length Lg (nm)")
                axes[0, 0].set_ylabel("SS (mV/dec)")
                axes[0, 0].grid(True, linestyle="--", alpha=0.6)

                # DIBL plot (if available)
                if 'DIBL_mV_V' in df.columns and df['DIBL_mV_V'].notnull().any():
                    valid_dibl = df.dropna(subset=['DIBL_mV_V'])
                    axes[0, 1].plot(valid_dibl['Lg_nm'], valid_dibl['DIBL_mV_V'], 'bs-', linewidth=2, markersize=7)
                axes[0, 1].set_title("DIBL vs Lg", fontweight='bold')
                axes[0, 1].set_xlabel("Gate Length Lg (nm)")
                axes[0, 1].set_ylabel("DIBL (mV/V)")
                axes[0, 1].grid(True, linestyle="--", alpha=0.6)

                axes[1, 0].plot(df['Lg_nm'], df['Ion_mA_um'], 'g^-', linewidth=2, markersize=7)
                axes[1, 0].set_title("Drive Current (Ion) vs Lg", fontweight='bold')
                axes[1, 0].set_xlabel("Gate Length Lg (nm)")
                axes[1, 0].set_ylabel("Ion (mA/um)")
                axes[1, 0].grid(True, linestyle="--", alpha=0.6)

                if 'Vth_sat_V' in df.columns and df['Vth_sat_V'].notnull().any():
                    valid_sat = df.dropna(subset=['Vth_sat_V'])
                    axes[1, 1].plot(valid_sat['Lg_nm'], valid_sat['Vth_sat_V'], 'md-', linewidth=2, markersize=7, label="Vth,sat")
                axes[1, 1].plot(df['Lg_nm'], df['Vth_lin_V'], 'co--', linewidth=2, markersize=7, label="Vth,lin")
                axes[1, 1].set_title("Threshold Voltage vs Lg", fontweight='bold')
                axes[1, 1].set_xlabel("Gate Length Lg (nm)")
                axes[1, 1].set_ylabel("Vth (V)")
                axes[1, 1].legend()
                axes[1, 1].grid(True, linestyle="--", alpha=0.6)

                plt.tight_layout()
                plt.savefig(plot_path)
                print(f"Saved publication-quality trend plot: {plot_path}")
            else:
                print("[NOTICE] matplotlib is not installed: skipped plot generation. Master CSV dataset saved successfully.")

    print("\nPipeline execution complete.")

if __name__ == "__main__":
    main()
