#!/usr/bin/env python3
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

MASTER_CSV = '/home/ananthakrishnan/GAA_PROJECT/industry_calibrated_doe_vth0p25/gaafet_tcad_master_dataset.csv'
WORKSPACE_DIR = '/home/ananthakrishnan/GAA_PROJECT'
ARTIFACT_DIR = '/home/ananthakrishnan/.gemini/antigravity-ide/brain/a75710c9-0747-449e-95e8-db4faf5b61b4'

df = pd.read_csv(MASTER_CSV)
n_runs = len(df)
print(f"Loaded master dataset: {n_runs} runs.")

# ==========================================
# 1. Correlation Matrix Heatmap (216 Runs)
# ==========================================
features = ['Lg_nm', 'Wns_nm', 'Tns_nm', 'Weff_um', 'Vth_lin_V', 'Vth_sat_V', 
            'SS_mVdec', 'DIBL_mV_V', 'Ion_mA_um', 'logIoff', 'gm_max_mS_um', 'tau_int_ps', 'logIonIoff']
labels = ['Lg', 'Wns', 'Tns', 'Weff', 'Vth,lin', 'Vth,sat', 'SS', 'DIBL', 'Ion', 'log(Ioff)', 'gm,max', 'tau_int', 'log(Ion/Ioff)']

corr = df[features].corr().values

fig, ax = plt.subplots(figsize=(10, 8), dpi=300)
cax = ax.imshow(corr, cmap='RdBu_r', vmin=-1, vmax=1)
cbar = fig.colorbar(cax, fraction=0.046, pad=0.04)
cbar.set_label('Pearson Correlation Coefficient (r)', fontsize=11, fontweight='bold')

ax.set_xticks(range(len(labels)))
ax.set_yticks(range(len(labels)))
ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=10, fontweight='bold')
ax.set_yticklabels(labels, fontsize=10, fontweight='bold')

for i in range(len(labels)):
    for j in range(len(labels)):
        val = corr[i, j]
        color = 'white' if abs(val) > 0.55 else 'black'
        ax.text(j, i, f'{val:.2f}', ha='center', va='center', color=color, fontsize=8, fontweight='bold')

ax.set_title(f'GAAFET 3-Stack Nanosheet: Full Correlation Matrix ({n_runs} TCAD Runs)', fontsize=13, fontweight='bold', pad=15)
plt.tight_layout()

out_heatmap_ws = os.path.join(WORKSPACE_DIR, 'gaafet_correlation_matrix_heatmap.png')
out_heatmap_art = os.path.join(ARTIFACT_DIR, 'gaafet_correlation_matrix_heatmap.png')
plt.savefig(out_heatmap_ws, dpi=300)
plt.savefig(out_heatmap_art, dpi=300)
plt.close()
print("Heatmap saved.")

# ==========================================
# 2. 6-Panel PPA Optimization Dashboard
# ==========================================
fig, axes = plt.subplots(2, 3, figsize=(18, 11), dpi=300)
plt.subplots_adjust(hspace=0.32, wspace=0.28)

# Panel 1: Ion vs Ioff (Pareto Frontier & Operating Zones)
ax = axes[0, 0]
sc = ax.scatter(df['Ion_mA_um'], df['logIoff'], c=df['Tns_nm'], cmap='viridis', s=45, alpha=0.85, edgecolors='k', linewidth=0.5)
cbar = plt.colorbar(sc, ax=ax)
cbar.set_label('Tns (nm)', fontsize=9, fontweight='bold')
ax.axhline(np.log10(5000), color='r', linestyle='--', alpha=0.7, label='Ioff = 5 nA/um max (SP)')
ax.axvline(0.95, color='b', linestyle='--', alpha=0.7, label='Ion = 0.95 mA/um min (SP)')
ax.scatter([0.960], [np.log10(2398)], color='red', marker='*', s=200, label='Recommended SP (L12_W30_T04)', zorder=5)
ax.set_title('1. Ion vs Ioff Pareto Space & Zones', fontweight='bold', fontsize=11)
ax.set_xlabel('Ion (mA/um)', fontweight='bold')
ax.set_ylabel('log10(Ioff in pA/um)', fontweight='bold')
ax.grid(True, linestyle=':', alpha=0.6)
ax.legend(fontsize=8, loc='upper left')

