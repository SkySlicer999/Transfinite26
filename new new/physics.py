# ------------------------------------------------------------
# Physics for the Earth Migration Simulator.
#
# What changed from the first version:
#   * World holds ALL bodies and applies gravity between every pair, so
#     every force has its equal and opposite reaction (the Sun moves too).
#   * Leapfrog integrator with an adaptive step for close flybys.
#   * impact(): a kinetic impactor hits an asteroid; momentum is booked.
#   * find_flyby(): tries impactor nudges and picks the one that gives the
#     wanted flyby of Earth (pass ahead) or Jupiter (pass behind).
#   * Energy and momentum are tracked so the physics can be validated.
# ------------------------------------------------------------

import copy
import math
import os
import sys
import time

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import constants as C
else:
    from . import constants as C

G = C.G


class Vector:
    # A Vector stores the horizontal and vertical parts of a force/velocity.
    def __init__(self, xi, yi, xf, yf):
        # A vector from point (xi, yi) to point (xf, yf)
        self.x = xf - xi
        self.y = yf - yi
        self.magnitude = math.hypot(self.x, self.y)
        self.magintude = self.magnitude  # old (misspelled) name kept

    def normalize(self):
        # Direction-only vector. A zero vector stays zero instead of crashing.
        if self.magnitude == 0:
            return Vector(0, 0, 0, 0)
        return Vector(0, 0, self.x / self.magnitude, self.y / self.magnitude)

    def multiply_scalar(self, k):
        # Scale the vector in place.
        self.x *= k
        self.y *= k
        self.magnitude *= abs(k)
        self.magintude = self.magnitude
        return self


class Body:
    # A Body is a moving object with a name, mass, position and velocity.
    def __init__(self, mass, x, y, vx, vy, name="body", color=(255, 255, 255), radius=4):
        self.mass = mass
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.name = name
        self.color = color
        self.radius = radius
        self.trail = []

    def kinetic_energy(self):
        return 0.5 * self.mass * (self.vx ** 2 + self.vy ** 2)

    def momentum(self):
        return self.mass * self.vx, self.mass * self.vy


