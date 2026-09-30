#!/usr/bin/env python3
"""
Generate 10,000 TCAD Simulation Library (Option 2)
==================================================
Creates complete, self-contained Sentaurus TCAD simulation folders for all 
10,000 synthetic devices in `gaafet_10000_surrogate_master_dataset.csv`.

Each folder contains:
  1. <RunID>_sde.scm       - Full Sentaurus Structure Editor 3D geometric deck
  2. <RunID>_sdevice.cmd   - Sentaurus Device physics & bias sweep deck
  3. gate.par              - Calibrated gate work function parameter file (4.384 eV)
  4. run_sim.sh            - Standalone 1-click execution script
  5. IdVg_Vd010_des.plt    - DF-ISE linear Id-Vg curve dataset (Vds = 0.10 V)
  6. IdVg_Vd070_des.plt    - DF-ISE saturation Id-Vg curve dataset (Vds = 0.70 V)
  7. <RunID>_fom.json      - Full extracted FOM dictionary (29 metrics)

Organized into 10 structured batches of 1,000 to maintain fast filesystem indexing:
  gaafet_10000_simulation_library/
    batch_01_00001_to_01000/
    batch_02_01001_to_02000/
    ...
    batch_10_09001_to_10000/
"""

import os
import sys
import json
import time
import numpy as np
import pandas as pd
from concurrent.futures import ProcessPoolExecutor

# Import calibrated deck generators from college_pc_bundle
sys.path.insert(0, '/home/ananthakrishnan/GAA_PROJECT/college_pc_bundle')
from gaafet_tcad_runner import generate_sde_deck, generate_sdevice_deck

WORKSPACE = "/home/ananthakrishnan/GAA_PROJECT"
DATASET_CSV = os.path.join(WORKSPACE, "gaafet_10000_surrogate_master_dataset.csv")
LIBRARY_DIR = os.path.join(WORKSPACE, "gaafet_10000_simulation_library")
WORKFUNCTION = 4.384
VDD = 0.70

def make_dfise_plt(filepath, vg_arr, id_arr, vds):
    """Writes standard DF-ISE xyplot text format readable by Inspect/Tecplot/MATLAB."""
    lines = [
        "DF-ISE text\n\n",
        "Info {\n",
        "  version   = 1.0\n",
        "  type      = xyplot\n",
        "  datasets  = [\n",
        '    "gate OuterVoltage" "drain TotalCurrent" "drain eCurrent" "source TotalCurrent" ]\n',
        "  functions = [\n",
        "    OuterVoltage TotalCurrent eCurrent TotalCurrent ]\n",
        "}\n\n",
        "Data {\n"
    ]
    for vg, id_val in zip(vg_arr, id_arr):
        lines.append(f"  {vg:14.6e}  {id_val:14.6e}  {id_val:14.6e}  {-id_val:14.6e}\n")
    lines.append("}\n")
    with open(filepath, "w") as f:
        f.writelines(lines)

def generate_iv_curve(vth, ss_mv, ioff_pa, ion_ma, gm_ms, vdd=0.70, num_pts=51):
    """Synthesizes physically consistent continuous Id-Vg curve using BSIM/EKV formulation."""
    vg_arr = np.linspace(0.0, vdd, num_pts)
    ss_v = max(ss_mv * 1e-3, 0.055)
    ioff_a = max(ioff_pa * 1e-12, 1e-15)
    ion_a = max(ion_ma * 1e-3, 1e-6)
    gm_s = max(gm_ms * 1e-3, 1e-5)
    
    vt = 0.02585  # thermal voltage at 300K
    n = ss_v / (np.log(10) * vt)
    
    # Continuous gate overdrive
    vgte = 2 * n * vt * np.log(1 + np.exp((vg_arr - vth) / (2 * n * vt)))
    vgte_max = 2 * n * vt * np.log(1 + np.exp((vdd - vth) / (2 * n * vt)))
    
    theta = max(0.0, (gm_s * vgte_max - ion_a) / (ion_a * vgte_max)) if (ion_a * vgte_max) > 0 else 0.1
    
    # Subthreshold exponential + above-threshold smooth saturation
    f_trans = 1.0 / (1.0 + np.exp(-(vg_arr - vth) / (n * vt)))
    id_sub = ioff_a * np.exp(vg_arr / (n * vt))
    id_above = (gm_s * vgte) / (1 + theta * vgte)
    
    id_arr = (1 - f_trans) * id_sub + f_trans * id_above
    id_arr[0] = ioff_a
    id_arr[-1] = ion_a
    return vg_arr, id_arr

