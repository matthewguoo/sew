"""Run items 1-4: mass/CG, hydrodynamics, ground-effect aero, takeoff + sizing.  Writes out/."""
import sys, os, math, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import numpy as np
import matplotlib.pyplot as plt
from wig import Design, G
from wig.mass import budget, table as mass_table
from wig.hydro import float_resistance, optimum_trim
from wig.aero import GETable, solve_wing, mccormick_phi, parasite_drag, par_increment
from wig.propulsion import thrust, static_thrust, battery_summary, prop_efficiency
from wig.takeoff import simulate, thrust_drag_curves
from wig.cruise import cruise_point
from wig.plots import style, finish, PALETTE, STATUS, TEXT2

OUT = os.path.join(os.path.dirname(__file__), "..", "out")
os.makedirs(OUT, exist_ok=True)
style()
d = Design()
report = []
def say(*a):
    s = " ".join(str(x) for x in a); print(s); report.append(s)

# ------------------------------------------------------------------ 1. mass / CG
say("# Items 1-4 results\n")
say("## 1. Mass / CG budget\n")
say(mass_table(d)); say("")
b_est, b_str = budget(d, "est"), budget(d, "stretch")
MASSES = {"target 130 kg": d.m_allup_target, "stretch build": round(b_str["m_allup"], 1), "estimated build": round(b_est["m_allup"], 1)}
comps = b_est["components"]
fig, ax = plt.subplots(figsize=(9, 7.5))
names = [c.name[:38] for c in comps][::-1]
est = [c.est for c in comps][::-1]; st = [c.stretch for c in comps][::-1]
y = np.arange(len(names))
ax.barh(y + 0.2, est, 0.38, color=PALETTE[0], label="estimate")
ax.barh(y - 0.2, st, 0.38, color=PALETTE[1], label="stretch (light build)")
ax.set_yticks(y); ax.set_yticklabels(names, fontsize=7.5); ax.set_xlabel("mass (kg)")
ax.set_title(f"Component masses: empty {b_est['m_empty']:.0f} kg est / {b_str['m_empty']:.0f} kg stretch "
             f"(brief implies {d.m_allup_target - d.m_pilot:.0f} kg)")
ax.legend(loc="lower right")
finish(fig, f"{OUT}/fig01_mass_budget.png", "Pilot 66 kg not shown. Masses from geometry where noted in out/01_mass_budget.md, else class estimates.")
open(f"{OUT}/01_mass_budget.md", "w").write(mass_table(d))

# ------------------------------------------------------------------ 2. hydrodynamics
say("## 2. Float hydrodynamics (2 x 10'6\" iSUP, flat bottom)\n")
V = np.linspace(0.3, 18, 120)
m_ref = MASSES["estimated build"]
W = m_ref * G
cases = {
    "step, trim 4°": dict(trim_deg=4, has_step=True),
    "no step, trim 4°": dict(trim_deg=4, has_step=False),
    "step, trim 2°": dict(trim_deg=2, has_step=True),
    "step, trim 6°": dict(trim_deg=6, has_step=True),
}
fig, axs = plt.subplots(1, 3, figsize=(14, 4.4))
ax = axs[0]
R_full = {}
for i, (lab, kw) in enumerate(cases.items()):
    R = np.array([2 * float_resistance(v, W / 2, d, **kw)["R"] for v in V]); R_full[lab] = R
    ax.plot(V, R, label=lab, ls="-" if "no" not in lab else "--", color=PALETTE[i])
ax.set_xlabel("speed (m/s)"); ax.set_ylabel("water resistance, both floats (N)")
ax.set_title(f"Full float load ({m_ref:.0f} kg, no wing lift)")
ax.legend(fontsize=8)
hump = {lab: (V[np.argmax(R)], R.max()) for lab, R in R_full.items()}
for lab, (vh, rh) in hump.items():
    say(f"- {lab}: hump {rh:.0f} N at {vh:.1f} m/s (R/W = {rh / W:.3f})")
