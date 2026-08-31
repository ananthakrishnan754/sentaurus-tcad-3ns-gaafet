#!/usr/bin/env python3
"""
parse_results.py  —  Post-processor for 3-Nanosheet GAA NMOS TCAD results
==========================================================================

Reads Sentaurus .plt files (CSV-like format) and produces:
  • ID-VG plots (linear + log scale) at VDS = 0.05 V and 0.70 V
  • ID-VD output characteristic (family of curves)
  • Extracted figures of merit saved to summary.csv:
      VTH_lin   (threshold voltage, linear region, max-gm method)
      VTH_sat   (threshold voltage, saturation region)
      SS        (sub-threshold swing, mV/dec)
      DIBL      (drain-induced barrier lowering, mV/V)
      ION       (on-state current at VGS = VDS = 0.70 V)  [A/um]
      IOFF      (off-state current at VGS = 0 V, VDS = 0.70 V) [A/um]
      ION_IOFF  (ratio)

Usage:
    python3 parse_results.py

Dependencies:
    pip install numpy matplotlib pandas
"""

import re
import os
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import LogLocator

# ── File paths ────────────────────────────────────────────────────────
SEARCH_DIRS = [".", "/home/ananthakrishnan/Documents/swb/GAA_3NS_SIM"]
OUT_DIR    = "results"
os.makedirs(OUT_DIR, exist_ok=True)

# ── Nanosheet width (normalisation) ──────────────────────────────────
WNS_UM = 0.015          # 15 nm in micrometres

def find_file(filename):
    for d in SEARCH_DIRS:
        p = os.path.join(d, filename)
        if os.path.isfile(p):
            return p
    return None

def parse_df_ise_plt(filepath):
    """
    Parses DF-ISE text format Sentaurus .plt files into a pandas DataFrame.
    """
    datasets = []
    data_values = []
    in_datasets = False
    in_data = False
    buffer = ""

    with open(filepath, "r") as f:
        content = f.read()

    # Extract datasets header
    ds_match = re.search(r'datasets\s*=\s*\[(.*?)\]', content, re.DOTALL)
    if ds_match:
        raw_ds = ds_match.group(1)
        # Find all quoted string tokens
        datasets = re.findall(r'"([^"]+)"', raw_ds)

    # Extract Data section
    data_match = re.search(r'Data\s*\{([\s\S]*?)\}', content)
    if data_match:
        raw_data = data_match.group(1)
        # Convert all tokens to floats
        tokens = raw_data.split()
        data_values = []
        for t in tokens:
            try:
                data_values.append(float(t))
            except ValueError:
                pass

    if datasets and data_values:
        num_cols = len(datasets)
        num_rows = len(data_values) // num_cols
        if num_rows > 0:
            truncated_len = num_rows * num_cols
            arr = np.array(data_values[:truncated_len]).reshape((num_rows, num_cols))
            df = pd.DataFrame(arr, columns=datasets)
            return df

    return None

def load_all_sweeps():
    """Loads all available PLT sweep files into a dictionary of DataFrames."""
    blocks = {}
    
    known_files = {
        "IdVg_Vd005": "IdVg_Vd005_GAA_3NS_NMOS_des.plt",
        "IdVg_Vd070": "IdVg_Vd070_GAA_3NS_NMOS_des.plt",
        "IdVd_Vg000": "IdVd_Vg000_GAA_3NS_NMOS_des.plt",
        "IdVd_Vg020": "IdVd_Vg020_GAA_3NS_NMOS_des.plt",
        "IdVd_Vg040": "IdVd_Vg040_GAA_3NS_NMOS_des.plt",
        "IdVd_Vg060": "IdVd_Vg060_GAA_3NS_NMOS_des.plt",
        "IdVd_Vg070": "IdVd_Vg070_GAA_3NS_NMOS_des.plt",
        "Main": "GAA_3NS_NMOS_des.plt"
    }

    for key, fname in known_files.items():
        path = find_file(fname)
        if path:
            df = parse_df_ise_plt(path)
            if df is not None and not df.empty:
                blocks[key] = df

    return blocks



