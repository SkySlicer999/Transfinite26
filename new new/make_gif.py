# Make earth_migration.gif from replay.csv (no pygame needed):  python make_gif.py
import csv
import math
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter

HERE = os.path.dirname(os.path.abspath(__file__))
K = 10                                                    # exaggeration of Earth's outward drift
rows = [{k: float(v) for k, v in r.items()} for r in csv.DictReader(open(os.path.join(HERE, "replay.csv")))]
a0 = rows[0]["earth_a"]
frames = rows[::100]                                      # one frame per simulated year
ts = [r["t"] for r in frames]
as_ = [r["earth_a"] for r in frames]

fig, (ax, g) = plt.subplots(1, 2, figsize=(11, 5.2), gridspec_kw={"width_ratios": [1.3, 1]})
ax.set_facecolor("black"); ax.set_xlim(-6, 6); ax.set_ylim(-6, 6); ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
ang = [i / 200 * 2 * math.pi for i in range(201)]
ax.plot([math.cos(t) for t in ang], [math.sin(t) for t in ang], color="#555", lw=0.8)
ax.plot([2.7 * math.cos(t) for t in ang], [2.7 * math.sin(t) for t in ang], color="#a89a30", lw=0.8, ls="--")
ax.text(0, 2.78, "2.7 AU goal", color="#a89a30", ha="center", fontsize=8)
ring, = ax.plot([], [], color="#4a78c8", lw=1.2)
sun = ax.scatter([0], [0], s=160, color="#ffdc00")
earth = ax.scatter([], [], s=45, color="#6495ed")
jup = ax.scatter([], [], s=90, color="#e6aa6e")
ast = ax.scatter([], [], s=22, color="#c85050")
title = ax.text(-5.8, 5.5, "", color="white", fontsize=10)
ax.text(-5.8, -5.8, f"Earth's outward drift shown x{K} (exaggerated)", color="#ffc850", fontsize=8)

g.set_xlim(0, ts[-1]); g.set_ylim(min(as_) - 0.005, max(as_) + 0.005)
g.set_xlabel("Simulated year"); g.set_ylabel("Earth orbit size (AU)"); g.grid(alpha=0.3)
line, = g.plot([], [], color="#1f77b4")
label = g.text(0.03, 0.9, "", transform=g.transAxes)


def draw(i):
    r = frames[i]
    sx, sy = r["sun_x"], r["sun_y"]
    lift = (K - 1) * (r["earth_a"] - a0)
    dx, dy = r["earth_x"] - sx, r["earth_y"] - sy
    d = math.hypot(dx, dy)
    earth.set_offsets([[sx + dx * (d + lift) / d, sy + dy * (d + lift) / d]])
    jup.set_offsets([[r["jup_x"], r["jup_y"]]])
    ast.set_offsets([[r["ast_x"], r["ast_y"]]])
    R = r["earth_a"] + lift
    ring.set_data([sx + R * math.cos(t) for t in ang], [sy + R * math.sin(t) for t in ang])
    title.set_text(f"Year {r['t']:.0f}   impacts {int(r['impacts'])}")
    line.set_data(ts[: i + 1], as_[: i + 1])
    label.set_text(f"{r['earth_a']:.4f} AU  ({(r['earth_a'] - a0) * 1.496e8:+,.0f} km)")
    return ring, earth, jup, ast, line


fig.tight_layout()
anim = FuncAnimation(fig, draw, frames=len(frames), blit=False)
out = os.path.join(HERE, "earth_migration.gif")
anim.save(out, writer=PillowWriter(fps=12), dpi=70)
print("saved", out, len(frames), "frames")