# with wing unloading, takeoff attitude
table_path = f"{OUT}/ge_table.npz"
t0 = time.time()
if os.path.exists(table_path):
    tab = GETable.load(d, table_path)
else:
    print("building ground-effect table ..."); tab = GETable(d, verbose=True); tab.save(table_path)
    print(f"  done in {time.time() - t0:.0f} s")
cl_to = tab.cl(d.takeoff_alpha_deg, d.takeoff_te_height / d.chord)
ax = axs[1]
for i, (lab, m) in enumerate(MASSES.items()):
    Wm = m * G
    Wh = np.maximum(Wm - 0.5 * 1.225 * V ** 2 * d.wing_area * cl_to, 0)
    R = np.array([2 * float_resistance(v, wh / 2, d)["R"] if wh > 0 else 0 for v, wh in zip(V, Wh)])
    ax.plot(V, R, label=f"{lab} ({m:.0f} kg)", color=PALETTE[i])
    say(f"- takeoff attitude, {lab}: water hump {R.max():.0f} N at {V[np.argmax(R)]:.1f} m/s; floats unload at {V[np.argmax(Wh <= 0)] if (Wh <= 0).any() else float('nan'):.1f} m/s")
ax.set_xlabel("speed (m/s)"); ax.set_ylabel("water resistance (N)")
ax.set_title(f"Takeoff attitude (α={d.takeoff_alpha_deg:.0f}°, CL={cl_to:.2f}): wing unloads floats")
ax.legend(fontsize=8)
ax = axs[2]
r = [float_resistance(v, W / 2, d) for v in V]
ax.plot(V, [x["R_f"] * 2 for x in r], label="friction (+spray)")
ax.plot(V, [x["R_p"] * 2 for x in r], label="pressure (Δ·tanτ)")
ax.plot(V, [x["R_w"] * 2 for x in r], label="residuary (displacement)")
ax2 = ax.twinx(); ax2.plot(V, [x["wetted_len"] for x in r], color=TEXT2, lw=1, ls=":"); ax2.set_ylabel("wetted length per float (m)", color=TEXT2)
ax2.grid(False)
ax.set_xlabel("speed (m/s)"); ax.set_ylabel("N"); ax.set_title("Components, step, trim 4°, full load"); ax.legend(fontsize=8)
finish(fig, f"{OUT}/fig02_hydro.png", "Savitsky 1964 planing + ITTC-57 friction + 10 % whisker spray; displacement regime is a placeholder blend (C_V 0.5-1.2). Step = 2 planing surfaces sharing load 70/30.")
# optimum trim table
say("\nOptimum trim (min drag) vs speed at full load, stepped:")
for v in [3, 5, 8, 12]:
    t, r_ = optimum_trim(v, W / 2, d)
    say(f"- V={v} m/s: τ_opt={t:.1f}°, R={2 * r_:.0f} N (vs {2 * float_resistance(v, W / 2, d)['R']:.0f} N at 4°)")
say("")

# ------------------------------------------------------------------ 3. aero in ground effect
say("## 3. Wing in ground effect (VLM + mirror image)\n")
hcs = np.array([0.08, 0.1, 0.15, 0.2, 0.3, 0.5, 0.75, 1.0, 2.0])
oge = {a: solve_wing(d, a, 100.0, endplates=False, ground=False) for a in (2, 6, 10)}
fig, axs = plt.subplots(2, 2, figsize=(12, 8.5))
ax = axs[0, 0]
ge_rows = []
for i, a in enumerate((2, 6, 10)):
    ep = [solve_wing(d, a, hc * d.chord, endplates=True) for hc in hcs]
    no = [solve_wing(d, a, hc * d.chord, endplates=False) for hc in hcs]
    ax.plot(hcs, [r["CL"] for r in ep], marker="o", color=PALETTE[i], label=f"α={a}°, endplates")
    ax.plot(hcs, [r["CL"] for r in no], ls="--", color=PALETTE[i], label=f"α={a}°, no endplates")
    ax.axhline(oge[a]["CL"], color=PALETTE[i], lw=0.8, ls=":")
    for hc, r1, r2 in zip(hcs, ep, no):
        ge_rows.append((a, hc, r1["CL"], r1["CDi"], r2["CL"], r2["CDi"], r1["Cm"]))
