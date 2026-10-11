"""Propeller thrust vs speed from shaft power (actuator-disk momentum theory), battery sizing.

Thrust model: kappa * T * (V + v_i) = P_shaft * eta(V),  v_i = -V/2 + sqrt(V^2/4 + T/(2 rho A))
  kappa   induced-power factor (non-uniform inflow, tip loss)  ~1.10-1.20
  eta(V)  blade profile-drag + cage losses: linear from eta_static (V=0) to eta_cruise (V=cruise),
          because a fixed-pitch prop is badly loaded at zero advance ratio.
Static thrust: T0 = (P eta_static / kappa)^(2/3) (2 rho A)^(1/3).
Calibration: with the defaults a 1.3 m prop gives 58 kgf at 15 kW and 81 kgf at 25 kW shaft.
The OpenPPG SP140 (1.4 m prop) is quoted at 79 kgf / 25 kW peak (xcmag.com, 2020); scaled to
1.3 m that is ~75 kgf, so the model is ~8 % optimistic there and conservative at lower power.
Cruise prop efficiency comes out ~0.65-0.70 at 25 m/s, typical for a 2-blade fixed-pitch prop.
"""
import math
from scipy.optimize import brentq
from .params import Design, AIR


def eta_profile(V, d: Design):
    f = min(max(V / d.cruise_speed, 0.0), 1.0)
    return d.prop_eta_static + (d.prop_eta_cruise - d.prop_eta_static) * f


def thrust(P_shaft, V, d: Design):
    """Thrust (N) at airspeed V (m/s) for shaft power P_shaft (W)."""
    if P_shaft <= 0:
        return 0.0
    P = P_shaft * eta_profile(V, d)
    A = d.prop_area
    rho = AIR.rho
    def f(T):
        vi = -V / 2 + math.sqrt(V ** 2 / 4 + T / (2 * rho * A))
        return d.prop_kappa * T * (V + vi) - P
    T0 = (P / d.prop_kappa) ** (2 / 3) * (2 * rho * A) ** (1 / 3)
    return brentq(f, 1e-6, 2 * T0 + 10)


def static_thrust(P_shaft, d: Design):
    return thrust(P_shaft, 0.0, d)


def power_for_thrust(T, V, d: Design):
    """Shaft power (W) to make thrust T at airspeed V."""
    vi = -V / 2 + math.sqrt(V ** 2 / 4 + T / (2 * AIR.rho * d.prop_area))
    return d.prop_kappa * T * (V + vi) / eta_profile(V, d)


def prop_efficiency(P_shaft, V, d: Design):
    T = thrust(P_shaft, V, d)
    return T * V / P_shaft if P_shaft > 0 else 0.0


def battery_summary(d: Design, p_elec_peak, p_elec_cruise, t_cruise_s, e_takeoff_wh):
    """Pack numbers: usable energy, currents, C-rate, endurance."""
    wh = d.batt_kwh * 1000
    usable = wh * d.batt_usable_frac
    i_peak = p_elec_peak / d.batt_v_nominal
    i_cruise = p_elec_cruise / d.batt_v_nominal
    e_cruise = p_elec_cruise * t_cruise_s / 3600
    return dict(wh=wh, usable_wh=usable, mass_kg=wh / d.batt_wh_per_kg,
                i_peak=i_peak, c_peak=p_elec_peak / wh, i_cruise=i_cruise,
                e_cruise_wh=e_cruise, e_takeoff_wh=e_takeoff_wh,
                e_total_wh=e_cruise + e_takeoff_wh,
                margin_wh=usable - e_cruise - e_takeoff_wh,
                endurance_min=(usable - e_takeoff_wh) / p_elec_cruise * 60 if p_elec_cruise > 0 else float("inf"))