def get_vg(df):
    for c in df.columns:
        if "gate" in c.lower() and ("voltage" in c.lower() or "outervoltage" in c.lower() or "innervoltage" in c.lower()):
            return df[c].values
        if c.lower() in ["vg", "gate"]:
            return df[c].values
    # Fallback to first gate column
    for c in df.columns:
        if "gate" in c.lower():
            return df[c].values
    raise KeyError(f"Gate voltage column not found in {list(df.columns)}")

def get_vd(df):
    for c in df.columns:
        if "drain" in c.lower() and ("voltage" in c.lower() or "outervoltage" in c.lower() or "innervoltage" in c.lower()):
            return df[c].values
        if c.lower() in ["vd", "drain"]:
            return df[c].values
    # Fallback to first drain voltage column
    for c in df.columns:
        if "drain" in c.lower() and "voltage" in c.lower():
            return df[c].values
    raise KeyError(f"Drain voltage column not found in {list(df.columns)}")

def get_id(df):
    for c in df.columns:
        if "drain" in c.lower() and "totalcurrent" in c.lower():
            return df[c].values
    for c in df.columns:
        if "drain" in c.lower() and "ecurrent" in c.lower():
            return df[c].values
    for c in df.columns:
        if "drain" in c.lower() and "current" in c.lower() and "displacement" not in c.lower():
            return df[c].values
    if "id" in [c.lower() for c in df.columns]:
        for c in df.columns:
            if c.lower() == "id":
                return df[c].values
    raise KeyError(f"Drain current column not found in {list(df.columns)}")





# ─────────────────────────────────────────────────────────────────────
# 2.  FIGURES OF MERIT
# ─────────────────────────────────────────────────────────────────────

def extract_vth_maxgm(vg, id_a):
    """
    Threshold voltage by peak transconductance (max-gm) method.
    Returns VTH in volts.
    """
    gm = np.gradient(id_a, vg)
    idx_peak = np.argmax(gm)
    gm_peak  = gm[idx_peak]
    vg_peak  = vg[idx_peak]
    id_peak  = id_a[idx_peak]
    # Tangent line:  id = gm_peak * (vg - vth)  →  vth = vg_peak - id_peak/gm_peak
    vth = vg_peak - id_peak / gm_peak if gm_peak > 0 else float("nan")
    return vth


def extract_ss(vg, id_a):
    """
    Sub-threshold swing  SS = dVG / d(log10(ID))  in mV/dec.
    Uses the steepest linear region below VTH (log scale).
    """
    if len(vg) < 4:
        return float("nan")
    log_id = np.log10(np.abs(id_a) + 1e-30)
    d_log  = np.gradient(log_id, vg)
    vth = extract_vth_maxgm(vg, id_a)
    if not np.isnan(vth):
        mask = (vg < vth) & (d_log > 0)
    else:
        id_peak = np.max(np.abs(id_a))
        mask = (np.abs(id_a) < 0.1 * id_peak) & (d_log > 0)

    if mask.sum() < 2:
        mask = d_log > 0

    if mask.sum() == 0:
        return float("nan")

    ss_inv = np.max(d_log[mask])           # max of  d(log ID)/dVG
    ss_mv  = 1000.0 / ss_inv if ss_inv > 0 else float("nan")
    return ss_mv



# ─────────────────────────────────────────────────────────────────────
# 3.  PLOTTING HELPERS
# ─────────────────────────────────────────────────────────────────────

STYLE = {
    "figure.facecolor": "#0d1117",
    "axes.facecolor":   "#161b22",
    "axes.edgecolor":   "#30363d",
    "axes.labelcolor":  "#e6edf3",
    "xtick.color":      "#e6edf3",
    "ytick.color":      "#e6edf3",
    "text.color":       "#e6edf3",
    "grid.color":       "#21262d",
    "grid.linestyle":   "--",
    "grid.alpha":       0.7,
    "legend.facecolor": "#161b22",
    "legend.edgecolor": "#30363d",
    "font.family":      "sans-serif",
}

