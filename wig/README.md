# WIG craft: parametric model + simulation

Single-seat electric wing-in-ground-effect craft for SF Bay (inflatable floats at the wingtips,
sewn fabric wing, caged pusher prop, pedal-assist cargo-quad land mode).

```
pip install -r requirements.txt
python3 scripts/run_items_1_4.py      # mass/CG, hydro, ground-effect aero, takeoff + sizing
```
Outputs land in `out/` (figures, `summary_1_4.md`, `01_mass_budget.md`). Methods, assumptions
and safety flags: `docs/METHODS_1_4.md`. All parameters: `wig/params.py`.

| item | module | status |
|---|---|---|
| 1 mass / CG | `wig/mass.py` | done |
| 2 float hydro (Savitsky, hump, step) | `wig/hydro.py` | done, displacement regime is a placeholder pending a tow test |
| 3 ground-effect aero (VLM + image, endplates, PAR) | `wig/aero.py` | done, validated vs Helmbold / McCormick |
| 4 takeoff sim + motor/prop/ESC/battery sizing | `wig/takeoff.py`, `wig/propulsion.py`, `wig/cruise.py` | done |
| 5 longitudinal stability + 2D dynamic sim | | next |
| 6–10 cruise sweeps, sensitivities, structures, BOM, test plan, legal | | pending review |
