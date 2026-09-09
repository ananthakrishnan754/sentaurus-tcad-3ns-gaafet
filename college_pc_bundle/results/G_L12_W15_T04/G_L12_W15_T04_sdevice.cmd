# SDevice Command Deck: G_L12_W15_T04
File {
    Grid    = "G_L12_W15_T04_msh.tdr"
    Plot    = "G_L12_W15_T04_des.tdr"
    Current = "G_L12_W15_T04_des.plt"
    Output  = "G_L12_W15_T04_des.log"
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
    Iterations      = 40
    NotDamped       = 15
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
        Iterations  = 40
        InitialStep = 0.01   Increment = 1.4   Decrement = 2.0
        MinStep     = 1e-6   MaxStep   = 0.025
        Goal { Name = "drain" Voltage = 0.05 }
    ) {
        Coupled ( Iterations = 40 ) { Poisson Electron Hole }
    }

    NewCurrentPrefix = "IdVg_Vd005_"

    Quasistationary (
        Iterations  = 40
        InitialStep = 0.02   Increment = 1.3   Decrement = 2.0
        MinStep     = 1e-6   MaxStep   = 0.035
        Goal { Name = "gate" Voltage = 0.70 }
    ) {
        Coupled ( Iterations = 40 ) { Poisson Electron Hole }
    }

    # 4. Saturation Transfer Sweep (Vds = 0.70 V)
    Quasistationary (
        Iterations  = 40
        InitialStep = 0.02   Increment = 1.3   Decrement = 2.0
        MinStep     = 1e-6   MaxStep   = 0.035
        Goal { Name = "gate" Voltage = 0.0 }
    ) {
        Coupled ( Iterations = 40 ) { Poisson Electron Hole }
    }

    Quasistationary (
        Iterations  = 40
        InitialStep = 0.02   Increment = 1.4   Decrement = 2.0
        MinStep     = 1e-6   MaxStep   = 0.05
        Goal { Name = "drain" Voltage = 0.70 }
    ) {
        Coupled ( Iterations = 40 ) { Poisson Electron Hole }
    }

    NewCurrentPrefix = "IdVg_Vd070_"

    Quasistationary (
        Iterations  = 40
        InitialStep = 0.02   Increment = 1.3   Decrement = 2.0
        MinStep     = 1e-6   MaxStep   = 0.035
        Goal { Name = "gate" Voltage = 0.70 }
    ) {
        Coupled ( Iterations = 40 ) { Poisson Electron Hole }
    }

    # 5. Output Curves (Id-Vd at Vgs = 0.70 V)
    NewCurrentPrefix = "IdVd_Vg070_"

    Quasistationary (
        Iterations  = 40
        InitialStep = 0.02   Increment = 1.4   Decrement = 2.0
        MinStep     = 1e-6   MaxStep   = 0.05
        Goal { Name = "drain" Voltage = 0.0 }
    ) {
        Coupled ( Iterations = 40 ) { Poisson Electron Hole }
    }

    Quasistationary (
        Iterations  = 40
        InitialStep = 0.02   Increment = 1.4   Decrement = 2.0
        MinStep     = 1e-6   MaxStep   = 0.05
        Goal { Name = "drain" Voltage = 0.70 }
    ) {
        Coupled ( Iterations = 40 ) { Poisson Electron Hole }
    }
}
