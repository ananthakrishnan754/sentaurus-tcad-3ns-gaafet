# GAA_3NS_SIM — Sentaurus TCAD Project for 3-Nanosheet GAAFET

## Device Specification

| Parameter            | Value        |
|----------------------|-------------|
| Technology           | N3/N2 class NMOS GAAFET |
| Gate length (Lg)     | 10 nm        |
| Nanosheet width (Wns)| 15 nm        |
| Nanosheet thickness  | 4 nm         |
| # of nanosheets      | **3**        |
| Inter-sheet gap      | 8 nm         |
| Gate dielectric      | HfO2, 1 nm   |
| Gate metal Φm        | 4.4 eV       |
| S/D doping           | N+ Phosphorus 1×10²⁰ cm⁻³ |
| Channel doping       | P-type Boron 1×10¹⁵ cm⁻³  |
| Supply voltage (VDD) | 0.70 V       |

---

## File Manifest

| File | Tool | Purpose |
|------|------|---------|
| `GAA_3NS_sde.scm`      | Sentaurus SDE     | Geometry + mesh generation |
| `GAA_3NS_sdevice.cmd`  | Sentaurus SDevice | Device physics + IV sweeps |
| `run_gaa_sim.sh`       | Bash              | Full pipeline runner       |
| `parse_results.py`     | Python 3          | Plot + FOM extraction      |

---

## Simulation Characteristics Obtained

### Transfer Curves (ID-VG)
- **Linear region**: VGS: 0 → 0.70 V @ VDS = 0.05 V → extracts VTH_lin, SS
- **Saturation region**: VGS: 0 → 0.70 V @ VDS = 0.70 V → extracts VTH_sat, DIBL, ION, IOFF

### Output Curves (ID-VD)
- VDS: 0 → 0.70 V at VGS = 0.0, 0.2, 0.4, 0.6, 0.70 V

### Extracted Figures of Merit
| FOM  | Description |
|------|-------------|
| VTH_lin | Threshold voltage (linear, max-gm) |
| VTH_sat | Threshold voltage (saturation) |
| SS      | Sub-threshold swing (mV/dec) |
| DIBL    | Drain-induced barrier lowering (mV/V) |
| ION     | On-state current @ VGS=VDS=0.70 V (A/µm) |
| IOFF    | Off-state current @ VGS=0, VDS=0.70 V (A/µm) |
| ION/IOFF| On/Off ratio |

---

## How to Run (inside the VM)

```bash
# 1. Navigate to this folder
cd /path/to/GAA_3NS_SIM

# 2. Source Sentaurus environment (adjust path for your installation)
source /opt/synopsys/sentaurus/tcad/R-2022.09/env.sh

# 3. Make runner executable and launch
chmod +x run_gaa_sim.sh
./run_gaa_sim.sh
```

Or run steps manually:

```bash
# Step 1: Generate mesh
sde -e -l GAA_3NS_sde.scm

# Step 2: Run device simulation
sdevice GAA_3NS_sdevice.cmd

# Step 3: Post-process results
python3 parse_results.py
```

---

## Physics Models Active

| Model | Reason |
|-------|--------|
| Fermi-Dirac statistics | N+ S/D at 1×10²⁰ cm⁻³ → degenerate |
| DopingDep mobility | Impurity scattering in S/D |
| Enormal mobility | Surface roughness at gate interface |
| HighFieldSaturation | Velocity saturation in short channel |
| SRH recombination | Carrier lifetime effects |
| OldSlotboom BGN | Bandgap narrowing in N+ S/D |
| eQuantumPotential | Quantum confinement in 4 nm body |

---

## Expected Results (Reference from Literature)

For a 10 nm Lg 3-NS NMOS GAAFET (N3 class):

| FOM | Expected Range |
|-----|---------------|
| VTH (lin) | ~0.20 – 0.30 V |
| SS | 65 – 70 mV/dec |
| DIBL | 20 – 50 mV/V |
| ION | 1 – 3 mA/µm |
| IOFF | < 100 nA/µm |
| ION/IOFF | > 10⁴ |
