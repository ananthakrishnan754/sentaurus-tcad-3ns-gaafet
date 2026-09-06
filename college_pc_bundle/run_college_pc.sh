#!/bin/bash
#=============================================================================
# run_college_pc.sh
# One-click launcher for the College PC (bare-metal Linux / multi-core)
#=============================================================================

echo "================================================================"
echo "    GAAFET Automated TCAD Simulation & PPA Pipeline             "
echo "    College PC Multi-Threaded Execution Runner                  "
echo "================================================================"

# 1. Source Sentaurus Environment (if needed)
if command -v sdevice &>/dev/null; then
    echo "[OK] Sentaurus binaries detected in PATH."
elif [ -f "/opt/synopsys/sentaurus/tcad/R-2022.09/env.sh" ]; then
    echo "[INFO] Sourcing /opt/synopsys/sentaurus/tcad/R-2022.09/env.sh"
    source /opt/synopsys/sentaurus/tcad/R-2022.09/env.sh
elif [ -f "/home/eda/sentaurus-2017.09/sentaurus/N_2017.09/bin/sdevice" ]; then
    export PATH="/home/eda/sentaurus-2017.09/sentaurus/N_2017.09/bin:$PATH"
    echo "[INFO] Added /home/eda/sentaurus-2017.09 to PATH."
else
    echo "[WARNING] sdevice not found in default paths. Ensure TCAD environment is loaded."
fi

# Detect CPU cores for parallel jobs (default to 4)
NUM_CORES=$(nproc 2>/dev/null || echo 4)
JOBS=$(( NUM_CORES > 4 ? 4 : NUM_CORES ))

echo "[INFO] Running 6-point Lg sensitivity sweep across $JOBS parallel workers..."
python3 gaafet_tcad_runner.py --mode lg_sweep --jobs "$JOBS" --out-dir ./results

echo "================================================================"
echo "Simulation sweep complete!"
echo "Master dataset: ./results/gaafet_tcad_master_dataset.csv"
echo "Trend plots:    ./results/lg_sensitivity_trends.png"
echo "================================================================"
