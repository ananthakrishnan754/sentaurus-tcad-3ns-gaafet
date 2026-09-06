#!/usr/bin/env python3
"""
extract_lg_sweep_fom.py
=============================================================================
Parses TCAD .plt files from the 6-point Lg sensitivity sweep:
  Lg = 10, 12, 14, 16, 18, 20 nm
Extracts FOMs using the standard project formulas:
  Vth_lin, Vth_sat, SS, DIBL, Ion, Ioff, gm_max, Pleak, Ion/Ioff
Exports:
  - lg_sensitivity_summary.csv
  - lg_sensitivity_trends.png (4-panel trend plot)
=============================================================================
"""

import os
import re
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE_DIR = "/home/ananthakrishnan/GAA_PROJECT/GAA_3NS_SIM/experiments/exp1_lg_sweep"
SWB_DIR = "/home/ananthakrishnan/Documents/swb/exp1_lg_sweep"

RUN_LIST = [
    ("G_L10_W15_T04", 10.0),
    ("G_L12_W15_T04", 12.0),
    ("G_L14_W15_T04", 14.0),
    ("G_L16_W15_T04", 16.0),
    ("G_L18_W15_T04", 18.0),
    ("G_L20_W15_T04", 20.0)
]

WNS_UM = 0.015
TNS_UM = 0.004
NSHEET = 3
WEFF_TOTAL_UM = NSHEET * 2.0 * (WNS_UM + TNS_UM)  # 0.114 um
VDD = 0.70

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

def extract_fom_from_run(run_name, lg_nm):
    # Check if run exists in BASE_DIR or SWB_DIR
    run_path = os.path.join(BASE_DIR, run_name)
    if not os.path.exists(os.path.join(run_path, f"IdVg_Vd005_{run_name}_des.plt")):
        run_path = os.path.join(SWB_DIR, run_name)
        
    file_lin = os.path.join(run_path, f"IdVg_Vd005_{run_name}_des.plt")
    file_sat = os.path.join(run_path, f"IdVg_Vd070_{run_name}_des.plt")
    
    if not os.path.exists(file_lin) or not os.path.exists(file_sat):
        return None
        
    # 1. Parse Linear (Vds = 0.05 V)
    ds_l, mat_l = parse_df_ise(file_lin)
    vg_col_l = [c for c in ds_l if 'gate' in c.lower() and ('voltage' in c.lower() or 'outervoltage' in c.lower())][0]
    id_col_l = [c for c in ds_l if 'drain' in c.lower() and ('current' in c.lower() or 'totalcurrent' in c.lower()) and 'displacement' not in c.lower()][0]
    vg_l = mat_l[:, ds_l.index(vg_col_l)]
    id_l = np.abs(mat_l[:, ds_l.index(id_col_l)])
    
    sort_l = np.argsort(vg_l)
    vg_l, id_l = vg_l[sort_l], id_l[sort_l]
    mask_l = (vg_l >= 0.0) & (vg_l <= 0.705)
    vg_l, id_l = vg_l[mask_l], id_l[mask_l]
    
    # 2. Parse Saturation (Vds = 0.70 V)
    ds_s, mat_s = parse_df_ise(file_sat)
    vg_col_s = [c for c in ds_s if 'gate' in c.lower() and ('voltage' in c.lower() or 'outervoltage' in c.lower())][0]
    id_col_s = [c for c in ds_s if 'drain' in c.lower() and ('current' in c.lower() or 'totalcurrent' in c.lower()) and 'displacement' not in c.lower()][0]
    vg_s = mat_s[:, ds_s.index(vg_col_s)]
    id_s = np.abs(mat_s[:, ds_s.index(id_col_s)])
    
    sort_s = np.argsort(vg_s)
    vg_s, id_s = vg_s[sort_s], id_s[sort_s]
    mask_s = (vg_s >= 0.0) & (vg_s <= 0.705)
    vg_s, id_s = vg_s[mask_s], id_s[mask_s]
    
    # FOM Calculations
    # Currents
    ioff_raw = id_s[0] if id_s[0] > 0 else 1e-15
    ion_raw = id_s[-1]
    
    ion_norm_mA_um = (ion_raw / WEFF_TOTAL_UM) * 1e3
    ioff_norm_pA_um = (ioff_raw / WEFF_TOTAL_UM) * 1e12
    ion_ioff_ratio = ion_raw / ioff_raw
    
    # Vth (Max-gm method on linear curve)
    gm_lin = np.gradient(id_l, vg_l)
    idx_maxgm = np.argmax(gm_lin)
    vth_lin = vg_l[idx_maxgm] - id_l[idx_maxgm] / gm_lin[idx_maxgm] - 0.05 / 2.0
    
    # Saturation Vth (constant current method: 100 nA * Weff / Lg)
    target_id_sat = 1e-7 * (WEFF_TOTAL_UM / (lg_nm * 1e-3))
    vth_sat = np.interp(target_id_sat, id_s, vg_s)
    
    # DIBL
    dibl = (vth_lin - vth_sat) / (0.70 - 0.05) * 1000.0
    
    # Subthreshold Swing (SS)
    mask_ss = (id_s >= 1e-12) & (id_s <= 1e-8)
    if np.sum(mask_ss) >= 3:
        log_id = np.log10(id_s[mask_ss])
        v_sub = vg_s[mask_ss]
        slope, _ = np.polyfit(v_sub, log_id, 1)
        ss = 1000.0 / slope if slope > 0 else 65.0
    else:
        ss = 65.0
        
    gm_max_mS_um = (np.max(np.gradient(id_s, vg_s)) / WEFF_TOTAL_UM) * 1e3
    pleak_pW_um = ioff_norm_pA_um * VDD
    
    return {
        "RunID": run_name,
        "Lg_nm": lg_nm,
        "Wns_nm": 15.0,
        "Tns_nm": 4.0,
        "Weff_um": WEFF_TOTAL_UM,
        "Vth_lin_V": round(float(vth_lin), 4),
        "Vth_sat_V": round(float(vth_sat), 4),
        "SS_mVdec": round(float(ss), 2),
        "DIBL_mV_V": round(float(dibl), 2),
        "Ion_mA_um": round(float(ion_norm_mA_um), 3),
        "Ioff_pA_um": round(float(ioff_norm_pA_um), 3),
        "logIoff": round(float(np.log10(ioff_norm_pA_um)), 3),
        "gm_max_mS_um": round(float(gm_max_mS_um), 3),
        "Pleak_pW_um": round(float(pleak_pW_um), 3),
        "Ion_Ioff_ratio": float(f"{ion_ioff_ratio:.2e}")
    }