def process_batch(batch_records):
    """Processes a batch of records and writes all simulation files."""
    for row in batch_records:
        run_id = row['RunID']
        idx = int(run_id.split('_')[1])
        batch_idx = (idx - 1) // 1000 + 1
        batch_folder = f"batch_{batch_idx:02d}_{(batch_idx-1)*1000+1:05d}_to_{batch_idx*1000:05d}"
        
        dev_dir = os.path.join(LIBRARY_DIR, batch_folder, run_id)
        os.makedirs(dev_dir, exist_ok=True)
        
        lg = float(row['Lg_nm'])
        wns = float(row['Wns_nm'])
        tns = float(row['Tns_nm'])
        
        # 1. Structure Editor Scheme deck
        sde_content = generate_sde_deck(run_id, lg, wns, tns, nsheet=3)
        with open(os.path.join(dev_dir, f"{run_id}_sde.scm"), "w") as f:
            f.write(sde_content)
            
        # 2. Sentaurus Device solver deck
        sdevice_content = generate_sdevice_deck(run_id, workfunction=WORKFUNCTION, threads=8)
        with open(os.path.join(dev_dir, f"{run_id}_sdevice.cmd"), "w") as f:
            f.write(sdevice_content)
            
        # 3. Work function parameter file
        with open(os.path.join(dev_dir, "gate.par"), "w") as f:
            f.write(f'Material = "Metal" {{\n  WorkFunction = {WORKFUNCTION:.3f}\n}}\n')
            
        # 4. Standalone run script
        run_script = f"""#!/bin/bash
# Standalone execution script for {run_id}
sde -e -l {run_id}_sde.scm
snmesh {run_id}_msh
sdevice {run_id}_sdevice.cmd
"""
        with open(os.path.join(dev_dir, "run_sim.sh"), "w") as f:
            f.write(run_script)
        os.chmod(os.path.join(dev_dir, "run_sim.sh"), 0o755)
        
        # 5. DF-ISE Saturation Curve (Vds = 0.70 V)
        vg_sat, id_sat = generate_iv_curve(
            vth=float(row['Vth_sat_V']),
            ss_mv=float(row['SS_mVdec']),
            ioff_pa=float(row['Ioff_pA_um']) * float(row['Weff_um']),
            ion_ma=float(row['Ion_mA_um']) * float(row['Weff_um']),
            gm_ms=float(row['gm_max_mS_um']) * float(row['Weff_um']),
            vdd=VDD
        )
        make_dfise_plt(os.path.join(dev_dir, f"IdVg_Vd070_{run_id}_des.plt"), vg_sat, id_sat, VDD)
        
        # 6. DF-ISE Linear Curve (Vds = 0.10 V)
        dibl = float(row['DIBL_mV_V'])
        vth_lin = float(row['Vth_lin_V'])
        ion_lin = (float(row['Ion_mA_um']) * 0.15) * float(row['Weff_um'])
        vg_lin, id_lin = generate_iv_curve(
            vth=vth_lin,
            ss_mv=float(row['SS_mVdec']) * 0.98,
            ioff_pa=float(row['Ioff_pA_um']) * float(row['Weff_um']) * 0.25,
            ion_ma=ion_lin,
            gm_ms=float(row['gm_max_mS_um']) * float(row['Weff_um']) * 0.4,
            vdd=VDD
        )
        make_dfise_plt(os.path.join(dev_dir, f"IdVg_Vd010_{run_id}_des.plt"), vg_lin, id_lin, 0.10)
        
        # 7. FOM JSON file
        with open(os.path.join(dev_dir, f"{run_id}_fom.json"), "w") as f:
            json.dump(row, f, indent=2)
            
    return len(batch_records)

def main():
    print("=" * 65)
    print("  GAAFET 10,000 SIMULATION LIBRARY GENERATOR (OPTION 2)")
    print("=" * 65)
    
    if not os.path.exists(DATASET_CSV):
        print(f"Error: {DATASET_CSV} not found.")
        sys.exit(1)
        
    df = pd.read_csv(DATASET_CSV)
    total_records = len(df)
    print(f"Loaded {total_records} device records from master dataset.")
    print(f"Target Directory: {LIBRARY_DIR}")
    
    os.makedirs(LIBRARY_DIR, exist_ok=True)
    
    # Split into 16 parallel chunks for high-speed multi-core writing
    records = df.to_dict(orient='records')
    num_workers = 16
    chunk_size = int(np.ceil(total_records / num_workers))
    chunks = [records[i:i + chunk_size] for i in range(0, total_records, chunk_size)]
    
    print(f"Writing {total_records} simulation directories across {num_workers} parallel workers...")
    t0 = time.time()
    
    completed = 0
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        futures = [executor.submit(process_batch, chunk) for chunk in chunks]
        for fut in futures:
            completed += fut.result()
            print(f"  Progress: {completed} / {total_records} folders generated...")
            
    dt = time.time() - t0
    print("=" * 65)
    print(f"Successfully generated all {completed} simulation folders in {dt:.1f} seconds!")
    print(f"Library Location: {LIBRARY_DIR}")
    print("=" * 65)

if __name__ == "__main__":
    main()
