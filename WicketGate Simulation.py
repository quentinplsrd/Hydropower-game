import pygame
import sys
import numpy as np  # Import numpy

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 800, 600
BACKGROUND_COLOR = (30, 30, 30)
OVAL_COLOR = (255, 0, 0)
OVAL_WIDTH, OVAL_HEIGHT = 100, 50
ROTATION_ANGLE = 10
NUM_OVALS = 8
CIRCLE_RADIUS = 125
movement = 0

# Set up the display
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Circular Oval Rotation')

# Create an oval surface
oval_surface = pygame.Surface((OVAL_WIDTH, OVAL_HEIGHT), pygame.SRCALPHA)
pygame.draw.ellipse(oval_surface, OVAL_COLOR, oval_surface.get_rect())

# Calculate positions for ovals in a circular pattern
center_x, center_y = WIDTH // 2, HEIGHT // 2
positions = [
    (center_x + CIRCLE_RADIUS * np.cos(2 * np.pi * i / NUM_OVALS),
     center_y + CIRCLE_RADIUS * np.sin(2 * np.pi * i / NUM_OVALS))
    for i in range(NUM_OVALS)
]

# Initial rotation angles for each oval
angles = []
for i in range(NUM_OVALS):
    angle = 2 * np.pi * i / NUM_OVALS
    if i == 0 or i == NUM_OVALS // 2:  # North and South
        angles.append(90)
    elif i == NUM_OVALS // 4 or i == 3 * NUM_OVALS // 4:  # East and West
        angles.append(0)
    else:
        angles.append(np.degrees(angle))

# Main loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP and movement < 90:
                angles = [angle - ROTATION_ANGLE for angle in angles]
                movement += 10
            elif event.key == pygame.K_DOWN and movement > 0:
                angles = [angle + ROTATION_ANGLE for angle in angles]
                movement -= 10

    # Clear the screen
    screen.fill(BACKGROUND_COLOR)

    # Draw and rotate each oval
    for i, (pos_x, pos_y) in enumerate(positions):
        rotated_oval = pygame.transform.rotate(oval_surface, angles[i])
        rect = rotated_oval.get_rect(center=(pos_x, pos_y))
        screen.blit(rotated_oval, rect.topleft)

    # Update the display
    pygame.display.flip()

# Quit Pygame
pygame.quit()
sys.exit()