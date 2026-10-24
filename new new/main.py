import math
import os
import sys

import pygame

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import constants as C
    from physics import build_solar_system, find_flyby, orbital_elements
    from mission import Autopilot
else:
    from . import constants as C
    from .physics import build_solar_system, find_flyby, orbital_elements
    from .mission import Autopilot

pygame.init()

# =========================================================
# WINDOW AND LAYOUT
# =========================================================
# The simulation now runs in AU and years (see constants.py). The left 70%
# of the window shows the solar system; the right 30% is Mission Control.

WIDTH = 1200
HEIGHT = 700

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Earth Migration Simulator")

SIM_WIDTH = int(WIDTH * 0.7)
PANEL_WIDTH = WIDTH - SIM_WIDTH

VIEW_RADIUS_AU = 6.0                                   # Jupiter (5.2 AU) fits on screen
SCALE = (min(SIM_WIDTH, HEIGHT) / 2 - 20) / VIEW_RADIUS_AU   # pixels per AU

# =========================================================
# COLORS AND FONTS
# =========================================================
BLACK = (0, 0, 0)
PANEL_BG = (25, 25, 25)
WHITE = (255, 255, 255)
GREY = (70, 70, 70)
GREEN = (90, 220, 120)
RED = (255, 90, 90)
YELLOW = (255, 220, 0)

font = pygame.font.SysFont("consolas", 18)
small = pygame.font.SysFont("consolas", 15)
title_font = pygame.font.SysFont("consolas", 22)

# =========================================================
# SIMULATION STATE
# =========================================================
TIME_SCALES = [0.05, 0.25, 1, 5, 20, 50]               # simulated years per real second

world = None
speed_index = 2
paused = False
message = "Press P to plan an Earth flyby"
min_asteroid_earth = float("inf")                      # closest approach seen so far (AU)
frame_count = 0
pilot = None                                           # Autopilot when switched on (key A)


def reset():
    global world, min_asteroid_earth, message, pilot
    world = build_solar_system()
    pilot = None
    min_asteroid_earth = float("inf")
    message = "Reset. Press P to plan an Earth flyby"