def apply_style():
    plt.rcParams.update(STYLE)


def save_fig(name):
    path = os.path.join(OUT_DIR, name)
    plt.savefig(path, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {path}")


# ─────────────────────────────────────────────────────────────────────
# 4.  MAIN
# ─────────────────────────────────────────────────────────────────────

def extract_forward_sweep(vg, id_arr):
    """Slices array to the first monotonic increasing gate voltage sweep segment."""
    if len(vg) == 0:
        return vg, id_arr
    max_idx = np.argmax(vg)
    return vg[:max_idx + 1], id_arr[:max_idx + 1]

def extract_forward_sweep_vd(vd, id_arr):
    """Slices array to the first monotonic increasing drain voltage sweep segment."""
    if len(vd) == 0:
        return vd, id_arr
    max_idx = np.argmax(vd)
    return vd[:max_idx + 1], id_arr[:max_idx + 1]

def main():
    apply_style()
    blocks = load_all_sweeps()

    if not blocks:
        print("No data blocks found in PLT file.")
        sys.exit(1)

    print(f"  Loaded {len(blocks)} sweep block(s): {list(blocks.keys())}")

    # ── Normalise drain current by nanosheet width ────────────────────
    fom = {}

    # ── 4a.  ID-VG  Linear region  (VDS = 0.05 V) ────────────────────
    key_lin = next((k for k in blocks if "Vd005" in k), None)
    if key_lin:
        df  = blocks[key_lin]
        vg_raw  = get_vg(df)
        idr_raw = get_id(df)
        vg, idr = extract_forward_sweep(vg_raw, idr_raw)
        id_norm = np.abs(idr) / WNS_UM

        vth_lin = extract_vth_maxgm(vg, id_norm)
        ss_val  = extract_ss(vg, id_norm)
        ioff    = id_norm[0] if len(id_norm) > 0 else float("nan")
        fom["VTH_lin_V"]   = vth_lin
        fom["SS_mVdec"]    = ss_val
        fom["IOFF_A_um"]   = ioff

        fig, axes = plt.subplots(1, 2, figsize=(12, 5))
        fig.suptitle("ID-VG Transfer Characteristic — VDS = 0.05 V (Linear)", fontsize=13)

        ax = axes[0]
        ax.plot(vg, id_norm * 1e6, color="#58a6ff", lw=2)
        ax.set_xlabel("VGS (V)");  ax.set_ylabel("ID (µA/µm)")
        ax.set_title("Linear scale");  ax.grid(True)
        if not np.isnan(vth_lin):
            ax.axvline(vth_lin, color="#f78166", ls="--", label=f"VTH = {vth_lin:.3f} V")
            ax.legend()

        ax = axes[1]
        ax.semilogy(vg, np.abs(id_norm), color="#3fb950", lw=2)
        ax.set_xlabel("VGS (V)");  ax.set_ylabel("|ID| (A/µm)")
        ax.set_title("Log scale");  ax.grid(True, which="both")
        if not np.isnan(ss_val):
            ax.text(0.05, 0.95, f"SS = {ss_val:.1f} mV/dec",
                    transform=ax.transAxes, color="#e6edf3",
                    va="top", fontsize=10,
                    bbox=dict(boxstyle="round", fc="#21262d", ec="#30363d"))

        plt.tight_layout()
        save_fig("IdVg_linear.png")

    # ── 4b.  ID-VG  Saturation region  (VDS = 0.70 V) ────────────────
    key_sat = next((k for k in blocks if "Vd070" in k and "IdVg" in k), None)
    if key_sat:
        df   = blocks[key_sat]
        vg_raw   = get_vg(df)
        idr_raw  = get_id(df)
        vg, idr  = extract_forward_sweep(vg_raw, idr_raw)
        id_norm = np.abs(idr) / WNS_UM

        vth_sat = extract_vth_maxgm(vg, id_norm)
        ion     = id_norm[-1] if len(id_norm) > 0 else float("nan")
        fom["VTH_sat_V"]  = vth_sat
        fom["ION_A_um"]   = ion

        # DIBL
        if "VTH_lin_V" in fom and not np.isnan(fom["VTH_lin_V"]) and not np.isnan(vth_sat):
            fom["DIBL_mV_V"] = abs(fom["VTH_lin_V"] - vth_sat) / (0.70 - 0.05) * 1000.0
        else:
            fom["DIBL_mV_V"] = float("nan")

        if "IOFF_A_um" in fom and fom["IOFF_A_um"] > 0:
            fom["ION_IOFF"] = ion / fom["IOFF_A_um"]

        fig, ax = plt.subplots(figsize=(7, 5))
        ax.semilogy(vg, np.abs(id_norm), color="#e3b341", lw=2, label="VDS = 0.70 V")
        if key_lin:
            df2 = blocks[key_lin]
            vg2_raw = get_vg(df2)
            id2_raw = get_id(df2)
            vg2, id2 = extract_forward_sweep(vg2_raw, id2_raw)
            ax.semilogy(vg2, np.abs(id2)/WNS_UM, color="#58a6ff", lw=2, ls="--",
                        label="VDS = 0.05 V")
        ax.set_xlabel("VGS (V)");  ax.set_ylabel("|ID| (A/µm)")
        ax.set_title("ID-VG Transfer Curves (Log Scale)");  ax.grid(True, which="both")
        ax.legend()
        if "DIBL_mV_V" in fom and not np.isnan(fom["DIBL_mV_V"]):
            ax.text(0.05, 0.05,
                    f"DIBL = {fom['DIBL_mV_V']:.1f} mV/V",
                    transform=ax.transAxes, color="#e6edf3", va="bottom", fontsize=10,
                    bbox=dict(boxstyle="round", fc="#21262d", ec="#30363d"))
        plt.tight_layout()
        save_fig("IdVg_both_Vds.png")

    # ── 4c.  ID-VD  Output characteristics ───────────────────────────
    vg_labels = {"Vg000": "VGS = 0.0 V", "Vg020": "VGS = 0.2 V",
                 "Vg040": "VGS = 0.4 V", "Vg060": "VGS = 0.6 V",
                 "Vg070": "VGS = 0.7 V"}
    colors_out = ["#6e7681", "#58a6ff", "#3fb950", "#e3b341", "#f78166"]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.set_xlabel("VDS (V)");  ax.set_ylabel("ID (µA/µm)")
    ax.set_title("ID-VD Output Characteristics")
    ax.grid(True)

    for (tag, label), col in zip(vg_labels.items(), colors_out):
        key = next((k for k in blocks if tag in k and "IdVd" in k), None)
        if key:
            df  = blocks[key]
            vd_raw  = get_vd(df)
            idr_raw = get_id(df)
            vd, idr = extract_forward_sweep_vd(vd_raw, idr_raw)
            ax.plot(vd, np.abs(idr)/WNS_UM * 1e6, color=col, lw=2, label=label)

    ax.legend(fontsize=9)
    plt.tight_layout()
    save_fig("IdVd_output.png")



    ax.legend(fontsize=9)
    plt.tight_layout()
    save_fig("IdVd_output.png")

    # ── 4d.  Print and save FOM summary ──────────────────────────────
    print("\n  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  Figures of Merit — 3-NS GAA NMOS  (10 nm Lg)")
    print("  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    for k, v in fom.items():
        if np.isnan(v):
            print(f"  {k:<20} = N/A")
        elif "ION_IOFF" in k:
            print(f"  {k:<20} = {v:.2e}")
        elif "_A_um" in k:
            print(f"  {k:<20} = {v:.3e}  A/µm")
        else:
            print(f"  {k:<20} = {v:.3f}")
    print("  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

    pd.DataFrame([fom]).to_csv(os.path.join(OUT_DIR, "summary_FOM.csv"), index=False)
    print(f"  Summary saved: {OUT_DIR}/summary_FOM.csv")


if __name__ == "__main__":
    main()
