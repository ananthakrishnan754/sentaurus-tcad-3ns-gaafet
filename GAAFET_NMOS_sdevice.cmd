#======================================================================
# 3-STACK NANOSHEET NMOS GAAFET
# Sentaurus Device (SDevice) Simulation Deck
#
# Simulation:
#   Step 1 — Poisson only (initial electrostatics)
#   Step 2 — Add Electron + Hole transport
#   Step 3 — Enable quantum correction (eQuantumPotential)
#   Step 4 — Ramp VDS to 0.05 V
#   Step 5 — ID-VG sweep  VG: 0 → 0.70 V  @ VDS = 0.05 V
#
# FIXES APPLIED
# ---------------------------------------------------------------------
# 1. Closing brace of Solve{} uses only "}" — stray semicolon removed.
# 2. NewCurrentPrefix is confirmed inside Solve{} braces.
# 3. MaxStep tightened to 0.005 V on VDS ramp for better convergence.
#======================================================================


File {

    Grid    = "GAAFET_3Sheet_NMOS_msh.tdr"

    Plot    = "GAAFET_NMOS_des.tdr"

    Current = "GAAFET_NMOS_des.plt"

    Output  = "GAAFET_NMOS_des.log"
}


Electrode {

    {
        Name    = "source"
        Voltage = 0.0
    }

    {
        Name    = "drain"
        Voltage = 0.0
    }

    {
        Name         = "gate"
        Voltage      = 0.0

        # NMOS metal work function.
        # Calibrate this value rather than treating it as fixed.
        Workfunction = 4.4
    }

    {
        Name         = "substrate"
        Voltage      = 0.0
    }
}



#=====================================================================
# GLOBAL PHYSICS
#=====================================================================

Physics {

    # Degenerate carrier statistics (important for N+ S/D at 1e20).
    Fermi


    #------------------------------------------------------------------
    # MOBILITY
    #   Computed locally by SDevice considering:
    #     - Doping (DopingDep)
    #     - Normal electric field at gate interface (Enormal)
    #     - High lateral field / velocity saturation (HighFieldSaturation)
    #------------------------------------------------------------------

    Mobility (
        DopingDep
        Enormal
        HighFieldSaturation
    )


    #------------------------------------------------------------------
    # RECOMBINATION
    #------------------------------------------------------------------

    Recombination (
        SRH (
            DopingDep
            TempDependence
        )
    )


    #------------------------------------------------------------------
    # EFFECTIVE INTRINSIC DENSITY
    # Bandgap narrowing correction; important for N+ 1e20 S/D.
    #------------------------------------------------------------------

    EffectiveIntrinsicDensity (
        OldSlotboom
    )


    #------------------------------------------------------------------
    # QUANTUM CORRECTION
    # Critical: nanosheet thickness = 4 nm → strong quantisation.
    #------------------------------------------------------------------

    eQuantumPotential
}


#=====================================================================
# NUMERICAL SETTINGS
#=====================================================================

Math {

    Extrapolate

    Derivatives

    RelErrControl

    Digits = 5

    Iterations = 30

    NotDamped = 100

    Method = ParDiSo

    NumberOfThreads = 4
}


#=====================================================================
# QUANTITIES SAVED TO TDR
#=====================================================================

Plot {

    # Electrostatics
    Potential
    ElectricField/Vector

    # Carrier concentrations
    eDensity
    hDensity

    # Currents
    eCurrent/Vector
    hCurrent/Vector
    TotalCurrent/Vector

    # Mobility
    eMobility
    hMobility

    # Velocity
    eVelocity/Vector
    hVelocity/Vector

    # Parallel field components
    eEparallel
    hEparallel

    # Energy bands
    ConductionBand
    ValenceBand

    # Quasi-Fermi levels
    eQuasiFermi
    hQuasiFermi

    # Doping
    Doping
    DonorConcentration
    AcceptorConcentration

    # Recombination
    SRHRecombination

    # Quantum correction
    eQuantumPotential
}


#=====================================================================
# SOLUTION SEQUENCE
#=====================================================================

Solve {

    #=================================================================
    # STEP 1 — Initial electrostatic solution (Poisson only)
    #=================================================================

    Coupled (
        Iterations = 100
        LineSearchDamping = 1e-4
    ) {
        Poisson
    }


    #=================================================================
    # STEP 2 — Add electron and hole transport
    #=================================================================

    Coupled (
        Iterations = 100
    ) {
        Poisson
        Electron
        Hole
    }


    #=================================================================
    # STEP 3 — Enable quantum correction
    #=================================================================

    Coupled (
        Iterations = 100
    ) {
        Poisson
        Electron
        Hole
        eQuantumPotential
    }


    #=================================================================
    # STEP 4 — Ramp drain to VDS = 0.05 V
    #
    # MaxStep tightened from 0.01 to 0.005 V to help convergence
    # with quantum correction active in a 4 nm nanosheet channel.
    #=================================================================

    Quasistationary (

        InitialStep      = 1e-3
        Increment        = 1.3
        Decrement        = 2.0
        MinStep          = 1e-6
        MaxStep          = 0.005

        Goal {
            Name    = "drain"
            Voltage = 0.05
        }

    ) {
        Coupled {
            Poisson
            Electron
            Hole
            eQuantumPotential
        }
    }


    #=================================================================
    # STEP 5 — Low-VDS ID-VG sweep
    #
    # VG  : 0 → 0.70 V   (captures sub-threshold, VTH, ON-state)
    # VDS : 0.05 V        (linear region — extracts VTH, SS, DIBL)
    #
    # NewCurrentPrefix is placed INSIDE Solve{} between steps.
    # FIX: Previously had stray ";" — removed.
    #=================================================================

    NewCurrentPrefix = "IdVg_Vd005_"

    Quasistationary (

        InitialStep      = 1e-3
        Increment        = 1.3
        Decrement        = 2.0
        MinStep          = 1e-6
        MaxStep          = 0.01

        Goal {
            Name    = "gate"
            Voltage = 0.70
        }

    ) {
        Coupled {
            Poisson
            Electron
            Hole
            eQuantumPotential
        }
    }

}
