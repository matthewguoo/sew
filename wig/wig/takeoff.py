"""Item 4: time-stepped takeoff simulation.

State: speed V, distance x.  Each step:
  T       = thrust(P_shaft, V)                       propulsion.py
  L_air   = q S CL(alpha_to, h_to/c) [+ PAR]          aero.py table
  D_air   = q S CDi + parasite [+ PAR]
  W_h     = max(W - L_air - T sin(thrust angle), 0)   load left on the floats
  R_water = 2 * float_resistance(V, W_h/2)            hydro.py (fixed trim)
  dV/dt   = (T cos(angle) - D_air - R_water) / m
Lift-off when W_h -> 0.  Attitude is held fixed at the takeoff incidence (the pilot/ballast
can't rotate much on floats); item 5 adds pitch dynamics.
Headwind: the aerodynamic terms use V + headwind, the water terms use V.
"""
import math
import numpy as np
from .params import Design, AIR, G
from .aero import GETable, parasite_drag, par_increment
from .hydro import float_resistance
from .propulsion import thrust


def simulate(d: Design, m, P_shaft, table: GETable, dt=0.02, t_max=120.0, headwind=0.0,
             trim_deg=None, has_step=None, alpha_deg=None, h_te=None, stop_margin=1.05):
    W = m * G
    alpha = d.takeoff_alpha_deg if alpha_deg is None else alpha_deg
    h = d.takeoff_te_height if h_te is None else h_te
    hc = h / d.chord
    cl, cdi = table.cl(alpha, hc), table.cdi(alpha, hc)
    ang = math.radians(d.thrust_angle_deg)
    V, x, t = 0.0, 0.0, 0.0
    hist = {k: [] for k in ["t", "x", "V", "T", "L_air", "D_air", "R_water", "W_h", "a"]}
    v_lo, t_lo, x_lo, e_wh = None, None, None, 0.0
    peak_water, v_hump = 0.0, 0.0
    while t < t_max:
        Va = V + headwind
        q = 0.5 * AIR.rho * Va ** 2
        T = thrust(P_shaft, Va, d)
        dL, dD, T_fwd = par_increment(T, Va, cl, cdi, d)
        L_air = q * d.wing_area * cl + dL
        D_air = q * d.wing_area * cdi + parasite_drag(Va, d) + dD
        W_h = max(W - L_air - T_fwd * math.sin(ang), 0.0)
        R_w = 2 * float_resistance(V, W_h / 2, d, trim_deg, has_step)["R"] if W_h > 0 else 0.0
        a = (T_fwd * math.cos(ang) - D_air - R_w) / m
        for k, v in zip(hist, [t, x, V, T, L_air, D_air, R_w, W_h, a]):
            hist[k].append(v)
        if R_w > peak_water:
            peak_water, v_hump = R_w, V
        if W_h <= 0 and v_lo is None:
            v_lo, t_lo, x_lo = V, t, x
        if v_lo is not None and V >= v_lo * stop_margin:
            break
        if a < 0.02 and t > 2.0 and v_lo is None:
            break                     # stuck: can't get over the hump
        e_wh += P_shaft / d.eta_motor_esc * dt / 3600
        V += a * dt; x += V * dt; t += dt
    H = {k: np.array(v) for k, v in hist.items()}
    ok = v_lo is not None
    return dict(ok=ok, v_lo=v_lo, t_lo=t_lo, x_lo=x_lo, e_wh=e_wh if ok else float("nan"),
                peak_water=peak_water, v_hump=v_hump, hist=H, m=m, P_shaft=P_shaft,
                min_margin=float(np.min(H["T"] - H["D_air"] - H["R_water"])) if len(H["T"]) else 0.0,
                stuck_V=None if ok else V)


def thrust_drag_curves(d: Design, m, P_list, table: GETable, V=None, trim_deg=None, has_step=None):
    """Static (constant-attitude) thrust-available vs drag-required curves for the classic hump plot."""
    V = np.linspace(0.2, 22, 110) if V is None else V
    W = m * G
    alpha, hc = d.takeoff_alpha_deg, d.takeoff_te_height / d.chord
    cl, cdi = table.cl(alpha, hc), table.cdi(alpha, hc)
    q = 0.5 * AIR.rho * V ** 2
    L = q * d.wing_area * cl
    W_h = np.maximum(W - L, 0)
    D_air = q * d.wing_area * cdi + np.array([parasite_drag(v, d) for v in V])
    R_w = np.array([2 * float_resistance(v, wh / 2, d, trim_deg, has_step)["R"] if wh > 0 else 0 for v, wh in zip(V, W_h)])
    T = {P: np.array([thrust(P, v, d) for v in V]) for P in P_list}
    return dict(V=V, D_air=D_air, R_water=R_w, D_total=D_air + R_w, W_h=W_h, T=T)
