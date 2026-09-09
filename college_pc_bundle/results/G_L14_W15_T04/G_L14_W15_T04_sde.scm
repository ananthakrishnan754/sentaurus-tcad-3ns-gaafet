; Run: G_L14_W15_T04 (Lg=14nm, Wns=15.0nm, Tns=4.0nm, N=3)
(sde:clear)
(sdegeo:set-default-boolean "ABA")

;--- Substrate & BDI Base ---
(sdegeo:create-cuboid (position -0.0150 -0.0115 -0.0340) (position 0.0290 0.0115 -0.0140) "Silicon" "R.Substrate")
(sdegeo:create-cuboid (position -0.0150 -0.0115 -0.0140) (position 0.0290 0.0115 -0.0040) "SiO2" "R.BDI")

;--- Nanosheet Layer 1 ---
(sdegeo:create-cuboid (position -0.0150 -0.0075 0.0000) (position 0.0000 0.0075 0.0040) "Silicon" "R.Source1")
(sdegeo:create-cuboid (position 0.0000 -0.0075 0.0000) (position 0.0140 0.0075 0.0040) "Silicon" "R.Channel1")
(sdegeo:create-cuboid (position 0.0140 -0.0075 0.0000) (position 0.0290 0.0075 0.0040) "Silicon" "R.Drain1")
;--- Nanosheet Layer 2 ---
(sdegeo:create-cuboid (position -0.0150 -0.0075 0.0120) (position 0.0000 0.0075 0.0160) "Silicon" "R.Source2")
(sdegeo:create-cuboid (position 0.0000 -0.0075 0.0120) (position 0.0140 0.0075 0.0160) "Silicon" "R.Channel2")
(sdegeo:create-cuboid (position 0.0140 -0.0075 0.0120) (position 0.0290 0.0075 0.0160) "Silicon" "R.Drain2")
;--- Nanosheet Layer 3 ---
(sdegeo:create-cuboid (position -0.0150 -0.0075 0.0240) (position 0.0000 0.0075 0.0280) "Silicon" "R.Source3")
(sdegeo:create-cuboid (position 0.0000 -0.0075 0.0240) (position 0.0140 0.0075 0.0280) "Silicon" "R.Channel3")
(sdegeo:create-cuboid (position 0.0140 -0.0075 0.0240) (position 0.0290 0.0075 0.0280) "Silicon" "R.Drain3")

;--- Outer Metal Gate Block ---
(sdegeo:create-cuboid (position 0.0000 -0.0115 -0.0040) (position 0.0140 0.0115 0.0320) "Metal" "R.Gate")

;--- Oxide & Channel Core 1 ---
(sdegeo:create-cuboid (position 0.0000 -0.0085 -0.0010) (position 0.0140 0.0085 0.0050) "HfO2" "R.Oxide1")
(sdegeo:create-cuboid (position 0.0000 -0.0075 0.0000) (position 0.0140 0.0075 0.0040) "Silicon" "R.Channel1_Core")
;--- Oxide & Channel Core 2 ---
(sdegeo:create-cuboid (position 0.0000 -0.0085 0.0110) (position 0.0140 0.0085 0.0170) "HfO2" "R.Oxide2")
(sdegeo:create-cuboid (position 0.0000 -0.0075 0.0120) (position 0.0140 0.0075 0.0160) "Silicon" "R.Channel2_Core")
;--- Oxide & Channel Core 3 ---
(sdegeo:create-cuboid (position 0.0000 -0.0085 0.0230) (position 0.0140 0.0085 0.0290) "HfO2" "R.Oxide3")
(sdegeo:create-cuboid (position 0.0000 -0.0075 0.0240) (position 0.0140 0.0075 0.0280) "Silicon" "R.Channel3_Core")

