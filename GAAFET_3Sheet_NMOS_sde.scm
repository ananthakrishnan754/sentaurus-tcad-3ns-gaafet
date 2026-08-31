;======================================================================
; 3-STACK NANOSHEET NMOS GAAFET WITH SUBSTRATE & BDI ISOLATION
; Sentaurus Structure Editor (SDE)
; Output mesh file: GAAFET_3Sheet_NMOS_msh.tdr
;
; Geometry (all in micrometres unless stated):
;   Gate length  Lg  = 10 nm   Nanosheet width  Wns = 15 nm
;   NS thickness Tns =  4 nm   Inter-sheet gap Tgap =  8 nm
;   S/D length   Ls/d= 15 nm   HfO2 oxide       Tox =  1 nm
;   Gate metal margin Tgm = 3 nm
;   BDI thickness Tbdi = 10 nm (SiO2 Bottom Dielectric Isolation)
;   Substrate thickness Tsub = 20 nm (P-type Silicon Substrate)
;======================================================================

(sde:clear)
(sdegeo:set-default-boolean "ABA")

;--- Parameters -------------------------------------------------------
(define Lg   0.010)  (define Ls   0.015)  (define Ld   0.015)
(define Wns  0.015)  (define Tns  0.004)  (define Tgap 0.008)
(define Tox  0.001)  (define Tgm  0.003)
(define Tbdi 0.010)  (define Tsub 0.020)

;--- X coordinates ---------------------------------------------------
(define xS0 (- Ls))  (define xG0 0.000)
(define xG1 Lg)      (define xD1 (+ Lg Ld))

;--- Y coordinates (width, centred) ----------------------------------
(define y0 (- (/ Wns 2.0)))   (define y1 (/ Wns 2.0))

;--- Z coordinates (3 stacked nanosheets) ----------------------------
(define z1b 0.000)             (define z1t (+ z1b Tns))
(define z2b (+ z1t Tgap))     (define z2t (+ z2b Tns))
(define z3b (+ z2t Tgap))     (define z3t (+ z3b Tns))

; Gate metal Z boundaries
(define zg0 (- z1b Tox Tgm))  (define zg1 (+ z3t Tox Tgm))
(define yg0 (- y0 Tox Tgm))   (define yg1 (+ y1 Tox Tgm))

; BDI and Substrate Z boundaries below bottom gate
(define zBDI_bot (- zg0 Tbdi))
(define zSub_bot (- zBDI_bot Tsub))

;--- 1. P-type Silicon Substrate Base -------------------------------
(sdegeo:create-cuboid (position xS0 yg0 zSub_bot) (position xD1 yg1 zBDI_bot) "Silicon" "R.Substrate")

;--- 2. Bottom Dielectric Isolation (BDI / SiO2) -------------------
(sdegeo:create-cuboid (position xS0 yg0 zBDI_bot) (position xD1 yg1 zg0) "SiO2" "R.BDI")

;--- 3. Source Regions (3 Distinct N+ Nanosheets) -------------------
(sdegeo:create-cuboid (position xS0 y0 z1b) (position xG0 y1 z1t) "Silicon" "R.Source1")
(sdegeo:create-cuboid (position xS0 y0 z2b) (position xG0 y1 z2t) "Silicon" "R.Source2")
(sdegeo:create-cuboid (position xS0 y0 z3b) (position xG0 y1 z3t) "Silicon" "R.Source3")

;--- 4. Channel Regions (3 Distinct Nanosheet Cores) ---------------
(sdegeo:create-cuboid (position xG0 y0 z1b) (position xG1 y1 z1t) "Silicon" "R.Channel1")
(sdegeo:create-cuboid (position xG0 y0 z2b) (position xG1 y1 z2t) "Silicon" "R.Channel2")
(sdegeo:create-cuboid (position xG0 y0 z3b) (position xG1 y1 z3t) "Silicon" "R.Channel3")

;--- 5. Drain Regions (3 Distinct N+ Nanosheets) --------------------
(sdegeo:create-cuboid (position xG1 y0 z1b) (position xD1 y1 z1t) "Silicon" "R.Drain1")
(sdegeo:create-cuboid (position xG1 y0 z2b) (position xD1 y1 z2t) "Silicon" "R.Drain2")
(sdegeo:create-cuboid (position xG1 y0 z3b) (position xD1 y1 z3t) "Silicon" "R.Drain3")

;--- 6. Gate Metal Outer Block --------------------------------------
(sdegeo:create-cuboid (position xG0 yg0 zg0) (position xG1 yg1 zg1) "Metal" "R.Gate")

;--- 7. HfO2 Oxide Sleeves (ABA: overwrites Metal around Channels) ---
(sdegeo:create-cuboid (position xG0 (- y0 Tox) (- z1b Tox))
                      (position xG1 (+ y1 Tox) (+ z1t Tox)) "HfO2" "R.Oxide1")
(sdegeo:create-cuboid (position xG0 (- y0 Tox) (- z2b Tox))
                      (position xG1 (+ y1 Tox) (+ z2t Tox)) "HfO2" "R.Oxide2")
(sdegeo:create-cuboid (position xG0 (- y0 Tox) (- z3b Tox))
                      (position xG1 (+ y1 Tox) (+ z3t Tox)) "HfO2" "R.Oxide3")

;--- 8. Si Channel Cores (ABA: overwrites HfO2; unique _Core names) -
(sdegeo:create-cuboid (position xG0 y0 z1b) (position xG1 y1 z1t) "Silicon" "R.Channel1_Core")
(sdegeo:create-cuboid (position xG0 y0 z2b) (position xG1 y1 z2t) "Silicon" "R.Channel2_Core")
(sdegeo:create-cuboid (position xG0 y0 z3b) (position xG1 y1 z3t) "Silicon" "R.Channel3_Core")

;--- Doping Profiles -------------------------------------------------
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

;--- Contacts --------------------------------------------------------
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

;--- Mesh Refinement -------------------------------------------------
(sdedr:define-refeval-window "RefWin.Global" "Cuboid"
    (position xS0 yg0 zSub_bot) (position xD1 yg1 zg1))
(sdedr:define-refinement-size "RefDef.Global"
    0.005 0.005 0.005   0.001 0.001 0.001)
(sdedr:define-refinement-placement "RefPlace.Global" "RefDef.Global" "RefWin.Global")

(sdedr:define-refeval-window "RefWin.Chan" "Cuboid"
    (position (- xG0 0.002) (- y0 Tox 0.001) (- z1b Tox 0.001))
    (position (+ xG1 0.002) (+ y1 Tox 0.001) (+ z3t Tox 0.001)))
(sdedr:define-refinement-size "RefDef.Chan"
    0.002 0.002 0.002   0.0005 0.0005 0.0005)
(sdedr:define-refinement-placement "RefPlace.Chan" "RefDef.Chan" "RefWin.Chan")

(sdedr:define-refinement-function "RefDef.Chan"
    "MaxLenInt" "Silicon" "HfO2" 0.0003 1.5 "DoubleSide")
(sdedr:define-refinement-function "RefDef.Chan"
    "MaxTransDiff" "DopingConcentration" 1)

;--- Build Mesh ------------------------------------------------------
(sde:build-mesh "snmesh" "" "GAAFET_3Sheet_NMOS")

; END OF SDE SCRIPT
