import pygame
import os

# Initialize Pygame
pygame.init()

# Set up the display
window_size = (800, 600)  # You can adjust the window size as needed
screen = pygame.display.set_mode(window_size)
pygame.display.set_caption("Display Images")

# Set up the background color
background_color = 0xaacbbc # Green Grass

# Image filenames
generators = [
    "CoalPlant.png",
    "GasPlant.png",
    "NuclearPlant.png",
    "SolarPanels.png",
    "WindTurbines.png",
    "HydroDamGrid.png"
]

facilities = [
    "DataCenter.png",
    "Factory.png",
    "House1.png",
    "House2.png",
    "Office1.png",
    "Office2.png"
]

# Load and scale images
def load_and_scale_images(filenames, scale_factors):
    images = []
    for filename, scale_factor in zip(filenames, scale_factors):
        image_path = os.path.join("assets2", "GridImages", filename)
        original_image = pygame.image.load(image_path)
        scaled_image = pygame.transform.scale(
            original_image,
            (int(original_image.get_width() * scale_factor), int(original_image.get_height() * scale_factor))
        )
        images.append(scaled_image)
    return images

generator_scaled_images = load_and_scale_images(generators, [0.05] * len(generators))
facility_scaled_images = load_and_scale_images(facilities, [0.03] + [0.02] * (len(facilities) - 1))

# Assign fixed positions for generators
generator_positions = [
    pygame.Rect(275, 400, generator_scaled_images[0].get_width(), generator_scaled_images[0].get_height()),  # CoalPlant
    pygame.Rect(420, 175, generator_scaled_images[1].get_width(), generator_scaled_images[1].get_height()),  # GasPlant
    pygame.Rect(350, 0, generator_scaled_images[2].get_width(), generator_scaled_images[2].get_height()),  # NuclearPlant
    pygame.Rect(550, 450, generator_scaled_images[3].get_width(), generator_scaled_images[3].get_height()),  # SolarPanels
    pygame.Rect(200, 250, generator_scaled_images[4].get_width(), generator_scaled_images[4].get_height()),  # WindTurbines
    pygame.Rect(0, 0, generator_scaled_images[5].get_width(), generator_scaled_images[5].get_height())  # HydroDamGrid
]

# Assign fixed positions for facilities
facility_positions = [
    pygame.Rect(50, 165, facility_scaled_images[0].get_width(), facility_scaled_images[0].get_height()),  # DataCenter
    pygame.Rect(200, 100, facility_scaled_images[1].get_width(), facility_scaled_images[1].get_height()),  # Factory
    pygame.Rect(450, 350, facility_scaled_images[2].get_width(), facility_scaled_images[2].get_height()),  # House1
    pygame.Rect(625, 80, facility_scaled_images[3].get_width(), facility_scaled_images[3].get_height()),  # House2
    pygame.Rect(650, 250, facility_scaled_images[4].get_width(), facility_scaled_images[4].get_height()),  # Office1
    pygame.Rect(100, 400, facility_scaled_images[5].get_width(), facility_scaled_images[5].get_height())  # Office2
]

# Main loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Fill the background
    screen.fill(background_color)

    # Draw lines between centers of objects
    hydrodam_rect = generator_positions[5]
    datacenter_rect = facility_positions[0]
    factory_rect = facility_positions[1]
    house1_rect = facility_positions[2]
    house2_rect = facility_positions[3]
    office1_rect = facility_positions[4]
    office2_rect = facility_positions[5]
    windturbines_rect = generator_positions[4]
    nuclearplant_rect = generator_positions[2]
    gasplant_rect = generator_positions[1]
    coalplant_rect = generator_positions[0]
    solarpanels_rect = generator_positions[3]

    # Draw lines
    pygame.draw.line(screen, (0, 0, 0), hydrodam_rect.center, datacenter_rect.center, 2)
    pygame.draw.line(screen, (0, 0, 0), hydrodam_rect.center, factory_rect.center, 2)
    pygame.draw.line(screen, (0, 0, 0), windturbines_rect.center, (300,250), 2)
    pygame.draw.line(screen, (0, 0, 0), datacenter_rect.center, (300,250), 2)
    pygame.draw.line(screen, (0, 0, 0), factory_rect.center, (300,250), 2)
    pygame.draw.line(screen, (0, 0, 0), windturbines_rect.center, house1_rect.center, 2)
    pygame.draw.line(screen, (0, 0, 0), nuclearplant_rect.center, factory_rect.center, 2)
    pygame.draw.line(screen, (0, 0, 0), nuclearplant_rect.center, house2_rect.center, 2)
    pygame.draw.line(screen, (0, 0, 0), gasplant_rect.center, house1_rect.center, 2)
    pygame.draw.line(screen, (0, 0, 0), gasplant_rect.center, (550,180), 2)
    pygame.draw.line(screen, (0, 0, 0), nuclearplant_rect.center, (550,180), 2)
    pygame.draw.line(screen, (0, 0, 0), office1_rect.center, (550,180), 2)
    pygame.draw.line(screen, (0, 0, 0), gasplant_rect.center, factory_rect.center, 2)
    pygame.draw.line(screen, (0, 0, 0), office2_rect.center, coalplant_rect.center, 2)
    pygame.draw.line(screen, (0, 0, 0), coalplant_rect.center, house1_rect.center, 2)
    pygame.draw.line(screen, (0, 0, 0), solarpanels_rect.center, house1_rect.center, 2)
    pygame.draw.line(screen, (0, 0, 0), solarpanels_rect.center, office1_rect.center, 2)

 # Blit the images onto the screen
    for image, rect in zip(generator_scaled_images, generator_positions):
        screen.blit(image, rect.topleft)

    for image, rect in zip(facility_scaled_images, facility_positions):
        screen.blit(image, rect.topleft)

    # Update the display
    pygame.display.flip()

# Quit Pygame
pygame.quit()