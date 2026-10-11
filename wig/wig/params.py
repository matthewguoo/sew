"""Design parameters. Everything else in the package reads from one `Design` object.

Units: SI throughout (m, kg, s, N, W, rad unless a name ends in _deg).
Coordinate convention for positions: x measured aft from the spine nose (m),
z measured up from the bottom of the spine / keel line (m).
"""
from dataclasses import dataclass, field, asdict
import math

G = 9.81

@dataclass(frozen=True)
class Fluid:
    rho: float   # kg/m^3
    nu: float    # m^2/s kinematic viscosity

SEAWATER = Fluid(rho=1025.0, nu=1.05e-6)   # SF Bay, ~15 C, brackish-to-salt
AIR      = Fluid(rho=1.225,  nu=1.46e-5)   # sea level ISA


@dataclass
class Design:
    # ---- Masses (kg) -----------------------------------------------------------
    m_pilot: float = 66.0
    m_allup_target: float = 130.0          # the brief's all-up target

    # ---- Wing ------------------------------------------------------------------
    span: float = 5.0                      # b, tip-to-tip between endplates (m)
    chord: float = 1.6                     # c, rectangular planform (m)
    camber: float = 0.04                   # max camber / chord, parabolic mean line
    wing_le_x: float = 0.9                 # x of wing leading edge from spine nose (m)
    wing_z: float = 0.45                   # height of wing TE above keel line (m)
    endplate_depth: float = 0.30          # endplate (float side) height below wing TE (m)
    endplate_gap: float = 0.05            # gap endplate bottom -> water in cruise (m); 0 = sealed
    cd_profile_wing: float = 0.018         # sewn double-surface fabric wing, battens; Re~2.5e6
    alpha_stall_deg: float = 12.0          # fabric low-AR wing in GE: conservative

    # ---- Tail (T-tail on boom) --------------------------------------------------
    tail_area: float = 0.9                 # horizontal tail area (m^2)
    tail_arm: float = 2.6                  # wing 1/4c -> tail 1/4c (m)
    tail_z: float = 1.2                    # tail height above keel line (m)

    # ---- Floats (two OTS inflatables at the wingtips) ---------------------------
    float_len: float = 3.20                # L (m)   e.g. 10'6" iSUP
    float_beam: float = 0.81               # b (m)   32"
    float_thick: float = 0.15              # (m)     6"
    float_volume: float = 0.30             # m^3 each (290-310 L class)
    float_deadrise_deg: float = 0.0        # flat drop-stitch bottom
    float_step_x: float = 1.60             # step position from the bow (m); None = no step
    float_has_step: bool = True
    float_aft_wetted_frac: float = 0.5     # unstepped: fraction of afterbody that stays wetted
    float_spray_frac: float = 0.10         # whisker-spray drag as a fraction of friction drag
    planing_trim_deg: float = 4.0          # running trim used for Savitsky (fixed-trim mode)

    # ---- Propulsion -------------------------------------------------------------
    p_shaft_max: float = 15_000.0          # continuous-rated shaft power available (W)
    p_shaft_peak: float = 20_000.0         # short-burst (takeoff) shaft power (W)
    prop_diam: float = 1.30                # m (caged pusher)
    prop_eta_profile: float = 0.85         # non-ideal losses (profile drag, tip, cage)
    prop_kappa: float = 1.15               # induced-power factor
    prop_x: float = 2.3                    # prop disk x from spine nose (m)
    prop_z: float = 1.0                    # prop axis height above keel line (m)
    thrust_angle_deg: float = 0.0          # + = nose-up component (thrust tilted down at the back)
    par_enabled: bool = False              # power-augmented ram (needs prop AHEAD of wing)
    par_capture: float = 0.5               # fraction of slipstream momentum ducted under the wing
    par_turn_deg: float = 10.0             # mean downward deflection of the captured jet

    # ---- Battery ----------------------------------------------------------------
    batt_kwh: float = 2.5
    batt_usable_frac: float = 0.85
    batt_v_nominal: float = 50.4           # 14S Li-ion (3.6 V/cell)
    batt_wh_per_kg: float = 185.0          # pack-level incl. BMS, case (21700 cells)
    eta_motor_esc: float = 0.88            # electrical -> shaft at takeoff power

    # ---- Land mode --------------------------------------------------------------
    wheel_diam: float = 0.5                # 20" wheels
    n_wheels: int = 4

    # ---- Parasite drag items (equivalent flat-plate area CdA, m^2) ---------------
    # Rough build-up; see docs/ASSUMPTIONS.md. Override to study fairings.
    cda_pilot: float = 0.40                # reclined pilot + harness, unfaired (0.15 faired)
    cda_wheels: float = 0.10               # 4 spoked 20" wheels folded up in the airstream
    cda_cage: float = 0.07                 # prop cage hoop + netting + pylon
    cda_floats: float = 0.06               # 2 inflatable floats above water, nose + skin
    cda_misc: float = 0.05                 # spine ends, boom, hub motor, cables, controls
    interference_factor: float = 1.10

    # ---- Operations -------------------------------------------------------------
    cruise_speed: float = 25.0             # m/s (90 km/h)
    cruise_height: float = 0.6             # TE height above water (m)
    takeoff_alpha_deg: float = 9.0         # wing incidence to the water surface on the floats
    takeoff_te_height: float = 0.35        # TE height above water while on the floats (m)

    # ---- derived --------------------------------------------------------------
    @property
    def wing_area(self):  return self.span * self.chord
    @property
    def aspect_ratio(self): return self.span / self.chord
    @property
    def mac(self): return self.chord
    @property
    def prop_area(self): return math.pi * (self.prop_diam / 2) ** 2
    @property
    def cda_parasite(self):
        """Total non-wing equivalent flat-plate area (m^2)."""
        return (self.cda_pilot + self.cda_wheels + self.cda_cage + self.cda_floats +
                self.cda_misc) * self.interference_factor

    def as_dict(self): return asdict(self)