class World:
    # Holds every body and moves them together.
    def __init__(self, bodies):
        self.bodies = list(bodies)
        self.time = 0.0                 # simulated years
        self.injected_energy = 0.0      # energy added by impactors (booked, not hidden)
        self.injected_px = 0.0          # momentum added by impactors
        self.injected_py = 0.0
        self.impacts = []               # log of impacts
        self.projectile_mass_used = 0.0 # total projectile mass supplied (solar masses)
        self.heat = 0.0                 # energy turned into heat by impacts
        self.e0 = self.total_energy()
        self.p_scale = sum(b.mass * math.hypot(b.vx, b.vy) for b in self.bodies) or 1.0

    # ---------- lookup / copy ----------
    def get(self, name):
        for b in self.bodies:
            if b.name == name:
                return b
        raise KeyError(name)

    def clone(self):
        # Copy used by the planner. Trails are dropped to keep it fast.
        saved = [b.trail for b in self.bodies]
        for b in self.bodies:
            b.trail = []
        w = copy.deepcopy(self)
        for b, t in zip(self.bodies, saved):
            b.trail = t
        return w

    # ---------- gravity ----------
    def accelerations(self):
        # Pairwise gravity. Body j pulls body i with G*mj/r^2, and body i
        # pulls body j with the opposite vector, so m_i*a_i = -m_j*a_j.
        n = len(self.bodies)
        ax = [0.0] * n
        ay = [0.0] * n
        eps2 = C.SOFTENING ** 2
        for i in range(n):
            bi = self.bodies[i]
            for j in range(i + 1, n):
                bj = self.bodies[j]
                dx = bj.x - bi.x
                dy = bj.y - bi.y
                r2 = dx * dx + dy * dy + eps2
                f = G / (r2 * math.sqrt(r2))
                ax[i] += f * bj.mass * dx
                ay[i] += f * bj.mass * dy
                ax[j] -= f * bi.mass * dx
                ay[j] -= f * bi.mass * dy
        return ax, ay

    def choose_dt(self):
        # Smaller steps when two bodies are close and moving fast.
        dt = C.DT
        n = len(self.bodies)
        for i in range(n):
            bi = self.bodies[i]
            for j in range(i + 1, n):
                bj = self.bodies[j]
                r = math.hypot(bj.x - bi.x, bj.y - bi.y)
                v = math.hypot(bj.vx - bi.vx, bj.vy - bi.vy)
                if v > 0:
                    dt = min(dt, C.DT_SAFETY * r / v)
        return max(dt, C.MIN_DT)

    def step(self, dt):
        # Leapfrog (kick-drift-kick): good energy behaviour for orbits.
        ax, ay = self.accelerations()
        for b, a, c in zip(self.bodies, ax, ay):
            b.vx += 0.5 * dt * a
            b.vy += 0.5 * dt * c
        for b in self.bodies:
            b.x += b.vx * dt
            b.y += b.vy * dt
        ax, ay = self.accelerations()
        for b, a, c in zip(self.bodies, ax, ay):
            b.vx += 0.5 * dt * a
            b.vy += 0.5 * dt * c
        self.time += dt

    def advance(self, duration, budget_s=None):
        # Advance by `duration` years (or until the wall-clock budget runs out).
        # Returns how many years were really simulated.
        start = self.time
        target = self.time + duration
        t0 = time.perf_counter()
        while self.time < target - 1e-12:
            self.step(min(self.choose_dt(), target - self.time))
            if budget_s is not None and time.perf_counter() - t0 > budget_s:
                break
        return self.time - start

    # ---------- diagnostics ----------
    def total_energy(self):
        e = sum(b.kinetic_energy() for b in self.bodies)
        eps2 = C.SOFTENING ** 2
        n = len(self.bodies)
        for i in range(n):
            for j in range(i + 1, n):
                bi, bj = self.bodies[i], self.bodies[j]
                r = math.sqrt((bi.x - bj.x) ** 2 + (bi.y - bj.y) ** 2 + eps2)
                e -= G * bi.mass * bj.mass / r
        return e

    def total_momentum(self):
        px = sum(b.mass * b.vx for b in self.bodies)
        py = sum(b.mass * b.vy for b in self.bodies)
        return px, py

    def energy_error(self):
        # Relative drift of (energy - energy injected by impactors).
        return abs(self.total_energy() - self.injected_energy - self.e0) / abs(self.e0)

    def momentum_error(self):
        px, py = self.total_momentum()
        return math.hypot(px - self.injected_px, py - self.injected_py) / self.p_scale

    # ---------- bookkeeping for things that enter or leave from outside ----------
    def _external(self, change):
        # Run `change()` and book the energy/momentum it added to the bodies, so
        # the conservation checks only judge the gravity integration.
        e_b = self.total_energy()
        px_b, py_b = self.total_momentum()
        change()
        px_a, py_a = self.total_momentum()
        self.injected_energy += self.total_energy() - e_b
        self.injected_px += px_a - px_b
        self.injected_py += py_a - py_b

    def replace_body(self, name, new_body):
        # Remove the body called `name` (if present) and add `new_body`.
        def change():
            self.bodies = [b for b in self.bodies if b.name != name]
            if new_body is not None:
                self.bodies.append(new_body)
        self._external(change)

    def potential_at(self, x, y, m):
        # Gravitational potential energy of a mass m at (x, y) due to all bodies.
        return -G * m * sum(b.mass / math.sqrt((b.x - x) ** 2 + (b.y - y) ** 2 + C.SOFTENING ** 2)
                            for b in self.bodies)

    # ---------- impact ----------
    def impact(self, target, m, pvx, pvy):
        # A projectile of mass m (velocity pvx, pvy) hits `target`.
        # It sticks, and crater ejecta of mass EJECTA_RATIO*m leaves backwards.
        #   1. merged body velocity   vc = (M v + m vp) / (M + m)
        #   2. ejecta leaves at       ve = vc - w d      (d = incoming direction)
        #   3. asteroid keeps         v' = vc + me w d / (M + m - me)
        # Mass and momentum are exactly conserved. Energy: whatever is not in
        # the asteroid or ejecta afterwards is heat (reported, must be >= 0).
        M = target.mass
        urx, ury = pvx - target.vx, pvy - target.vy
        u = math.hypot(urx, ury)
        dx, dy = urx / u, ury / u
        me = C.EJECTA_RATIO * m
        w = C.EJECTA_SPEED_FRACTION * u
        M_new = M + m - me
        if M_new <= 0:
            raise ValueError("impact would destroy the asteroid")

        e_proj = 0.5 * m * (pvx ** 2 + pvy ** 2) + self.potential_at(target.x, target.y, m)
        e_before = self.total_energy()
        vcx = (M * target.vx + m * pvx) / (M + m)
        vcy = (M * target.vy + m * pvy) / (M + m)
        old_vx, old_vy = target.vx, target.vy

        def change():
            target.vx = vcx + me * w * dx / M_new
            target.vy = vcy + me * w * dy / M_new
            target.mass = M_new

        self._external(change)
        e_ej = (0.5 * me * ((vcx - w * dx) ** 2 + (vcy - w * dy) ** 2)
                + self.potential_at(target.x, target.y, me))
        heat = e_before + e_proj - self.total_energy() - e_ej

        dvx, dvy = target.vx - old_vx, target.vy - old_vy
        self.projectile_mass_used += m
        self.heat += heat
        self.impacts.append((self.time, target.name, dvx, dvy, m))
        return dvx, dvy

    def _dv_for_projectile(self, M, m):
        u, rho, kap = C.IMPACT_SPEED, C.EJECTA_RATIO, C.EJECTA_SPEED_FRACTION
        return u * (m / (M + m) + rho * kap * m / (M + m - rho * m))

    def max_projectile(self, target):
        # Largest projectile allowed: the enabler cap, and never more than 30% of
        # the asteroid (a bigger hit would break it up instead of nudging it).
        return min(C.MAX_PROJECTILE, 0.3 * target.mass)

    def projectile_mass_for_dv(self, target, dv):
        # Projectile mass that gives the asteroid a speed change |dv| (AU/yr).
        M, dv = target.mass, abs(dv)
        m = dv * M / (C.IMPACT_SPEED * (1 + C.EJECTA_RATIO * C.EJECTA_SPEED_FRACTION))
        m = min(m, self.max_projectile(target))
        for _ in range(8):
            gain = self._dv_for_projectile(M, m)
            if gain <= 0:
                break
            m = min(m * dv / gain, self.max_projectile(target))
        return m

    def impact_max_dv(self, target):
        # Largest speed change one projectile (up to MAX_PROJECTILE) can give.
        return self._dv_for_projectile(target.mass, self.max_projectile(target))

    def impact_along_track(self, target, dv):
        # Fire a projectile so the asteroid's speed changes by dv (AU/yr) along
        # its direction of travel. dv > 0: hit from behind (speeds up).
        dv = max(-self.impact_max_dv(target), min(self.impact_max_dv(target), dv))
        if abs(dv) < 1e-15:
            return 0.0, 0.0                              # no nudge
        speed = math.hypot(target.vx, target.vy)
        ux, uy = target.vx / speed, target.vy / speed
        sign = 1.0 if dv >= 0 else -1.0
        m = self.projectile_mass_for_dv(target, dv)
        return self.impact(target, m, target.vx + sign * C.IMPACT_SPEED * ux,
                           target.vy + sign * C.IMPACT_SPEED * uy)

    # ---------- flyby search ----------
    def scan_closest(self, a_name, b_name, horizon):
        # Run forward and report the closest approach of a to b:
        # (distance, time, side) where side > 0 means a passes AHEAD of b.
        a, b, sun = self.get(a_name), self.get(b_name), self.get("Sun")
        t_end = self.time + horizon
        best_d, best_t, best_side = float("inf"), None, 0.0
        while self.time < t_end:
            self.step(min(self.choose_dt(), t_end - self.time))
            d = math.hypot(a.x - b.x, a.y - b.y)
            if d < best_d:
                best_d, best_t = d, self.time
                best_side = (a.x - b.x) * (b.vx - sun.vx) + (a.y - b.y) * (b.vy - sun.vy)
            elif best_d < 0.5 and d > 3 * best_d:
                break                               # already passed it
        return best_d, best_t, best_side


