;======================================================================
; 3-STACK NANOSHEET NMOS GAAFET — SDE Scheme Script
; Run: G_L14_W15_T04 (Lg = 14 nm, Wns = 15 nm, Tns = 4 nm)
; Dynamic Meshing Enabled for Fast Convergence
;======================================================================

(sde:clear)
(sdegeo:set-default-boolean "ABA")

;--- Geometric Dimensions (in micrometers) ---
(define Lg   0.0140)  (define Ls   0.0150)  (define Ld   0.0150)
(define Wns  0.0150)  (define Tns  0.0040)  (define Tgap 0.0080)
(define Tox  0.0010)  (define Tgm  0.0030)
(define Tbdi 0.0100)  (define Tsub 0.0200)

;--- X Coordinates ---
(define xS0 (- Ls))  (define xG0 0.000)
(define xG1 Lg)      (define xD1 (+ Lg Ld))

;--- Y Coordinates ---
(define y0 (- (/ Wns 2.0)))   (define y1 (/ Wns 2.0))

;--- Z Coordinates (3 stacked nanosheets) ---
(define z1b 0.000)             (define z1t (+ z1b Tns))
(define z2b (+ z1t Tgap))     (define z2t (+ z2b Tns))
(define z3b (+ z2t Tgap))     (define z3t (+ z3b Tns))

; Gate metal Z boundaries
(define zg0 (- z1b Tox Tgm))  (define zg1 (+ z3t Tox Tgm))
(define yg0 (- y0 Tox Tgm))   (define yg1 (+ y1 Tox Tgm))

; BDI and Substrate Z boundaries
(define zBDI_bot (- zg0 Tbdi))
(define zSub_bot (- zBDI_bot Tsub))

;--- 1. P-type Silicon Substrate Base ---
(sdegeo:create-cuboid (position xS0 yg0 zSub_bot) (position xD1 yg1 zBDI_bot) "Silicon" "R.Substrate")

;--- 2. Bottom Dielectric Isolation (SiO2) ---
(sdegeo:create-cuboid (position xS0 yg0 zBDI_bot) (position xD1 yg1 zg0) "SiO2" "R.BDI")

;--- 3. Source Regions (3 Distinct N+ Nanosheets) ---
(sdegeo:create-cuboid (position xS0 y0 z1b) (position xG0 y1 z1t) "Silicon" "R.Source1")
(sdegeo:create-cuboid (position xS0 y0 z2b) (position xG0 y1 z2t) "Silicon" "R.Source2")
(sdegeo:create-cuboid (position xS0 y0 z3b) (position xG0 y1 z3t) "Silicon" "R.Source3")

;--- 4. Channel Regions ---
(sdegeo:create-cuboid (position xG0 y0 z1b) (position xG1 y1 z1t) "Silicon" "R.Channel1")
(sdegeo:create-cuboid (position xG0 y0 z2b) (position xG1 y1 z2t) "Silicon" "R.Channel2")
(sdegeo:create-cuboid (position xG0 y0 z3b) (position xG1 y1 z3t) "Silicon" "R.Channel3")

;--- 5. Drain Regions (3 Distinct N+ Nanosheets) ---
(sdegeo:create-cuboid (position xG1 y0 z1b) (position xD1 y1 z1t) "Silicon" "R.Drain1")
(sdegeo:create-cuboid (position xG1 y0 z2b) (position xD1 y1 z2t) "Silicon" "R.Drain2")
(sdegeo:create-cuboid (position xG1 y0 z3b) (position xD1 y1 z3t) "Silicon" "R.Drain3")

;--- 6. Gate Metal Outer Shell ---
(sdegeo:create-cuboid (position xG0 yg0 zg0) (position xG1 yg1 zg1) "Metal" "R.Gate")

;--- 7. HfO2 Oxide Sleeves (ABA) ---
(sdegeo:create-cuboid (position xG0 (- y0 Tox) (- z1b Tox))
                      (position xG1 (+ y1 Tox) (+ z1t Tox)) "HfO2" "R.Oxide1")
(sdegeo:create-cuboid (position xG0 (- y0 Tox) (- z2b Tox))
                      (position xG1 (+ y1 Tox) (+ z2t Tox)) "HfO2" "R.Oxide2")
(sdegeo:create-cuboid (position xG0 (- y0 Tox) (- z3b Tox))
                      (position xG1 (+ y1 Tox) (+ z3t Tox)) "HfO2" "R.Oxide3")

;--- 8. Si Channel Cores (ABA) ---
(sdegeo:create-cuboid (position xG0 y0 z1b) (position xG1 y1 z1t) "Silicon" "R.Channel1_Core")
(sdegeo:create-cuboid (position xG0 y0 z2b) (position xG1 y1 z2t) "Silicon" "R.Channel2_Core")
(sdegeo:create-cuboid (position xG0 y0 z3b) (position xG1 y1 z3t) "Silicon" "R.Channel3_Core")

