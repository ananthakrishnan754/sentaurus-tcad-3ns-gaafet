#!/bin/bash
# ==============================================================================
# GAAFET 3-STACK NANOSHEET OVERNIGHT DOE BATCH RUNNER (47 CONDITIONS -> 7:00 AM)
# Calibrated: Workfunction = 4.68 eV | Vds_low = 0.10 V | Vds_high = 0.70 V
# Solver: Fast ParDiSo Sparse Solver + eQuantumPotential Confinement
# ==============================================================================

# 1. Environment Configuration
export STROOT=/home/eda/sentaurus-2017.09/sentaurus/N_2017.09
export SCL_ROOT=/home/eda/scl11.9
export SNPSLMD_LICENSE_FILE=27000@localhost.localdomain
export LM_LICENSE_FILE=27000@localhost.localdomain
export LD_LIBRARY_PATH=/opt/synopsys/compat_lib:${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}
export PATH=/usr/local/bin:$STROOT/bin:$SCL_ROOT/amd64/bin:$PATH
export STDB=$HOME/STDB

OUT_DIR="/home/ananthakrishnan/GAA_PROJECT/overnight_doe_4p68eV"
mkdir -p "$OUT_DIR"

echo "[$(date)] Starting 47-Device Overnight DOE Simulation Pipeline (ParDiSo Solver)..."
echo "[$(date)] Target Finish: ~06:30 AM to 07:00 AM IST"

# 2. Launch Master Pipeline
python3 -u /home/ananthakrishnan/GAA_PROJECT/college_pc_bundle/gaafet_tcad_runner.py \
    --mode full_doe \
    --workfunction 4.68 \
    --jobs 1 \
    --threads 8 \
    --resume \
    --out-dir "$OUT_DIR"

echo "[$(date)] Overnight DOE Simulation Pipeline Completed!"
