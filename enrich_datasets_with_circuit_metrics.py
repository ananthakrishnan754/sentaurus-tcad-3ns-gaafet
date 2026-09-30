#!/usr/bin/env python3
"""
Enrich GAAFET Datasets with Electrical, Timing, and RF Parameters
================================================================
Calculates and appends standard industry PPA, timing, and RF metrics:
- Ron_Ohm_um: DC On-state resistance (Ohm*um)
- Reff_Ohm_um: Effective switching resistance (Ohm*um)
- Ron_cell_kOhm: Total 3-nanosheet cell resistance (kOhm)
- tau_RC_ps: Effective gate RC switching delay (ps)
- tau_FO4_ps: Estimated Fanout-of-4 logic delay (ps)
- fT_GHz: Unity-gain cut-off frequency (GHz)
- PDP_fJ_um: Dynamic switching energy per cycle / Power-Delay Product (fJ/um)
- EDP_fJ_ps_um: Energy-Delay Product (fJ*ps/um)
- Av_gain_dB: Small-signal intrinsic voltage gain (dB)
"""

import os
import numpy as np
import pandas as pd

VDD = 0.70  # Nominal supply voltage (V)

TCAD_216_PATH = "/home/ananthakrishnan/GAA_PROJECT/industry_calibrated_doe_vth0p25/gaafet_tcad_master_dataset.csv"
SURROGATE_10K_PATH = "/home/ananthakrishnan/GAA_PROJECT/gaafet_10000_surrogate_master_dataset.csv"

def compute_metrics(df):
    # Ensure Weff is computed if missing
    if 'Weff_um' not in df.columns:
        df['Weff_um'] = 3 * 2 * (df['Wns_nm'] + df['Tns_nm']) * 1e-3

    # Total cell current (mA)
    if 'Ion_total_mA' not in df.columns:
        df['Ion_total_mA'] = (df['Ion_mA_um'] * df['Weff_um']).round(4)

    # 1. On-Resistance (Ohm*um): VDD / (Ion in A/um)
    df['Ron_Ohm_um'] = (VDD / (df['Ion_mA_um'] * 1e-3)).round(2)

    # 2. Effective Switching Resistance (Ohm*um): ITRS / BSIM convention ~ 0.5 * Ron
    df['Reff_Ohm_um'] = (0.5 * df['Ron_Ohm_um']).round(2)

    # 3. Total Cell Resistance (kOhm): VDD / (Ion_total in A) / 1000
    df['Ron_cell_kOhm'] = (VDD / (df['Ion_total_mA'] * 1e-3) / 1000).round(3)

    # 4. Effective gate RC delay (ps): Reff * Cgg
    # Reff in Ohm*um, Cgg in fF/um -> Reff * Cgg * 1e-15 s = Reff * Cgg * 1e-3 ps
    # Notice Reff * Cgg = (0.5 * VDD / Ion) * Cgg = 0.5 * tau_int!
    df['tau_RC_ps'] = (0.5 * df['tau_int_ps']).round(4)

    # 5. Estimated Fanout-of-4 Inverter Delay (ps): ~ 3.5 * tau_int
    df['tau_FO4_ps'] = (3.5 * df['tau_int_ps']).round(3)

    # 6. Unity Cut-off Frequency (GHz): gm / (2 * pi * Cgg)
    # gm in mS/um = 1e-3 S/um, Cgg in fF/um = 1e-15 F/um
    # fT = (gm * 1e-3) / (2 * pi * Cgg * 1e-15) = (gm / (2 * pi * Cgg)) * 1000 GHz
    df['fT_GHz'] = ((df['gm_max_mS_um'] / (2 * np.pi * df['Cgg_fF_um'])) * 1000).round(2)

    # 7. Power-Delay Product (fJ/um): Cgg * VDD^2
    # Cgg in fF/um, VDD in V -> fJ/um
    df['PDP_fJ_um'] = (df['Cgg_fF_um'] * (VDD ** 2)).round(4)

    # 8. Energy-Delay Product (fJ*ps/um): PDP * tau_int
    df['EDP_fJ_ps_um'] = (df['PDP_fJ_um'] * df['tau_int_ps']).round(4)

    # 9. Intrinsic Voltage Gain (dB): 20 * log10(gm / gds)
    av_linear = df['gm_max_mS_um'] / df['gds_mS_um']
    df['Av_gain_dB'] = (20 * np.log10(av_linear)).round(2)

    return df

def main():
    print("--- Enriching 216-Run TCAD Master Dataset ---")
    if os.path.exists(TCAD_216_PATH):
        df_216 = pd.read_csv(TCAD_216_PATH)
        df_216 = compute_metrics(df_216)
        df_216.to_csv(TCAD_216_PATH, index=False)
        print(f"Updated {TCAD_216_PATH} with {len(df_216)} rows and {len(df_216.columns)} columns.")
    else:
        print(f"Warning: {TCAD_216_PATH} not found.")

    print("\n--- Enriching 10,000-Point Surrogate Master Dataset ---")
    if os.path.exists(SURROGATE_10K_PATH):
        df_10k = pd.read_csv(SURROGATE_10K_PATH)
        df_10k = compute_metrics(df_10k)
        df_10k.to_csv(SURROGATE_10K_PATH, index=False)
        print(f"Updated {SURROGATE_10K_PATH} with {len(df_10k)} rows and {len(df_10k.columns)} columns.")
    else:
        print(f"Warning: {SURROGATE_10K_PATH} not found.")

    print("\nSample Preview of Computed Circuit & RF Parameters (216 TCAD):")
    sample_cols = ['RunID', 'Lg_nm', 'Wns_nm', 'Tns_nm', 'Ron_Ohm_um', 'Reff_Ohm_um', 'tau_RC_ps', 'tau_FO4_ps', 'fT_GHz', 'PDP_fJ_um', 'EDP_fJ_ps_um', 'Av_gain_dB']
    print(df_216[sample_cols].head(5).to_string())

if __name__ == "__main__":
    main()