def find_flyby(world, asteroid="Asteroid", target="Earth", side="ahead",
               target_miss=0.02, horizon=6.0, n=21):
    # Try n impactor nudges (along the asteroid's track) and pick the one whose
    # closest approach to `target` is nearest target_miss AU on the wanted side.
    #   side="ahead"  -> passes in front of the planet (pulls it forward, Earth gains energy)
    #   side="behind" -> passes behind the planet (asteroid gains energy, e.g. at Jupiter)
    ast = world.get(asteroid)
    dv_max = world.impact_max_dv(ast)
    best = None
    for k in range(n):
        dv = -dv_max + 2 * dv_max * k / (n - 1)
        w = world.clone()
        w.impact_along_track(w.get(asteroid), dv)
        miss, t_hit, s = w.scan_closest(asteroid, target, horizon)
        wrong_side = (s < 0) if side == "ahead" else (s > 0)
        score = abs(miss - target_miss) / target_miss + (5.0 if wrong_side else 0.0)
        if best is None or score < best["score"]:
            best = dict(dv=dv, miss=miss, time=t_hit, correct_side=not wrong_side, score=score)
    return best


def orbital_elements(body, sun):
    # Semi-major axis (AU) and eccentricity of `body` around `sun` (osculating).
    rx, ry = body.x - sun.x, body.y - sun.y
    vx, vy = body.vx - sun.vx, body.vy - sun.vy
    mu = G * (sun.mass + body.mass)
    r = math.hypot(rx, ry)
    eps = 0.5 * (vx * vx + vy * vy) - mu / r
    h = rx * vy - ry * vx
    a = -mu / (2 * eps) if eps < 0 else float("inf")
    e = math.sqrt(max(0.0, 1 + 2 * eps * h * h / mu ** 2))
    return a, e


