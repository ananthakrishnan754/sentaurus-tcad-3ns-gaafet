#!/usr/bin/env python3
"""
GAAFET Physical TCAD Cross-Verification Runner
==============================================
Simulates unseen intermediate validation geometries using Sentaurus TCAD
and compares the ground-truth simulation results against the surrogate model.
"""

import os
import sys
import json
import time
import shutil
import subprocess
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from concurrent.futures import ProcessPoolExecutor, as_completed

# Add college_pc_bundle to python path
sys.path.insert(0, '/home/ananthakrishnan/GAA_PROJECT/college_pc_bundle')
from gaafet_tcad_runner import generate_sde_deck, generate_sdevice_deck, extract_device_fom

WORKSPACE_DIR = "/home/ananthakrishnan/GAA_PROJECT"
VERIFY_CSV = os.path.join(WORKSPACE_DIR, "gaafet_verification_10_points.csv")
OUT_DIR = os.path.join(WORKSPACE_DIR, "industry_calibrated_doe_vth0p25/verification_runs")
RESULTS_CSV = os.path.join(WORKSPACE_DIR, "gaafet_verification_tcad_results.csv")
PLOT_PATH = os.path.join(WORKSPACE_DIR, "gaafet_tcad_vs_surrogate_cross_verification.png")

WORKFUNCTION = 4.384
PARALLEL_JOBS = 2
THREADS_PER_JOB = 8

os.makedirs(OUT_DIR, exist_ok=True)

def run_single_verification(row):
    run_id = row['RunID']
    lg = float(row['Lg_nm'])
    wns = float(row['Wns_nm'])
    tns = float(row['Tns_nm'])
    
    run_dir = os.path.join(OUT_DIR, run_id)
    os.makedirs(run_dir, exist_ok=True)
    json_path = os.path.join(run_dir, f"{run_id}_fom.json")
    
    # Check if already completed
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r') as jf:
                fom = json.load(jf)
            if fom.get("convergence_flag") == "PASS":
                print(f"[CACHED] {run_id} already simulated.")
                return {"RunID": run_id, "status": "SUCCESS", "fom": fom}
        except Exception:
            pass

    # Gate parameter file
    with open(os.path.join(run_dir, "gate.par"), "w") as gf:
        gf.write(f"""Material = "Metal" {{
    Bandgap {{
        WorkFunction = {WORKFUNCTION:.3f}
        FermiEnergy = 11.7
    }}
}}
""")

    # 1. SDE Geometry & Mesh Generation
    sde_path = os.path.join(run_dir, f"{run_id}_sde.scm")
    with open(sde_path, "w") as sf:
        sf.write(generate_sde_deck(run_id, lg, wns, tns))
        
    log_file = os.path.join(run_dir, "run_console.log")
    with open(log_file, "w") as out:
        out.write(f"--- Starting TCAD Verification for {run_id} (Lg={lg}, Wns={wns}, Tns={tns}) ---\n")
        out.flush()
        
        # Run SDE
        subprocess.run(["sde", "-e", "-l", f"{run_id}_sde.scm"], cwd=run_dir, stdout=out, stderr=subprocess.STDOUT)
        
        # 2. SDevice Simulation
        sdev_path = os.path.join(run_dir, f"{run_id}_sdevice.cmd")
        with open(sdev_path, "w") as df:
            df.write(generate_sdevice_deck(run_id, workfunction=WORKFUNCTION, threads=THREADS_PER_JOB))
            
        subprocess.run(["sdevice", f"{run_id}_sdevice.cmd"], cwd=run_dir, stdout=out, stderr=subprocess.STDOUT)

    # 3. Extract FOM
    fom = extract_device_fom(run_dir, run_id, lg, wns, tns)
    if fom and fom.get("convergence_flag") == "PASS":
        with open(json_path, "w") as jf:
            json.dump(fom, jf, indent=2)
        print(f"[SUCCESS] {run_id} simulated and FOM extracted.")
        return {"RunID": run_id, "status": "SUCCESS", "fom": fom}
    else:
        print(f"[FAIL] {run_id} simulation failed.")
        return {"RunID": run_id, "status": "FAIL", "fom": None}

