# Methods, assumptions and flags for items 1–4

Everything is parametric: `wig/params.py` holds one `Design` dataclass; every module reads from
it. Re-run `python3 scripts/run_items_1_4.py` after changing anything (≈50 s; the ground-effect
table is cached in `out/ge_table.npz`, delete it after changing wing geometry).

## 1. Mass / CG (`wig/mass.py`)

* Tube masses from π·D·t·L·ρ (6061: 2700 kg/m³, 7075: 2810 kg/m³). Battery from 185 Wh/kg
  pack-level (21700 power cells ~245 Wh/kg cell-level, minus BMS, wiring, case).
* Everything else is a "class" estimate from comparable products (paramotor cages, hub motors,
  iSUPs). Two columns: *estimate* (ordinary parts) and *stretch* (disciplined light build).
* CG uses x aft of the spine nose, z above the keel. Pilot hips at x = 1.35 m, z = 0.55 m.
* **Flag:** the brief's 130 kg all-up with a 66 kg pilot leaves 64 kg for the craft. The estimate
  is 92 kg (158 all-up); even the stretch build is 77 kg (143 all-up). The three biggest items are
  the floats (18 kg), the land gear (16 kg) and the battery (13.5 kg). Either accept ~145–160 kg or
  cut the land-mode hardware. All sims below are run at 130 / 143 / 158 kg.

## 2. Float hydrodynamics (`wig/hydro.py`)

* Float = 10'6" drop-stitch iSUP, 3.20 × 0.81 × 0.15 m, flat bottom (deadrise 0°). Candidates with
  published specs: Jobe Aero Nera 10.6 (310 L, 8.5 kg, ~£270–300), Decathlon 10'6" (290 L, 8.4 kg),
  Aquatone Wave 10'6" (320×81×15 cm, 300 L, 9.5 kg, ~$360 on sale). Inflatable catamaran tubes
  (Aqua Marina Aircat 3.35 m, ~£565 for the whole boat) are the alternative if you want round
  sponsons. Sources listed in the session summary; the BOM (item 9) will pin these down.
* Planing: Savitsky (1964) equations exactly as written in the module docstring; ITTC-57
  friction line + 0.0004 roughness allowance; mean bottom velocity per Savitsky; whisker spray as
  +10 % of friction (Savitsky, DeLorme & Datla 2007).
* Step: two prismatic surfaces (forebody 1.6 m / afterbody 1.6 m) sharing the load 70/30, each
  solved with Savitsky at the same trim. The benefit is small here (hump 203 N vs 213 N) because
  the floats are very lightly loaded (C_Δ = Δ/(ρ g b³) ≈ 0.15 against 0.3–0.8 for seaplane floats).
  The step still matters for *attitude* (letting the float rotate nose-up at lift-off without the
  tail dragging), which item 5 will look at.
* Displacement regime (C_V < ~1, i.e. below ~3 m/s): friction on the static wetted area plus a
  residuary term R_w = Δ·1.6·Fn_L⁴ (placeholder: R_w/Δ = 0.10 at Fn_L = 0.5). Blended into the
  planing solution with a smoothstep over C_V 0.5–1.2. **This is the least trustworthy part of
  the model.** A spring-scale tow test of the actual float behind a dinghy at 1–6 m/s (with the
  intended load as sandbags) replaces it for ~$0 and belongs in the unmanned test plan.
* Trim is fixed (4° default); the module also returns the drag-optimal trim. Real trim is set by
  CG, step position and thrust line and is solved in item 5.
* Below λ ≈ 0.6 (above ~8 m/s here) Savitsky is extrapolated; the drag there is dominated by
  Δ·tan τ, which is robust.
* No waves. SF Bay chop (0.3–0.6 m wind waves in the afternoon) will raise hump drag and, more
  importantly, slam the flat-bottomed floats. Flat-bottom iSUPs pound badly; a V-bottom planing
  strip is worth considering (parameter `float_deadrise_deg`).

## 3. Aerodynamics in ground effect (`wig/aero.py`)

* Steady vortex-ring lattice, 8 chordwise × 24 spanwise panels on the wing, 8 × 4 on each
  endplate, straight wake 60 chords long, mirror image at z = 0 with −Γ (Katz & Plotkin,
  *Low-Speed Aerodynamics*, 2nd ed., §12.3). Lift from Kutta–Joukowski on the bound segments,
  induced drag in the Trefftz plane (with images), pitching moment about c/4.
* Validation (printed by `python3 -c` in the session, reproducible from `solve_wing`):
  lift slope 3.29–3.41/rad vs Helmbold 3.44 for AR 3.1; Oswald e = 1.02–1.04 out of ground effect
  for a rectangular wing; in-ground-effect induced-drag ratio tracks McCormick's
  φ = (16h/b)²/(1+(16h/b)²) in shape (VLM is ~20 % more optimistic at h/c 0.2–0.5).
* Wing: 5.0 × 1.6 m rectangular (AR 3.1), parabolic camber 4 % (α₀ ≈ −4.6°), rotated about the
  trailing edge; `h` is the trailing-edge height. Endplates (float inboard faces) 0.30 m deep,
  clipped to the water gap.
* Grid convergence: CL within 0.5 %, CDi within ±10 % between 6×16 and 12×36 grids.
* Limits: linear and inviscid. No stall (the table clips at `alpha_stall_deg` = 12°, a guess for a
  fabric low-AR wing). Below h/c ≈ 0.1 the real flow is nonlinear and lift is higher than the
  VLM says. Fabric billow, batten sag and leading-edge spar pocket are not modelled; the wing
  profile drag coefficient 0.018 covers them roughly.