def make_asteroid(r0, theta, q, mass=None):
    # An asteroid at the far point of an orbit with perihelion q, prograde.
    mu = G * C.SUN_MASS
    a = (r0 + q) / 2
    v = math.sqrt(mu * (2 / r0 - 1 / a))
    return Body(C.ASTEROID_MASS if mass is None else mass,
                r0 * math.cos(theta), r0 * math.sin(theta),
                -v * math.sin(theta), v * math.cos(theta),
                "Asteroid", (200, 80, 80), 4)


def spawn_asteroid(world, rng, delays=40):
    # Drop a new asteroid in from a random place in space. Its position, angle
    # and perihelion are random; the only thing chosen is WHEN it is released
    # (Earth's phase), so the fall brings it close to Earth.
    r0 = rng.uniform(*C.SPAWN_R_RANGE)
    theta = rng.uniform(0, 2 * math.pi)
    q = rng.uniform(*C.SPAWN_PERI_RANGE)
    period = ((r0 + q) / 2) ** 1.5
    best = None
    for k in range(delays):
        tau = k / delays                                  # Earth's period is 1 year
        w = world.clone()
        w.replace_body("Asteroid", None)
        w.advance(tau)
        w.replace_body("Asteroid", make_asteroid(r0, theta, q))
        miss, t, side = w.scan_closest("Asteroid", "Earth", period + 0.5)
        score = abs(miss - 0.05) + (1.0 if side < 0 else 0.0)
        if best is None or score < best[0]:
            best = (score, tau, miss)
    world.replace_body("Asteroid", None)
    world.advance(best[1])
    world.replace_body("Asteroid", make_asteroid(r0, theta, q))
    return dict(r0=r0, theta_deg=math.degrees(theta), q=q, wait=best[1], miss=best[2])


def build_solar_system(asteroid_angle_deg=90.0, asteroid_a=1.7, asteroid_e=0.45):
    # Sun, Earth, Jupiter and one asteroid on an Earth-crossing orbit.
    # The Sun's velocity is set so total momentum starts at zero.
    mu = G * C.SUN_MASS

    def circular(r):
        return math.sqrt(mu / r)

    sun = Body(C.SUN_MASS, 0, 0, 0, 0, "Sun", (255, 220, 0), 12)
    earth = Body(C.EARTH_MASS, C.EARTH_START_AU, 0, 0, circular(C.EARTH_START_AU),
                 "Earth", (100, 149, 237), 6)
    jupiter = Body(C.JUPITER_MASS, C.JUPITER_AU, 0, 0, circular(C.JUPITER_AU),
                   "Jupiter", (230, 170, 110), 9)

    th = math.radians(asteroid_angle_deg)
    r = asteroid_a * (1 + asteroid_e)                       # start at aphelion
    v = math.sqrt(mu * (2 / r - 1 / asteroid_a))
    asteroid = Body(C.ASTEROID_MASS, r * math.cos(th), r * math.sin(th),
                    -v * math.sin(th), v * math.cos(th), "Asteroid", (200, 80, 80), 4)

    bodies = [sun, earth, jupiter, asteroid]
    px = sum(b.mass * b.vx for b in bodies[1:])
    py = sum(b.mass * b.vy for b in bodies[1:])
    sun.vx, sun.vy = -px / sun.mass, -py / sun.mass
    return World(bodies)
