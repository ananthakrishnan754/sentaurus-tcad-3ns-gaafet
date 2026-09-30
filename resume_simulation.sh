#!/bin/bash
# ==============================================================================
# GAAFET SIMULATION RESUME LAUNCHER
# Automatically skips all completed runs and continues the remaining queue
# ==============================================================================

export STROOT=/home/eda/sentaurus-2017.09/sentaurus/N_2017.09
export SCL_ROOT=/home/eda/scl11.9
export SNPSLMD_LICENSE_FILE=27000@localhost.localdomain
export LM_LICENSE_FILE=27000@localhost.localdomain
export LD_LIBRARY_PATH=/opt/synopsys/compat_lib:${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}
export PATH=/usr/local/bin:$STROOT/bin:$SCL_ROOT/amd64/bin:$PATH
export STDB=$HOME/STDB

OUT_DIR="/home/ananthakrishnan/GAA_PROJECT/overnight_doe_4p68eV"

echo "[$(date)] Resuming GAAFET TCAD Master DOE Pipeline..."

python3 -u /home/ananthakrishnan/GAA_PROJECT/college_pc_bundle/gaafet_tcad_runner.py \
    --mode full_doe \
    --workfunction 4.68 \
    --jobs 2 \
    --threads 8 \
    --resume \
    --out-dir "$OUT_DIR"
