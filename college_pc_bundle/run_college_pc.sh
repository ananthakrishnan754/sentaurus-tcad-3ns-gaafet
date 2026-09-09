#!/bin/bash
#=============================================================================
# run_college_pc.sh
# One-click optimized launcher for the College PC (bare-metal Linux / multi-core)
#=============================================================================

echo "================================================================"
echo "    GAAFET Automated TCAD Simulation & PPA Pipeline (Optimized)  "
echo "    College PC Execution Runner                                 "
echo "================================================================"

# 1. Source Sentaurus Environment (if needed)
if command -v sdevice &>/dev/null; then
    echo "[OK] Sentaurus binaries detected in PATH: $(which sdevice)"
elif [ -f "/opt/synopsys/sentaurus/tcad/R-2022.09/env.sh" ]; then
    echo "[INFO] Sourcing /opt/synopsys/sentaurus/tcad/R-2022.09/env.sh"
    source /opt/synopsys/sentaurus/tcad/R-2022.09/env.sh
elif [ -f "/home/amrita/setup/sentaurus/sentaurus/T-2022.03-SP2/bin/sdevice" ]; then
    export PATH="/home/amrita/setup/sentaurus/sentaurus/T-2022.03-SP2/bin:$PATH"
    echo "[INFO] Added /home/amrita/setup/sentaurus/sentaurus/T-2022.03-SP2/bin to PATH."
elif [ -f "/home/eda/sentaurus-2017.09/sentaurus/N_2017.09/bin/sdevice" ]; then
    export PATH="/home/eda/sentaurus-2017.09/sentaurus/N_2017.09/bin:$PATH"
    echo "[INFO] Added /home/eda/sentaurus-2017.09 to PATH."
else
    echo "[WARNING] sdevice not found in default paths. Ensure TCAD environment is loaded."
fi

# Detect CPU cores: set safe parallel job count (default 2 on 8-core machines to prevent memory bus contention)
NUM_CORES=$(nproc 2>/dev/null || echo 4)
if [ "$NUM_CORES" -ge 8 ]; then
    DEFAULT_JOBS=2
else
    DEFAULT_JOBS=1
fi

echo "[INFO] Detected $NUM_CORES CPU cores. Defaulting to $DEFAULT_JOBS parallel worker(s), 4 threads per SDevice."
if [ $# -gt 0 ]; then
    echo "[INFO] Forwarding user options: $@"
fi

# Run the optimized master pipeline with resume enabled by default
python3 gaafet_tcad_runner.py --mode lg_sweep --jobs "$DEFAULT_JOBS" --threads 4 --out-dir ./results --resume "$@"

echo "================================================================"
echo "Simulation sweep session complete!"
echo "Master dataset: ./results/gaafet_tcad_master_dataset.csv"
echo "Trend plots:    ./results/lg_sensitivity_trends.png"
echo "================================================================"
