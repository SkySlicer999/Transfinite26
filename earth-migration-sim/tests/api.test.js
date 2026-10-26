import test from 'node:test';
import assert from 'node:assert/strict';
import { createServer } from '../server/index.js';

test('API and static files', async () => {
  const s = createServer(); await new Promise((r) => s.listen(0, r));
  const base = `http://localhost:${s.address().port}`, j = async (p) => (await fetch(base + p)).json();
  assert.equal((await j('/api/health')).ok, true);
  assert.ok((await j('/api/migration')).passes > 1e6);
  assert.ok((await j('/api/flyby?r=2')).energyPerPassJ > 0);
  assert.equal((await fetch(base + '/api/flyby?m=abc')).status, 400);
  assert.equal((await fetch(base + '/api/nope')).status, 404);
  const page = await fetch(base + '/'); assert.equal(page.status, 200); assert.match(await page.text(), /Earth Migration 3D/);
  assert.equal((await fetch(base + '/js/app.js')).status, 200);
  assert.equal((await fetch(base + '/..%2fpackage.json')).status === 200, false);
  s.close();
});
