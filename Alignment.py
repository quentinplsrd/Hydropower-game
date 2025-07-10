import pygame

# Initialize Pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 900

# Create the screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Image Alignment")

# Load images
original_image = pygame.image.load('assets2/PSHSequences/PSHStatics/UpperReservoirStatics.jpg')
cropped_image = pygame.image.load('assets2/PSHSequences/PSHUpperReservoirFramesCut/3.0 - Pumped Storage 02 - Upper Res (Generating Power)_000.jpg')

# Scale images to fit the screen
original_image = pygame.transform.scale(original_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
cropped_image = pygame.transform.scale(cropped_image, (cropped_image.get_width()*SCREEN_WIDTH/1920, cropped_image.get_height()*SCREEN_HEIGHT/1080))  # Example dimensions for cropped image

# Initial position of the cropped image
cropped_x = 100  # Starting x-coordinate
cropped_y = 100  # Starting y-coordinate

# Movement speed
MOVE_SPEED = 0.1

# Main loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Get pressed keys
    keys = pygame.key.get_pressed()

    # Move the cropped image using arrow keys
    if keys[pygame.K_UP]:
        cropped_y -= MOVE_SPEED
    if keys[pygame.K_DOWN]:
        cropped_y += MOVE_SPEED
    if keys[pygame.K_LEFT]:
        cropped_x -= MOVE_SPEED
    if keys[pygame.K_RIGHT]:
        cropped_x += MOVE_SPEED

    # Ensure the cropped image stays within the screen boundaries
    cropped_x = max(0, min(cropped_x, SCREEN_WIDTH - cropped_image.get_width()))
    cropped_y = max(0, min(cropped_y, SCREEN_HEIGHT - cropped_image.get_height()))

    # Display coordinates
    font = pygame.font.Font(None, 36)
    coordinates_text = f"X: {cropped_x}, Y: {cropped_y}"
    text_surface = font.render(coordinates_text, True, (255, 255, 255))
    screen.blit(text_surface, (10, 10))  # Display at the top-left corner

    # Save alignment coordinates
    if keys[pygame.K_s]:
        with open("alignment_coordinates.txt", "w") as file:
            file.write(f"cropped_x = {cropped_x}\n")
            file.write(f"cropped_y = {cropped_y}\n")
        print("Alignment coordinates saved!")

    # Clear the screen
    screen.fill((0, 0, 0))

    # Draw the original image
    screen.blit(original_image, (0, 0))

    # Draw the cropped image at its current position
    screen.blit(cropped_image, (cropped_x, cropped_y))

    # Update the display
    pygame.display.flip()

# Quit Pygame
pygame.quit()