# Panel 2: SS vs DIBL
ax = axes[0, 1]
sc2 = ax.scatter(df['DIBL_mV_V'], df['SS_mVdec'], c=df['Lg_nm'], cmap='plasma', s=45, alpha=0.85, edgecolors='k', linewidth=0.5)
cbar2 = plt.colorbar(sc2, ax=ax)
cbar2.set_label('Lg (nm)', fontsize=9, fontweight='bold')
ax.axvline(35, color='r', linestyle='--', alpha=0.7, label='DIBL = 35 mV/V max')
ax.axhline(65, color='g', linestyle='--', alpha=0.7, label='SS = 65 mV/dec max')
ax.scatter([28.61], [62.74], color='red', marker='*', s=200, label='Recommended SP', zorder=5)
ax.set_title('2. Electrostatic Integrity: SS vs DIBL', fontweight='bold', fontsize=11)
ax.set_xlabel('DIBL (mV/V)', fontweight='bold')
ax.set_ylabel('Subthreshold Swing SS (mV/dec)', fontweight='bold')
ax.grid(True, linestyle=':', alpha=0.6)
ax.legend(fontsize=8, loc='upper left')

# Panel 3: Tns Scaling
ax = axes[0, 2]
tns_summary = df.groupby('Tns_nm')[['Vth_lin_V', 'Vth_sat_V', 'DIBL_mV_V']].mean()
ax.plot(tns_summary.index, tns_summary['Vth_lin_V'], 'o-', color='#1f77b4', linewidth=2, label='Mean Vth,lin (V)')
ax.plot(tns_summary.index, tns_summary['Vth_sat_V'], 's--', color='#ff7f0e', linewidth=2, label='Mean Vth,sat (V)')
ax.set_xlabel('Nanosheet Thickness Tns (nm)', fontweight='bold')
ax.set_ylabel('Threshold Voltage (V)', fontweight='bold', color='#1f77b4')
ax.tick_params(axis='y', labelcolor='#1f77b4')
ax.grid(True, linestyle=':', alpha=0.6)

ax_dibl = ax.twinx()
ax_dibl.plot(tns_summary.index, tns_summary['DIBL_mV_V'], '^-.', color='#d62728', linewidth=2, label='Mean DIBL (mV/V)')
ax_dibl.set_ylabel('DIBL (mV/V)', fontweight='bold', color='#d62728')
ax_dibl.tick_params(axis='y', labelcolor='#d62728')
ax.set_title('3. Tns Scaling: Threshold & DIBL Roll-off', fontweight='bold', fontsize=11)

lines1, labels1 = ax.get_legend_handles_labels()
lines2, labels2 = ax_dibl.get_legend_handles_labels()
ax.legend(lines1 + lines2, labels1 + labels2, fontsize=8, loc='center left')

# Panel 4: Lg Scaling
ax = axes[1, 0]
lg_summary = df.groupby('Lg_nm')[['tau_int_ps', 'SS_mVdec']].mean()
ax.plot(lg_summary.index, lg_summary['tau_int_ps'], 'o-', color='#2ca02c', linewidth=2, label='Intrinsic Delay tau_int (ps)')
ax.set_xlabel('Gate Length Lg (nm)', fontweight='bold')
ax.set_ylabel('Intrinsic Delay (ps)', fontweight='bold', color='#2ca02c')
ax.tick_params(axis='y', labelcolor='#2ca02c')
ax.grid(True, linestyle=':', alpha=0.6)