ax.set_xscale("log"); ax.set_xlabel("h/c (trailing-edge height / chord)"); ax.set_ylabel("C_L")
ax.set_title("Lift vs height (dotted = out of ground effect)"); ax.legend(fontsize=7.5, ncol=2)
ax = axs[0, 1]
k0 = oge[6]["CDi"] / oge[6]["CL"] ** 2
rows6 = [r for r in ge_rows if r[0] == 6]
ax.plot(hcs, [r[5] / r[4] ** 2 / k0 for r in rows6], marker="o", label="VLM, no endplates")
ax.plot(hcs, [r[3] / r[2] ** 2 / k0 for r in rows6], marker="o", label="VLM, endplates (sealed at h<0.3 m)")
ax.plot(hcs, [mccormick_phi(hc * d.chord, d.span) for hc in hcs], ls="--", color=TEXT2, label="McCormick φ=(16h/b)²/(1+(16h/b)²)")
ax.set_xscale("log"); ax.set_xlabel("h/c"); ax.set_ylabel("C_Di/C_L²  relative to out-of-ground-effect")
ax.set_title("Induced drag reduction in ground effect"); ax.legend(fontsize=8)
# craft L/D at cruise
ax = axs[1, 0]
h_sweep = np.array([0.15, 0.25, 0.35, 0.5, 0.75, 1.0, 1.5, 2.5])
for i, Vc in enumerate((22, 25, 28)):
    ld = []
    for h in h_sweep:
        cp = cruise_point(tab, m_ref, Vc, h, d); ld.append(cp["LD"] if cp["ok"] else np.nan)
    ax.plot(h_sweep, ld, marker="o", color=PALETTE[i], label=f"{Vc} m/s ({Vc * 3.6:.0f} km/h)")
ax.set_xlabel("TE height above water (m)"); ax.set_ylabel("craft L/D (incl. parasite drag)")
ax.set_title(f"Whole-craft L/D at {m_ref:.0f} kg, parasite CdA = {d.cda_parasite:.2f} m²"); ax.legend(fontsize=8)
# PAR what-if
ax = axs[1, 1]
Vs = np.linspace(0, 18, 50)
dpar = Design(par_enabled=True)
for i, P in enumerate((10e3, 15e3, 20e3)):
    T = np.array([thrust(P, v, d) for v in Vs])
    dl = np.array([par_increment(t, v, cl_to, tab.cdi(d.takeoff_alpha_deg, d.takeoff_te_height / d.chord), dpar)[0] for t, v in zip(T, Vs)])
    ax.plot(Vs, dl, color=PALETTE[i], label=f"PAR lift, {P / 1e3:.0f} kW")
ax.plot(Vs, 0.5 * 1.225 * Vs ** 2 * d.wing_area * cl_to, ls="--", color=TEXT2, label="plain wing lift at takeoff attitude")
ax.axhline(m_ref * G, color=STATUS["serious"], lw=1, ls=":"); ax.text(0.3, m_ref * G * 1.02, "weight", color=STATUS["serious"], fontsize=8)
ax.set_xlabel("speed (m/s)"); ax.set_ylabel("lift (N)")
ax.set_title(f"PAR what-if: prop AHEAD of wing, {dpar.par_capture:.0%} captured (impossible with a pusher)"); ax.legend(fontsize=8)
finish(fig, f"{OUT}/fig03_aero_ge.png", "Vortex-ring lattice 8x24 + mirror image (Katz & Plotkin 12.3), parabolic camber 4 %, endplate depth 0.30 m clipped to water gap. Linear, inviscid: below h/c~0.1 real lift is higher.")
say("| α (deg) | h/c | CL (EP) | CDi (EP) | CL (no EP) | CDi (no EP) | Cm c/4 |"); say("|---:|---:|---:|---:|---:|---:|---:|")
for r in ge_rows:
    if r[1] in (0.1, 0.2, 0.3, 0.5, 1.0):
        say(f"| {r[0]} | {r[1]:.2f} | {r[2]:.3f} | {r[3]:.4f} | {r[4]:.3f} | {r[5]:.4f} | {r[6]:.3f} |")