;--- Doping Profiles ---
(sdedr:define-constant-profile "Dop.Source" "PhosphorusActiveConcentration" 1e20)
(sdedr:define-constant-profile "Dop.Drain" "PhosphorusActiveConcentration" 1e20)
(sdedr:define-constant-profile "Dop.Channel" "BoronActiveConcentration" 1e15)
(sdedr:define-constant-profile-region "Place.Source1" "Dop.Source" "R.Source1")
(sdedr:define-constant-profile-region "Place.Drain1" "Dop.Drain" "R.Drain1")
(sdedr:define-constant-profile-region "Place.Ch1" "Dop.Channel" "R.Channel1_Core")
(sdedr:define-constant-profile-region "Place.Source2" "Dop.Source" "R.Source2")
(sdedr:define-constant-profile-region "Place.Drain2" "Dop.Drain" "R.Drain2")
(sdedr:define-constant-profile-region "Place.Ch2" "Dop.Channel" "R.Channel2_Core")
(sdedr:define-constant-profile-region "Place.Source3" "Dop.Source" "R.Source3")
(sdedr:define-constant-profile-region "Place.Drain3" "Dop.Drain" "R.Drain3")
(sdedr:define-constant-profile-region "Place.Ch3" "Dop.Channel" "R.Channel3_Core")
(sdedr:define-constant-profile-region "Place.Sub" "Dop.Channel" "R.Substrate")

;--- Contacts ---
(sdegeo:define-contact-set "source" 4.0 (color:rgb 1 0 0) "##")
(sdegeo:define-contact-set "drain" 4.0 (color:rgb 0 0 1) "##")
(sdegeo:define-contact-set "gate" 4.0 (color:rgb 0 1 0) "##")
(sdegeo:define-contact-set "substrate" 4.0 (color:rgb 0.5 0.5 0.5) "##")
(sdegeo:set-current-contact-set "source")
(sdegeo:set-contact (find-face-id (position -0.0150 0.0 0.0020)) "source")
(sdegeo:set-contact (find-face-id (position -0.0150 0.0 0.0140)) "source")
(sdegeo:set-contact (find-face-id (position -0.0150 0.0 0.0260)) "source")
(sdegeo:set-current-contact-set "drain")
(sdegeo:set-contact (find-face-id (position 0.0290 0.0 0.0020)) "drain")
(sdegeo:set-contact (find-face-id (position 0.0290 0.0 0.0140)) "drain")
(sdegeo:set-contact (find-face-id (position 0.0290 0.0 0.0260)) "drain")
(sdegeo:set-current-contact-set "gate")
(sdegeo:set-contact (find-face-id (position 0.0070 0.0 0.0320)) "gate")
(sdegeo:set-current-contact-set "substrate")
(sdegeo:set-contact (find-face-id (position 0.0070 0.0 -0.0340)) "substrate")

;======================================================================
; DYNAMIC & REGION-ADAPTIVE MESHING
;======================================================================
; 1. Coarse Global Window (Saves nodes in non-critical areas)
(sdedr:define-refeval-window "RefWin.Global" "Cuboid"
    (position -0.0150 -0.0115 -0.0340) (position 0.0290 0.0115 0.0320))
(sdedr:define-refinement-size "RefDef.Global" 0.006 0.006 0.006 0.002 0.002 0.002)
(sdedr:define-refinement-placement "RefPlace.Global" "RefDef.Global" "RefWin.Global")

; 2. Coarse Substrate & BDI Base (Zero current flow)
(sdedr:define-refeval-window "RefWin.SubBDI" "Cuboid"
    (position -0.0150 -0.0115 -0.0340) (position 0.0290 0.0115 -0.0040))
(sdedr:define-refinement-size "RefDef.SubBDI" 0.008 0.008 0.008 0.004 0.004 0.004)
(sdedr:define-refinement-placement "RefPlace.SubBDI" "RefDef.SubBDI" "RefWin.SubBDI")

; 3. Fine Active Inversion Channels (Precision where carriers flow)
(sdedr:define-refeval-window "RefWin.Chan" "Cuboid"
    (position -0.0010 -0.0090 -0.0015)
    (position 0.0150 0.0090 0.0295))
(sdedr:define-refinement-size "RefDef.Chan" 0.0015 0.0015 0.0010 0.0004 0.0004 0.0003)
(sdedr:define-refinement-placement "RefPlace.Chan" "RefDef.Chan" "RefWin.Chan")

; Interface & Doping Transitions
(sdedr:define-refinement-function "RefDef.Chan" "MaxLenInt" "Silicon" "HfO2" 0.0003 1.5 "DoubleSide")
(sdedr:define-refinement-function "RefDef.Chan" "MaxTransDiff" "DopingConcentration" 1)

(sde:build-mesh "snmesh" "" "G_L14_W15_T04")
