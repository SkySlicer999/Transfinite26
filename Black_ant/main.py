import pygame
import sys
import time
from physics import Vector,Body
from constants import G,EARTH_MASS,MOON_MASS,SUN_MASS # Has G,Earth_mass,Sun_mass

pygame.init()

# ==========================
# WINDOW SETTINGS
# ==========================

WIDTH = 1200
HEIGHT = 700
FRAME_COUNT = 0


screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Earth Migration Simulator")

# Layout
SIM_WIDTH = int(WIDTH * 0.7)      # 70% so 840pixels wide
PANEL_WIDTH = WIDTH - SIM_WIDTH   # 30%
Earth = Body(EARTH_MASS,250,HEIGHT//2,0,10)
Sun = Body(SUN_MASS,SIM_WIDTH//2,HEIGHT//2,0,0)
Other = Body(200,SIM_WIDTH//2,(HEIGHT//2)-300,10,0)
# ==========================
# COLORS
# ==========================

BLACK = (0, 0, 0)
PANEL_BG = (25, 25, 25)
WHITE = (255, 255, 255)
RED = (255,0,0)
YELLOW = (255, 220, 0)
BLUE = (100, 149, 237)

# ==========================
# FONT
# ==========================

font = pygame.font.SysFont("consolas", 22)

# ==========================
# OBJECT POSITIONS
# ==========================

sun_x = SIM_WIDTH // 2
sun_y = HEIGHT // 2

earth_x = sun_x + 180
earth_y = sun_y

# ==========================
# CLOCK
# ==========================

def interactions():
    pass

def update():
    Earth.update(Sun)
    #Other.update(Sun)
    #Other.update(Earth)
    #Earth.update(Other)




def draw():
    update()
    pygame.draw.circle(#sun
        screen,
        YELLOW,
        (Sun.x,Sun.y),
        30
    )
    pygame.draw.circle(#Earth
        screen,
        BLUE,
        (Earth.x,Earth.y),
        8
        )
    #pygame.draw.circle(#Earth
    #        screen,
     #       RED ,
      #      (Other.x,Other.y),
       #     8
        #    )


def main():
    

    clock = pygame.time.Clock()
    #Setup bodies
    
    # ==========================
    # MAIN LOOP
    # ==========================

    running = True

    while running:

        # ----------------------
        # EVENTS
        # ----------------------

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # ----------------------
        # DRAW BACKGROUNDS
        # ----------------------

        screen.fill(BLACK)

        # Metrics panel
        pygame.draw.rect(
            screen,
            PANEL_BG,
            (SIM_WIDTH, 0, PANEL_WIDTH, HEIGHT)
        )

        # Divider line
        pygame.draw.line(
            screen,
            WHITE,
            (SIM_WIDTH, 0),
            (SIM_WIDTH, HEIGHT),
            2
        )
        draw()
        #time.sleep(0.5)

        

        # ----------------------
        # METRICS PANEL
        # ----------------------

        title = font.render("MISSION CONTROL", True, WHITE)

        year_text = font.render("Year: 0", True, WHITE)
        orbit_text = font.render("Orbit: 1.00 AU", True, WHITE)
        moon_text = font.render("Moon Stability: 100%", True, WHITE)
        asteroid_text = font.render("Asteroids: 0", True, WHITE)
        score_text = font.render("Mission Score: --", True, WHITE)

        screen.blit(title, (SIM_WIDTH + 20, 20))

        screen.blit(year_text, (SIM_WIDTH + 20, 100))
        screen.blit(orbit_text, (SIM_WIDTH + 20, 140))
        screen.blit(moon_text, (SIM_WIDTH + 20, 180))
        screen.blit(asteroid_text, (SIM_WIDTH + 20, 220))
        screen.blit(score_text, (SIM_WIDTH + 20, 260))

        # ----------------------
        # UPDATE SCREEN
        # ----------------------

        pygame.display.flip()
        #FRAME_COUNT +=1

        clock.tick(60)

    pygame.quit()
    sys.exit()



main()