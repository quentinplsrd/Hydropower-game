import pygame
import sys
import numpy as np  # Import numpy

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 800, 600
BACKGROUND_COLOR = (30, 30, 30)
ROTATION_ANGLE = 10
NUM_OVALS = 8
CIRCLE_RADIUS = 210
movement = 0

# Set up the display
screen = pygame.display.set_mode((WIDTH,HEIGHT))
pygame.display.set_caption('Circular Image Rotation')

# Load the image and set white background to transparent
image_surface = pygame.image.load('GatePiece.png').convert_alpha()
# Get image dimensions
IMAGE_WIDTH, IMAGE_HEIGHT = image_surface.get_size()
image_surface = pygame.transform.scale(image_surface,((IMAGE_WIDTH)*0.1,(IMAGE_HEIGHT)*0.1))
#image_surface.set_colorkey((255, 255, 255))  # Assuming white is the background color to be made transparent


# Calculate positions for images in a circular pattern
center_x, center_y = WIDTH // 2, HEIGHT // 2
positions = [
    (center_x + CIRCLE_RADIUS * np.cos(2 * np.pi * i / NUM_OVALS),
     center_y + CIRCLE_RADIUS * np.sin(2 * np.pi * i / NUM_OVALS))
    for i in range(NUM_OVALS)
]

# Initial rotation angles for each image
angles = [90,45,0,315,270,225,180,135]


# Main loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_DOWN and movement < 90:
                angles = [angle + ROTATION_ANGLE for angle in angles]
                movement += 10
            elif event.key == pygame.K_UP and movement > 0:
                angles = [angle - ROTATION_ANGLE for angle in angles]
                movement -= 10

    # Clear the screen
    screen.fill(BACKGROUND_COLOR)

    # Draw and rotate each image
    for i, (pos_x, pos_y) in enumerate(positions):
        rotated_image = pygame.transform.rotate(image_surface, angles[i])
        rect = rotated_image.get_rect(center=(pos_x, pos_y))
        screen.blit(rotated_image, rect.topleft)

    # Update the display
    pygame.display.flip()

# Quit Pygame
pygame.quit()
sys.exit()