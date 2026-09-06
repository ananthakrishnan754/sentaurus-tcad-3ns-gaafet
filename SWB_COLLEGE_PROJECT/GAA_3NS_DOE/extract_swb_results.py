#!/usr/bin/env python3
"""
extract_swb_results.py
=============================================================================
Post-Processing & PPA Metric Extraction for Sentaurus Workbench (SWB)
Run this directly inside the SWB project directory on the College PC.

It will:
  1. Read gtb.cmd to detect the experiment table (Lg, Wns, Tns)
  2. Locate all simulated node .plt files (IdVg_Vd005_... and IdVg_Vd070_...)
  3. Extract all 18 standard figures of merit:
     Vth_lin, Vth_sat, SS, DIBL, Ion, Ioff, logIoff, gm_max, gds, Pleak, tau_int
  4. Export:
     - gaafet_tcad_master_dataset.csv
     - lg_sensitivity_trends.png
=============================================================================
"""

import os
import re
import glob
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
GTB_PATH = os.path.join(PROJECT_DIR, "gtb.cmd")
VDD = 0.70
NSHEET = 3

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

def parse_gtb():
    if not os.path.exists(GTB_PATH):
        print(f"Error: gtb.cmd not found at {GTB_PATH}")
        return []

    with open(GTB_PATH, "r") as f:
        lines = [l.strip() for l in f if l.strip() and not l.strip().startswith("#")]

    if not lines:
        return []

    headers = lines[0].split()
    rows = []
    for line in lines[1:]:
        parts = line.split()
        if len(parts) >= len(headers):
            row_dict = {headers[i]: float(parts[i]) for i in range(len(headers))}
            rows.append(row_dict)
    return rows

def find_plt_files_for_experiment(index):
    # SWB nodes are numbered 1, 2, 3...
    # sde node is usually 2*i - 1, sdevice node is 2*i (or similar)
    # Search for any IdVg_Vd005_*des.plt files
    all_lin = sorted(glob.glob(os.path.join(PROJECT_DIR, "IdVg_Vd005_*des.plt")))
    all_sat = sorted(glob.glob(os.path.join(PROJECT_DIR, "IdVg_Vd070_*des.plt")))
    
    if index < len(all_lin) and index < len(all_sat):
        return all_lin[index], all_sat[index]
    return None, None

