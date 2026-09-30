#!/bin/bash
# ==============================================================================
# Self-Sustaining Offline Overnight TCAD Runner
# Survives terminal detachment, internet disconnection, and IDE shutdown.
# ==============================================================================

cd /home/ananthakrishnan/GAA_PROJECT

# Launch python runner detached from terminal
nohup python3 -u run_overnight_100_verification.py > /home/ananthakrishnan/GAA_PROJECT/overnight_100_simulation.log 2>&1 &
PID=$!
echo $PID > /home/ananthakrishnan/GAA_PROJECT/overnight_100_simulation.pid

echo "======================================================================"
echo "  OVERNIGHT TCAD SIMULATION BATCH LAUNCHED SUCCESSFULLY"
echo "  Process ID (PID) : $PID"
echo "  Log File         : /home/ananthakrishnan/GAA_PROJECT/overnight_100_simulation.log"
echo "  Results CSV      : /home/ananthakrishnan/GAA_PROJECT/gaafet_overnight_100_results.csv"
echo "  Final Report     : /home/ananthakrishnan/GAA_PROJECT/GAAFET_OVERNIGHT_100_VERIFICATION_REPORT.md"
echo "======================================================================"
echo "You can now safely disconnect the internet or close the terminal."
