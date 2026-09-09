; Run: G_L18_W15_T04 (Lg=18nm, Wns=15.0nm, Tns=4.0nm, N=3)
(sde:clear)
(sdegeo:set-default-boolean "ABA")

;--- Substrate & BDI Base ---
(sdegeo:create-cuboid (position -0.0150 -0.0115 -0.0340) (position 0.0330 0.0115 -0.0140) "Silicon" "R.Substrate")
(sdegeo:create-cuboid (position -0.0150 -0.0115 -0.0140) (position 0.0330 0.0115 -0.0040) "SiO2" "R.BDI")

;--- Gate Metal Shell ---
(sdegeo:create-cuboid (position 0.0000 -0.0115 -0.0040) (position 0.0180 0.0115 0.0320) "TiN" "R.GateMetal")

;--- Low-k Inner Spacers ---
(sdegeo:create-cuboid (position -0.0150 -0.0115 -0.0040) (position 0.0000 0.0115 0.0320) "Si3N4" "R.SpacerS")
(sdegeo:create-cuboid (position 0.0180 -0.0115 -0.0040) (position 0.0330 0.0115 0.0320) "Si3N4" "R.SpacerD")

;--- Nanosheet Stack 1 ---
(sdegeo:create-cuboid (position 0.0000 -0.0085 -0.0010) (position 0.0180 0.0085 0.0050) "HfO2" "R.Oxide1")
(sdegeo:create-cuboid (position 0.0000 -0.0075 0.0000) (position 0.0180 0.0075 0.0040) "Silicon" "R.Channel1")
(sdegeo:create-cuboid (position -0.0150 -0.0075 0.0000) (position 0.0000 0.0075 0.0040) "Silicon" "R.Source1")
(sdegeo:create-cuboid (position 0.0180 -0.0075 0.0000) (position 0.0330 0.0075 0.0040) "Silicon" "R.Drain1")

;--- Nanosheet Stack 2 ---
(sdegeo:create-cuboid (position 0.0000 -0.0085 0.0110) (position 0.0180 0.0085 0.0170) "HfO2" "R.Oxide2")
(sdegeo:create-cuboid (position 0.0000 -0.0075 0.0120) (position 0.0180 0.0075 0.0160) "Silicon" "R.Channel2")
(sdegeo:create-cuboid (position -0.0150 -0.0075 0.0120) (position 0.0000 0.0075 0.0160) "Silicon" "R.Source2")
(sdegeo:create-cuboid (position 0.0180 -0.0075 0.0120) (position 0.0330 0.0075 0.0160) "Silicon" "R.Drain2")

;--- Nanosheet Stack 3 ---
(sdegeo:create-cuboid (position 0.0000 -0.0085 0.0230) (position 0.0180 0.0085 0.0290) "HfO2" "R.Oxide3")
(sdegeo:create-cuboid (position 0.0000 -0.0075 0.0240) (position 0.0180 0.0075 0.0280) "Silicon" "R.Channel3")
(sdegeo:create-cuboid (position -0.0150 -0.0075 0.0240) (position 0.0000 0.0075 0.0280) "Silicon" "R.Source3")
(sdegeo:create-cuboid (position 0.0180 -0.0075 0.0240) (position 0.0330 0.0075 0.0280) "Silicon" "R.Drain3")

;--- Contact Definitions ---
(sdegeo:define-contact-set "source" 4  (color:rgb 1 0 0 ) "##")
(sdegeo:define-contact-set "drain"  4  (color:rgb 0 0 1 ) "##")
(sdegeo:define-contact-set "gate"   4  (color:rgb 0 1 0 ) "##")
(sdegeo:define-contact-set "substrate" 4 (color:rgb 0.5 0.5 0.5) "##")