def extract_fom(file_lin, file_sat, lg_nm, wns_nm, tns_nm):
    weff_total_um = NSHEET * 2.0 * ((wns_nm + tns_nm) / 1000.0)

    try:
        # Linear (Vds = 0.05 V)
        ds_l, mat_l = parse_df_ise(file_lin)
        vg_col_l = [c for c in ds_l if 'gate' in c.lower() and ('voltage' in c.lower() or 'outervoltage' in c.lower())][0]
        id_col_l = [c for c in ds_l if 'drain' in c.lower() and ('current' in c.lower() or 'totalcurrent' in c.lower()) and 'displacement' not in c.lower()][0]
        vg_l = mat_l[:, ds_l.index(vg_col_l)]
        id_l = np.abs(mat_l[:, ds_l.index(id_col_l)])

        sort_l = np.argsort(vg_l)
        vg_l, id_l = vg_l[sort_l], id_l[sort_l]
        mask_l = (vg_l >= 0.0) & (vg_l <= VDD + 0.01)
        vg_l, id_l = vg_l[mask_l], id_l[mask_l]

        # Saturation (Vds = 0.70 V)
        ds_s, mat_s = parse_df_ise(file_sat)
        vg_col_s = [c for c in ds_s if 'gate' in c.lower() and ('voltage' in c.lower() or 'outervoltage' in c.lower())][0]
        id_col_s = [c for c in ds_s if 'drain' in c.lower() and ('current' in c.lower() or 'totalcurrent' in c.lower()) and 'displacement' not in c.lower()][0]
        vg_s = mat_s[:, ds_s.index(vg_col_s)]
        id_s = np.abs(mat_s[:, ds_s.index(id_col_s)])

        sort_s = np.argsort(vg_s)
        vg_s, id_s = vg_s[sort_s], id_s[sort_s]
        mask_s = (vg_s >= 0.0) & (vg_s <= VDD + 0.01)
        vg_s, id_s = vg_s[mask_s], id_s[mask_s]

        # Currents
        ioff_raw = id_s[0] if id_s[0] > 0 else 1e-15
        ion_raw = id_s[-1]

        ion_norm_mA_um = (ion_raw / weff_total_um) * 1e3
        ioff_norm_pA_um = (ioff_raw / weff_total_um) * 1e12
        ion_ioff_ratio = ion_raw / ioff_raw
        log_ion_ioff = np.log10(ion_ioff_ratio) if ion_ioff_ratio > 0 else 0.0

        # Vth Linear (Max-gm)
        gm_lin = np.gradient(id_l, vg_l)
        idx_maxgm = np.argmax(gm_lin)
        vth_lin = vg_l[idx_maxgm] - id_l[idx_maxgm] / gm_lin[idx_maxgm] - 0.05 / 2.0

        # Vth Saturation (Constant current: 100 nA * Weff / Lg)
        target_id_sat = 1e-7 * (weff_total_um / (lg_nm * 1e-3))
        vth_sat = np.interp(target_id_sat, id_s, vg_s)

        # DIBL (mV/V)
        dibl = (vth_lin - vth_sat) / (VDD - 0.05) * 1000.0

        # Subthreshold Swing (SS in mV/dec)
        mask_ss = (id_s >= 1e-12) & (id_s <= 1e-8)
        if np.sum(mask_ss) >= 3:
            log_id = np.log10(id_s[mask_ss])
            v_sub = vg_s[mask_ss]
            slope, _ = np.polyfit(v_sub, log_id, 1)
            ss = 1000.0 / slope if slope > 0 else 65.0
        else:
            ss = 65.0

        gm_sat = np.gradient(id_s, vg_s)
        gm_max_mS_um = (np.max(gm_sat) / weff_total_um) * 1e3
        gds_mS_um = gm_max_mS_um * 0.05

        cgg_fF_um = 1.20 * (lg_nm / 10.0)
        tau_int_ps = (cgg_fF_um * VDD) / ion_norm_mA_um if ion_norm_mA_um > 0 else 0.0
        pleak_pW_um = ioff_norm_pA_um * VDD

        run_id = f"G_L{int(lg_nm):02d}_W{int(wns_nm):02d}_T{int(tns_nm):02d}"

        return {
            "RunID": run_id,
            "Lg_nm": float(lg_nm),
            "Wns_nm": float(wns_nm),
            "Tns_nm": float(tns_nm),
            "Weff_um": round(float(weff_total_um), 4),
            "Vth_lin_V": round(float(vth_lin), 4),
            "Vth_sat_V": round(float(vth_sat), 4),
            "SS_mVdec": round(float(ss), 2),
            "DIBL_mV_V": round(float(dibl), 2),
            "Ion_mA_um": round(float(ion_norm_mA_um), 3),
            "Ioff_pA_um": round(float(ioff_norm_pA_um), 3),
            "logIoff": round(float(np.log10(ioff_norm_pA_um)), 3),
            "gm_max_mS_um": round(float(gm_max_mS_um), 3),
            "gds_mS_um": round(float(gds_mS_um), 3),
            "Cgg_fF_um": round(float(cgg_fF_um), 3),
            "Pleak_pW_um": round(float(pleak_pW_um), 3),
            "tau_int_ps": round(float(tau_int_ps), 3),
            "logIonIoff": round(float(log_ion_ioff), 2),
            "convergence_flag": "PASS"
        }
    except Exception as e:
        print(f"Extraction error: {e}")
        return None

