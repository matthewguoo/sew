"""Cruise point (needed for battery sizing in item 4; item 6 expands this to full sweeps)."""
import math
from scipy.optimize import brentq
from .params import Design, AIR
from .aero import GETable, parasite_drag
from .propulsion import power_for_thrust, thrust


def trim_alpha(table: GETable, W, V, h_te, d: Design):
    """Wing incidence (deg) that makes wing lift = weight at speed V and TE height h_te."""
    q = 0.5 * AIR.rho * V ** 2
    hc = h_te / d.chord
    f = lambda a: q * d.wing_area * table.cl(a, hc) - W
    lo, hi = table.alphas[0], d.alpha_stall_deg
    if f(hi) < 0:
        return None                         # can't carry the weight below stall
    if f(lo) > 0:
        return lo
    return brentq(f, lo, hi)


def cruise_point(table: GETable, m, V, h_te, d: Design):
    W = m * 9.81
    a = trim_alpha(table, W, V, h_te, d)
    if a is None:
        return dict(ok=False, V=V, h=h_te)
    q = 0.5 * AIR.rho * V ** 2
    hc = h_te / d.chord
    cdi = table.cdi(a, hc)
    D_ind = q * d.wing_area * cdi
    D_par = parasite_drag(V, d)
    D = D_ind + D_par
    P_shaft = power_for_thrust(D, V, d)
    P_elec = P_shaft / d.eta_motor_esc
    return dict(ok=True, V=V, h=h_te, alpha=a, CL=table.cl(a, hc), CDi=cdi, D_ind=D_ind, D_par=D_par,
                D=D, LD=W / D, P_shaft=P_shaft, P_elec=P_elec, eta_prop=D * V / P_shaft)
