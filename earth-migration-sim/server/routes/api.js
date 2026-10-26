import { flybyEnergy, migration, flybySim, gaussDaDt, orbitEnergy, circularSpeed, AU } from '../lib/physics.js';
import { defenseSim } from '../lib/defense.js';

const num = (q, k, d, lo = -Infinity, hi = Infinity) => {
  const raw = q.get(k); if (raw === null || raw === '') return d;
  const v = Number(raw); if (!Number.isFinite(v) || v < lo || v > hi) throw Object.assign(new Error(`invalid ${k}`), { status: 400 });
  return v;
};
const bool = (q, k, d) => (q.has(k) ? q.get(k) !== '0' && q.get(k) !== 'false' : d);

/** Each handler takes URLSearchParams and returns a JSON-serialisable object. */
export const routes = {
  '/api/health': () => ({ ok: true, service: 'earth-migration-sim', time: new Date().toISOString() }),
  '/api/flyby': (q) => {
    const m = num(q, 'm', 10, 1e-3, 1e6) * 1e18, vInf = num(q, 'vinf', 11, 0.1, 100), qkm = num(q, 'q', 14800, 6500, 1e6);
    const r = num(q, 'r', 1, 0.3, 10);
    return { energyPerPassJ: flybyEnergy({ m, vInf, q: qkm, vOrbit: circularSpeed(r) }), atRadiusAU: r };
  },
  '/api/migration': (q) => {
    const p = { m: num(q, 'm', 10, 1e-3, 1e6) * 1e18, rf: num(q, 'rf', 2.7, 1.01, 10), rate: num(q, 'rate', 35, 0, 1e6), vInf: num(q, 'vinf', 11, 0.1, 100), q: num(q, 'q', 14800, 6500, 1e6) };
    return migration(p);
  },
  '/api/orbit': (q) => {
    const a = num(q, 'a', 1, 0.3, 10), vPush = num(q, 'push', 1e-3, -1e3, 1e3);
    return { semiMajorAxisAU: a, energyPerKgJ: orbitEnergy(a), daDtMps: gaussDaDt(a * AU, circularSpeed(a) * vPush) };
  },
  '/api/nbody': (q) => flybySim({ massRatio: num(q, 'ratio', 1e-9, 0, 1), bKm: num(q, 'b', 30000, 1e3, 1e6), vInfKms: num(q, 'vinf', 11, 0.1, 100), days: num(q, 'days', 40, 1, 200) }),
  '/api/defense': (q) => defenseSim({ seconds: num(q, 'seconds', 100, 1, 600), ratePer10s: num(q, 'rate', 2, 0, 20), mirrors: Math.round(num(q, 'mirrors', 14, 1, 48)), mirrorsOn: bool(q, 'mirrorsOn', true), nukesOn: bool(q, 'nukesOn', true), seed: num(q, 'seed', 7, 0, 1e9) }),
};
