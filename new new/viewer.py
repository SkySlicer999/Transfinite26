# ------------------------------------------------------------
# Fast playback of a recorded run (replay.csv from record_run.py).
# The real orbit change is small, so the viewer can EXAGGERATE Earth's outward
# drift (key E). The panel always shows the true numbers; when exaggeration
# is on, the scene says so on screen.
#   SPACE pause   UP/DOWN speed   E exaggeration   R restart
# ------------------------------------------------------------
import csv
import math
import os
import sys

import pygame

HERE = os.path.dirname(os.path.abspath(__file__))
AU_KM = 1.496e8
TARGET_AU = 2.7

WIDTH, HEIGHT = 1200, 700
SIM_WIDTH = int(WIDTH * 0.7)
SCALE = (min(SIM_WIDTH, HEIGHT) / 2 - 20) / 6.0          # pixels per AU (6 AU fits)

SPEEDS = [1, 5, 20, 50, 100, 200]                         # simulated years per real second
EXAGGERATIONS = [1, 5, 10, 20]


def load(path):
    with open(path) as f:
        rows = [{k: float(v) for k, v in r.items()} for r in csv.DictReader(f)]
    if not rows:
        raise SystemExit("replay.csv is empty - run record_run.py first")
    return rows


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "replay.csv")
    if not os.path.exists(path):
        raise SystemExit("No replay.csv found. Run:  python record_run.py 150 3")
    rows = load(path)
    a0 = rows[0]["earth_a"]
    a_lo = min(r["earth_a"] for r in rows)
    a_hi = max(r["earth_a"] for r in rows)
    graph = rows[::100]                                    # about one point per year

    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Earth Migration - replay")
    font = pygame.font.SysFont("consolas", 18)
    small = pygame.font.SysFont("consolas", 15)
    clock = pygame.time.Clock()

    t_end = rows[-1]["t"]
    t = 0.0
    speed_i, exag_i, paused = 2, 2, False
    trail = []

    def to_px(x, y):
        return int(SIM_WIDTH // 2 + x * SCALE), int(HEIGHT // 2 - y * SCALE)

    running = True
    while running:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_SPACE:
                    paused = not paused
                elif e.key == pygame.K_UP:
                    speed_i = min(speed_i + 1, len(SPEEDS) - 1)
                elif e.key == pygame.K_DOWN:
                    speed_i = max(speed_i - 1, 0)
                elif e.key == pygame.K_e:
                    exag_i = (exag_i + 1) % len(EXAGGERATIONS)
                elif e.key == pygame.K_r:
                    t, trail = 0.0, []

        if not paused:
            t += SPEEDS[speed_i] / 60.0
            if t > t_end:
                t, trail = 0.0, []
        idx = min(int(t / 0.01), len(rows) - 1)
        r = rows[idx]
        K = EXAGGERATIONS[exag_i]

        sx, sy = r["sun_x"], r["sun_y"]
        a_now = r["earth_a"]
        lift = (K - 1) * (a_now - a0)                      # extra outward shift (AU)

        # Earth, pushed outward by `lift` along the Sun-Earth line
        dx, dy = r["earth_x"] - sx, r["earth_y"] - sy
        dist = math.hypot(dx, dy)
        ex, ey = sx + dx * (dist + lift) / dist, sy + dy * (dist + lift) / dist
        if not paused:
            trail.append(to_px(ex, ey))
            trail = trail[-400:]

        screen.fill((0, 0, 0))
        c = to_px(sx, sy)
        pygame.draw.circle(screen, (70, 70, 70), c, int(1.0 * SCALE), 1)             # 1 AU
        pygame.draw.circle(screen, (110, 110, 40), c, int(TARGET_AU * SCALE), 1)      # goal
        pygame.draw.circle(screen, (60, 90, 160), c, max(2, int((a_now + lift) * SCALE)), 1)  # Earth's orbit now
        if len(trail) > 1:
            pygame.draw.lines(screen, (50, 75, 120), False, trail, 1)
        pygame.draw.circle(screen, (255, 220, 0), c, 12)
        pygame.draw.circle(screen, (100, 149, 237), to_px(ex, ey), 6)
        pygame.draw.circle(screen, (230, 170, 110), to_px(r["jup_x"], r["jup_y"]), 9)
        pygame.draw.circle(screen, (200, 80, 80), to_px(r["ast_x"], r["ast_y"]), 4)
        if K > 1:
            screen.blit(small.render(f"Earth's outward drift shown x{K} (exaggerated)", True, (255, 200, 80)), (12, 10))
        screen.blit(small.render("yellow ring: 2.7 AU goal   grey ring: 1 AU   blue ring: Earth's orbit now", True, (150, 150, 150)), (12, HEIGHT - 24))

        # ---- panel ----
        pygame.draw.rect(screen, (25, 25, 25), (SIM_WIDTH, 0, WIDTH - SIM_WIDTH, HEIGHT))
        pygame.draw.line(screen, (255, 255, 255), (SIM_WIDTH, 0), (SIM_WIDTH, HEIGHT), 2)
        x, y = SIM_WIDTH + 20, 20
        for text, f in ((f"Year: {r['t']:.1f}", font),
                        (f"Earth orbit: {a_now:.4f} AU", font),
                        (f"Moved: {(a_now - a0) * AU_KM:+,.0f} km", font),
                        (f"Goal: {TARGET_AU} AU", font),
                        (f"Impacts: {int(r['impacts'])}", small),
                        (f"Projectile used: {r['proj_kg']:.2e} kg", small),
                        (f"Asteroid mass: {r['ast_kg']:.2e} kg", small),
                        (f"Speed: {SPEEDS[speed_i]} yr/s" + ("  [PAUSED]" if paused else ""), small)):
            screen.blit(f.render(text, True, (255, 255, 255)), (x, y))
            y += 26 if f is font else 21

        # graph of Earth's orbit size over time, zoomed to the data range
        gx, gy, gw, gh = x, y + 20, WIDTH - SIM_WIDTH - 40, 220
        pygame.draw.rect(screen, (45, 45, 45), (gx, gy, gw, gh), 1)
        span = max(a_hi - a_lo, 1e-9)
        pts = []
        for g in graph:
            if g["t"] > r["t"]:
                break
            pts.append((gx + int(g["t"] / t_end * gw), gy + gh - int((g["earth_a"] - a_lo) / span * (gh - 8)) - 4))
        if len(pts) > 1:
            pygame.draw.lines(screen, (100, 180, 255), False, pts, 2)
        screen.blit(small.render(f"{a_hi:.3f}", True, (150, 150, 150)), (gx + 4, gy + 2))
        screen.blit(small.render(f"{a_lo:.3f}", True, (150, 150, 150)), (gx + 4, gy + gh - 18))
        screen.blit(small.render("Earth orbit size (AU) vs year", True, (150, 150, 150)), (gx, gy + gh + 4))
        y = gy + gh + 40
        for text in ("SPACE pause  UP/DOWN speed", "E exaggeration  R restart"):
            screen.blit(small.render(text, True, (160, 160, 160)), (x, y))
            y += 20

        pygame.display.flip()
        clock.tick(60)
    pygame.quit()


if __name__ == "__main__":
    main()
