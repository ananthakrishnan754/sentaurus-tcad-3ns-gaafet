# SDevice Command Deck: G_L18_W15_T04
File {
    Grid    = "G_L18_W15_T04_msh.tdr"
    Plot    = "G_L18_W15_T04_des.tdr"
    Current = "G_L18_W15_T04_des.plt"
    Output  = "G_L18_W15_T04_des.log"
}

Electrode {
    { Name = "source"    Voltage = 0.0 }
    { Name = "drain"     Voltage = 0.0 }
    { Name = "gate"      Voltage = 0.0   Workfunction = 4.4 }
    { Name = "substrate" Voltage = 0.0 }
}

Physics {
    Fermi
    Mobility (
        DopingDep
        Enormal
        HighFieldSaturation
    )
    Recombination (
        SRH ( DopingDep TempDependence )
    )
    EffectiveIntrinsicDensity ( OldSlotboom )
}

Math {
    Extrapolate
    Derivatives
    RelErrControl
    Digits          = 4
    Iterations      = 35
    NotDamped       = 25
    RhsMin          = 1e-15
    Method          = Super
    NumberOfThreads = 4
}

Plot {
    Potential ElectricField/Vector
    eDensity hDensity
    eCurrent/Vector hCurrent/Vector TotalCurrent/Vector
    eMobility eVelocity/Vector
    Doping DonorConcentration AcceptorConcentration
}

Solve {
    # 1. Equilibrium Poisson
    Coupled ( Iterations = 50 ) { Poisson }

    # 2. Initial Drift-Diffusion
    Coupled ( Iterations = 50 ) { Poisson Electron Hole }

    # 3. Linear Transfer Sweep (Vds = 0.05 V)
    Quasistationary (
        Iterations  = 35
        InitialStep = 0.02   Increment = 1.4   Decrement = 2.0
        MinStep     = 1e-5   MaxStep   = 0.05
        Goal { Name = "drain" Voltage = 0.05 }
    ) {
        Coupled ( Iterations = 35 ) { Poisson Electron Hole }
    }

    NewCurrentPrefix = "IdVg_Vd005_"

    Quasistationary (
        Iterations  = 35
        InitialStep = 0.03   Increment = 1.3   Decrement = 1.8
        MinStep     = 1e-5   MaxStep   = 0.05
        Goal { Name = "gate" Voltage = 0.70 }
    ) {
        Coupled ( Iterations = 35 ) { Poisson Electron Hole }
    }

    # 4. Output Characteristic & Ramp to Saturation (Vgs = 0.70 V, Vds: 0.05 V -> 0.70 V)
    NewCurrentPrefix = "IdVd_Vg070_"

    Quasistationary (
        Iterations  = 35
        InitialStep = 0.03   Increment = 1.4   Decrement = 1.8
        MinStep     = 1e-5   MaxStep   = 0.06
        Goal { Name = "drain" Voltage = 0.70 }
    ) {
        Coupled ( Iterations = 35 ) { Poisson Electron Hole }
    }

    # 5. Saturation Transfer Sweep (Vds = 0.70 V, sweep Vgs: 0.70 V -> 0.0 V)
    # Sweeping downward from strong inversion avoids threshold bifurcation oscillations
    NewCurrentPrefix = "IdVg_Vd070_"

    Quasistationary (
        Iterations  = 35
        InitialStep = 0.03   Increment = 1.3   Decrement = 1.8
        MinStep     = 1e-5   MaxStep   = 0.05
        Goal { Name = "gate" Voltage = 0.0 }
    ) {
        Coupled ( Iterations = 35 ) { Poisson Electron Hole }
    }
}
