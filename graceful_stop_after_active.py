#!/usr/bin/env python3
import time
import os
import subprocess
import pandas as pd
import glob

MASTER_CSV = "/home/ananthakrishnan/GAA_PROJECT/industry_calibrated_doe_vth0p25/gaafet_tcad_master_dataset.csv"
TARGET_DEVICES = ["G_L16_W15_T08", "G_L16_W18_T03"]
LOG_FILE = "/home/ananthakrishnan/GAA_PROJECT/graceful_shutdown.log"

with open(LOG_FILE, "w") as log:
    log.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Graceful shutdown watcher started.\n")
    log.write(f"Waiting for target devices to complete: {TARGET_DEVICES}\n")
    log.flush()

    while True:
        try:
            if os.path.exists(MASTER_CSV):
                df = pd.read_csv(MASTER_CSV)
                completed_ids = set(df["RunID"])
                remaining = [d for d in TARGET_DEVICES if d not in completed_ids]
                
                log.write(f"[{time.strftime('%H:%M:%S')}] Completed: {len(completed_ids)} total devices. Remaining targets: {remaining}\n")
                log.flush()
                
                if not remaining:
                    log.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Both target devices have finished and saved!\n")
                    break
        except Exception as e:
            log.write(f"Check error: {e}\n")
            log.flush()
            
        time.sleep(20)

    # Both target devices have finished! Now cleanly stop runner and any new child tasks
    log.write("Stopping master runner processes...\n")
    log.flush()
    
    # Kill the runner python process
    subprocess.run(["pkill", "-f", "college_pc_bundle/gaafet_tcad_runner.py"], check=False)
    subprocess.run(["pkill", "-f", "sdevice"], check=False)
    subprocess.run(["pkill", "-f", "sde"], check=False)
    time.sleep(2)
    
    # Clean partial/stale files from any other devices that just began
    df = pd.read_csv(MASTER_CSV)
    saved_ids = set(df["RunID"])
    cleaned = 0
    for d in glob.glob("/home/ananthakrishnan/GAA_PROJECT/industry_calibrated_doe_vth0p25/G_*"):
        rname = os.path.basename(d)
        if rname not in saved_ids:
            for f in glob.glob(os.path.join(d, "*.plt")) + glob.glob(os.path.join(d, "*.sav")):
                try:
                    os.remove(f)
                    cleaned += 1
                except Exception:
                    pass
                    
    log.write(f"Cleaned {cleaned} partial files from non-completed runs.\n")
    log.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] READY FOR LAPTOP SHUTDOWN. Total saved records: {len(df)}\n")
    log.flush()
    print("GRACEFUL_SHUTDOWN_READY")
