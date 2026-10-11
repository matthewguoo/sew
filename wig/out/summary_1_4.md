# Items 1-4 results

## 1. Mass / CG budget

| Component | est (kg) | stretch (kg) | x (m) | z (m) | how |
|---|---:|---:|---:|---:|---|
| Battery pack 2.5 kWh (14S12P 21700 + BMS + case) | 13.5 | 13.5 | 1.25 | 0.10 | 2.5 kWh / 185.0 Wh/kg pack-level |
| Motor (SP140-class outrunner) | 4.5 | 4.2 | 2.30 | 1.00 | vendor class data |
| ESC + wiring + contactor | 1.2 | 1.0 | 2.00 | 0.80 | estimate |
| Propeller 130 cm 2-blade | 0.6 | 0.5 | 2.30 | 1.00 | vendor class data |
| Prop cage (Al hoop + Dyneema net) | 2.5 | 2.0 | 2.30 | 1.00 | paramotor cage class |
| Prop pylon + mount | 1.5 | 1.2 | 2.10 | 0.70 | estimate |
| Spine tube 2.5 m x 200 mm (6061) | 6.4 | 5.1 | 1.25 | 0.10 | pi*D*t*L*rho, t=1.5 mm (stretch 1.2 mm) |
| Spine end caps, bulkheads, hatch, seals | 1.5 | 1.2 | 1.25 | 0.10 | estimate |
| Main spar 50x1.5 7075 | 3.4 | 3.4 | 1.30 | 0.55 | pi*D*t*L*rho |
| Rear spar 38x1.2 7075 | 2.1 | 2.1 | 2.34 | 0.45 | pi*D*t*L*rho |
| Battens / ribs (9 x GRP rod) | 2.2 | 1.7 | 1.62 | 0.50 | 9 x chord x 0.15 kg/m |
| Wing skin (Dacron, 2 surfaces) | 3.1 | 3.1 | 1.62 | 0.50 | 2*S*170 g/m2*1.15 |
| Wing fittings, brace wires, brackets [3D-print ok] | 2.0 | 1.5 | 1.62 | 0.45 | estimate |
| Floats: 2 x drop-stitch iSUP | 18.0 | 13.0 | 1.70 | 0.08 | 2 x 9 kg (10'6") / stretch 2 x 6.5 kg (9') |
| Float planing strips (HDPE) + step | 2.4 | 1.6 | 1.70 | 0.00 | 2 x 3 mm HDPE 0.4x1.6 m |
| Float mounts / saddles [3D-print ok] | 1.5 | 1.0 | 1.70 | 0.15 | estimate |
| Tail boom 2 m 50x1.2 6061 | 1.0 | 1.0 | 3.50 | 0.90 | pi*D*t*L*rho |
| T-tail surfaces (frame + skin) | 2.0 | 1.6 | 3.90 | 1.20 | 1.2 m2 at ~1.7 kg/m2 |
| Tail fittings [3D-print ok] | 0.5 | 0.4 | 3.90 | 1.20 | estimate |
| Wheels 4 x 20" (rim, tire, tube) | 6.4 | 5.0 | 1.25 | 0.25 | 4 x 1.6 kg |
| 750 W geared hub motor | 3.5 | 3.2 | 2.10 | 0.25 | vendor class (Bafang G020 class) |
| Wheel pivot arms + axles + latches | 3.2 | 2.4 | 1.25 | 0.25 | 4 x 0.8 kg |
| Crank, pedals, chain, freewheel | 2.5 | 2.0 | 0.60 | 0.30 | bike parts |
| E-bike controller, throttle, lights | 0.5 | 0.4 | 1.00 | 0.20 | estimate |
| Paramotor harness (used) | 2.5 | 2.2 | 1.30 | 0.45 | vendor class |
| Flight controls, RC rx, kill switch, telemetry [3D-print ok] | 1.5 | 1.2 | 1.10 | 0.50 | estimate |
| Misc hardware, paint, straps | 2.0 | 1.5 | 1.40 | 0.30 | estimate |

**Empty mass:** est 92.0 kg, stretch 77.1 kg (brief implies 64 kg)
**All-up with 66 kg pilot:** est 158.0 kg, stretch 143.1 kg (target 130 kg)
**CG (all-up, est):** x = 1.52 m aft of nose, z = 0.42 m above keel; wing 1/4-chord at x = 1.30 m -> CG at 39 % chord

## 2. Float hydrodynamics (2 x 10'6" iSUP, flat bottom)

