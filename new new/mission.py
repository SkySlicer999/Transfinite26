# ------------------------------------------------------------
# Autopilot for the asteroid-reuse loop.
#
#   * A new asteroid is dropped in from a random place in space.
#   * A projectile nudges it so it passes AHEAD of Earth (Earth is pulled
#     forward and its orbit grows; the asteroid loses the same energy).
#   * A second projectile lines it up for a Jupiter pass BEHIND Jupiter,
#     which hands the asteroid its energy back so it can be used again.
#   * If the asteroid is lost (hits the Sun, is thrown out) or nothing
#     useful happens for `patience` years, a fresh one is dropped in.
# Every decision is logged.
# ------------------------------------------------------------

import math
import os
import random
import sys

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import constants as C
    from physics import find_flyby, orbital_elements, spawn_asteroid
else:
    from . import constants as C
    from .physics import find_flyby, orbital_elements, spawn_asteroid

WANTED_MISS = {"Earth": 0.02, "Jupiter": 0.3}      # AU
MAX_ACCEPT_MISS = {"Earth": 0.1, "Jupiter": 0.6}   # AU: worse than this is not a usable flyby
SIDE = {"Earth": "ahead", "Jupiter": "behind"}
HORIZON = {"Earth": 8.0, "Jupiter": 12.0}          # years to look ahead


class Autopilot:
    def __init__(self, world, seed=None, retry_after=0.5, patience=30.0):
        self.world = world
        self.rng = random.Random(seed)
        self.retry_after = retry_after
        self.patience = patience
        self.busy_until = 0.0
        self.last_success = world.time
        self.log = []                                  # (year, text)
        self.flybys = {"Earth": 0, "Jupiter": 0}
        self.spawns = 0
        self.spawn("start")

    def _note(self, text):
        self.log.append((self.world.time, text))
        return text

    def spawn(self, why):
        info = spawn_asteroid(self.world, self.rng)
        self.spawns += 1
        self.busy_until = self.world.time
        self.last_success = self.world.time
        return self._note(f"new asteroid ({why}): from {info['r0']:.1f} AU, angle "
                          f"{info['theta_deg']:.0f} deg, perihelion {info['q']:.2f} AU")

    def asteroid_lost(self):
        sun, ast = self.world.get("Sun"), self.world.get("Asteroid")
        r = math.hypot(ast.x - sun.x, ast.y - sun.y)
        a, _ = orbital_elements(ast, sun)
        return r > 20 or r < 0.05 or a < 0

    def update(self):
        # Call every frame. Returns a message when it acts, else None.
        w = self.world
        if self.asteroid_lost():
            return self.spawn("old one lost")
        if w.get("Asteroid").mass < 0.1 * C.ASTEROID_MASS:
            return self.spawn("old one used up")
        if w.time - self.last_success > self.patience:
            return self.spawn("nothing useful for a long time")
        if w.time < self.busy_until:
            return None

        for target in ("Earth", "Jupiter"):
            wanted = WANTED_MISS[target]
            res = find_flyby(w, "Asteroid", target, SIDE[target], target_miss=wanted,
                             horizon=HORIZON[target], n=15)
            if (res["correct_side"] and res["miss"] <= MAX_ACCEPT_MISS[target]
                    and res["time"] - w.time > 0.5):      # must still be in the future
                w.impact_along_track(w.get("Asteroid"), res["dv"])
                self.busy_until = res["time"] + 0.1
                self.last_success = w.time
                self.flybys[target] += 1
                return self._note(f"{target} flyby planned: miss {res['miss']:.3f} AU "
                                  f"at year {res['time']:.2f}")

        self.busy_until = w.time + self.retry_after
        return None
