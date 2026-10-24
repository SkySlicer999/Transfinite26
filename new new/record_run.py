# Record a mission run to replay.csv so it can be played back fast:
#   python record_run.py [years] [seed]      then      python viewer.py
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import constants as C
from mission import Autopilot
from physics import build_solar_system, orbital_elements

years = float(sys.argv[1]) if len(sys.argv) > 1 else 150.0
seed = int(sys.argv[2]) if len(sys.argv) > 2 else 3
STEP = 0.01                                    # years between recorded rows

w = build_solar_system()
pilot = Autopilot(w, seed=seed)
sun, earth = w.get("Sun"), w.get("Earth")
path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "replay.csv")
out = open(path, "w")
out.write("t,sun_x,sun_y,earth_x,earth_y,jup_x,jup_y,ast_x,ast_y,earth_a,impacts,proj_kg,ast_kg\n")

n = 0
while w.time < years:
    if n % 5 == 0:
        pilot.update()
    w.advance(STEP)
    n += 1
    j, a = w.get("Jupiter"), w.get("Asteroid")
    out.write(f"{w.time:.3f},{sun.x:.6f},{sun.y:.6f},{earth.x:.6f},{earth.y:.6f},"
              f"{j.x:.5f},{j.y:.5f},{a.x:.5f},{a.y:.5f},{orbital_elements(earth, sun)[0]:.7f},"
              f"{len(w.impacts)},{w.projectile_mass_used * C.KG_PER_MSUN:.4e},{a.mass * C.KG_PER_MSUN:.4e}\n")
    if n % 500 == 0:
        out.flush()
out.close()
print(f"recorded {n} rows to {path}")