- step, trim 4°: hump 203 N at 4.5 m/s (R/W = 0.131)
- no step, trim 4°: hump 213 N at 5.7 m/s (R/W = 0.138)
- step, trim 2°: hump 274 N at 6.1 m/s (R/W = 0.177)
- step, trim 6°: hump 223 N at 3.0 m/s (R/W = 0.144)
- takeoff attitude, target 130 kg: water hump 159 N at 3.0 m/s; floats unload at 14.9 m/s
- takeoff attitude, stretch build: water hump 172 N at 3.0 m/s; floats unload at 15.6 m/s
- takeoff attitude, estimated build: water hump 189 N at 4.0 m/s; floats unload at 16.5 m/s

Optimum trim (min drag) vs speed at full load, stepped:
- V=3 m/s: τ_opt=2.0°, R=147 N (vs 193 N at 4°)
- V=5 m/s: τ_opt=4.5°, R=200 N (vs 201 N at 4°)
- V=8 m/s: τ_opt=4.0°, R=160 N (vs 160 N at 4°)
- V=12 m/s: τ_opt=3.3°, R=128 N (vs 133 N at 4°)

## 3. Wing in ground effect (VLM + mirror image)

| α (deg) | h/c | CL (EP) | CDi (EP) | CL (no EP) | CDi (no EP) | Cm c/4 |
|---:|---:|---:|---:|---:|---:|---:|
| 2 | 0.10 | 0.741 | 0.0092 | 0.697 | 0.0104 | -0.175 |
| 2 | 0.20 | 0.621 | 0.0083 | 0.544 | 0.0109 | -0.145 |
| 2 | 0.30 | 0.539 | 0.0099 | 0.484 | 0.0111 | -0.130 |
| 2 | 0.50 | 0.470 | 0.0111 | 0.432 | 0.0116 | -0.119 |
| 2 | 1.00 | 0.423 | 0.0123 | 0.394 | 0.0124 | -0.114 |
| 6 | 0.10 | 1.120 | 0.0201 | 1.060 | 0.0234 | -0.182 |
| 6 | 0.20 | 0.979 | 0.0199 | 0.867 | 0.0268 | -0.150 |
| 6 | 0.30 | 0.867 | 0.0248 | 0.780 | 0.0282 | -0.131 |
| 6 | 0.50 | 0.763 | 0.0284 | 0.701 | 0.0298 | -0.117 |
| 6 | 1.00 | 0.688 | 0.0317 | 0.639 | 0.0319 | -0.109 |
| 10 | 0.10 | 1.410 | 0.0309 | 1.343 | 0.0369 | -0.188 |
| 10 | 0.20 | 1.280 | 0.0330 | 1.147 | 0.0458 | -0.155 |
| 10 | 0.30 | 1.159 | 0.0432 | 1.050 | 0.0498 | -0.134 |
| 10 | 0.50 | 1.038 | 0.0513 | 0.956 | 0.0540 | -0.116 |
| 10 | 1.00 | 0.945 | 0.0584 | 0.880 | 0.0589 | -0.106 |

Out of ground effect: CL(6°)=0.601, CDi=0.0343, lift slope ≈ 3.30/rad (Helmbold 3.44)
Takeoff attitude (α=9.0°, TE at 0.35 m, h/c=0.22): CL=1.177, CDi=0.0325

Cruise points (trimmed wing lift = weight):
| mass (kg) | V (m/s) | h (m) | α (deg) | CL | D_ind (N) | D_parasite (N) | L/D | P_shaft (kW) | P_elec (kW) | 30-min energy (kWh) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 130 | 22 | 0.6 | 2.4 | 0.54 | 28 | 264 | 4.4 | 11.5 | 13.1 | 6.55 |
| 130 | 25 | 0.6 | 0.9 | 0.42 | 23 | 341 | 3.5 | 15.8 | 17.9 | 8.96 |
| 130 | 28 | 0.6 | -0.1 | 0.33 | 18 | 428 | 2.9 | 21.6 | 24.5 | 12.26 |
| 158 | 22 | 0.6 | 3.9 | 0.65 | 41 | 264 | 5.1 | 12.1 | 13.7 | 6.87 |
| 158 | 25 | 0.6 | 2.0 | 0.51 | 32 | 341 | 4.1 | 16.2 | 18.4 | 9.22 |
| 158 | 28 | 0.6 | 0.8 | 0.40 | 27 | 428 | 3.4 | 22.1 | 25.1 | 12.54 |

## 4. Takeoff simulation and sizing

Baseline (158 kg, 15 kW shaft): lift-off at 16.4 m/s (59 km/h) after 7.9 s and 73 m; water hump 189 N at 4.0 m/s; min thrust margin 199 N; energy used 41 Wh

