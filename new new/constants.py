# ------------------------------------------------------------
# Constants for the Earth Migration Simulator.
#
# UNITS (important): the simulation now uses astronomical units so that
# the numbers are real and the 1 AU -> 2.7 AU goal means something.
#   length = AU,   time = years,   mass = solar masses
# In these units G = 4*pi^2, and Earth's circular speed at 1 AU is 2*pi AU/yr.
# ------------------------------------------------------------

import math

# Gravity constant in AU^3 / (solar mass * year^2)
G = 4 * math.pi ** 2

# ---- Masses (solar masses) ----
SUN_MASS = 1.0
EARTH_MASS = 3.003e-6
JUPITER_MASS = 9.546e-4
MOON_MASS = 3.694e-8          # kept for later; the Moon is not simulated yet

# ---- Unit conversions (for display and for asteroid sizing) ----
KG_PER_MSUN = 1.989e30
AU = 1.496e11                 # metres in one AU
AU_KM = 1.496e8               # kilometres in one AU
AU_PER_YR_TO_KMS = 4.7405     # 1 AU/yr in km/s

# ---- Orbits ----
EARTH_START_AU = 1.0
JUPITER_AU = 5.2
TARGET_ORBIT_AU = 2.7         # goal from the challenge
TARGET_YEARS = 10000          # time limit from the challenge

# ------------------------------------------------------------
# HYPOTHETICAL ENABLERS (the challenge allows up to three).
#
# Enabler 1: a Moon-class asteroid (6e22 kg). A real 1 km rock (~1e15 kg) is
#            ~1e8 times too light to move Earth measurably.
# Enabler 2: projectiles are supplied from outside the system (they are NOT
#            launched from Earth, so Earth feels no recoil). Each one can
#            weigh up to MAX_PROJECTILE_KG and arrive at IMPACT_SPEED.
# (A third enabler is unused. Jupiter reuse needs no enabler: it is gravity.)
#
# Everything else is ordinary Newtonian physics: no momentum boost factor,
# no free mass. Projectile mass is consumed and counted; ejecta carries away
# real mass and momentum.
# ------------------------------------------------------------
ASTEROID_MASS_KG = 6e22
ASTEROID_MASS = ASTEROID_MASS_KG / KG_PER_MSUN
MAX_PROJECTILE_KG = 1e20
MAX_PROJECTILE = MAX_PROJECTILE_KG / KG_PER_MSUN
IMPACT_SPEED = 2.0            # projectile speed relative to asteroid, AU/yr (~9.5 km/s)

# Impact model: crater ejecta leaves back along the incoming direction.
EJECTA_RATIO = 2.0            # ejecta mass / projectile mass
EJECTA_SPEED_FRACTION = 0.5   # ejecta speed / impact speed (relative to the merged body)

# Where new asteroids start ("anywhere in space"): random distance, angle and
# perihelion, prograde, starting at the far point of the orbit.
SPAWN_R_RANGE = (3.0, 8.0)        # AU
SPAWN_PERI_RANGE = (0.4, 0.9)     # AU (crosses Earth's orbit)

# ---- Integrator settings ----
DT = 0.002                    # largest time step, years (~0.73 day)
MIN_DT = 1e-6                 # smallest step allowed during close flybys
DT_SAFETY = 0.01              # step <= this * (distance / relative speed)
SOFTENING = 1e-5              # AU; avoids division by zero in a collision

# ---- Safety placeholder (replace with the rulebook appendix values) ----
EARTH_SAFE_DISTANCE_AU = 0.0026   # roughly the Earth-Moon distance
CONSERVATION_TOLERANCE = 1e-6