def to_screen(x, y):
    # World (AU, y up) -> screen pixels (y down)
    return int(SIM_WIDTH // 2 + x * SCALE), int(HEIGHT // 2 - y * SCALE)


def show_message(text):
    # Draw a message immediately (used before slow planning calls).
    global message
    message = text
    draw_panel()
    pygame.display.flip()


# =========================================================
# ACTIONS
# =========================================================
def fire_impactor(direction):
    # Hit the asteroid with the largest nudge one projectile can give.
    global message
    ast = world.get("Asteroid")
    dv = direction * world.impact_max_dv(ast)
    world.impact_along_track(ast, dv)
    message = f"Impact! asteroid dv = {dv * C.AU_PER_YR_TO_KMS * 1000:+.1f} m/s"


def plan(target, side):
    # Search for the impactor nudge that gives a good flyby, then fire it.
    global message
    show_message(f"Planning {target} flyby... (please wait)")
    wanted = 0.02 if target == "Earth" else 0.3         # Jupiter is much bigger: pass farther out
    result = find_flyby(world, "Asteroid", target, side,
                        target_miss=wanted, horizon=8.0, n=15)
    if not result["correct_side"] or result["miss"] > 5 * wanted:
        message = f"No good {side} pass found (best miss {result['miss']:.3f} AU)"
        return
    world.impact_along_track(world.get("Asteroid"), result["dv"])
    message = (f"Fired: {target} pass {side} at {result['miss']:.3f} AU "
               f"in {result['time'] - world.time:.1f} yr")


# =========================================================
# DRAWING
# =========================================================
def draw_scene():
    # Reference circles: Earth's start orbit and the target orbit.
    sx, sy = to_screen(0, 0)
    pygame.draw.circle(screen, GREY, (sx, sy), int(C.EARTH_START_AU * SCALE), 1)
    pygame.draw.circle(screen, (90, 90, 40), (sx, sy), int(C.TARGET_ORBIT_AU * SCALE), 1)

    for b in world.bodies:
        if frame_count % 3 == 0:
            b.trail.append(to_screen(b.x, b.y))
            if len(b.trail) > 700:
                b.trail.pop(0)
        if len(b.trail) > 1 and b.name != "Sun":
            pygame.draw.lines(screen, tuple(c // 2 for c in b.color), False, b.trail, 1)

    for b in world.bodies:
        pygame.draw.circle(screen, b.color, to_screen(b.x, b.y), b.radius)


def draw_panel():
    pygame.draw.rect(screen, PANEL_BG, (SIM_WIDTH, 0, PANEL_WIDTH, HEIGHT))
    pygame.draw.line(screen, WHITE, (SIM_WIDTH, 0), (SIM_WIDTH, HEIGHT), 2)

    earth, ast, sun = world.get("Earth"), world.get("Asteroid"), world.get("Sun")
    a_e, e_e = orbital_elements(earth, sun)
    a_a, e_a = orbital_elements(ast, sun)
    d_now = math.hypot(ast.x - earth.x, ast.y - earth.y)

    x = SIM_WIDTH + 20
    y = 20
    screen.blit(title_font.render("MISSION CONTROL", True, WHITE), (x, y))
    y += 40

    def line(text, color=WHITE, f=font):
        nonlocal y
        screen.blit(f.render(text, True, color), (x, y))
        y += 24 if f is font else 20

    line(f"Year: {world.time:,.2f} / {C.TARGET_YEARS:,}")
    line(f"Orbit: {a_e:.4f} AU (goal {C.TARGET_ORBIT_AU})")
    line(f"Earth ecc: {e_e:.3f}")
    line(f"Asteroid a: {a_a:.2f} AU  e: {e_a:.2f}")
    line(f"Ast-Earth now: {d_now:.3f} AU")
    line(f"Closest ever:  {min_asteroid_earth:.4f} AU")
    line(f"Impacts: {len(world.impacts)}  Dropped in: {pilot.spawns if pilot else 0}")
    line(f"Projectile used: {world.projectile_mass_used * C.KG_PER_MSUN:.2e} kg", WHITE, small)
    line(f"Asteroid mass: {ast.mass * C.KG_PER_MSUN:.2e} kg", WHITE, small)
    line(f"Speed: {TIME_SCALES[speed_index]} yr/s" + ("  [PAUSED]" if paused else ""))
    y += 8

    ok_e = world.energy_error() < C.CONSERVATION_TOLERANCE
    ok_p = world.momentum_error() < C.CONSERVATION_TOLERANCE
    safe = min_asteroid_earth > C.EARTH_SAFE_DISTANCE_AU
    line("CHECKLIST", WHITE)
    line(f"Target orbit: {'YES' if a_e >= C.TARGET_ORBIT_AU else 'not yet'}",
         GREEN if a_e >= C.TARGET_ORBIT_AU else YELLOW, small)
    line(f"Energy err {world.energy_error():.1e}: {'ok' if ok_e else 'FAIL'}", GREEN if ok_e else RED, small)
    line(f"Momentum err {world.momentum_error():.1e}: {'ok' if ok_p else 'FAIL'}", GREEN if ok_p else RED, small)
    line(f"Earth safe (placeholder): {'ok' if safe else 'FAIL'}", GREEN if safe else RED, small)
    y += 8

    line(message, YELLOW, small)
    y += 8
    for text in ("SPACE pause   UP/DOWN speed", "P plan Earth flyby (ahead)",
                 "J plan Jupiter assist (behind)", "I / K projectile + / -",
                 "A autopilot on/off   R reset"):
        line(text, (160, 160, 160), small)


# =========================================================
# MAIN GAME LOOP
# =========================================================
def main():
    global speed_index, paused, frame_count, min_asteroid_earth, pilot, message

    clock = pygame.time.Clock()
    reset()
    running = True

    while running:
        # ----------------------
        # EVENT HANDLING
        # ----------------------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_UP:
                    speed_index = min(speed_index + 1, len(TIME_SCALES) - 1)
                elif event.key == pygame.K_DOWN:
                    speed_index = max(speed_index - 1, 0)
                elif event.key == pygame.K_i:
                    fire_impactor(+1)
                elif event.key == pygame.K_k:
                    fire_impactor(-1)
                elif event.key == pygame.K_p:
                    plan("Earth", "ahead")
                elif event.key == pygame.K_j:
                    plan("Jupiter", "behind")
                elif event.key == pygame.K_a:
                    if pilot:
                        pilot = None
                        message = "Autopilot OFF"
                    else:
                        show_message("Dropping in a new asteroid... (please wait)")
                        pilot = Autopilot(world)
                        message = "Autopilot ON"
                elif event.key == pygame.K_r:
                    reset()

        # ----------------------
        # PHYSICS
        # ----------------------
        if not paused:
            if pilot:
                msg = pilot.update()
                if msg:
                    message = msg
            world.advance(TIME_SCALES[speed_index] / 60.0, budget_s=0.012)
        earth, ast = world.get("Earth"), world.get("Asteroid")
        min_asteroid_earth = min(min_asteroid_earth, math.hypot(ast.x - earth.x, ast.y - earth.y))

        # ----------------------
        # DRAWING
        # ----------------------
        screen.fill(BLACK)
        draw_scene()
        draw_panel()
        pygame.display.flip()
        frame_count += 1
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
