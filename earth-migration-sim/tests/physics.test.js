import test from 'node:test';
import assert from 'node:assert/strict';
import { flybyEnergy, migration, flybySim, orbitEnergy, gaussDaDt, circularSpeed, AU } from '../server/lib/physics.js';
import { defenseSim } from '../server/lib/defense.js';

test('orbit energy is -mu/(2a)', () => assert.ok(orbitEnergy(1) < 0 && orbitEnergy(2) > orbitEnergy(1)));
test('Gauss da/dt matches energy change: d(eps)=v.dv and da/dt=2a^2 v.a/mu', () => {
  const a = AU, v = circularSpeed(1), acc = 1e-6, mu = 1.3271244e20;
  const dEps = v * acc, dA = (2 * a * a / mu) * dEps; // da = 2a^2 d(eps)/mu
  assert.ok(Math.abs(gaussDaDt(a, v * acc) - dA) / dA < 1e-12);
});
test('flyby energy per pass falls as Earth moves outwards', () => {
  const p = { m: 1e19, vInf: 11, q: 14800 };
  assert.ok(flybyEnergy({ ...p, vOrbit: circularSpeed(2.7) }) < flybyEnergy({ ...p, vOrbit: circularSpeed(1) }));
});
test('default migration needs about 1.74e6 passes (speed-dependent energy)', () => {
  const r = migration({ m: 1e19, rf: 2.7, rate: 35, vInf: 11, q: 14800 });
  assert.ok(r.passes > 1.7e6 && r.passes < 1.78e6, String(r.passes));
});
test('N-body flyby conserves energy', () => assert.ok(Math.abs(flybySim().relEnergyDrift) < 1e-8));
test('defense: both off lets asteroids through, each defence works alone', () => {
  assert.ok(defenseSim({ mirrorsOn: false, nukesOn: false }).hit > 0);
  const m = defenseSim({ nukesOn: false }), n = defenseSim({ mirrorsOn: false });
  assert.ok(m.mirror > 0 && n.nuclear > 0);
});
