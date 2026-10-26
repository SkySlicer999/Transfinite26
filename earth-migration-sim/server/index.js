import http from 'node:http';
import { readFile, stat } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { routes } from './routes/api.js';

const PUBLIC = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', 'public');
const TYPES = { '.html': 'text/html; charset=utf-8', '.css': 'text/css; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.json': 'application/json', '.png': 'image/png', '.svg': 'image/svg+xml', '.ico': 'image/x-icon' };

export function createServer() {
  return http.createServer(async (req, res) => {
    const url = new URL(req.url, 'http://localhost');
    const send = (code, body, type = 'application/json') => { res.writeHead(code, { 'Content-Type': type, 'X-Content-Type-Options': 'nosniff', 'Access-Control-Allow-Origin': '*' }); res.end(body); };
    if (req.method !== 'GET' && req.method !== 'HEAD') return send(405, JSON.stringify({ error: 'method not allowed' }));
    if (url.pathname.startsWith('/api/')) {
      const h = routes[url.pathname];
      if (!h) return send(404, JSON.stringify({ error: 'unknown endpoint', endpoints: Object.keys(routes) }));
      try { return send(200, JSON.stringify(h(url.searchParams))); }
      catch (e) { return send(e.status || 500, JSON.stringify({ error: e.message })); }
    }
    let rel = decodeURIComponent(url.pathname); if (rel.endsWith('/')) rel += 'index.html';
    const file = path.normalize(path.join(PUBLIC, rel));
    if (!file.startsWith(PUBLIC)) return send(403, 'forbidden', 'text/plain');
    try { if (!(await stat(file)).isFile()) throw 0; send(200, await readFile(file), TYPES[path.extname(file)] || 'application/octet-stream'); }
    catch { send(404, 'not found', 'text/plain'); }
  });
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const port = Number(process.env.PORT) || 3000;
  createServer().listen(port, () => console.log(`Earth Migration 3D on http://localhost:${port}`));
}
