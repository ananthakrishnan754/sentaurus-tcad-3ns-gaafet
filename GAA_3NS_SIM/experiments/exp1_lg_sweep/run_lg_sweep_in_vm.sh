#!/bin/bash
#======================================================================
# run_lg_sweep_in_vm.sh
# Runs Experiment 1 (6-point Lg sensitivity sweep) inside the TCAD VM
# Includes AUTO-RESUME & CHECKPOINTING:
#   - Automatically detects completed devices and skips them
#   - Automatically detects existing valid meshes and skips SDE
#   - Can be safely stopped, rebooted, and restarted anytime
#======================================================================

export taurus=/home/eda/sentaurus-2017.09/sentaurus/N_2017.09
export PATH=$PATH:$taurus/bin
export SNPS_HOME=/home/eda
export STDB=$HOME/STDB
export SNPSLMD_LICENSE_FILE=27000@localhost.localdomain
export LM_LICENSE_FILE=27000@localhost.localdomain
export DISPLAY=unix:0

RUN_LIST=("G_L10_W15_T04" "G_L12_W15_T04" "G_L14_W15_T04" "G_L16_W15_T04" "G_L18_W15_T04" "G_L20_W15_T04")
SHARED_BASE="/media/sf_swb/exp1_lg_sweep"
MASTER_LOG="$SHARED_BASE/master_sweep_execution.log"

echo "======================================================" >> "$MASTER_LOG"
echo "Lg Sweep Session Started/Resumed: $(date)" >> "$MASTER_LOG"
echo "======================================================" >> "$MASTER_LOG"

for RUN in "${RUN_LIST[@]}"; do
    echo "" >> "$MASTER_LOG"
    echo "------------------------------------------------------" >> "$MASTER_LOG"
    echo "Checking Device: $RUN" >> "$MASTER_LOG"
    echo "------------------------------------------------------" >> "$MASTER_LOG"
    
    WORKDIR="$HOME/STDB/exp1_lg_sweep/$RUN"
    mkdir -p "$WORKDIR"
    
    # ------------------------------------------------------------------
    # CHECKPOINT 1: Check if full simulation already completed
    # ------------------------------------------------------------------
    FINAL_PLT="$SHARED_BASE/$RUN/IdVg_Vd070_${RUN}_des.plt"
    if [ -f "$FINAL_PLT" ] && [ $(wc -c < "$FINAL_PLT") -gt 1000 ]; then
        echo "[RESUME] Device $RUN already completed successfully. Skipping." >> "$MASTER_LOG"
        continue
    fi
    
    # Copy fresh SDE and SDevice files
    cp "$SHARED_BASE/$RUN/${RUN}_sde.scm" "$WORKDIR/"
    cp "$SHARED_BASE/$RUN/${RUN}_sdevice.cmd" "$WORKDIR/"
    cd "$WORKDIR"
    
    # ------------------------------------------------------------------
    # CHECKPOINT 2: Check if valid mesh already generated
    # ------------------------------------------------------------------
    if [ -f "$WORKDIR/${RUN}_msh.tdr" ] && [ $(wc -c < "$WORKDIR/${RUN}_msh.tdr") -gt 10000 ]; then
        echo "[RESUME] Valid 3D mesh already exists for $RUN. Skipping SDE." >> "$MASTER_LOG"
    else
        echo "[1/2] Generating 3D Structure and Dynamic Mesh (sde)..." >> "$MASTER_LOG"
        $taurus/bin/sde -e -l "${RUN}_sde.scm" >> "${RUN}_sde_run.log" 2>&1
        SDE_EXIT=$?
        echo "SDE Exit Code: $SDE_EXIT" >> "$MASTER_LOG"
        
        if [ $SDE_EXIT -ne 0 ] || [ ! -f "${RUN}_msh.tdr" ]; then
            echo "ERROR: Mesh file ${RUN}_msh.tdr not created. Aborting $RUN." >> "$MASTER_LOG"
            continue
        fi
        echo "Mesh generated successfully (${RUN}_msh.tdr)" >> "$MASTER_LOG"
    fi
    
    # ------------------------------------------------------------------
    # STEP 2: Device Physics Simulation (SDevice)
    # ------------------------------------------------------------------
    echo "[2/2] Running Device Physics Simulation (sdevice)..." >> "$MASTER_LOG"
    $taurus/bin/sdevice "${RUN}_sdevice.cmd" >> "${RUN}_sdevice_run.log" 2>&1
    SDEV_EXIT=$?
    echo "SDevice Exit Code: $SDEV_EXIT" >> "$MASTER_LOG"
    
    # Sync results back to shared folder
    cp -r "$WORKDIR"/* "$SHARED_BASE/$RUN/"
    echo "Completed and synced back: $RUN" >> "$MASTER_LOG"
done

echo "" >> "$MASTER_LOG"
echo "======================================================" >> "$MASTER_LOG"
echo "All sweep devices verified/completed. Timestamp: $(date)" >> "$MASTER_LOG"
echo "======================================================" >> "$MASTER_LOG"
echo "COMPLETED" > "$SHARED_BASE/status_sweep_complete.txt"
