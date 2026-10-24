# Plot Earth's orbit growth from orbit_history.csv:  python plot_orbit.py
import csv
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

here = os.path.dirname(os.path.abspath(__file__))
rows = list(csv.DictReader(open(os.path.join(here, "orbit_history.csv"))))
year = [float(r["year"]) for r in rows]
a = [float(r["earth_a_au"]) for r in rows]
proj = [float(r["projectile_kg"]) for r in rows]

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 7), sharex=True)
ax1.plot(year, a, color="#1f77b4")
ax1.axhline(1.0, color="grey", ls=":", lw=1)
ax1.set_ylabel("Earth orbit size (AU)")
ax1.set_title("Earth's orbit under asteroid flybys (goal: 2.7 AU)")
ax1.grid(alpha=0.3)
ax2.plot(year, proj, color="#d62728")
ax2.set_ylabel("Projectile mass used (kg)")
ax2.set_xlabel("Simulated year")
ax2.grid(alpha=0.3)
fig.tight_layout()
out = os.path.join(here, "earth_orbit.png")
fig.savefig(out, dpi=130)
print("saved", out, f"| {year[-1]:.0f} yr, a: {a[0]:.4f} -> {a[-1]:.4f}")
