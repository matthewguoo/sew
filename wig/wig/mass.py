"""Item 1: mass and CG budget.

Each component carries two mass numbers:
  est     - what I expect this architecture to actually weigh with ordinary parts
  stretch - a disciplined light build (smaller floats, thinner walls, lighter wheels)
and a position (x aft of spine nose, z above keel line) for the CG.
Where a mass is computed from geometry the formula is in `how`.
"""
from dataclasses import dataclass
import math
from .params import Design

RHO_AL = 2700.0      # 6061
RHO_AL7075 = 2810.0

def tube_mass(d_out, wall, length, rho=RHO_AL):
    return math.pi * d_out * wall * length * rho   # thin-wall approximation

@dataclass
class Component:
    name: str
    est: float
    stretch: float
    x: float
    z: float
    how: str
    printable: bool = False   # 3D-printable (non-structural) candidate

def components(d: Design):
    spine = tube_mass(0.20, 0.0015, 2.5)
    spine_stretch = tube_mass(0.20, 0.0012, 2.5)
    main_spar = tube_mass(0.050, 0.0015, d.span + 0.2, RHO_AL7075)
    rear_spar = tube_mass(0.038, 0.0012, d.span + 0.2, RHO_AL7075)
    battens = 9 * d.chord * 0.15                       # 16 mm pultruded GRP rod ~0.15 kg/m
    skin = 2 * d.wing_area * 0.17 * 1.15               # 2 surfaces, 170 g/m2 Dacron, 15 % seams/pockets
    batt = d.batt_kwh * 1000 / d.batt_wh_per_kg
    wing_cg_x = d.wing_le_x + 0.45 * d.chord
    tail_x = d.wing_le_x + 0.25 * d.chord + d.tail_arm
    float_x = d.wing_le_x + 0.5 * d.chord
    return [
        Component("Battery pack 2.5 kWh (14S12P 21700 + BMS + case)", batt, batt, 1.25, 0.10,
                  f"{d.batt_kwh} kWh / {d.batt_wh_per_kg} Wh/kg pack-level"),
        Component("Motor (SP140-class outrunner)", 4.5, 4.2, d.prop_x, d.prop_z, "vendor class data"),
        Component("ESC + wiring + contactor", 1.2, 1.0, d.prop_x - 0.3, d.prop_z - 0.2, "estimate"),
        Component("Propeller 130 cm 2-blade", 0.6, 0.5, d.prop_x, d.prop_z, "vendor class data"),
        Component("Prop cage (Al hoop + Dyneema net)", 2.5, 2.0, d.prop_x, d.prop_z, "paramotor cage class"),
        Component("Prop pylon + mount", 1.5, 1.2, d.prop_x - 0.2, 0.7, "estimate"),
        Component("Spine tube 2.5 m x 200 mm (6061)", spine, spine_stretch, 1.25, 0.10,
                  "pi*D*t*L*rho, t=1.5 mm (stretch 1.2 mm)"),
        Component("Spine end caps, bulkheads, hatch, seals", 1.5, 1.2, 1.25, 0.10, "estimate"),
        Component("Main spar 50x1.5 7075", main_spar, main_spar, d.wing_le_x + 0.25*d.chord, d.wing_z + 0.1, "pi*D*t*L*rho"),
        Component("Rear spar 38x1.2 7075", rear_spar, rear_spar, d.wing_le_x + 0.9*d.chord, d.wing_z, "pi*D*t*L*rho"),
        Component("Battens / ribs (9 x GRP rod)", battens, battens * 0.8, wing_cg_x, d.wing_z + 0.05, "9 x chord x 0.15 kg/m"),
        Component("Wing skin (Dacron, 2 surfaces)", skin, skin, wing_cg_x, d.wing_z + 0.05, "2*S*170 g/m2*1.15"),
        Component("Wing fittings, brace wires, brackets", 2.0, 1.5, wing_cg_x, d.wing_z, "estimate", printable=True),
        Component("Floats: 2 x drop-stitch iSUP", 18.0, 13.0, float_x, 0.08,
                  "2 x 9 kg (10'6\") / stretch 2 x 6.5 kg (9')"),
        Component("Float planing strips (HDPE) + step", 2.4, 1.6, float_x, 0.0, "2 x 3 mm HDPE 0.4x1.6 m"),
        Component("Float mounts / saddles", 1.5, 1.0, float_x, 0.15, "estimate", printable=True),
        Component("Tail boom 2 m 50x1.2 6061", tube_mass(0.05, 0.0012, 2.0), tube_mass(0.05, 0.0012, 2.0),
                  2.5 + 1.0, 0.9, "pi*D*t*L*rho"),
        Component("T-tail surfaces (frame + skin)", 2.0, 1.6, tail_x, d.tail_z, "1.2 m2 at ~1.7 kg/m2"),
        Component("Tail fittings", 0.5, 0.4, tail_x, d.tail_z, "estimate", printable=True),
        Component("Wheels 4 x 20\" (rim, tire, tube)", 6.4, 5.0, 1.25, 0.25, "4 x 1.6 kg"),
        Component("750 W geared hub motor", 3.5, 3.2, 2.1, 0.25, "vendor class (Bafang G020 class)"),
        Component("Wheel pivot arms + axles + latches", 3.2, 2.4, 1.25, 0.25, "4 x 0.8 kg"),
        Component("Crank, pedals, chain, freewheel", 2.5, 2.0, 0.6, 0.30, "bike parts"),
        Component("E-bike controller, throttle, lights", 0.5, 0.4, 1.0, 0.2, "estimate"),
        Component("Paramotor harness (used)", 2.5, 2.2, 1.3, 0.45, "vendor class"),
        Component("Flight controls, RC rx, kill switch, telemetry", 1.5, 1.2, 1.1, 0.5, "estimate", printable=True),
        Component("Misc hardware, paint, straps", 2.0, 1.5, 1.4, 0.3, "estimate"),
    ]

