#!/bin/bash
LOG="/home/ananthakrishnan/GAA_PROJECT/overnight_doe_4p68eV/overnight_pipeline.log"
echo "[$(date)] Daemon initialized. Waiting for baseline test to complete..." >> "$LOG"

while pgrep -f "sdevice G_L10_W15_T04" > /dev/null; do
    sleep 5
done

echo "[$(date)] Baseline test complete! Launching full 24-condition DOE sweep..." >> "$LOG"
/home/ananthakrishnan/GAA_PROJECT/run_overnight_batch.sh >> "$LOG" 2>&1
