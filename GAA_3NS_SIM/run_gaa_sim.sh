#!/bin/bash
#======================================================================
# run_gaa_sim.sh  —  Full Sentaurus TCAD pipeline for 3-NS GAA NMOS
#
# USAGE:
#   chmod +x run_gaa_sim.sh
#   ./run_gaa_sim.sh
#
# Prerequisites:
#   • Synopsys Sentaurus TCAD 2022 or later (swb / sde / sdevice)
#   • Environment loaded:  source /path/to/synopsys/sentaurus_env.sh
#   • Valid SNPSLMD_LICENSE_FILE or LM_LICENSE_FILE set
#
# Steps executed:
#   1. Run SDE (gdp/scheme)  →  generates GAA_3NS_NMOS_msh.tdr
#   2. Run SDevice           →  generates plt / tdr / log files
#   3. Run Python parser     →  generates plots + CSV summary
#======================================================================

set -e   # exit on any error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "======================================================"
echo "  GAA 3-Nanosheet NMOS TCAD Simulation Pipeline"
echo "  Working directory: $SCRIPT_DIR"
echo "======================================================"

#----------------------------------------------------------------------
# STEP 1: Structure Editor — geometry + mesh generation
#----------------------------------------------------------------------
echo ""
echo "[STEP 1] Running Sentaurus Structure Editor (sde)..."
echo "  Input : GAA_3NS_sde.scm"
echo "  Output: GAA_3NS_NMOS_msh.tdr"

sde -e -l GAA_3NS_sde.scm 2>&1 | tee sde_run.log

if [ ! -f "GAA_3NS_NMOS_msh.tdr" ]; then
    echo "ERROR: Mesh file GAA_3NS_NMOS_msh.tdr not created. Check sde_run.log"
    exit 1
fi
echo "[STEP 1] SDE completed. Mesh file created."

#----------------------------------------------------------------------
# STEP 2: Device Simulation
#----------------------------------------------------------------------
echo ""
echo "[STEP 2] Running Sentaurus Device (sdevice)..."
echo "  Input : GAA_3NS_sdevice.cmd"
echo "  Output: GAA_3NS_NMOS_des.plt / .tdr / .log"

sdevice GAA_3NS_sdevice.cmd 2>&1 | tee sdevice_run.log

if [ ! -f "GAA_3NS_NMOS_des.plt" ] && [ ! -f "IdVg_Vd005_des.plt" ]; then
    echo "ERROR: PLT file not created. Check sdevice_run.log"
    exit 1
fi
echo "[STEP 2] SDevice completed. Results saved."

#----------------------------------------------------------------------
# STEP 3: Python post-processing (if available)
#----------------------------------------------------------------------
echo ""
if command -v python3 &>/dev/null && [ -f "parse_results.py" ]; then
    echo "[STEP 3] Running Python post-processor..."
    python3 parse_results.py 2>&1 | tee parse_run.log
    echo "[STEP 3] Plots and CSV summary generated."
else
    echo "[STEP 3] Skipping Python post-processing (not found or no script)."
fi

echo ""
echo "======================================================"
echo "  SIMULATION COMPLETE"
echo "  Log files:   sde_run.log   sdevice_run.log"
echo "  TDR:         GAA_3NS_NMOS_des.tdr  (open in Sentaurus Visual)"
echo "  IV data:     GAA_3NS_NMOS_des.plt  (open in Inspect / svisual)"
echo "======================================================"
