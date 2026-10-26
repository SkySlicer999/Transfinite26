# Earth Migration 3D

Interactive 3D simulation of moving Earth to a wider orbit, with climate effects and a planetary-defense scene.
**Frontend:** static HTML/CSS/JS with three.js. **Backend:** a dependency-free Node.js API that exposes the same physics.

## Structure

```
public/                 frontend (served as-is)
  index.html
  css/styles.css
  js/app.js             simulation, 3D scenes, climate and defense pages
  js/api-badge.js       optional badge that calls the backend when present
server/                 backend (Node >= 18, no npm dependencies)
  index.js              HTTP server: static files + /api/*
  routes/api.js         endpoint handlers and input validation
  lib/physics.js        gravity, orbit energy, Gauss equation, flyby energy, migration, N-body
  lib/defense.js        headless planetary-defense simulation
tests/                  node:test suites for physics and API
Dockerfile, .github/    container image, CI and GitHub Pages workflows
```

## Run

```bash
npm start            # http://localhost:3000  (frontend + API)
npm test             # physics and API tests
```

Or just open `public/index.html` in a browser (needs internet once for three.js). Without the backend everything works; only the API badge is skipped.

## API

All endpoints are `GET` and return JSON. Invalid input returns `400`.

| Endpoint | Parameters (defaults) | Returns |
|---|---|---|
| `/api/health` | none | service status |
| `/api/flyby` | `m` (10, ×10¹⁸ kg), `vinf` (11 km/s), `q` (14800 km), `r` (1 AU) | energy per flyby, J |
| `/api/migration` | `m`, `rf` (2.7 AU), `rate` (35/yr), `vinf`, `q` | total energy, passes needed, years, asteroids needed |
| `/api/orbit` | `a` (1 AU), `push` (fraction of orbital speed) | orbit energy per kg and Gauss `da/dt` |
| `/api/nbody` | `ratio`, `b`, `vinf`, `days` | Earth–Moon–asteroid energy drift and barycentre kick |
| `/api/defense` | `seconds`, `rate`, `mirrors`, `mirrorsOn`, `nukesOn`, `seed` | counts of asteroids stopped by beams, warheads, or reaching Earth |

Example: `curl "http://localhost:3000/api/migration?rf=3&rate=50"`

## Physics

- N-body gravity: `a_i = Σ_{j≠i} G m_j (r_j − r_i) / |r_j − r_i|³`, integrated with velocity-Verlet.
- Orbit energy: `ε = v²/2 − μ/r = −μ/(2a)`.
- Gauss's equation: `da/dt = 2a² (v · a_push) / μ`. Energy per flyby is `v·Δv` at Earth's speed at its current radius, so more passes are needed as the orbit widens.

## Limits

The defense scene is illustrative and not to scale. Climate and mission figures are simplified models, not predictions.

## Deploy

- **Full stack:** `docker build -t earth-migration . && docker run -p 3000:3000 earth-migration`, or any Node host (`npm start`, honours `PORT`).
- **Frontend only:** the Pages workflow publishes `public/` to GitHub Pages (Settings → Pages → Source: GitHub Actions).

MIT licensed.