def main():
    records = []
    for run_name, lg in RUN_LIST:
        fom = extract_fom_from_run(run_name, lg)
        if fom is not None:
            records.append(fom)
            print(f"Extracted FOM for {run_name} (Lg = {lg} nm)")
        else:
            print(f"Pending simulation outputs for {run_name}")
            
    if not records:
        print("No simulation outputs ready to extract yet.")
        return
        
    df = pd.DataFrame(records)
    csv_out = os.path.join(BASE_DIR, "lg_sensitivity_summary.csv")
    df.to_csv(csv_out, index=False)
    print(f"\nSaved summary CSV: {csv_out}")
    
    # Generate 4-panel trend plot
    fig, axes = plt.subplots(2, 2, figsize=(11, 9), dpi=300)
    fig.suptitle("3-Stack GAAFET NMOS: Gate Length (Lg) Sensitivity Analysis", fontsize=14, fontweight='bold')
    
    # 1. SS vs Lg
    axes[0, 0].plot(df['Lg_nm'], df['SS_mVdec'], 'ro-', linewidth=2, markersize=7)
    axes[0, 0].set_title("Subthreshold Swing (SS) vs Lg", fontweight='bold')
    axes[0, 0].set_xlabel("Gate Length Lg (nm)")
    axes[0, 0].set_ylabel("SS (mV/dec)")
    axes[0, 0].grid(True, linestyle="--", alpha=0.6)
    
    # 2. DIBL vs Lg
    axes[0, 1].plot(df['Lg_nm'], df['DIBL_mV_V'], 'bs-', linewidth=2, markersize=7)
    axes[0, 1].set_title("DIBL vs Lg", fontweight='bold')
    axes[0, 1].set_xlabel("Gate Length Lg (nm)")
    axes[0, 1].set_ylabel("DIBL (mV/V)")
    axes[0, 1].grid(True, linestyle="--", alpha=0.6)
    
    # 3. Ion vs Lg
    axes[1, 0].plot(df['Lg_nm'], df['Ion_mA_um'], 'g^-', linewidth=2, markersize=7)
    axes[1, 0].set_title("Drive Current (Ion) vs Lg", fontweight='bold')
    axes[1, 0].set_xlabel("Gate Length Lg (nm)")
    axes[1, 0].set_ylabel("Ion (mA/um)")
    axes[1, 0].grid(True, linestyle="--", alpha=0.6)
    
    # 4. Vth vs Lg
    axes[1, 1].plot(df['Lg_nm'], df['Vth_sat_V'], 'md-', linewidth=2, markersize=7, label="Vth,sat")
    axes[1, 1].plot(df['Lg_nm'], df['Vth_lin_V'], 'co--', linewidth=2, markersize=7, label="Vth,lin")
    axes[1, 1].set_title("Threshold Voltage (Vth) vs Lg", fontweight='bold')
    axes[1, 1].set_xlabel("Gate Length Lg (nm)")
    axes[1, 1].set_ylabel("Vth (V)")
    axes[1, 1].legend()
    axes[1, 1].grid(True, linestyle="--", alpha=0.6)
    
    plt.tight_layout()
    plot_out = os.path.join(BASE_DIR, "lg_sensitivity_trends.png")
    plt.savefig(plot_out)
    print(f"Saved trend plot: {plot_out}")

if __name__ == "__main__":
    main()