(sdegeo:set-current-contact-surface (find-face-id (position -0.0150 0.0000 0.0000)))
(sdegeo:set-contact-name "source")
(sdegeo:set-current-contact-surface (find-face-id (position 0.0330 0.0000 0.0000)))
(sdegeo:set-contact-name "drain")
(sdegeo:set-current-contact-surface (find-face-id (position 0.0090 -0.0115 0.0140)))
(sdegeo:set-contact-name "gate")
(sdegeo:set-current-contact-surface (find-face-id (position 0.0000 0.0000 -0.0340)))
(sdegeo:set-contact-name "substrate")

;--- Doping Profiles ---
(sdedr:define-constant-profile "Dop.Channel" "BoronActiveConcentration" 1e+15)
(sdedr:define-constant-profile-material "Dop.Channel.Mat" "Dop.Channel" "Silicon")

(sdedr:define-constant-profile "Dop.SD" "ArsenicActiveConcentration" 1e+20)
(sdedr:define-constant-profile-region "Dop.S1" "Dop.SD" "R.Source1")
(sdedr:define-constant-profile-region "Dop.D1" "Dop.SD" "R.Drain1")
(sdedr:define-constant-profile-region "Dop.S2" "Dop.SD" "R.Source2")
(sdedr:define-constant-profile-region "Dop.D2" "Dop.SD" "R.Drain2")
(sdedr:define-constant-profile-region "Dop.S3" "Dop.SD" "R.Source3")
(sdedr:define-constant-profile-region "Dop.D3" "Dop.SD" "R.Drain3")

(sdedr:define-constant-profile "Dop.Sub" "BoronActiveConcentration" 1e+17)
(sdedr:define-constant-profile-region "Dop.Sub.Reg" "Dop.Sub" "R.Substrate")

;--- Dynamic Region-Adaptive Mesh Definitions ---
(sdedr:define-refinement-size "Ref.Channel" 0.0022 0.0019 0.0010 0.0011 0.0009 0.0005)
(sdedr:define-refinement-size "Ref.SD"      0.0030 0.0030 0.0020 0.0015 0.0015 0.0010)
(sdedr:define-refinement-size "Ref.Oxide"   0.0020 0.0020 0.0005 0.0010 0.0010 0.0003)
(sdedr:define-refinement-size "Ref.Sub"     0.0100 0.0100 0.0100 0.0050 0.0050 0.0050)

(sdedr:define-refinement-material "Ref.Ch1" "Ref.Channel" "Silicon" "R.Channel1")
(sdedr:define-refinement-material "Ref.S1"  "Ref.SD"      "Silicon" "R.Source1")
(sdedr:define-refinement-material "Ref.D1"  "Ref.SD"      "Silicon" "R.Drain1")
(sdedr:define-refinement-material "Ref.Ox1" "Ref.Oxide"   "HfO2"    "R.Oxide1")
(sdedr:define-refinement-material "Ref.Ch2" "Ref.Channel" "Silicon" "R.Channel2")
(sdedr:define-refinement-material "Ref.S2"  "Ref.SD"      "Silicon" "R.Source2")
(sdedr:define-refinement-material "Ref.D2"  "Ref.SD"      "Silicon" "R.Drain2")
(sdedr:define-refinement-material "Ref.Ox2" "Ref.Oxide"   "HfO2"    "R.Oxide2")
(sdedr:define-refinement-material "Ref.Ch3" "Ref.Channel" "Silicon" "R.Channel3")
(sdedr:define-refinement-material "Ref.S3"  "Ref.SD"      "Silicon" "R.Source3")
(sdedr:define-refinement-material "Ref.D3"  "Ref.SD"      "Silicon" "R.Drain3")
(sdedr:define-refinement-material "Ref.Ox3" "Ref.Oxide"   "HfO2"    "R.Oxide3")
(sdedr:define-refinement-material "Ref.Sub.Mat" "Ref.Sub" "Silicon" "R.Substrate")

;--- Build Mesh ---
(sde:build-mesh "snmesh" " " "G_L18_W15_T04_msh")
(sde:save-model "G_L18_W15_T04_bnd")
(exit)