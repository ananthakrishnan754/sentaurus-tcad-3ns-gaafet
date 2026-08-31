import numpy as np
import pandas as pd
import json
import os

# Set seed for reproducibility
np.random.seed(42)

num_samples = 100

# Input parameter ranges (Physics-informed GAAFET Design Space)
Lg_nm = np.random.uniform(8.0, 16.0, num_samples)          # Gate Length (nm)
Wns_nm = np.random.uniform(10.0, 30.0, num_samples)        # Nanosheet Width (nm)
Tns_nm = np.random.uniform(3.0, 7.0, num_samples)          # Nanosheet Thickness (nm)
Tox_nm = np.random.uniform(0.8, 1.5, num_samples)          # Oxide Thickness (nm)
WorkFunction_eV = np.random.uniform(4.35, 4.75, num_samples)# Work Function (eV)
Nsd_cm3 = 10**np.random.uniform(19.7, 20.3, num_samples)   # S/D Doping (cm^-3)
Nch_cm3 = 10**np.random.uniform(15.0, 17.0, num_samples)   # Channel Doping (cm^-3)

# Analytical Physics Approximation for Baseline FOMs (matching TCAD trends)
# Vth increases with WorkFunction, decreases with short-channel effects (shorter Lg, thicker Tns)
Vth_lin = 0.2 + (WorkFunction_eV - 4.4) - 0.015 * (14.0 - Lg_nm) + 0.01 * (Tns_nm - 4.0) + np.random.normal(0, 0.005, num_samples)
Vth_sat = Vth_lin - (0.05 + 0.005 * (16.0 - Lg_nm)) + np.random.normal(0, 0.003, num_samples)

# Subthreshold Swing (SS) in mV/dec (60 mV/dec thermal limit + short channel penalty)
SS_mVdec = 60.0 + 8.0 * (Tns_nm / Lg_nm) * (Tox_nm / 1.0) + np.random.normal(0, 0.5, num_samples)

# DIBL in mV/V
DIBL_mV_V = 30.0 + 25.0 * (Tns_nm / Lg_nm) + np.random.normal(0, 1.0, num_samples)

# I_OFF (A/um) exponential with Vth
Ioff_A_um = 1e-7 * np.exp(-(Vth_sat - 0.25) / 0.026) + np.random.normal(0, 1e-9, num_samples)
Ioff_A_um = np.clip(Ioff_A_um, 1e-11, 1e-5)

# I_ON (A/um) overdrive current model: ~ (Wns/Lg) * (Vdd - Vth)^1.5
Ion_A_um = 1.2e-3 * (Wns_nm / 15.0) * ((0.70 - Vth_sat) / 0.45)**1.5 * (10.0 / Lg_nm)**0.5 + np.random.normal(0, 5e-5, num_samples)
Ion_A_um = np.clip(Ion_A_um, 1e-4, 5e-3)

Ion_Ioff = Ion_A_um / Ioff_A_um

# Create Pandas DataFrame
df = pd.DataFrame({
    'sample_id': np.arange(1, num_samples + 1),
    'Lg_nm': np.round(Lg_nm, 2),
    'Wns_nm': np.round(Wns_nm, 2),
    'Tns_nm': np.round(Tns_nm, 2),
    'Tox_nm': np.round(Tox_nm, 2),
    'WorkFunction_eV': np.round(WorkFunction_eV, 3),
    'Nsd_cm3': Nsd_cm3,
    'Nch_cm3': Nch_cm3,
    'VTH_lin_V': np.round(Vth_lin, 4),
    'VTH_sat_V': np.round(Vth_sat, 4),
    'SS_mVdec': np.round(SS_mVdec, 2),
    'DIBL_mV_V': np.round(DIBL_mV_V, 2),
    'ION_A_um': Ion_A_um,
    'IOFF_A_um': Ioff_A_um,
    'ION_IOFF': Ion_Ioff
})

csv_path = '/home/ananthakrishnan/GAA_PROJECT/gaafet_dataset_sample.csv'
df.to_csv(csv_path, index=False)
print(f"Generated CSV dataset: {csv_path} ({df.shape[0]} samples, {df.shape[1]} columns)")

# Generate multi-curve JSON dataset format (for deep surrogate / GNN models)
json_dataset = []
vg_sweep = np.linspace(0.0, 0.7, 36) # 0 to 0.7V in steps of 0.02V

for idx, row in df.iterrows():
    vth = row['VTH_sat_V']
    ss = row['SS_mVdec'] / 1000.0 # V/dec
    ioff = row['IOFF_A_um']
    ion = row['ION_A_um']
    
    # ID-VG curve model (Subthreshold log region + Above-threshold square/linear region)
    id_vg = []
    for vg in vg_sweep:
        if vg < vth:
            id_val = ioff * 10**((vg) / ss)
        else:
            id_val = ioff * 10**(vth / ss) + (ion - ioff * 10**(vth / ss)) * ((vg - vth)/(0.7 - vth))**1.5
        id_vg.append(float(id_val))
        
    sample_entry = {
        'sample_id': int(row['sample_id']),
        'design_parameters': {
            'Lg_nm': float(row['Lg_nm']),
            'Wns_nm': float(row['Wns_nm']),
            'Tns_nm': float(row['Tns_nm']),
            'Tox_nm': float(row['Tox_nm']),
            'WorkFunction_eV': float(row['WorkFunction_eV']),
            'Nsd_cm3': float(row['Nsd_cm3']),
            'Nch_cm3': float(row['Nch_cm3'])
        },
        'figures_of_merit': {
            'VTH_lin_V': float(row['VTH_lin_V']),
            'VTH_sat_V': float(row['VTH_sat_V']),
            'SS_mVdec': float(row['SS_mVdec']),
            'DIBL_mV_V': float(row['DIBL_mV_V']),
            'ION_A_um': float(row['ION_A_um']),
            'IOFF_A_um': float(row['IOFF_A_um']),
            'ION_IOFF': float(row['ION_IOFF'])
        },
        'curves': {
            'VGS_V': vg_sweep.tolist(),
            'ID_A_um': id_vg
        }
    }
    json_dataset.append(sample_entry)

json_path = '/home/ananthakrishnan/GAA_PROJECT/gaafet_dataset_sample.json'
with open(json_path, 'w') as f:
    json.dump(json_dataset, f, indent=2)

print(f"Generated JSON multi-curve dataset: {json_path}")
