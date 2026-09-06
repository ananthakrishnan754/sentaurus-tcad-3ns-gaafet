#!/usr/bin/env python3
import os
import shutil

swb_base = "/home/ananthakrishnan/Documents/swb"

projects = {
    "GAA_3NS_NMOS": {
        "sde": "GAA_3NS_sde.scm",
        "sdevice": "GAA_3NS_sdevice.cmd"
    },
    "GAA_3NS_SIM": {
        "sde": "GAA_3NS_sde.scm",
        "sdevice": "GAA_3NS_sdevice.cmd"
    },
    "GAA_3NS_HfO2_BDI": {
        "sde": "GAA_3NS_sde_hfo2_bdi.scm",
        "sdevice": "GAA_3NS_sdevice_hfo2_bdi.cmd"
    }
}

gtn_content = """tool sde "sde" {
}

tool sdevice "sdevice" {
}

node 1 sde "sde" {
}

node 2 sdevice "sdevice" {
  parent 1
}
"""

gtb_content = """# Sentaurus Workbench Parameter Table
"""

source_dir = "/home/ananthakrishnan/GAA_PROJECT/GAA_3NS_SIM"

for proj_name, files in projects.items():
    proj_dir = os.path.join(swb_base, proj_name)
    os.makedirs(proj_dir, exist_ok=True)
    
    # Write gtn.cmd and gtb.cmd
    with open(os.path.join(proj_dir, "gtn.cmd"), "w") as f:
        f.write(gtn_content)
    with open(os.path.join(proj_dir, "gtb.cmd"), "w") as f:
        f.write(gtb_content)
        
    # Copy sde and sdevice as sde_dvs.cmd and sdevice_des.cmd
    sde_src = os.path.join(source_dir, files["sde"])
    sdev_src = os.path.join(source_dir, files["sdevice"])
    
    if os.path.exists(sde_src):
        shutil.copy(sde_src, os.path.join(proj_dir, "sde_dvs.cmd"))
    if os.path.exists(sdev_src):
        shutil.copy(sdev_src, os.path.join(proj_dir, "sdevice_des.cmd"))

print("SWB Projects initialized with gtn.cmd, gtb.cmd, sde_dvs.cmd, sdevice_des.cmd successfully!")
