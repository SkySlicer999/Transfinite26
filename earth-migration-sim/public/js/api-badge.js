// Optional: when served by the Node backend, show a small badge with live API results.
(async () => {
  try {
    const h = await (await fetch('/api/health')).json();
    if (!h.ok) return;
    const m = await (await fetch('/api/migration')).json();
    const b = document.createElement('div');
    b.style.cssText = 'position:fixed;left:8px;bottom:8px;z-index:50;font:11px system-ui;padding:4px 8px;border-radius:6px;background:rgba(10,20,34,.85);color:#9fe6c0;border:1px solid #2b4a69';
    b.textContent = `API online · default migration: ${m.passes.toExponential(2)} passes, ${m.years ? m.years.toFixed(0) : '∞'} yr`;
    document.body.appendChild(b);
  } catch { /* static hosting: no backend, nothing to show */ }
})();