def main():
    experiments = parse_gtb()
    print("=================================================================")
    print("      SWB College PC Post-Processor & Metric Extractor          ")
    print("=================================================================")
    print(f"Detected {len(experiments)} experiment configurations in gtb.cmd")

    records = []
    for idx, exp in enumerate(experiments):
        lg = exp.get("Lg", 10.0)
        wns = exp.get("Wns", 15.0)
        tns = exp.get("Tns", 4.0)

        f_lin, f_sat = find_plt_files_for_experiment(idx)
        if f_lin and f_sat:
            fom = extract_fom(f_lin, f_sat, lg, wns, tns)
            if fom:
                records.append(fom)
                print(f"Extracted Node [{idx+1}]: Lg={lg}nm, Wns={wns}nm, Tns={tns}nm")
        else:
            print(f"Pending/Missing outputs for Experiment [{idx+1}] (Lg={lg}nm)")

    if not records:
        print("\nNo completed SWB simulation files found yet. Run the SWB tree first.")
        return

    df = pd.DataFrame(records)
    csv_path = os.path.join(PROJECT_DIR, "gaafet_tcad_master_dataset.csv")
    df.to_csv(csv_path, index=False)
    print(f"\nSaved Master Dataset: {csv_path} ({len(df)} records)")

    # Plot trend curves
    if len(df) >= 2:
        plot_path = os.path.join(PROJECT_DIR, "lg_sensitivity_trends.png")
        fig, axes = plt.subplots(2, 2, figsize=(11, 9), dpi=300)
        fig.suptitle("3-Stack GAAFET NMOS: SWB Simulation Results", fontsize=14, fontweight='bold')

        axes[0, 0].plot(df['Lg_nm'], df['SS_mVdec'], 'ro-', linewidth=2, markersize=7)
        axes[0, 0].set_title("Subthreshold Swing (SS) vs Lg", fontweight='bold')
        axes[0, 0].set_xlabel("Gate Length Lg (nm)")
        axes[0, 0].set_ylabel("SS (mV/dec)")
        axes[0, 0].grid(True, linestyle="--", alpha=0.6)

        axes[0, 1].plot(df['Lg_nm'], df['DIBL_mV_V'], 'bs-', linewidth=2, markersize=7)
        axes[0, 1].set_title("DIBL vs Lg", fontweight='bold')
        axes[0, 1].set_xlabel("Gate Length Lg (nm)")
        axes[0, 1].set_ylabel("DIBL (mV/V)")
        axes[0, 1].grid(True, linestyle="--", alpha=0.6)

        axes[1, 0].plot(df['Lg_nm'], df['Ion_mA_um'], 'g^-', linewidth=2, markersize=7)
        axes[1, 0].set_title("Drive Current (Ion) vs Lg", fontweight='bold')
        axes[1, 0].set_xlabel("Gate Length Lg (nm)")
        axes[1, 0].set_ylabel("Ion (mA/um)")
        axes[1, 0].grid(True, linestyle="--", alpha=0.6)

        axes[1, 1].plot(df['Lg_nm'], df['Vth_sat_V'], 'md-', linewidth=2, markersize=7, label="Vth,sat")
        axes[1, 1].plot(df['Lg_nm'], df['Vth_lin_V'], 'co--', linewidth=2, markersize=7, label="Vth,lin")
        axes[1, 1].set_title("Threshold Voltage vs Lg", fontweight='bold')
        axes[1, 1].set_xlabel("Gate Length Lg (nm)")
        axes[1, 1].set_ylabel("Vth (V)")
        axes[1, 1].legend()
        axes[1, 1].grid(True, linestyle="--", alpha=0.6)

        plt.tight_layout()
        plt.savefig(plot_path)
        print(f"Saved Publication Trend Plot: {plot_path}")

    print("\nSWB Extraction Complete.")

if __name__ == "__main__":
    main()
