// Headless version of the planetary-defense scene (same rules as the browser page).
function rng(seed) { let s = seed >>> 0; return () => ((s = (Math.imul(s, 1664525) + 1013904223) >>> 0) / 4294967296); }

export function defenseSim({ seconds = 100, ratePer10s = 2, mirrors = 14, mirrorsOn = true, nukesOn = true, seed = 7 } = {}) {
  const R = rng(seed), W = 960, earth = { x: 210, y: 300, r: 78 };
  const mir = Array.from({ length: mirrors }, (_, i) => {
    const a = (mirrors === 1 ? 0 : -1 + (2 * i) / (mirrors - 1)) * 1.15;
    return { x: earth.x + Math.cos(a) * 140, y: earth.y + Math.sin(a) * 140 };
  });
  const st = { mirror: 0, nuclear: 0, hit: 0, sent: 0 };
  let ast = [], mis = [], spawn = 1, cd = 0;
  const dt = 1 / 60;
  const kill = (a, who) => { if (!a.dead) { a.dead = true; st[who]++; } };
  const det = (x, y, rad) => ast.forEach((a) => { if (!a.dead && Math.hypot(a.x - x, a.y - y) < rad + a.r) kill(a, 'nuclear'); });
  for (let t = 0; t < seconds; t += dt) {
    spawn -= dt;
    if (spawn <= 0 && ratePer10s > 0) {
      const r = 5 + R() * 8, ty = earth.y + (R() - 0.5) * earth.r * 1.3, y = 30 + R() * 540, sp = 40 + R() * 30;
      const dx = earth.x - (W + 20), dy = ty - y, L = Math.hypot(dx, dy);
      ast.push({ x: W + 20 + R() * 60, y, vx: (dx / L) * sp, vy: (dy / L) * sp, r, hp: r * 6, dead: false, tracked: false });
      st.sent++; spawn = (-Math.log(1 - R() * 0.999) * 10) / ratePer10s;
    }
    ast.forEach((a) => {
      a.x += a.vx * dt; a.y += a.vy * dt;
      if (!a.dead && Math.hypot(a.x - earth.x, a.y - earth.y) < earth.r + a.r * 0.5) { a.dead = true; st.hit++; }
    });
    const live = ast.filter((a) => !a.dead);
    if (mirrorsOn) mir.forEach((m) => {
      let tg = null, bd = 1e9;
      live.forEach((a) => { if (a.dead || Math.hypot(a.x - m.x, a.y - m.y) > 520) return; const d = Math.hypot(a.x - earth.x, a.y - earth.y); if (d < bd) { bd = d; tg = a; } });
      if (tg) { tg.hp -= dt; if (tg.hp <= 0) kill(tg, 'mirror'); }
    });
    cd -= dt;
    if (nukesOn && cd <= 0) {
      const a = live.find((q) => !q.dead && !q.tracked && Math.hypot(q.x - earth.x, q.y - earth.y) < 420);
      if (a) { const L = Math.hypot(a.x - earth.x, a.y - earth.y); mis.push({ x: earth.x + ((a.x - earth.x) / L) * earth.r, y: earth.y + ((a.y - earth.y) / L) * earth.r, vx: ((a.x - earth.x) / L) * 60, vy: ((a.y - earth.y) / L) * 60, t: a, age: 0 }); a.tracked = true; cd = 0.45; }
    }
    mis.forEach((m) => {
      m.age += dt; const a = m.t;
      if (a.dead) { m.done = true; det(m.x, m.y, 26); return; }
      const sp = Math.min(380, 200 + m.age * 120), d = Math.hypot(a.x - m.x, a.y - m.y), tt = d / sp;
      const px = a.x + a.vx * tt, py = a.y + a.vy * tt, L = Math.hypot(px - m.x, py - m.y) || 1, k = Math.min(1, dt * 4);
      m.vx += ((px - m.x) / L * sp - m.vx) * k; m.vy += ((py - m.y) / L * sp - m.vy) * k; m.x += m.vx * dt; m.y += m.vy * dt;
      if (d < 16 || m.age > 8) { m.done = true; det(m.x, m.y, 64); }
    });
    mis = mis.filter((m) => !m.done); ast = ast.filter((a) => !a.dead && a.x > -60);
  }
  return st;
}