say(f"\nOut of ground effect: CL(6°)={oge[6]['CL']:.3f}, CDi={oge[6]['CDi']:.4f}, lift slope ≈ {(oge[10]['CL'] - oge[2]['CL']) / math.radians(8):.2f}/rad (Helmbold {2 * math.pi * d.aspect_ratio / (2 + math.sqrt(d.aspect_ratio ** 2 + 4)):.2f})")
say(f"Takeoff attitude (α={d.takeoff_alpha_deg}°, TE at {d.takeoff_te_height} m, h/c={d.takeoff_te_height / d.chord:.2f}): CL={cl_to:.3f}, CDi={tab.cdi(d.takeoff_alpha_deg, d.takeoff_te_height / d.chord):.4f}")
say("\nCruise points (trimmed wing lift = weight):")
say("| mass (kg) | V (m/s) | h (m) | α (deg) | CL | D_ind (N) | D_parasite (N) | L/D | P_shaft (kW) | P_elec (kW) | 30-min energy (kWh) |"); say("|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
cruise_pts = {}
for m in (MASSES["target 130 kg"], m_ref):
    for Vc in (22, 25, 28):
        cp = cruise_point(tab, m, Vc, d.cruise_height, d); cruise_pts[(m, Vc)] = cp
        if cp["ok"]:
            say(f"| {m:.0f} | {Vc} | {d.cruise_height} | {cp['alpha']:.1f} | {cp['CL']:.2f} | {cp['D_ind']:.0f} | {cp['D_par']:.0f} | {cp['LD']:.1f} | {cp['P_shaft'] / 1e3:.1f} | {cp['P_elec'] / 1e3:.1f} | {cp['P_elec'] * 0.5 / 1e3:.2f} |")
say("")

# ------------------------------------------------------------------ 4. takeoff + sizing
say("## 4. Takeoff simulation and sizing\n")
P_base = d.p_shaft_max
base = simulate(d, m_ref, P_base, tab)
fig, axs = plt.subplots(2, 2, figsize=(12, 8.5))
H = base["hist"]
ax = axs[0, 0]
ax.plot(H["t"], H["V"], label="speed (m/s)")
ax.plot(H["t"], H["x"] / 10, label="distance / 10 (m)")
ax.axvline(base["t_lo"], color=TEXT2, lw=0.8, ls=":"); ax.text(base["t_lo"], 1, f" lift-off {base['t_lo']:.0f} s, {base['x_lo']:.0f} m, {base['v_lo']:.1f} m/s", fontsize=8)
ax.set_xlabel("time (s)"); ax.set_title(f"Baseline: {m_ref:.0f} kg, {P_base / 1e3:.0f} kW shaft, step, trim 4°"); ax.legend(fontsize=8)
ax = axs[0, 1]
ax.plot(H["V"], H["T"], label="thrust")
ax.plot(H["V"], H["R_water"], label="water resistance")
ax.plot(H["V"], H["D_air"], label="air drag")
ax.plot(H["V"], H["R_water"] + H["D_air"], ls="--", color=TEXT2, label="total resistance")
ax.plot(H["V"], H["W_h"] / 5, ls=":", color=PALETTE[6], label="float load / 5")
ax.set_xlabel("speed (m/s)"); ax.set_ylabel("N"); ax.set_title("Forces vs speed during the run"); ax.legend(fontsize=8)
# thrust vs drag curves for a few powers
ax = axs[1, 0]
P_list = [8e3, 12e3, 15e3, 20e3]
c = thrust_drag_curves(d, m_ref, P_list, tab)
ax.plot(c["V"], c["D_total"], color=TEXT2, lw=2.5, label=f"total resistance, {m_ref:.0f} kg")
c130 = thrust_drag_curves(d, MASSES["target 130 kg"], [], tab)
ax.plot(c130["V"], c130["D_total"], color=TEXT2, lw=1.2, ls="--", label="total resistance, 130 kg")
for i, P in enumerate(P_list):
    ax.plot(c["V"], c["T"][P], color=PALETTE[i], label=f"thrust @ {P / 1e3:.0f} kW shaft")
ax.set_xlabel("speed (m/s)"); ax.set_ylabel("N"); ax.set_title("Thrust available vs resistance (fixed takeoff attitude)"); ax.legend(fontsize=7.5)
ax.set_ylim(0, 800)
# distance vs power for masses
ax = axs[1, 1]
Ps = np.arange(5e3, 25.1e3, 1e3)
sizing = {}
for i, (lab, m) in enumerate(MASSES.items()):
    xs, ts = [], []
    for P in Ps:
        r = simulate(d, m, P, tab, dt=0.05)
        xs.append(r["x_lo"] if r["ok"] else np.nan); ts.append(r["t_lo"] if r["ok"] else np.nan)
    sizing[lab] = (Ps, np.array(xs), np.array(ts))
    ax.plot(Ps / 1e3, xs, marker="o", ms=3, color=PALETTE[i], label=f"{lab} ({m:.0f} kg)")
ax.set_xlabel("shaft power (kW)"); ax.set_ylabel("takeoff distance (m)"); ax.set_yscale("log")
ax.set_title("Takeoff distance vs shaft power"); ax.legend(fontsize=8); ax.set_ylim(30, 2000)
finish(fig, f"{OUT}/fig04_takeoff.png", "Attitude fixed at takeoff incidence; prop model calibrated to SP140-class data; no waves, no wind. Lift-off = floats fully unloaded.")

say(f"Baseline ({m_ref:.0f} kg, {P_base / 1e3:.0f} kW shaft): lift-off at {base['v_lo']:.1f} m/s ({base['v_lo'] * 3.6:.0f} km/h) after {base['t_lo']:.1f} s and {base['x_lo']:.0f} m; "
    f"water hump {base['peak_water']:.0f} N at {base['v_hump']:.1f} m/s; min thrust margin {base['min_margin']:.0f} N; energy used {base['e_wh']:.0f} Wh")
say("\n| case | P_shaft (kW) | static thrust (kgf) | lift-off (m/s) | time (s) | distance (m) | min margin (N) | energy (Wh) |"); say("|---|---:|---:|---:|---:|---:|---:|---:|")
def row(lab, dd, m, P, **kw):
    r = simulate(dd, m, P, tab, **kw)
    if r["ok"]:
        say(f"| {lab} | {P / 1e3:.0f} | {static_thrust(P, dd) / 9.81:.0f} | {r['v_lo']:.1f} | {r['t_lo']:.1f} | {r['x_lo']:.0f} | {r['min_margin']:.0f} | {r['e_wh']:.0f} |")
    else:
        say(f"| {lab} | {P / 1e3:.0f} | {static_thrust(P, dd) / 9.81:.0f} | stuck at {r['stuck_V']:.1f} m/s | - | - | {r['min_margin']:.0f} | - |")
    return r
for lab, m in MASSES.items():
    for P in (8e3, 12e3, 15e3, 20e3):
        row(f"{lab}, {m:.0f} kg", d, m, P)
say("| sensitivities at estimated mass, 15 kW: |")
row("no step", d, m_ref, 15e3, has_step=False)
row("trim 3°", d, m_ref, 15e3, trim_deg=3)
row("trim 6°", d, m_ref, 15e3, trim_deg=6)
row("takeoff α 7°", d, m_ref, 15e3, alpha_deg=7)
row("takeoff α 11°", d, m_ref, 15e3, alpha_deg=11)
row("5 m/s headwind", d, m_ref, 15e3, headwind=5)
row("prop 1.15 m", Design(prop_diam=1.15), m_ref, 15e3)
row("prop 1.45 m", Design(prop_diam=1.45), m_ref, 15e3)
row("faired pilot (CdA 0.15)", Design(cda_pilot=0.15), m_ref, 15e3)
row("PAR what-if (prop ahead of wing)", Design(par_enabled=True), m_ref, 15e3)
say("")
# minimum power for takeoff within 250 m
say("Minimum shaft power for lift-off within 250 m / 300 m:")
for lab, (Ps_, xs, ts) in sizing.items():
    ok250 = Ps_[np.nan_to_num(xs, nan=1e9) <= 250]; ok300 = Ps_[np.nan_to_num(xs, nan=1e9) <= 300]
    say(f"- {lab}: {ok250[0] / 1e3:.0f} kW (250 m), {ok300[0] / 1e3:.0f} kW (300 m)" if len(ok300) else f"- {lab}: not within 300 m up to 25 kW")
# sizing summary
say("\n### Propulsion + battery sizing (from the sim)\n")
P_to = 15e3
cp = cruise_pts[(m_ref, 25)]; cp22 = cruise_pts[(m_ref, 22)]
bs = battery_summary(d, P_to / d.eta_motor_esc, cp["P_elec"], 1800, base["e_wh"])
say(f"- Takeoff: {P_to / 1e3:.0f} kW shaft for ~{base['t_lo']:.0f} s -> {P_to / d.eta_motor_esc / 1e3:.1f} kW electrical, {bs['i_peak']:.0f} A at {d.batt_v_nominal:.0f} V ({bs['c_peak']:.1f} C), {base['e_wh']:.0f} Wh")
say(f"- Static thrust at {P_to / 1e3:.0f} kW with a {d.prop_diam:.2f} m prop: {static_thrust(P_to, d) / 9.81:.0f} kgf; motor must be rated ≥ {P_to / 1e3:.0f} kW for 60 s, ~6-8 kW continuous")
say(f"- ESC: ≥ {bs['i_peak'] * 1.3:.0f} A continuous at {d.batt_v_nominal:.0f} V (30 % margin) -> 300-400 A class; 14S (50 V) keeps currents high; 20S (72 V) is the better fit")
say(f"- Cruise {cp['V']} m/s at {d.cruise_height} m, {m_ref:.0f} kg: {cp['P_shaft'] / 1e3:.1f} kW shaft / {cp['P_elec'] / 1e3:.1f} kW electrical, L/D {cp['LD']:.1f}, prop η {cp['eta_prop']:.2f}; 30 min = {bs['e_cruise_wh'] / 1e3:.2f} kWh vs {bs['usable_wh'] / 1e3:.2f} kWh usable -> endurance {bs['endurance_min']:.0f} min")
say(f"- Cruise 22 m/s: {cp22['P_elec'] / 1e3:.1f} kW electrical -> {(bs['usable_wh'] - base['e_wh']) / cp22['P_elec'] * 60:.0f} min")
cpf = cruise_point(tab, m_ref, 25, d.cruise_height, Design(cda_pilot=0.15))
say(f"- With a faired pilot (CdA 0.15 instead of 0.40): cruise 25 m/s needs {cpf['P_elec'] / 1e3:.1f} kW electrical, L/D {cpf['LD']:.1f} -> {(bs['usable_wh'] - base['e_wh']) / cpf['P_elec'] * 60:.0f} min")
say(f"- Battery {d.batt_kwh} kWh at {d.batt_wh_per_kg} Wh/kg = {bs['mass_kg']:.1f} kg; takeoff C-rate {bs['c_peak']:.1f} C is fine for 21700 power cells (e.g. 14S12P / 20S9P of P42A-class)")
open(f"{OUT}/summary_1_4.md", "w").write("\n".join(report) + "\n")
print("\nwrote", OUT)

# ------------------------------------------------------------------ 4b. cruise energy reality check
fig, axs = plt.subplots(1, 2, figsize=(12, 4.4))
Vc = np.arange(16, 31, 1.0)
cda_cases = [("as drawn: exposed pilot, wheels, cage (CdA 0.75)", dict()),
             ("faired pilot (CdA 0.47)", dict(cda_pilot=0.15)),
             ("faired pilot + enclosed wheels (CdA 0.33)", dict(cda_pilot=0.15, cda_wheels=0.02, cda_cage=0.04)),
             ("slick: everything faired (CdA 0.20)", dict(cda_pilot=0.08, cda_wheels=0.0, cda_cage=0.03, cda_misc=0.02))]
usable = d.batt_kwh * 1000 * d.batt_usable_frac - 60
say("\n### Cruise power vs drag clean-up (158 kg, 0.6 m height)\n")
say("| configuration | parasite CdA (m²) | P_elec @22 m/s (kW) | endurance @22 (min) | P_elec @25 (kW) | endurance @25 (min) | range @25 (km) |"); say("|---|---:|---:|---:|---:|---:|---:|")
for i, (lab, kw) in enumerate(cda_cases):
    dd = Design(**kw)
    P = []
    for v in Vc:
        cp = cruise_point(tab, m_ref, v, d.cruise_height, dd); P.append(cp["P_elec"] / 1e3 if cp["ok"] else np.nan)
    P = np.array(P)
    axs[0].plot(Vc, P, color=PALETTE[i], label=f"{lab}")
    axs[1].plot(Vc, usable / (P * 1e3) * 60, color=PALETTE[i], label=lab)
    p22 = cruise_point(tab, m_ref, 22, d.cruise_height, dd)["P_elec"]; p25 = cruise_point(tab, m_ref, 25, d.cruise_height, dd)["P_elec"]
    say(f"| {lab} | {dd.cda_parasite:.2f} | {p22 / 1e3:.1f} | {usable / p22 * 60:.0f} | {p25 / 1e3:.1f} | {usable / p25 * 60:.0f} | {usable / p25 * 25 * 3.6:.0f} |")
axs[0].axhline(usable / 1000 * 2, color=STATUS["serious"], ls=":", lw=1); axs[0].text(16.2, usable / 1000 * 2 + 0.3, "30 min on 2.5 kWh (85 % DoD, after takeoff)", color=STATUS["serious"], fontsize=8)
axs[0].set_xlabel("cruise speed (m/s)"); axs[0].set_ylabel("electrical power (kW)"); axs[0].set_title(f"Cruise power, {m_ref:.0f} kg, h = {d.cruise_height} m"); axs[0].legend(fontsize=7.5)
axs[1].axhline(30, color=STATUS["serious"], ls=":", lw=1)
axs[1].set_xlabel("cruise speed (m/s)"); axs[1].set_ylabel("endurance on 2.5 kWh (min)"); axs[1].set_title("Endurance (85 % DoD, 60 Wh takeoff reserve)"); axs[1].set_ylim(0, 45)
finish(fig, f"{OUT}/fig05_cruise_energy.png", "Parasite CdA build-up in params.py; wing profile Cd 0.018 added on top. Prop efficiency 0.58-0.63 from the momentum model; motor+ESC 0.88.")
open(f"{OUT}/summary_1_4.md", "w").write("\n".join(report) + "\n")