def budget(d: Design, which="est"):
    comps = components(d)
    m = sum(getattr(c, which) for c in comps)
    mx = sum(getattr(c, which) * c.x for c in comps)
    mz = sum(getattr(c, which) * c.z for c in comps)
    # pilot: reclined, hips ~ on the spine behind the wing LE
    px, pz = 1.35, 0.55
    m_all = m + d.m_pilot
    cg_x = (mx + d.m_pilot * px) / m_all
    cg_z = (mz + d.m_pilot * pz) / m_all
    return dict(components=comps, m_empty=m, m_allup=m_all, cg_x=cg_x, cg_z=cg_z,
                cg_x_empty=mx / m, cg_z_empty=mz / m,
                wing_quarter_chord_x=d.wing_le_x + 0.25 * d.chord)

def table(d: Design):
    b = budget(d)
    lines = ["| Component | est (kg) | stretch (kg) | x (m) | z (m) | how |", "|---|---:|---:|---:|---:|---|"]
    for c in b["components"]:
        tag = " [3D-print ok]" if c.printable else ""
        lines.append(f"| {c.name}{tag} | {c.est:.1f} | {c.stretch:.1f} | {c.x:.2f} | {c.z:.2f} | {c.how} |")
    s = budget(d, "stretch")
    lines += ["", f"**Empty mass:** est {b['m_empty']:.1f} kg, stretch {s['m_empty']:.1f} kg "
              f"(brief implies {d.m_allup_target - d.m_pilot:.0f} kg)",
              f"**All-up with {d.m_pilot:.0f} kg pilot:** est {b['m_allup']:.1f} kg, stretch {s['m_allup']:.1f} kg "
              f"(target {d.m_allup_target:.0f} kg)",
              f"**CG (all-up, est):** x = {b['cg_x']:.2f} m aft of nose, z = {b['cg_z']:.2f} m above keel; "
              f"wing 1/4-chord at x = {b['wing_quarter_chord_x']:.2f} m "
              f"-> CG at {100*(b['cg_x']-d.wing_le_x)/d.chord:.0f} % chord"]
    return "\n".join(lines)