* Whole-craft parasite drag is a flat-plate-area build-up (`cda_*` in params): reclined pilot
  0.40 m² (recumbent cyclist ~0.25, motorcyclist ~0.55), folded wheels 0.10, cage 0.07, floats
  0.06, misc 0.05, ×1.10 interference → 0.75 m², plus wing profile 0.018 × 8 m² = 0.14 m².
  **These numbers drive the cruise result and are ±30 %.**
* PAR: a pusher prop *behind* the wing cannot blow under it. The what-if curve assumes a tractor
  prop ahead of the wing with 50 % of the slipstream captured (blown-area model + jet turning);
  it is optimistic and only there to show what you would gain by moving the prop.

## 4. Takeoff simulation and sizing (`wig/takeoff.py`, `wig/propulsion.py`, `wig/cruise.py`)

* Prop: actuator-disk momentum theory with induced-power factor 1.20 and a profile/cage factor
  that goes from 0.62 at V = 0 to 0.80 at cruise. Calibrated so a 1.3 m prop makes 58 kgf at
  15 kW and 81 kgf at 25 kW; the OpenPPG SP140 (1.4 m prop) is quoted at 79 kgf / 25 kW peak,
  ~75 kgf scaled to 1.3 m, so the model is ~8 % optimistic there. Cruise prop efficiency comes out
  0.58–0.63, conservative for a well-matched 2-blade prop (0.65–0.72).
* Integration: dV/dt = (T − D_air − R_water)/m at 20 ms steps, attitude fixed at 9° wing
  incidence with the TE 0.35 m above water (floats at 4° trim ⇒ the wing is rigged +5° to the
  float keels). Lift-off = floats fully unloaded. Headwind, trim, step, incidence, prop size and
  PAR are all switches.
* Results: lift-off 15–16.5 m/s (54–59 km/h); at 15 kW shaft, 5–8 s and 43–73 m; the water hump
  is only 160–190 N at 3–4 m/s and the thrust margin never drops below 200 N. Takeoff is **not**
  the sizing case. 8 kW already lifts off within 200 m at 158 kg.
* Cruise is the sizing case. At 25 m/s and 0.6 m height the craft L/D is 3.5–4.1 and the
  electrical power 18 kW (158 kg). 2.5 kWh then lasts 7 min. Halving the parasite drag with a
  pilot fairing and enclosed wheels gets 10–12 min; a fully faired craft 16 min; 30 min needs
  ≤ 4.2 kW electrical, i.e. total CdA ≈ 0.25 m² at 22 m/s *or* a 7–9 kWh battery (40–50 kg).
* Sizing that follows: motor 15 kW for 60 s and ≥ 10 kW continuous (SP140 class fits); ESC 300–
  400 A at 14S or ~250 A at 20S (72 V is the better fit); prop 1.3 m 2-blade; battery 2.5 kWh
  21700 power cells (takeoff 6.8 C is fine for P42A-class cells, cruise 5–7 C continuous is not —
  at the as-drawn drag the pack is current-limited as much as energy-limited).

## Safety flags so far

* Lift-off speed ~58 km/h in a craft with the pilot's body as the leading structure. Any dig-in of a
  float at that speed pitch-poles the craft. Item 5 (stability) decides whether this configuration
  is flyable at all; do not build the wing before it is done.
* Flat-bottomed drop-stitch floats slam hard in chop; drop-stitch boards fold if the bending load
  exceeds what ~15 psi supports (a 2-point saddle mount and a planing strip help).
* Prop behind a reclined pilot: anything that comes off the pilot (harness strap, hat, phone) goes
  through the prop. Cage netting is mandatory; keep the prop disk above shoulder height.
* 300–400 A at 50 V in a sealed aluminium tube: fuse at the pack, contactor + kill switch outside
  the tube, and a vent/pressure relief for thermal runaway. The spine is the keel; a flooded
  spine is a flooded battery.

## References

* Savitsky, D. (1964). Hydrodynamic design of planing hulls. *Marine Technology* 1(1), 71–95.
* Savitsky, D., DeLorme, M. F., Datla, R. (2007). Inclusion of whisker spray drag in performance
  prediction method for high-speed planing hulls. *Marine Technology* 44(1), 35–56.
* Savitsky, D., Morabito, M. (2010). Surface wave contours associated with the forebody wake of
  stepped planing hulls. *Marine Technology* 47(1), 1–16.
* ITTC (1957). Model-ship correlation line.
* Katz, J., Plotkin, A. (2001). *Low-Speed Aerodynamics*, 2nd ed., Cambridge UP, §12.3 (vortex
  ring method) and ch. 8 (Trefftz-plane induced drag).
* Helmbold, H. B. (1942) lift-slope formula as given in Anderson, *Fundamentals of Aerodynamics*.
* McCormick, B. W. (1979/1995). *Aerodynamics, Aeronautics and Flight Mechanics*, Wiley — ground
  effect induced-drag factor.
* Rozhdestvensky, K. V. (2006). Wing-in-ground effect vehicles. *Progress in Aerospace Sciences*
  42, 211–283 — survey, PAR and stability background for item 5.
* Gallington, R. W. (1987). Power augmentation of ram wings. *RAeS WIG symposium* — PAR theory.
* OpenPPG SP140 figures: xcmag.com news item (2020), see session sources.