| case | P_shaft (kW) | static thrust (kgf) | lift-off (m/s) | time (s) | distance (m) | min margin (N) | energy (Wh) |
|---|---:|---:|---:|---:|---:|---:|---:|
| target 130 kg, 130 kg | 8 | 39 | 14.9 | 11.2 | 97 | 78 | 31 |
| target 130 kg, 130 kg | 12 | 51 | 14.9 | 6.7 | 55 | 179 | 27 |
| target 130 kg, 130 kg | 15 | 59 | 14.9 | 5.3 | 43 | 250 | 27 |
| target 130 kg, 130 kg | 20 | 72 | 14.9 | 4.0 | 32 | 362 | 27 |
| stretch build, 143 kg | 8 | 39 | 15.6 | 14.7 | 136 | 55 | 41 |
| stretch build, 143 kg | 12 | 51 | 15.6 | 8.3 | 73 | 155 | 34 |
| stretch build, 143 kg | 15 | 59 | 15.6 | 6.4 | 55 | 226 | 33 |
| stretch build, 143 kg | 20 | 72 | 15.6 | 4.8 | 41 | 337 | 32 |
| estimated build, 158 kg | 8 | 39 | 16.4 | 20.3 | 204 | 30 | 59 |
| estimated build, 158 kg | 12 | 51 | 16.4 | 10.5 | 98 | 129 | 43 |
| estimated build, 158 kg | 15 | 59 | 16.4 | 7.9 | 73 | 199 | 41 |
| estimated build, 158 kg | 20 | 72 | 16.4 | 5.8 | 52 | 308 | 39 |
| sensitivities at estimated mass, 15 kW: |
| no step | 15 | 59 | 16.4 | 8.1 | 74 | 199 | 41 |
| trim 3° | 15 | 59 | 16.4 | 7.9 | 72 | 199 | 40 |
| trim 6° | 15 | 59 | 16.4 | 8.4 | 77 | 194 | 43 |
| takeoff α 7° | 15 | 59 | 17.5 | 8.9 | 88 | 171 | 46 |
| takeoff α 11° | 15 | 59 | 15.5 | 7.3 | 62 | 219 | 37 |
| 5 m/s headwind | 15 | 59 | 11.4 | 6.0 | 38 | 208 | 30 |
| prop 1.15 m | 15 | 55 | 16.4 | 8.7 | 79 | 182 | 45 |
| prop 1.45 m | 15 | 64 | 16.4 | 7.3 | 67 | 213 | 37 |
| faired pilot (CdA 0.15) | 15 | 59 | 16.4 | 7.5 | 67 | 249 | 38 |
| PAR what-if (prop ahead of wing) | 15 | 59 | 13.6 | 5.6 | 41 | 280 | 28 |

Minimum shaft power for lift-off within 250 m / 300 m:
- target 130 kg: 6 kW (250 m), 6 kW (300 m)
- stretch build: 7 kW (250 m), 6 kW (300 m)
- estimated build: 8 kW (250 m), 8 kW (300 m)

### Propulsion + battery sizing (from the sim)

- Takeoff: 15 kW shaft for ~8 s -> 17.0 kW electrical, 338 A at 50 V (6.8 C), 41 Wh
- Static thrust at 15 kW with a 1.30 m prop: 59 kgf; motor must be rated ≥ 15 kW for 60 s, ~6-8 kW continuous
- ESC: ≥ 440 A continuous at 50 V (30 % margin) -> 300-400 A class; 14S (50 V) keeps currents high; 20S (72 V) is the better fit
- Cruise 25 m/s at 0.6 m, 158 kg: 16.2 kW shaft / 18.4 kW electrical, L/D 4.1, prop η 0.58; 30 min = 9.22 kWh vs 2.12 kWh usable -> endurance 7 min
- Cruise 22 m/s: 13.7 kW electrical -> 9 min
- With a faired pilot (CdA 0.15 instead of 0.40): cruise 25 m/s needs 12.8 kW electrical, L/D 5.8 -> 10 min
- Battery 2.5 kWh at 185.0 Wh/kg = 13.5 kg; takeoff C-rate 6.8 C is fine for 21700 power cells (e.g. 14S12P / 20S9P of P42A-class)

### Cruise power vs drag clean-up (158 kg, 0.6 m height)

| configuration | parasite CdA (m²) | P_elec @22 m/s (kW) | endurance @22 (min) | P_elec @25 (kW) | endurance @25 (min) | range @25 (km) |
|---|---:|---:|---:|---:|---:|---:|
| as drawn: exposed pilot, wheels, cage (CdA 0.75) | 0.75 | 13.7 | 9 | 18.4 | 7 | 10 |
| faired pilot (CdA 0.47) | 0.47 | 9.7 | 13 | 12.8 | 10 | 15 |
| faired pilot + enclosed wheels (CdA 0.33) | 0.35 | 8.0 | 15 | 10.4 | 12 | 18 |
| slick: everything faired (CdA 0.20) | 0.21 | 6.1 | 20 | 7.7 | 16 | 24 |
