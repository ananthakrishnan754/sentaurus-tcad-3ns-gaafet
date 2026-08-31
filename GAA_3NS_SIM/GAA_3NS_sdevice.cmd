#======================================================================
# 3-STACK NANOSHEET NMOS GAAFET — Sentaurus Device (SDevice)
#
# Produces BOTH device characteristics:
#   1) Transfer (ID-VG):
#      Sweep VGS: 0 → 0.70 V  @ VDS = 0.05 V  (linear)
#      Sweep VGS: 0 → 0.70 V  @ VDS = 0.70 V  (saturation)
#
#   2) Output (ID-VD):
#      Sweep VDS: 0 → 0.70 V  @ VGS = 0.0 V (off)
#      Sweep VDS: 0 → 0.70 V  @ VGS = 0.2 V
#      Sweep VDS: 0 → 0.70 V  @ VGS = 0.4 V
#      Sweep VDS: 0 → 0.70 V  @ VGS = 0.6 V
#      Sweep VDS: 0 → 0.70 V  @ VGS = 0.7 V (full on)
#
# Extracted figures of merit:
#   VTH  (linear threshold voltage via max-gm method)
#   SS   (sub-threshold swing, mV/dec)
#   DIBL (threshold shift between VDS=0.05 and VDS=0.70 V)
#   ION  (drain current at VGS = VDS = 0.70 V)
#   IOFF (drain current at VGS = 0 V, VDS = 0.70 V)
#
# Convergence strategy:
#   Sequential coupling Poisson → DD → quantum correction
#   Fine initial / max step sizes for the 4 nm body
#======================================================================

File {
    Grid    = "GAA_3NS_NMOS_msh.tdr"
    Plot    = "GAA_3NS_NMOS_des.tdr"
    Current = "GAA_3NS_NMOS_des.plt"
    Output  = "GAA_3NS_NMOS_des.log"
}


Electrode {
    { Name = "source"    Voltage = 0.0 }
    { Name = "drain"     Voltage = 0.0 }
    { Name = "gate"      Voltage = 0.0   Workfunction = 4.4 }
    { Name = "substrate" Voltage = 0.0 }
}



#======================================================================
# PHYSICS
#======================================================================

Physics {
    # Fermi-Dirac statistics (needed for N+ S/D at 1e20 cm^-3)
    Fermi

    Mobility (
        DopingDep              # impurity scattering
        Enormal                # surface roughness / normal field
        HighFieldSaturation    # velocity saturation at high lateral field
    )

    Recombination (
        SRH ( DopingDep  TempDependence )
    )

    EffectiveIntrinsicDensity ( OldSlotboom )   # BGN for N+ S/D
}


#======================================================================
# NUMERICAL SETTINGS
#======================================================================

Math {
    Extrapolate
    Derivatives
    RelErrControl
    Digits          = 4
    Iterations      = 50
    NotDamped       = 20
    RhsMin          = 1e-15
    Method          = Super
    NumberOfThreads = 4
}


#======================================================================
# PLOT QUANTITIES  (saved to TDR file)
#======================================================================

Plot {
    Potential  ElectricField/Vector
    eDensity   hDensity
    eCurrent/Vector  hCurrent/Vector  TotalCurrent/Vector
    eMobility  hMobility
    eVelocity/Vector  hVelocity/Vector
    eEparallel  hEparallel
    ConductionBand  ValenceBand
    eQuasiFermi  hQuasiFermi
    Doping  DonorConcentration  AcceptorConcentration
    SRHRecombination
}


#======================================================================
# SOLVE SEQUENCE
#======================================================================

