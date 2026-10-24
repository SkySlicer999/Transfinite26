# Benchmarks for the physics. Run:  python validate.py
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import constants as C
from physics import Body, World, build_solar_system, find_flyby, orbital_elements

results = []


def check(name, ok, detail=""):
    results.append(ok)
    print(("PASS  " if ok else "FAIL  ") + name + ("  " + detail if detail else ""))


# 1. Circular orbit stays circular (Sun + Earth only).
sun = Body(1.0, 0, 0, 0, 0, "Sun")
earth = Body(C.EARTH_MASS, 1, 0, 0, 2 * math.pi, "Earth")
sun.vy = -earth.mass * earth.vy / sun.mass
w = World([sun, earth])
w.advance(10.0)
a, e = orbital_elements(earth, sun)
check("circular orbit keeps a = 1 AU", abs(a - 1) < 1e-4, f"a={a:.6f}")
check("two-body energy conserved", w.energy_error() < 1e-8, f"err={w.energy_error():.2e}")
check("two-body momentum conserved", w.momentum_error() < 1e-12, f"err={w.momentum_error():.2e}")

# 2. Full system (Sun, Earth, Jupiter, asteroid) over 50 years.
w = build_solar_system()
w.advance(50.0)
check("4-body energy conserved (50 yr)", w.energy_error() < C.CONSERVATION_TOLERANCE,
      f"err={w.energy_error():.2e}")
check("4-body momentum conserved (50 yr)", w.momentum_error() < C.CONSERVATION_TOLERANCE,
      f"err={w.momentum_error():.2e}")

# 3. Impact physics: mass and momentum conserved, dv as requested, heat >= 0.
w = build_solar_system()
ast = w.get("Asteroid")
M0 = ast.mass
px0, py0 = w.total_momentum()
dvx, dvy = w.impact_along_track(ast, 1e-3)
m_p = w.projectile_mass_used
m_ej = C.EJECTA_RATIO * m_p
check("impact gives requested dv", abs(math.hypot(dvx, dvy) - 1e-3) < 1e-9, f"dv={math.hypot(dvx, dvy):.6f}")
check("mass conserved (asteroid + ejecta = before + projectile)",
      abs((ast.mass + m_ej) - (M0 + m_p)) < 1e-18, f"projectile={m_p * C.KG_PER_MSUN:.2e} kg")
check("impact heat is not negative", w.heat >= 0, f"heat={w.heat:.2e}")
w.advance(5.0)
check("conservation holds after an impact", w.momentum_error() < 1e-6 and w.energy_error() < 1e-6,
      f"E={w.energy_error():.2e} p={w.momentum_error():.2e}")

# 4. Planner runs and reports a flyby.
w = build_solar_system()
w.advance(1.0)
res = find_flyby(w, side="ahead", n=9, horizon=4.0)
print("      planner result:", {k: (round(v, 5) if isinstance(v, float) else v) for k, v in res.items()})
check("planner returns a result", res is not None)

print(f"\n{sum(results)}/{len(results)} checks passed")
sys.exit(0 if all(results) else 1)
