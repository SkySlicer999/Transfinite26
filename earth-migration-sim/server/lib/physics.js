// Physics shared by the API. Mirrors the formulas used by the browser simulation.
export const AU = 1.495978707e11;       // m
export const GMS = 1.3271244e20;        // Sun GM, m^3/s^2
export const G = 6.674e-11;
export const M_EARTH = 5.9722e24;       // kg
export const YEAR = 365.25 * 86400;     // s

/** Circular orbital speed (m/s) at r astronomical units. */
export const circularSpeed = (rAU) => Math.sqrt(GMS / (rAU * AU));

/** Specific orbital energy: eps = v^2/2 - mu/r = -mu/(2a). */
export const orbitEnergy = (aAU) => -GMS / (2 * aAU * AU);

/** Gauss's equation: da/dt = 2 a^2 (v . a_push) / mu  (m/s). */
export const gaussDaDt = (a, vDotPush, mu = GMS) => (2 * a * a * vDotPush) / mu;

/**
 * Energy (J) given to Earth by one hyperbolic flyby of an asteroid of mass m (kg).
 * Gauss: d(eps) = v . dv, so the gain scales with Earth's orbital speed vOrbit (m/s).
 */
export function flybyEnergy({ m, vInf, q, vOrbit = 29784.7 }) {
  const v = vInf * 1000, qm = q * 1000, mu = G * (M_EARTH + m);
  const b = qm * Math.sqrt(1 + (2 * mu) / (qm * v * v));
  const theta = 2 * Math.atan(mu / (b * v * v));
  const dv = (m / (M_EARTH + m)) * 2 * v * Math.sin(theta / 2);
  return M_EARTH * (vOrbit * dv + (dv * dv) / 2);
}

/** Gravity-assist migration from 1 AU to rf AU, integrated shell by shell. */
export function migration({ m, rf, rate, vInf, q, steps = 300 }) {
  let passes = 0, e0 = 0;
  for (let i = 0; i < steps; i++) {
    const x0 = 1 + ((rf - 1) * i) / steps, x1 = 1 + ((rf - 1) * (i + 1)) / steps;
    const dE = (GMS * M_EARTH / 2) * (1 / (x0 * AU) - 1 / (x1 * AU));
    const perPass = flybyEnergy({ m, vInf, q, vOrbit: circularSpeed((x0 + x1) / 2) });
    passes += dE / perPass;
    if (i === 0) e0 = perPass;
  }
  const totalEnergy = (GMS * M_EARTH / 2) * (1 / AU - 1 / (rf * AU));
  return {
    totalEnergyJ: totalEnergy,
    energyPerPassAt1AUJ: e0,
    energyPerPassAtTargetJ: flybyEnergy({ m, vInf, q, vOrbit: circularSpeed(rf) }),
    passes,
    years: rate > 0 ? passes / rate : null,
    asteroidsNeeded: rate * 5859,
  };
}

/** Velocity-Verlet N-body step (km, s). bodies: [{x,y,vx,vy,g}] with g = GM in km^3/s^2. */
function accel(bs) {
  return bs.map((p, i) => {
    let ax = 0, ay = 0;
    bs.forEach((q, j) => {
      if (i === j) return;
      const dx = q.x - p.x, dy = q.y - p.y, r2 = dx * dx + dy * dy + 1, k = q.g / (r2 * Math.sqrt(r2));
      ax += k * dx; ay += k * dy;
    });
    return [ax, ay];
  });
}
export function nbodyStep(bs, dt) {
  const a1 = accel(bs);
  bs.forEach((p, i) => { p.x += p.vx * dt + 0.5 * a1[i][0] * dt * dt; p.y += p.vy * dt + 0.5 * a1[i][1] * dt * dt; });
  const a2 = accel(bs);
  bs.forEach((p, i) => { p.vx += 0.5 * (a1[i][0] + a2[i][0]) * dt; p.vy += 0.5 * (a1[i][1] + a2[i][1]) * dt; });
}

export function totalEnergy(bs) {
  let K = 0, U = 0;
  bs.forEach((p, i) => {
    K += 0.5 * p.g * (p.vx ** 2 + p.vy ** 2);
    bs.forEach((q, j) => { if (j > i) U -= (p.g * q.g) / Math.hypot(p.x - q.x, p.y - q.y); });
  });
  return K + U;
}

/** Earth-Moon pair, optionally with one asteroid on a flyby; returns energy drift and Earth-Moon barycentre kick. */
export function flybySim({ massRatio = 1e-9, bKm = 30000, vInfKms = 11, days = 40 } = {}) {
  const GE = 398600, GM = 4902.8, mu = GE + GM, v = Math.sqrt(mu / 384400);
  const earth = { x: (-384400 * GM) / mu, y: 0, vx: 0, vy: (-v * GM) / mu, g: GE };
  const moon = { x: (384400 * GE) / mu, y: 0, vx: 0, vy: (v * GE) / mu, g: GM };
  const ast = { x: earth.x - 9e5, y: earth.y + bKm, vx: earth.vx + vInfKms, vy: earth.vy, g: GE * massRatio };
  const bs = [earth, moon, ast], e0 = totalEnergy(bs);
  for (let t = 0, h = 30; t < days * 86400; t += h) {
    h = Math.hypot(ast.x - earth.x, ast.y - earth.y) < 2e5 ? 5 : 30;
    nbodyStep(bs, h);
  }
  return {
    relEnergyDrift: (totalEnergy(bs) - e0) / Math.abs(e0),
    baryKickKms: (earth.vy * GE + moon.vy * GM) / mu,
  };
}
