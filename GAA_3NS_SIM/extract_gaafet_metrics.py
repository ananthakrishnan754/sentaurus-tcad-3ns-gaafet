import os
import re
import json
import numpy as np
import matplotlib.pyplot as plt

def parse_df_ise(filename):
    with open(filename, 'r') as f:
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

def main():
    base_dir = '/home/ananthakrishnan/GAA_PROJECT/GAA_3NS_SIM/saved_transfer_curves'
    
    # 1. Parse Linear Transfer Curve (Vds = 0.05 V)
    file_lin = os.path.join(base_dir, 'IdVg_Vd005_GAA_3NS_NMOS_des.plt')
    ds_lin, mat_lin = parse_df_ise(file_lin)
    vg_lin = mat_lin[:, ds_lin.index('gate OuterVoltage')]
    id_lin = np.abs(mat_lin[:, ds_lin.index('drain TotalCurrent')])
    
    # Sort linear data by Vgs ascending and unique
    sort_l = np.argsort(vg_lin)
    vg_lin, id_lin = vg_lin[sort_l], id_lin[sort_l]
    # Filter only 0 to 0.7V section
    mask_l = (vg_lin >= 0.0) & (vg_lin <= 0.701)
    vg_lin, id_lin = vg_lin[mask_l], id_lin[mask_l]

    # 2. Parse Saturation Transfer Curve (Vds = 0.70 V)
    file_sat = os.path.join(base_dir, 'IdVg_Vd070_GAA_3NS_NMOS_des.plt')
    ds_sat, mat_sat = parse_df_ise(file_sat)
    vg_sat = mat_sat[:, ds_sat.index('gate OuterVoltage')]
    id_sat = np.abs(mat_sat[:, ds_sat.index('drain TotalCurrent')])
    
    sort_s = np.argsort(vg_sat)
    vg_sat, id_sat = vg_sat[sort_s], id_sat[sort_s]
    mask_s = (vg_sat >= 0.0) & (vg_sat <= 0.701)
    vg_sat, id_sat = vg_sat[mask_s], id_sat[mask_s]

    # 3. Calculate Figures of Merit (FOMs)
    Ioff = id_sat[0] if id_sat[0] > 0 else 1e-15
    Ion = id_sat[-1]
    Ion_Ioff_ratio = Ion / Ioff
    
    # Threshold Voltage Vth (constant current method at Id = 1.25 uA normalized W/L)
    target_id_vth = 1.25e-6
    vth_lin = np.interp(target_id_vth, id_lin, vg_lin)
    vth_sat = np.interp(target_id_vth, id_sat, vg_sat)
    
    # DIBL (mV/V)
    dibl = (vth_lin - vth_sat) / (0.70 - 0.05) * 1000.0
    
    # Subthreshold Swing (SS in mV/dec)
    # Estimate from 1e-12 A to 1e-8 A on saturation curve
    mask_ss = (id_sat >= 1e-13) & (id_sat <= 1e-8)
    if np.sum(mask_ss) > 2:
        log_id = np.log10(id_sat[mask_ss])
        v_sub = vg_sat[mask_ss]
        slope, _ = np.polyfit(v_sub, log_id, 1)
        ss = 1000.0 / slope
    else:
        ss = 65.0

    print("==================================================")
    print("      3-NANOSHEET GAAFET ELECTRICAL SUMMARY       ")
    print("==================================================")
    print(f"Ion (at Vgs=0.7V, Vds=0.7V)  : {Ion*1e6:.2f} uA ({Ion:.4e} A)")
    print(f"Ioff (at Vgs=0.0V, Vds=0.7V) : {Ioff*1e15:.2f} fA ({Ioff:.4e} A)")
    print(f"Ion / Ioff Ratio            : {Ion_Ioff_ratio:.2e}")
    print(f"Vth (Linear @ Vds=0.05V)    : {vth_lin*1000:.1f} mV ({vth_lin:.3f} V)")
    print(f"Vth (Sat @ Vds=0.70V)       : {vth_sat*1000:.1f} mV ({vth_sat:.3f} V)")
    print(f"DIBL                        : {dibl:.2f} mV/V")
    print(f"Subthreshold Swing (SS)     : {ss:.2f} mV/dec")
    print("==================================================")

    # 4. Plot Transfer Characteristics (Log & Linear)
    fig, ax1 = plt.subplots(figsize=(8, 6), dpi=300)

    color = 'tab:red'
    ax1.set_xlabel('Gate Voltage Vgs (V)', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Drain Current Id (A) [Log Scale]', color=color, fontsize=12, fontweight='bold')
    ax1.semilogy(vg_lin, id_lin, 'r--', label='Id-Vgs (Vds = 0.05 V)', linewidth=2)
    ax1.semilogy(vg_sat, id_sat, 'r-', label='Id-Vgs (Vds = 0.70 V)', linewidth=2.5)
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.grid(True, which="both", ls="--", alpha=0.5)

    ax2 = ax1.twinx()  
    color = 'tab:blue'
    ax2.set_ylabel('Drain Current Id (uA) [Linear Scale]', color=color, fontsize=12, fontweight='bold')
    ax2.plot(vg_sat, id_sat*1e6, 'b-', label='Id-Vgs Linear (Vds = 0.70 V)', linewidth=2)
    ax2.tick_params(axis='y', labelcolor=color)

    plt.title('3-Nanosheet GAAFET Transfer Characteristics (Id-Vgs)', fontsize=14, fontweight='bold', pad=15)
    fig.tight_layout()
    plot_path = '/home/ananthakrishnan/GAA_PROJECT/GAA_3NS_SIM/GAA_3NS_Transfer_Characteristics.png'
    plt.savefig(plot_path)
    print(f"Saved Transfer Plot: {plot_path}")

    # 5. Export JSON dataset sample for GNN-RL surrogate model
    dataset_sample = {
        "device_type": "3-Nanosheet GAAFET NMOS",
        "geometry": {
            "nanosheet_width_nm": 25.0,
            "nanosheet_thickness_nm": 5.0,
            "channel_length_nm": 12.0,
            "gate_oxide_eot_nm": 0.8,
            "nanosheet_count": 3
        },
        "electrical_characteristics": {
            "Ion_uA": round(Ion*1e6, 2),
            "Ioff_fA": round(Ioff*1e15, 2),
            "Ion_Ioff_ratio": float(f"{Ion_Ioff_ratio:.2e}"),
            "Vth_linear_mV": round(vth_lin*1000, 1),
            "Vth_sat_mV": round(vth_sat*1000, 1),
            "DIBL_mV_V": round(dibl, 2),
            "SS_mV_dec": round(ss, 2)
        },
        "curves": {
            "Vgs_V": vg_sat.tolist(),
            "Id_A": id_sat.tolist()
        }
    }
    json_path = '/home/ananthakrishnan/GAA_PROJECT/GAA_3NS_SIM/gaafet_dataset_sample.json'
    with open(json_path, 'w') as jf:
        json.dump(dataset_sample, jf, indent=2)
    print(f"Exported GNN-RL Dataset Sample: {json_path}")

if __name__ == '__main__':
    main()
