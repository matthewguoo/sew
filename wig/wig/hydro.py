"""Item 2: float resistance from displacement through hump to planing.

Method
------
Planing regime: Savitsky (1964), "Hydrodynamic Design of Planing Hulls",
Marine Technology 1(1), for a prismatic surface of beam b, deadrise beta,
running trim tau, carrying hydrodynamic load Delta:

    C_V    = V / sqrt(g b)                                   speed coefficient
    C_L0   = tau_deg^1.1 (0.0120 lam^0.5 + 0.0055 lam^2.5 / C_V^2)   flat plate
    C_Lb   = C_L0 - 0.0065 beta_deg C_L0^0.6                 deadrise correction
    Delta  = C_Lb * 0.5 rho V^2 b^2                          -> solve for lam (mean wetted length / b)
    V_m    = V sqrt(1 - (0.012 lam^0.5 tau^1.1 ...)/(lam cos tau))     mean bottom velocity
    R_f    = C_f 0.5 rho V_m^2 (lam b^2 / cos beta),  C_f = ITTC-57 + 0.0004 roughness
    R      = Delta tan tau + R_f / cos tau          (pressure drag + friction)
    l_p    = lam b (0.75 - 1/(5.21 C_V^2/lam^2 + 2.39))      centre of pressure fwd of transom
Validity: 0.6 <= lam <= 4, 2 <= tau_deg <= 15, C_V >= ~0.6.

Whisker spray drag: added as a fraction of friction drag (Savitsky, DeLorme & Datla 2007,
"Inclusion of whisker spray drag in performance prediction method for high-speed planing
hulls", Marine Technology 44(1)); 10 % is typical for low deadrise.

Step: modelled as two prismatic planing surfaces (forebody + afterbody) sharing the load,
each solved with Savitsky at the same trim. Because Savitsky lift goes as lam^0.5 the two
shorter surfaces need less total wetted area for the same lift -> less friction. This is a
simplification of Savitsky & Morabito (2010) (afterbody runs in the forebody wake).

Displacement regime (C_V < ~1): flat-bottomed pontoon treated as a box. Friction on the
static wetted area (ITTC-57) + a residuary (wave) term R_w = Delta * k_w * Fn_L^4 with k_w a
fitted placeholder (default gives R_w/Delta = 0.10 at Fn_L = 0.5, typical for a blunt
pontoon). The two regimes are blended with a smoothstep in C_V over [0.5, 1.2].
** The displacement/hump numbers are the least trustworthy part of this model.  A tow test
of the real float (spring scale behind a dinghy at 1-6 m/s) replaces them cheaply. **
"""
import math
import numpy as np
from scipy.optimize import brentq, minimize_scalar
from .params import Design, SEAWATER, G

K_WAVE = 1.6   # residuary placeholder: R_w/Delta = K_WAVE * Fn_L^4

def cf_ittc(re, delta_cf=0.0004):
    re = max(re, 1e4)
    return 0.075 / (math.log10(re) - 2) ** 2 + delta_cf


def savitsky_cl(lam, tau_deg, cv, beta_deg):
    cl0 = tau_deg ** 1.1 * (0.0120 * lam ** 0.5 + 0.0055 * lam ** 2.5 / cv ** 2)
    return cl0 - 0.0065 * beta_deg * cl0 ** 0.6


def planing_surface(V, load, b, tau_deg, beta_deg, lam_max, fluid=SEAWATER, spray_frac=0.10):
    """One prismatic planing surface. Returns dict; 'ok' False if it can't carry the load."""
    rho, nu = fluid.rho, fluid.nu
    cv = V / math.sqrt(G * b)
    cl_req = load / (0.5 * rho * V ** 2 * b ** 2)
    f = lambda lam: savitsky_cl(lam, tau_deg, cv, beta_deg) - cl_req
    if f(lam_max) < 0:          # even full wetted length can't make the lift: plowing
        lam, ok = lam_max, False
    else:
        lam, ok = brentq(f, 1e-3, lam_max), True
    tau = math.radians(tau_deg)
    beta = math.radians(beta_deg)
    cl0 = tau_deg ** 1.1 * (0.0120 * lam ** 0.5 + 0.0055 * lam ** 2.5 / cv ** 2)
    term = (0.012 * lam ** 0.5 * tau_deg ** 1.1 - 0.0065 * beta_deg * cl0 ** 0.6)
    vm2 = V ** 2 * max(1 - term / (lam * math.cos(tau)), 0.3)
    vm = math.sqrt(vm2)
    s_wet = lam * b ** 2 / math.cos(beta)
    re = vm * lam * b / nu
    rf = cf_ittc(re) * 0.5 * rho * vm2 * s_wet
    rf *= (1 + spray_frac)
    lift = savitsky_cl(lam, tau_deg, cv, beta_deg) * 0.5 * rho * V ** 2 * b ** 2 if ok else load
    r_pressure = lift * math.tan(tau)
    r = r_pressure + rf / math.cos(tau)
    lp = lam * b * (0.75 - 1 / (5.21 * cv ** 2 / lam ** 2 + 2.39))
    return dict(R=r, R_f=rf / math.cos(tau), R_p=r_pressure, lam=lam, wetted_len=lam * b,
                S_wet=s_wet, cv=cv, lp=lp, ok=ok, cl=cl_req)