ax_ss = ax.twinx()
ax_ss.plot(lg_summary.index, lg_summary['SS_mVdec'], 's--', color='#9467bd', linewidth=2, label='Mean SS (mV/dec)')
ax_ss.set_ylabel('SS (mV/dec)', fontweight='bold', color='#9467bd')
ax_ss.tick_params(axis='y', labelcolor='#9467bd')
ax.set_title('4. Lg Scaling: Speed vs Gate Control', fontweight='bold', fontsize=11)

lines1, labels1 = ax.get_legend_handles_labels()
lines2, labels2 = ax_ss.get_legend_handles_labels()
ax.legend(lines1 + lines2, labels1 + labels2, fontsize=8, loc='center left')

# Panel 5: Wns Scaling
ax = axes[1, 1]
df['Ion_total_mA'] = df['Ion_mA_um'] * df['Weff_um']
wns_summary = df.groupby('Wns_nm')[['Ion_total_mA', 'Ion_mA_um']].mean()
ax.plot(wns_summary.index, wns_summary['Ion_total_mA'], 'o-', color='#8c564b', linewidth=2, label='Total 3-Stack Current (mA)')
ax.set_xlabel('Nanosheet Width Wns (nm)', fontweight='bold')
ax.set_ylabel('Absolute Current per Device (mA)', fontweight='bold', color='#8c564b')
ax.tick_params(axis='y', labelcolor='#8c564b')
ax.grid(True, linestyle=':', alpha=0.6)

ax_norm = ax.twinx()
ax_norm.plot(wns_summary.index, wns_summary['Ion_mA_um'], 'x--', color='#e377c2', linewidth=2, label='Normalized Ion (mA/um)')
ax_norm.set_ylabel('Normalized Ion (mA/um)', fontweight='bold', color='#e377c2')
ax_norm.tick_params(axis='y', labelcolor='#e377c2')
ax.set_title('5. Wns Scaling: Drivability & Density', fontweight='bold', fontsize=11)

l1, lab1 = ax.get_legend_handles_labels()
l2, lab2 = ax_norm.get_legend_handles_labels()
ax.legend(l1 + l2, lab1 + lab2, fontsize=8, loc='center left')

# Panel 6: Optimal Design Window
ax = axes[1, 2]
p_data = df.groupby(['Lg_nm', 'Tns_nm'])['Vth_lin_V'].mean().unstack()
im = ax.imshow(p_data.values, cmap='coolwarm', origin='lower', aspect='auto', extent=[2.5, 8.5, 9, 21])
cbar3 = plt.colorbar(im, ax=ax)
cbar3.set_label('Mean Vth,lin (V)', fontsize=9, fontweight='bold')
ax.set_xticks([3, 4, 5, 6, 7, 8])
ax.set_yticks([10, 12, 14, 16, 18, 20])
ax.set_xlabel('Nanosheet Thickness Tns (nm)', fontweight='bold')
ax.set_ylabel('Gate Length Lg (nm)', fontweight='bold')
ax.set_title('6. Final Fixing Window: Lg vs Tns', fontweight='bold', fontsize=11)

rect = plt.Rectangle((3.5, 11), 1.0, 3.0, fill=False, edgecolor='gold', linewidth=3, linestyle='--', label='Optimal Window (Tns=4nm, Lg=12-14nm)')
ax.add_patch(rect)
ax.scatter([4], [12], color='red', marker='*', s=250, label='Recommended Geometry (L12_W30_T04)', zorder=6)
ax.legend(fontsize=8, loc='upper left')

plt.suptitle(f'GAAFET 3-Stack Nanosheet: Design Space Sensitivity & Multi-Objective Geometry Optimization ({n_runs} Runs)', fontsize=14, fontweight='bold', y=0.98)
plt.tight_layout()

out_dash_ws = os.path.join(WORKSPACE_DIR, 'gaafet_comprehensive_ppa_optimization_dashboard.png')
out_dash_art = os.path.join(ARTIFACT_DIR, 'gaafet_comprehensive_ppa_optimization_dashboard.png')
plt.savefig(out_dash_ws, dpi=300)
plt.savefig(out_dash_art, dpi=300)
plt.close()
print("PPA Dashboard saved.")