;--- Doping Profiles ---
(sdedr:define-constant-profile "Dop.Source" "PhosphorusActiveConcentration" 1e20)
(sdedr:define-constant-profile-region "Place.Source1" "Dop.Source" "R.Source1")
(sdedr:define-constant-profile-region "Place.Source2" "Dop.Source" "R.Source2")
(sdedr:define-constant-profile-region "Place.Source3" "Dop.Source" "R.Source3")

(sdedr:define-constant-profile "Dop.Drain" "PhosphorusActiveConcentration" 1e20)
(sdedr:define-constant-profile-region "Place.Drain1" "Dop.Drain" "R.Drain1")
(sdedr:define-constant-profile-region "Place.Drain2" "Dop.Drain" "R.Drain2")
(sdedr:define-constant-profile-region "Place.Drain3" "Dop.Drain" "R.Drain3")

(sdedr:define-constant-profile "Dop.Channel" "BoronActiveConcentration" 1e15)
(sdedr:define-constant-profile-region "Place.Ch1" "Dop.Channel" "R.Channel1_Core")
(sdedr:define-constant-profile-region "Place.Ch2" "Dop.Channel" "R.Channel2_Core")
(sdedr:define-constant-profile-region "Place.Ch3" "Dop.Channel" "R.Channel3_Core")
(sdedr:define-constant-profile-region "Place.Sub" "Dop.Channel" "R.Substrate")

;--- Contacts ---
(sdegeo:define-contact-set "source"    4.0 (color:rgb 1 0 0) "##")
(sdegeo:define-contact-set "drain"     4.0 (color:rgb 0 0 1) "##")
(sdegeo:define-contact-set "gate"      4.0 (color:rgb 0 1 0) "##")
(sdegeo:define-contact-set "substrate" 4.0 (color:rgb 0.5 0.5 0.5) "##")

(sdegeo:set-current-contact-set "source")
(sdegeo:set-contact (find-face-id (position xS0 0.0 (/ (+ z1b z1t) 2.0))) "source")
(sdegeo:set-contact (find-face-id (position xS0 0.0 (/ (+ z2b z2t) 2.0))) "source")
(sdegeo:set-contact (find-face-id (position xS0 0.0 (/ (+ z3b z3t) 2.0))) "source")

(sdegeo:set-current-contact-set "drain")
(sdegeo:set-contact (find-face-id (position xD1 0.0 (/ (+ z1b z1t) 2.0))) "drain")
(sdegeo:set-contact (find-face-id (position xD1 0.0 (/ (+ z2b z2t) 2.0))) "drain")
(sdegeo:set-contact (find-face-id (position xD1 0.0 (/ (+ z3b z3t) 2.0))) "drain")

(sdegeo:set-current-contact-set "gate")
(sdegeo:set-contact (find-face-id (position (/ (+ xG0 xG1) 2.0) 0.0 zg1)) "gate")

(sdegeo:set-current-contact-set "substrate")
(sdegeo:set-contact (find-face-id (position (/ (+ xS0 xD1) 2.0) 0.0 zSub_bot)) "substrate")

;======================================================================
; DYNAMIC & REGION-ADAPTIVE MESHING
;======================================================================

; 1. Global Coarse Refinement (Saves nodes in passive areas)
(sdedr:define-refeval-window "RefWin.Global" "Cuboid"
    (position xS0 yg0 zSub_bot) (position xD1 yg1 zg1))
(sdedr:define-refinement-size "RefDef.Global"
    0.006 0.006 0.006   0.002 0.002 0.002)
(sdedr:define-refinement-placement "RefPlace.Global" "RefDef.Global" "RefWin.Global")

; 2. Highly Coarsened Substrate & BDI Base (No current flows here)
(sdedr:define-refeval-window "RefWin.SubBDI" "Cuboid"
    (position xS0 yg0 zSub_bot) (position xD1 yg1 zg0))
(sdedr:define-refinement-size "RefDef.SubBDI"
    0.008 0.008 0.008   0.004 0.004 0.004)
(sdedr:define-refinement-placement "RefPlace.SubBDI" "RefDef.SubBDI" "RefWin.SubBDI")

; 3. Active Channels & Inversion Layers (Focused High-Density Mesh)
(sdedr:define-refeval-window "RefWin.Chan" "Cuboid"
    (position (- xG0 0.001) (- y0 Tox 0.0005) (- z1b Tox 0.0005))
    (position (+ xG1 0.001) (+ y1 Tox 0.0005) (+ z3t Tox 0.0005)))
(sdedr:define-refinement-size "RefDef.Chan"
    0.0015 0.0015 0.0010   0.0004 0.0004 0.0003)
(sdedr:define-refinement-placement "RefPlace.Chan" "RefDef.Chan" "RefWin.Chan")

; Interface refinement between Si channel and HfO2
(sdedr:define-refinement-function "RefDef.Chan"
    "MaxLenInt" "Silicon" "HfO2" 0.0003 1.5 "DoubleSide")
(sdedr:define-refinement-function "RefDef.Chan"
    "MaxTransDiff" "DopingConcentration" 1)

;--- Build Mesh ---
(sde:build-mesh "snmesh" "" "G_L14_W15_T04")