def displacement_resistance(V, load, d: Design, fluid=SEAWATER):
    """Box pontoon at rest attitude: friction on static wetted area + residuary placeholder."""
    rho, nu = fluid.rho, fluid.nu
    L, b = d.float_len, d.float_beam
    draft = load / (rho * G * L * b)
    s_wet = L * b + 2 * (L + b) * draft
    re = V * L / nu
    rf = cf_ittc(re) * 0.5 * rho * V ** 2 * s_wet
    fn = V / math.sqrt(G * L)
    rw = load * K_WAVE * fn ** 4
    return dict(R=rf + rw, R_f=rf, R_w=rw, draft=draft, S_wet=s_wet, fn=fn)


def smoothstep(x, lo, hi):
    t = min(max((x - lo) / (hi - lo), 0.0), 1.0)
    return t * t * (3 - 2 * t)


def float_resistance(V, load, d: Design, trim_deg=None, has_step=None, fluid=SEAWATER):
    """Resistance of ONE float carrying hydrodynamic load `load` (N) at speed V (m/s).

    Blends displacement and planing regimes; applies the step model if enabled.
    Returns dict with R (total), components and regime info.  load<=0 -> all zeros.
    """
    if load <= 1e-6 or V <= 1e-6:
        return dict(R=0.0, R_f=0.0, R_p=0.0, R_w=0.0, lam=0.0, wetted_len=0.0, regime="airborne",
                    cv=V / math.sqrt(G * d.float_beam), s=1.0, lp=0.0)
    tau = d.planing_trim_deg if trim_deg is None else trim_deg
    step = d.float_has_step if has_step is None else has_step
    b, beta = d.float_beam, d.float_deadrise_deg
    cv = V / math.sqrt(G * b)
    # --- planing part
    if step:
        f_aft = 0.30                       # afterbody share of load
        L_fb = d.float_step_x
        L_ab = d.float_len - d.float_step_x
        fb = planing_surface(V, load * (1 - f_aft), b, tau, beta, L_fb / b, fluid, d.float_spray_frac)
        ab = planing_surface(V, load * f_aft, b, tau, beta, L_ab / b, fluid, d.float_spray_frac)
        if not (fb["ok"] and ab["ok"]):     # fall back to a single surface over the whole length
            single = planing_surface(V, load, b, tau, beta, d.float_len / b, fluid, d.float_spray_frac)
            plan = single; regime = "plowing (step flooded)"
        else:
            plan = dict(R=fb["R"] + ab["R"], R_f=fb["R_f"] + ab["R_f"], R_p=fb["R_p"] + ab["R_p"],
                        lam=fb["lam"] + ab["lam"], wetted_len=fb["wetted_len"] + ab["wetted_len"],
                        ok=True, lp=fb["lp"] + L_ab)   # c.p. of the forebody, from the transom
            regime = "planing (stepped)"
    else:
        plan = planing_surface(V, load, b, tau, beta, d.float_len / b, fluid, d.float_spray_frac)
        regime = "planing" if plan["ok"] else "plowing"
    # --- displacement part and blend
    disp = displacement_resistance(V, load, d, fluid)
    s = smoothstep(cv, 0.5, 1.2)
    if not plan["ok"]:
        s = min(s, 0.5)                  # can't fully plane: keep half the displacement drag
    R = (1 - s) * disp["R"] + s * plan["R"]
    return dict(R=R, R_f=(1 - s) * disp["R_f"] + s * plan["R_f"], R_p=s * plan["R_p"],
                R_w=(1 - s) * disp["R_w"], lam=plan["lam"], wetted_len=plan["wetted_len"],
                regime=regime if s > 0.5 else "displacement", cv=cv, s=s, lp=plan.get("lp", 0.0))


def optimum_trim(V, load, d: Design, has_step=None, lo=2.0, hi=10.0):
    """Trim that minimises resistance at this speed and load (Savitsky validity 2-15 deg)."""
    res = minimize_scalar(lambda t: float_resistance(V, load, d, t, has_step)["R"],
                          bounds=(lo, hi), method="bounded")
    return res.x, res.fun


def resistance_curve(speeds, loads, d: Design, trim_deg=None, has_step=None, two_floats=True):
    """Total water resistance (both floats) vs speed for a given per-craft hydrodynamic load array."""
    n = 2 if two_floats else 1
    out = []
    for V, W in zip(speeds, loads):
        r = float_resistance(V, W / n, d, trim_deg, has_step)
        out.append(n * r["R"])
    return np.array(out)