def main():
    if not os.path.exists(VERIFY_CSV):
        print(f"Error: {VERIFY_CSV} not found.")
        return

    df_points = pd.read_csv(VERIFY_CSV)
    print(f"Loaded {len(df_points)} verification test geometries.")
    
    rows = [row for _, row in df_points.iterrows()]
    results = []

    print(f"Launching simulations across {PARALLEL_JOBS} parallel workers ({THREADS_PER_JOB} threads each)...")
    with ProcessPoolExecutor(max_workers=PARALLEL_JOBS) as executor:
        futures = {executor.submit(run_single_verification, r): r['RunID'] for r in rows}
        for future in as_completed(futures):
            res = future.result()
            results.append(res)

    # Compile comparison
    verified_data = []
    for r in results:
        if r['status'] == "SUCCESS" and r['fom']:
            fom = r['fom']
            run_id = r['RunID']
            orig_row = df_points[df_points['RunID'] == run_id].iloc[0]
            
            entry = {
                "RunID": run_id,
                "Lg_nm": orig_row['Lg_nm'],
                "Wns_nm": orig_row['Wns_nm'],
                "Tns_nm": orig_row['Tns_nm'],
                "Weff_um": orig_row['Weff_um'],
                
                # TCAD Ground Truth
                "Vth_lin_TCAD": fom['Vth_lin_V'],
                "Ion_TCAD": fom['Ion_mA_um'],
                "SS_TCAD": fom['SS_mVdec'],
                "DIBL_TCAD": fom['DIBL_mV_V'],
                
                # Surrogate Prediction
                "Vth_lin_PRED": orig_row['Vth_lin_V_pred'],
                "Ion_PRED": orig_row['Ion_mA_um_pred'],
                "SS_PRED": orig_row['SS_mVdec_pred'],
                "DIBL_PRED": orig_row['DIBL_mV_V_pred'],
                
                # Percentage Errors
                "Vth_Error_pct": abs(orig_row['Vth_lin_V_pred'] - fom['Vth_lin_V']) / fom['Vth_lin_V'] * 100,
                "Ion_Error_pct": abs(orig_row['Ion_mA_um_pred'] - fom['Ion_mA_um']) / fom['Ion_mA_um'] * 100,
                "SS_Error_pct": abs(orig_row['SS_mVdec_pred'] - fom['SS_mVdec']) / fom['SS_mVdec'] * 100,
                "DIBL_Error_pct": abs(orig_row['DIBL_mV_V_pred'] - fom['DIBL_mV_V']) / fom['DIBL_mV_V'] * 100,
            }
            verified_data.append(entry)

    df_res = pd.DataFrame(verified_data)
    df_res.to_csv(RESULTS_CSV, index=False)
    print(f"Results saved to: {RESULTS_CSV}")
    
    # Print Error Summary
    print("\n" + "=" * 60)
    print("  PHYSICAL TCAD CROSS-VERIFICATION ERROR REPORT")
    print("=" * 60)
    print(f"Mean Vth,lin Error : {df_res['Vth_Error_pct'].mean():.2f}%")
    print(f"Mean Ion Drive Error: {df_res['Ion_Error_pct'].mean():.2f}%")
    print(f"Mean SS Swing Error : {df_res['SS_Error_pct'].mean():.2f}%")
    print(f"Mean DIBL Error    : {df_res['DIBL_Error_pct'].mean():.2f}%")
    print("=" * 60)

    # 4. Generate Publication Parity & Error Plot
    print("\nGenerating Cross-Verification Parity Plot...")
    fig, axes = plt.subplots(2, 2, figsize=(14, 11), dpi=300)

    # Panel 1: Vth,lin Parity
    ax1 = axes[0, 0]
    ax1.scatter(df_res['Vth_lin_TCAD'], df_res['Vth_lin_PRED'], color='#2b6cb0', s=90, edgecolors='k', zorder=5, label='Verification Points')
    min_v = min(df_res['Vth_lin_TCAD'].min(), df_res['Vth_lin_PRED'].min()) - 0.005
    max_v = max(df_res['Vth_lin_TCAD'].max(), df_res['Vth_lin_PRED'].max()) + 0.005
    ax1.plot([min_v, max_v], [min_v, max_v], 'r--', linewidth=2, label='Ideal 1:1 Parity')
    ax1.fill_between([min_v, max_v], [min_v*0.985, max_v*0.985], [min_v*1.015, max_v*1.015], color='red', alpha=0.1, label='±1.5% Error Window')
    ax1.set_xlabel('Sentaurus TCAD Ground Truth Vth,lin (V)', fontweight='bold')
    ax1.set_ylabel('Surrogate Model Predicted Vth,lin (V)', fontweight='bold')
    ax1.set_title(f'1. Linear Threshold Parity (Mean Error: {df_res["Vth_Error_pct"].mean():.2f}%)', fontweight='bold', fontsize=11)
    ax1.grid(True, linestyle=':', alpha=0.6)
    ax1.legend(loc='upper left', fontsize=8)

    # Panel 2: Ion Drive Current Parity
    ax2 = axes[0, 1]
    ax2.scatter(df_res['Ion_TCAD'], df_res['Ion_PRED'], color='#38a169', s=90, edgecolors='k', zorder=5, label='Verification Points')
    min_i = min(df_res['Ion_TCAD'].min(), df_res['Ion_PRED'].min()) - 0.02
    max_i = max(df_res['Ion_TCAD'].max(), df_res['Ion_PRED'].max()) + 0.02
    ax2.plot([min_i, max_i], [min_i, max_i], 'r--', linewidth=2, label='Ideal 1:1 Parity')
    ax2.fill_between([min_i, max_i], [min_i*0.985, max_i*0.985], [min_i*1.015, max_i*1.015], color='green', alpha=0.1, label='±1.5% Error Window')
    ax2.set_xlabel('Sentaurus TCAD Ground Truth Ion (mA/µm)', fontweight='bold')
    ax2.set_ylabel('Surrogate Model Predicted Ion (mA/µm)', fontweight='bold')
    ax2.set_title(f'2. Drive Current Parity (Mean Error: {df_res["Ion_Error_pct"].mean():.2f}%)', fontweight='bold', fontsize=11)
    ax2.grid(True, linestyle=':', alpha=0.6)
    ax2.legend(loc='upper left', fontsize=8)

    # Panel 3: Subthreshold Swing Parity
    ax3 = axes[1, 0]
    ax3.scatter(df_res['SS_TCAD'], df_res['SS_PRED'], color='#dd6b20', s=90, edgecolors='k', zorder=5, label='Verification Points')
    min_s = min(df_res['SS_TCAD'].min(), df_res['SS_PRED'].min()) - 0.5
    max_s = max(df_res['SS_TCAD'].max(), df_res['SS_PRED'].max()) + 0.5
    ax3.plot([min_s, max_s], [min_s, max_s], 'r--', linewidth=2, label='Ideal 1:1 Parity')
    ax3.fill_between([min_s, max_s], [min_s*0.985, max_s*0.985], [min_s*1.015, max_s*1.015], color='orange', alpha=0.1, label='±1.5% Error Window')
    ax3.set_xlabel('Sentaurus TCAD Ground Truth SS (mV/dec)', fontweight='bold')
    ax3.set_ylabel('Surrogate Model Predicted SS (mV/dec)', fontweight='bold')
    ax3.set_title(f'3. Subthreshold Swing Parity (Mean Error: {df_res["SS_Error_pct"].mean():.2f}%)', fontweight='bold', fontsize=11)
    ax3.grid(True, linestyle=':', alpha=0.6)
    ax3.legend(loc='upper left', fontsize=8)

    # Panel 4: Error Breakdown Bar Chart across Unseen Geometries
    ax4 = axes[1, 1]
    x_pos = np.arange(len(df_res))
    width = 0.22
    ax4.bar(x_pos - 1.5*width, df_res['Vth_Error_pct'], width, label='Vth Error (%)', color='#2b6cb0')
    ax4.bar(x_pos - 0.5*width, df_res['Ion_Error_pct'], width, label='Ion Error (%)', color='#38a169')
    ax4.bar(x_pos + 0.5*width, df_res['SS_Error_pct'], width, label='SS Error (%)', color='#dd6b20')
    ax4.bar(x_pos + 1.5*width, df_res['DIBL_Error_pct'], width, label='DIBL Error (%)', color='#805ad5')
    ax4.axhline(1.5, color='red', linestyle='--', linewidth=1.5, label='1.5% Target Threshold')
    ax4.set_xticks(x_pos)
    ax4.set_xticklabels([r.replace("V_", "") for r in df_res['RunID']], rotation=45, ha='right', fontsize=8)
    ax4.set_ylabel('Percentage Error Relative to TCAD (%)', fontweight='bold')
    ax4.set_title('4. Error Percentage Across Unseen Test Geometries', fontweight='bold', fontsize=11)
    ax4.grid(True, linestyle=':', alpha=0.6)
    ax4.legend(loc='upper right', fontsize=7.5)

    plt.suptitle('GAAFET Multi-Fidelity Cross-Verification: Sentaurus TCAD vs. Surrogate Model', fontsize=14, fontweight='bold', y=0.98)
    plt.tight_layout()

    plt.savefig(PLOT_PATH, dpi=300)
    art_path = os.path.join("/home/ananthakrishnan/.gemini/antigravity-ide/brain/a75710c9-0747-449e-95e8-db4faf5b61b4", "gaafet_tcad_vs_surrogate_cross_verification.png")
    plt.savefig(art_path, dpi=300)
    plt.close()
    print(f"Plot saved successfully to: {PLOT_PATH}")

if __name__ == "__main__":
    main()
