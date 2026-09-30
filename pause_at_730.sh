#!/bin/bash
LOG="/home/ananthakrishnan/GAA_PROJECT/overnight_doe_4p68eV/overnight_pipeline.log"
TARGET_H=7
TARGET_M=28

echo "[$(date)] Auto-pause scheduler activated for 07:28 AM." >> "$LOG"

while true; do
    CURR_H=$(date +%-H)
    CURR_M=$(date +%-M)
    if [ "$CURR_H" -gt "$TARGET_H" ] || ([ "$CURR_H" -eq "$TARGET_H" ] && [ "$CURR_M" -ge "$TARGET_M" ]); then
        echo "[$(date)] Reached 07:28 AM deadline. Gracefully pausing simulation pipeline..." >> "$LOG"
        pkill -f "run_overnight_batch.sh" 2>/dev/null
        pkill -f "gaafet_tcad_runner.py" 2>/dev/null
        pkill -f "sdevice" 2>/dev/null
        pkill -f "sde" 2>/dev/null
        sleep 2

        # Compile Master CSV with all completed records
        python3 -c "
import os, glob, json, pandas as pd
out_dir = '/home/ananthakrishnan/GAA_PROJECT/overnight_doe_4p68eV'
json_files = sorted(glob.glob(os.path.join(out_dir, '*/*_fom.json')))
records = []
for jf in json_files:
    try:
        with open(jf) as f:
            records.append(json.load(f))
    except:
        pass
if records:
    df = pd.DataFrame(records)
    csv_path = os.path.join(out_dir, 'gaafet_tcad_master_dataset.csv')
    df.to_csv(csv_path, index=False)
    print(f'[AUTO-PAUSE] Master Dataset safely compiled: {len(df)} records saved.')
" >> "$LOG" 2>&1
        echo "[$(date)] CPU is now idle (0% load). Safe to unplug and carry laptop!" >> "$LOG"
        break
    fi
    sleep 5
done
