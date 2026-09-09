Title "Untitled"

Controls {
}

IOControls {
	EnableSections
}

Definitions {
	Constant "Dop.Source" {
		Species = "PhosphorusActiveConcentration"
		Value = 1e+20
	}
	Constant "Dop.Drain" {
		Species = "PhosphorusActiveConcentration"
		Value = 1e+20
	}
	Constant "Dop.Channel" {
		Species = "BoronActiveConcentration"
		Value = 1e+15
	}
	Refinement "RefDef.Global" {
		MaxElementSize = ( 0.006 0.006 0.006 )
		MinElementSize = ( 0.002 0.002 0.002 )
	}
	Refinement "RefDef.SubBDI" {
		MaxElementSize = ( 0.008 0.008 0.008 )
		MinElementSize = ( 0.004 0.004 0.004 )
	}
	Refinement "RefDef.Chan" {
		MaxElementSize = ( 0.0015 0.0015 0.001 )
		MinElementSize = ( 0.0004 0.0004 0.0003 )
		RefineFunction = MaxLenInt(Interface("Silicon","HfO2"), Value=0.0003, factor=1.5, DoubleSide)
		RefineFunction = MaxTransDiff(Variable = "MaxTransDiff",Value = 1)
	}
}

Placements {
	Constant "Place.Source1" {
		Reference = "Dop.Source"
		EvaluateWindow {
			Element = region ["R.Source1"]
		}
	}
	Constant "Place.Drain1" {
		Reference = "Dop.Drain"
		EvaluateWindow {
			Element = region ["R.Drain1"]
		}
	}
	Constant "Place.Ch1" {
		Reference = "Dop.Channel"
		EvaluateWindow {
			Element = region ["R.Channel1_Core"]
		}
	}
	Constant "Place.Source2" {
		Reference = "Dop.Source"
		EvaluateWindow {
			Element = region ["R.Source2"]
		}
	}
	Constant "Place.Drain2" {
		Reference = "Dop.Drain"
		EvaluateWindow {
			Element = region ["R.Drain2"]
		}
	}
	Constant "Place.Ch2" {
		Reference = "Dop.Channel"
		EvaluateWindow {
			Element = region ["R.Channel2_Core"]
		}
	}
	Constant "Place.Source3" {
		Reference = "Dop.Source"
		EvaluateWindow {
			Element = region ["R.Source3"]
		}
	}
	Constant "Place.Drain3" {
		Reference = "Dop.Drain"
		EvaluateWindow {
			Element = region ["R.Drain3"]
		}
	}
	Constant "Place.Ch3" {
		Reference = "Dop.Channel"
		EvaluateWindow {
			Element = region ["R.Channel3_Core"]
		}
	}
	Constant "Place.Sub" {
		Reference = "Dop.Channel"
		EvaluateWindow {
			Element = region ["R.Substrate"]
		}
	}
	Refinement "RefPlace.Global" {
		Reference = "RefDef.Global"
		RefineWindow = Cuboid [(-0.015 -0.0115 -0.034) (0.027 0.0115 0.032)]
	}
	Refinement "RefPlace.SubBDI" {
		Reference = "RefDef.SubBDI"
		RefineWindow = Cuboid [(-0.015 -0.0115 -0.034) (0.027 0.0115 -0.004)]
	}
	Refinement "RefPlace.Chan" {
		Reference = "RefDef.Chan"
		RefineWindow = Cuboid [(-0.001 -0.009 -0.0015) (0.013 0.009 0.0295)]
	}
}

