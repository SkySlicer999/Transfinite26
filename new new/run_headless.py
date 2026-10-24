# Run the whole mission with no window:  python run_headless.py [years] [seed]
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import constants as C
from mission import Autopilot
from physics import build_solar_system, orbital_elements

years = float(sys.argv[1]) if len(sys.argv) > 1 else 100.0
w = build_solar_system()
seed = int(sys.argv[2]) if len(sys.argv) > 2 else 1
pilot = Autopilot(w, seed=seed)
sun, earth = w.get("Sun"), w.get("Earth")
history = []
next_report = 0.0
csv = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'orbit_history.csv'), 'w')
csv.write('year,earth_a_au,asteroid_mass_kg,impacts,projectile_kg,energy_err,asteroids_dropped\n')
next_csv = 0.0

while w.time < years:
    msg = pilot.update()
    if msg:
        print(f"[{w.time:8.2f}] {msg}")
    w.advance(0.05)
    if w.time >= next_csv:
        csv.write(f"{w.time:.3f},{orbital_elements(earth, sun)[0]:.7f},{w.get('Asteroid').mass * C.KG_PER_MSUN:.4e},{len(w.impacts)},{w.projectile_mass_used * C.KG_PER_MSUN:.4e},{w.energy_error():.3e},{pilot.spawns}\n")
        csv.flush()
        next_csv += 1.0
    if w.time >= next_report:
        a, _ = orbital_elements(earth, sun)
        history.append((w.time, a))
        next_report += years / 20

a0 = history[0][1]
a1, e1 = orbital_elements(earth, sun)
print("\n--- RESULT ---")
print(f"simulated years      : {w.time:.1f} of {C.TARGET_YEARS}")
print(f"Earth orbit          : {a0:.6f} AU -> {a1:.6f} AU (goal {C.TARGET_ORBIT_AU})")
print(f"change in Earth a    : {a1 - a0:+.3e} AU ({(a1 - a0) * C.AU_KM:+.1f} km)")
print(f"projectile mass used : {w.projectile_mass_used * C.KG_PER_MSUN:.2e} kg over {len(w.impacts)} impacts; asteroids dropped in: {pilot.spawns}")
print(f"impacts fired        : {len(w.impacts)}  (Earth flybys {pilot.flybys['Earth']}, Jupiter {pilot.flybys['Jupiter']})")
print(f"energy error         : {w.energy_error():.2e}")
print(f"momentum error       : {w.momentum_error():.2e}")
print("goal reached         :", "YES" if a1 >= C.TARGET_ORBIT_AU else "NO")