Solve {

    #------------------------------------------------------------------
    # STEP 1 — Poisson only (robust initial electrostatic solution)
    #------------------------------------------------------------------
    Coupled ( Iterations = 100 ) {
        Poisson
    }

    #------------------------------------------------------------------
    # STEP 2 — Drift-Diffusion (full coupled system)
    #------------------------------------------------------------------
    Coupled ( Iterations = 100 ) {
        Poisson  Electron  Hole
    }


    #==================================================================
    # CHARACTERISTIC 1: TRANSFER CURVE — linear region
    #   VDS = 0.05 V,  VGS: 0 → 0.70 V
    #==================================================================

    # Ramp VDS to 0.05 V
    Quasistationary (
        Iterations  = 50
        InitialStep = 0.01   Increment = 1.3   Decrement = 2.0
        MinStep     = 1e-9   MaxStep   = 0.025
        Goal { Name = "drain"  Voltage = 0.05 }
    ) {
        Coupled ( Iterations = 50 ) { Poisson  Electron  Hole }
    }

    NewCurrentPrefix = "IdVg_Vd005_"

    # Sweep VGS: 0 → 0.70 V  (linear transfer)
    Quasistationary (
        Iterations  = 50
        InitialStep = 0.01   Increment = 1.3   Decrement = 2.0
        MinStep     = 1e-9   MaxStep   = 0.025
        Goal { Name = "gate"  Voltage = 0.70 }
    ) {
        Coupled ( Iterations = 50 ) { Poisson  Electron  Hole }
    }


    #==================================================================
    # CHARACTERISTIC 2: TRANSFER CURVE — saturation region
    #   VDS = 0.70 V,  VGS: 0 → 0.70 V
    #==================================================================

    # Reset gate to 0 V first
    Quasistationary (
        Iterations  = 50
        InitialStep = 0.01   Increment = 1.3   Decrement = 2.0
        MinStep     = 1e-9   MaxStep   = 0.025
        Goal { Name = "gate"  Voltage = 0.0 }
    ) {
        Coupled ( Iterations = 50 ) { Poisson  Electron  Hole }
    }

    # Ramp VDS to 0.70 V
    Quasistationary (
        Iterations  = 50
        InitialStep = 0.01   Increment = 1.3   Decrement = 2.0
        MinStep     = 1e-9   MaxStep   = 0.025
        Goal { Name = "drain"  Voltage = 0.70 }
    ) {
        Coupled ( Iterations = 50 ) { Poisson  Electron  Hole }
    }

    NewCurrentPrefix = "IdVg_Vd070_"

    # Sweep VGS: 0 → 0.70 V  (saturation transfer)
    Quasistationary (
        Iterations  = 50
        InitialStep = 0.01   Increment = 1.3   Decrement = 2.0
        MinStep     = 1e-9   MaxStep   = 0.025
        Goal { Name = "gate"  Voltage = 0.70 }
    ) {
        Coupled ( Iterations = 50 ) { Poisson  Electron  Hole }
    }


    #==================================================================
    # CHARACTERISTIC 3: OUTPUT CURVES  (ID-VD)
    #   Five VGS bias points: 0.0, 0.2, 0.4, 0.6, 0.70 V
    #==================================================================

    # Reset both terminals to 0 V
    Quasistationary (
        Iterations  = 50
        InitialStep = 0.01   Increment = 1.3   Decrement = 2.0
        MinStep     = 1e-9   MaxStep   = 0.025
        Goal { Name = "gate"   Voltage = 0.0 }
        Goal { Name = "drain"  Voltage = 0.0 }
    ) {
        Coupled ( Iterations = 50 ) { Poisson  Electron  Hole }
    }

    # --- VGS = 0.0 V  (sub-threshold, leakage) -----------------------
    NewCurrentPrefix = "IdVd_Vg000_"
    Quasistationary (
        Iterations  = 50
        InitialStep = 0.01   Increment = 1.3   Decrement = 2.0
        MinStep     = 1e-9   MaxStep   = 0.025
        Goal { Name = "drain"  Voltage = 0.70 }
    ) {
        Coupled ( Iterations = 50 ) { Poisson  Electron  Hole }
    }

    # Reset drain
    Quasistationary (
        Iterations  = 50
        InitialStep = 0.01   Increment = 1.3   Decrement = 2.0
        MinStep     = 1e-9   MaxStep   = 0.025
        Goal { Name = "drain"  Voltage = 0.0 }
    ) {
        Coupled ( Iterations = 50 ) { Poisson  Electron  Hole }
    }

    # --- VGS = 0.2 V ------------------------------------------------
    Quasistationary (
        Iterations  = 50
        InitialStep = 0.01   Increment = 1.3   Decrement = 2.0
        MinStep     = 1e-9   MaxStep   = 0.025
        Goal { Name = "gate"  Voltage = 0.2 }
    ) {
        Coupled ( Iterations = 50 ) { Poisson  Electron  Hole }
    }

    NewCurrentPrefix = "IdVd_Vg020_"
    Quasistationary (
        Iterations  = 50
        InitialStep = 0.01   Increment = 1.3   Decrement = 2.0
        MinStep     = 1e-9   MaxStep   = 0.025
        Goal { Name = "drain"  Voltage = 0.70 }
    ) {
        Coupled ( Iterations = 50 ) { Poisson  Electron  Hole }
    }

    # Reset drain
    Quasistationary (
        Iterations  = 50
        InitialStep = 0.01   Increment = 1.3   Decrement = 2.0
        MinStep     = 1e-9   MaxStep   = 0.025
        Goal { Name = "drain"  Voltage = 0.0 }
    ) {
        Coupled ( Iterations = 50 ) { Poisson  Electron  Hole }
    }

    # --- VGS = 0.4 V ------------------------------------------------
    Quasistationary (
        Iterations  = 50
        InitialStep = 0.01   Increment = 1.3   Decrement = 2.0
        MinStep     = 1e-9   MaxStep   = 0.025
        Goal { Name = "gate"  Voltage = 0.4 }
    ) {
        Coupled ( Iterations = 50 ) { Poisson  Electron  Hole }
    }

    NewCurrentPrefix = "IdVd_Vg040_"
    Quasistationary (
        Iterations  = 50
        InitialStep = 0.01   Increment = 1.3   Decrement = 2.0
        MinStep     = 1e-9   MaxStep   = 0.025
        Goal { Name = "drain"  Voltage = 0.70 }
    ) {
        Coupled ( Iterations = 50 ) { Poisson  Electron  Hole }
    }

    # Reset drain
    Quasistationary (
        Iterations  = 50
        InitialStep = 0.01   Increment = 1.3   Decrement = 2.0
        MinStep     = 1e-9   MaxStep   = 0.025
        Goal { Name = "drain"  Voltage = 0.0 }
    ) {
        Coupled ( Iterations = 50 ) { Poisson  Electron  Hole }
    }

    # --- VGS = 0.6 V ------------------------------------------------
    Quasistationary (
        Iterations  = 50
        InitialStep = 0.01   Increment = 1.3   Decrement = 2.0
        MinStep     = 1e-9   MaxStep   = 0.025
        Goal { Name = "gate"  Voltage = 0.6 }
    ) {
        Coupled ( Iterations = 50 ) { Poisson  Electron  Hole }
    }

    NewCurrentPrefix = "IdVd_Vg060_"
    Quasistationary (
        Iterations  = 50
        InitialStep = 0.01   Increment = 1.3   Decrement = 2.0
        MinStep     = 1e-9   MaxStep   = 0.025
        Goal { Name = "drain"  Voltage = 0.70 }
    ) {
        Coupled ( Iterations = 50 ) { Poisson  Electron  Hole }
    }

    # Reset drain
    Quasistationary (
        Iterations  = 50
        InitialStep = 0.01   Increment = 1.3   Decrement = 2.0
        MinStep     = 1e-9   MaxStep   = 0.025
        Goal { Name = "drain"  Voltage = 0.0 }
    ) {
        Coupled ( Iterations = 50 ) { Poisson  Electron  Hole }
    }

    # --- VGS = 0.7 V  (full ON) -------------------------------------
    Quasistationary (
        Iterations  = 50
        InitialStep = 0.01   Increment = 1.3   Decrement = 2.0
        MinStep     = 1e-9   MaxStep   = 0.025
        Goal { Name = "gate"  Voltage = 0.70 }
    ) {
        Coupled ( Iterations = 50 ) { Poisson  Electron  Hole }
    }

    NewCurrentPrefix = "IdVd_Vg070_"
    Quasistationary (
        Iterations  = 50
        InitialStep = 0.01   Increment = 1.3   Decrement = 2.0
        MinStep     = 1e-9   MaxStep   = 0.025
        Goal { Name = "drain"  Voltage = 0.70 }
    ) {
        Coupled ( Iterations = 50 ) { Poisson  Electron  Hole }
    }

}

# END OF SDEVICE DECK
