"""wig: parametric design + simulation package for a single-seat electric WIG craft.

Modules
-------
params      design parameters (one dataclass, everything derived from it)
mass        component mass / CG budget
hydro       float resistance: displacement -> hump -> planing (Savitsky), step effect
aero        wing lift/drag in ground effect (vortex-ring VLM with mirror image), parasite drag, PAR
propulsion  prop thrust vs speed from shaft power (momentum theory), battery/ESC sizing
takeoff     time-stepped takeoff simulation
plots       matplotlib styling and figure helpers
"""
from .params import Design, SEAWATER, AIR, G
