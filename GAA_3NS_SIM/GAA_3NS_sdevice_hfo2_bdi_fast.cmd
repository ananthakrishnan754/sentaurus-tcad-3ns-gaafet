#======================================================================
# 3-STACK NANOSHEET NMOS GAAFET — HfO2 BDI EXPERIMENTAL CASE (Tbdi = 51.3 nm)
# Sentaurus Device (SDevice) - NEW EXPERIMENTAL COPY
#
# Produces device characteristics for HfO2 BDI case:
#   1) Transfer (ID-VG): VDS = 0.05 V (linear) & VDS = 0.70 V (saturation)
#   2) Output (ID-VD): VGS = 0.0 V, 0.2 V, 0.4 V, 0.6 V, 0.7 V
#======================================================================

File {
    Grid    = "GAA_3NS_NMOS_hfo2_fast_msh.tdr"
    Plot    = "GAA_3NS_NMOS_hfo2_fast_des.tdr"
    Current = "GAA_3NS_NMOS_hfo2_fast_des.plt"
    Output  = "GAA_3NS_NMOS_hfo2_fast_des.log"
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
    Digits          = 3
    Iterations      = 60
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
        InitialStep = 0.002  Increment = 1.4   Decrement = 4.0
        MinStep     = 1e-9   MaxStep   = 0.01
        Goal { Name = "drain"  Voltage = 0.05 }
    ) {
        Coupled ( Iterations = 50 ) { Poisson  Electron  Hole }
    }

    NewCurrentPrefix = "IdVg_Vd005_hfo2_fast_"

    # Sweep VGS: 0 → 0.70 V  (linear transfer)
    Quasistationary (
        Iterations  = 50
        InitialStep = 0.002  Increment = 1.4   Decrement = 4.0
        MinStep     = 1e-9   MaxStep   = 0.01
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
        InitialStep = 0.002  Increment = 1.4   Decrement = 4.0
        MinStep     = 1e-9   MaxStep   = 0.01
        Goal { Name = "gate"  Voltage = 0.0 }
    ) {
        Coupled ( Iterations = 50 ) { Poisson  Electron  Hole }
    }

    # Ramp VDS to 0.70 V
    Quasistationary (
        Iterations  = 50
        InitialStep = 0.002  Increment = 1.4   Decrement = 4.0
        MinStep     = 1e-9   MaxStep   = 0.01
        Goal { Name = "drain"  Voltage = 0.70 }
    ) {
        Coupled ( Iterations = 50 ) { Poisson  Electron  Hole }
    }

    NewCurrentPrefix = "IdVg_Vd070_hfo2_fast_"

    # Sweep VGS: 0 → 0.70 V  (saturation transfer)
    Quasistationary (
        Iterations  = 50
        InitialStep = 0.002  Increment = 1.4   Decrement = 4.0
        MinStep     = 1e-9   MaxStep   = 0.01
        Goal { Name = "gate"  Voltage = 0.70 }
    ) {
        Coupled ( Iterations = 50 ) { Poisson  Electron  Hole }
    }


    #==================================================================
    # CHARACTERISTIC 3: OUTPUT CURVES  (ID-VD)
    #==================================================================

    # Reset both terminals to 0 V
    Quasistationary (
        Iterations  = 50
        InitialStep = 0.002  Increment = 1.4   Decrement = 4.0
        MinStep     = 1e-9   MaxStep   = 0.01
        Goal { Name = "gate"   Voltage = 0.0 }
        Goal { Name = "drain"  Voltage = 0.0 }
    ) {
        Coupled ( Iterations = 50 ) { Poisson  Electron  Hole }
    }

    # --- VGS = 0.0 V  (sub-threshold, leakage) -----------------------
    NewCurrentPrefix = "IdVd_Vg000_hfo2_fast_"
    Quasistationary (
        Iterations  = 50
        InitialStep = 0.002  Increment = 1.4   Decrement = 4.0
        MinStep     = 1e-9   MaxStep   = 0.01
        Goal { Name = "drain"  Voltage = 0.70 }
    ) {
        Coupled ( Iterations = 50 ) { Poisson  Electron  Hole }
    }

    # Reset drain
    Quasistationary (
        Iterations  = 50
        InitialStep = 0.002  Increment = 1.4   Decrement = 4.0
        MinStep     = 1e-9   MaxStep   = 0.01
        Goal { Name = "drain"  Voltage = 0.0 }
    ) {
        Coupled ( Iterations = 50 ) { Poisson  Electron  Hole }
    }

    # --- VGS = 0.2 V ------------------------------------------------
    Quasistationary (
        Iterations  = 50
        InitialStep = 0.002  Increment = 1.4   Decrement = 4.0
        MinStep     = 1e-9   MaxStep   = 0.01
        Goal { Name = "gate"  Voltage = 0.2 }
    ) {
        Coupled ( Iterations = 50 ) { Poisson  Electron  Hole }
    }

    NewCurrentPrefix = "IdVd_Vg020_hfo2_fast_"
    Quasistationary (
        Iterations  = 50
        InitialStep = 0.002  Increment = 1.4   Decrement = 4.0
        MinStep     = 1e-9   MaxStep   = 0.01
        Goal { Name = "drain"  Voltage = 0.70 }
    ) {
        Coupled ( Iterations = 50 ) { Poisson  Electron  Hole }
    }

    # Reset drain
    Quasistationary (
        Iterations  = 50
        InitialStep = 0.002  Increment = 1.4   Decrement = 4.0
        MinStep     = 1e-9   MaxStep   = 0.01
        Goal { Name = "drain"  Voltage = 0.0 }
    ) {
        Coupled ( Iterations = 50 ) { Poisson  Electron  Hole }
    }

    # --- VGS = 0.4 V ------------------------------------------------
    Quasistationary (
        Iterations  = 50
        InitialStep = 0.002  Increment = 1.4   Decrement = 4.0
        MinStep     = 1e-9   MaxStep   = 0.01
        Goal { Name = "gate"  Voltage = 0.4 }
    ) {
        Coupled ( Iterations = 50 ) { Poisson  Electron  Hole }
    }

    NewCurrentPrefix = "IdVd_Vg040_hfo2_fast_"
    Quasistationary (
        Iterations  = 50
        InitialStep = 0.002  Increment = 1.4   Decrement = 4.0
        MinStep     = 1e-9   MaxStep   = 0.01
        Goal { Name = "drain"  Voltage = 0.70 }
    ) {
        Coupled ( Iterations = 50 ) { Poisson  Electron  Hole }
    }

    # Reset drain
    Quasistationary (
        Iterations  = 50
        InitialStep = 0.002  Increment = 1.4   Decrement = 4.0
        MinStep     = 1e-9   MaxStep   = 0.01
        Goal { Name = "drain"  Voltage = 0.0 }
    ) {
        Coupled ( Iterations = 50 ) { Poisson  Electron  Hole }
    }

    # --- VGS = 0.6 V ------------------------------------------------
    Quasistationary (
        Iterations  = 50
        InitialStep = 0.002  Increment = 1.4   Decrement = 4.0
        MinStep     = 1e-9   MaxStep   = 0.01
        Goal { Name = "gate"  Voltage = 0.6 }
    ) {
        Coupled ( Iterations = 50 ) { Poisson  Electron  Hole }
    }

    NewCurrentPrefix = "IdVd_Vg060_hfo2_fast_"
    Quasistationary (
        Iterations  = 50
        InitialStep = 0.002  Increment = 1.4   Decrement = 4.0
        MinStep     = 1e-9   MaxStep   = 0.01
        Goal { Name = "drain"  Voltage = 0.70 }
    ) {
        Coupled ( Iterations = 50 ) { Poisson  Electron  Hole }
    }

    # Reset drain
    Quasistationary (
        Iterations  = 50
        InitialStep = 0.002  Increment = 1.4   Decrement = 4.0
        MinStep     = 1e-9   MaxStep   = 0.01
        Goal { Name = "drain"  Voltage = 0.0 }
    ) {
        Coupled ( Iterations = 50 ) { Poisson  Electron  Hole }
    }

    # --- VGS = 0.7 V  (full ON) -------------------------------------
    Quasistationary (
        Iterations  = 50
        InitialStep = 0.002  Increment = 1.4   Decrement = 4.0
        MinStep     = 1e-9   MaxStep   = 0.01
        Goal { Name = "gate"  Voltage = 0.70 }
    ) {
        Coupled ( Iterations = 50 ) { Poisson  Electron  Hole }
    }

    NewCurrentPrefix = "IdVd_Vg070_hfo2_fast_"
    Quasistationary (
        Iterations  = 50
        InitialStep = 0.002  Increment = 1.4   Decrement = 4.0
        MinStep     = 1e-9   MaxStep   = 0.01
        Goal { Name = "drain"  Voltage = 0.70 }
    ) {
        Coupled ( Iterations = 50 ) { Poisson  Electron  Hole }
    }

}

# END OF SDEVICE DECK
