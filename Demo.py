import pygame
import sys
import time
import json
import os

# Initialize Pygame
pygame.init()

# Constants
WINDOW_WIDTH, WINDOW_HEIGHT = 800, 600
TITLE = "The Hydropower Game"
FPS = 60
LEVELS = 10
FONT = pygame.font.Font(None, 36)
SAVE_FILE = 'game_save.json'

# Colors
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
BACKGROUND_COLOR = (135, 206, 235)

# Initialize screen
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption(TITLE)

# Determine if the application is running as a PyInstaller bundle
if getattr(sys, 'frozen', False):
    # If running as a bundle, set the base path to the temporary directory
    base_path = sys._MEIPASS
else:
    # If running in a normal Python environment, use the current directory
    base_path = os.path.abspath(".")

# Load the image
image_path = os.path.join(base_path, 'Dam.png')
# Load image
try:
    image = pygame.image.load(image_path)
except pygame.error as e:
    print(f"Unable to load image: {e}")
    pygame.quit()
    sys.exit()

scale_factor = 2  # Example scale factor to double the size
original_size = image.get_size()
new_size = (int(original_size[0] * scale_factor), int(original_size[1] * scale_factor))
scaled_image = pygame.transform.scale(image, new_size)

# Game state
accessible_levels = [True] + [False] * (LEVELS - 1)
level_best_times = [float('inf')] * LEVELS
current_screen = "main_menu"

# Level 1 objects
level1_initial_positions = [
    pygame.Rect(200, 200, 50, 50),  # Mouse draggable
    pygame.Rect(300, 300, 50, 50),  # Keyboard movable
]
level1_objects = level1_initial_positions.copy()
selected_object = None
object_movement = [0, 0]

# Timer variables
level1_start_time = None
level1_current_time = 0

def load_game_data():
    """Load game data from a JSON file."""
    global accessible_levels, level_best_times
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, 'r') as file:
            data = json.load(file)
            accessible_levels = data.get('accessible_levels', accessible_levels)
            level_best_times = data.get('level_best_times', level_best_times)

def save_game_data():
    """Save game data to a JSON file."""
    data = {
        'accessible_levels': accessible_levels,
        'level_best_times': level_best_times
    }
    with open(SAVE_FILE, 'w') as file:
        json.dump(data, file)

def reset_level1():
    """Reset the state of Level 1."""
    global level1_objects, selected_object, object_movement, level1_start_time
    level1_objects = [pygame.Rect(obj.x, obj.y, obj.width, obj.height) for obj in level1_initial_positions]
    selected_object = None
    object_movement = [0, 0]
    level1_start_time = time.time()  # Start the timer

def draw_text(text, x, y, color=BLACK):
    """Draw text on the screen at the specified position."""
    label = FONT.render(text, True, color)
    screen.blit(label, (x, y))

def main_menu():
    """Render the main menu screen."""
    screen.fill(BACKGROUND_COLOR)
    screen.blit(scaled_image, (40, -10))
    draw_text(TITLE, 270, 100, BLUE)
    draw_text("Click to select a level", 280, 200, BLACK)

    # Draw Level Select Button
    button_rect = pygame.Rect(325, 300, 150, 50)
    pygame.draw.rect(screen, GREEN, button_rect)
    draw_text("Level Select", 328, 310, WHITE)
    return button_rect

def level_select():
    """Render the level selection screen."""
    screen.fill(WHITE)
    draw_text("Select a Level", 325, 50, BLUE)

    buttons = []
    for i in range(LEVELS):
        color = GREEN if accessible_levels[i] else RED
        x, y = 80 + (i % 5) * 140, 150 + (i // 5) * 100
        button = pygame.Rect(x, y, 100, 50)
        pygame.draw.rect(screen, color, button)
        draw_text(f"Level {i + 1}", x + 2, y + 10, WHITE)
        buttons.append((button, accessible_levels[i]))

    return buttons

def level1():
    """Render and update logic for Level 1."""
    global selected_object, level_complete, level1_current_time
    screen.fill(WHITE)
    draw_text("Level 1: Complete this to unlock Level 2", 150, 50, BLACK)
    level_complete = False

    # Update and display the timer
    if level1_start_time is not None and not level_complete:
        level1_current_time = time.time() - level1_start_time
    draw_text(f"Current Time: {level1_current_time:.2f}s", 570, 10, BLACK)  
    if level_best_times[0] != float('inf'):
        draw_text(f"Best Time: {level_best_times[0]:.2f}s", 570, 40, BLACK)

    # Draw and update objects
    for obj in level1_objects:
        pygame.draw.rect(screen, BLUE, obj)

    # Move keyboard-controlled object
    level1_objects[1].x += object_movement[0]
    level1_objects[1].y += object_movement[1]

    # Check for collision
    if level1_objects[0].colliderect(level1_objects[1]):
        level_complete = True
    
    # Display completion button if level is complete
    if level_complete:
        draw_text("Level Complete!", 300, 150, GREEN)
        complete_button = pygame.Rect(325, 500, 175, 30)
        pygame.draw.rect(screen, GREEN, complete_button)
        draw_text("Back to Levels", 330, 500, WHITE)
        
        # Update best time if current time is better
        if level1_current_time < level_best_times[0]:
            level_best_times[0] = level1_current_time
            save_game_data()  # Save progress
        
        return complete_button
    else:
         # Add Exit Level button
        exit_button = pygame.Rect(15, 10, 120, 50)
        pygame.draw.rect(screen, RED, exit_button)
        draw_text("Exit Level", 15, 20, WHITE)
        return exit_button

def level2():
    """Render and update logic for Level 2."""
    screen.fill(WHITE)
    draw_text("Level 2: Click the button to complete", 150, 50, BLACK)

    # Draw the Level Complete button
    complete_button = pygame.Rect(325, 300, 150, 50)
    pygame.draw.rect(screen, GREEN, complete_button)
    draw_text("Level Complete", 330, 310, WHITE)

    return complete_button

def complete_level(level):
    """Unlock the next level."""
    if level < LEVELS:
        accessible_levels[level] = True
        save_game_data()  # Save progress

def handle_events():
    """Handle all game events."""
    global current_screen, selected_object, object_movement
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            save_game_data()  # Save progress on quit
            pygame.quit()
            sys.exit()

        if current_screen == "main_menu":
            if event.type == pygame.MOUSEBUTTONDOWN:
                button_rect = main_menu()
                if button_rect.collidepoint(event.pos):
                    current_screen = "level_select"

        elif current_screen == "level_select":
            if event.type == pygame.MOUSEBUTTONDOWN:
                buttons = level_select()
                for i, (button, accessible) in enumerate(buttons):
                    if button.collidepoint(event.pos) and accessible:
                        current_screen = f"level_{i + 1}"
                        reset_level1()  # Reset the level and start the timer

        elif current_screen.startswith("level_"):
            level_number = int(current_screen.split("_")[1])

            if level_number == 1:
                complete_button = level1()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if complete_button and complete_button.collidepoint(event.pos):
                        complete_level(1)
                        reset_level1()
                        current_screen = "level_select"
                    
                    exit_button = pygame.Rect(15, 10, 120, 50)
                    if exit_button.collidepoint(event.pos):
                        reset_level1()
                        current_screen = "level_select"

                    for obj in level1_objects:
                        if obj.collidepoint(event.pos):
                            selected_object = obj
                            break

                if event.type == pygame.MOUSEBUTTONUP:
                    selected_object = None

                if event.type == pygame.MOUSEMOTION and selected_object:
                    selected_object.x += event.rel[0]
                    selected_object.y += event.rel[1]

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        object_movement[1] = -5
                    elif event.key == pygame.K_DOWN:
                        object_movement[1] = 5
                    elif event.key == pygame.K_LEFT:
                        object_movement[0] = -5
                    elif event.key == pygame.K_RIGHT:
                        object_movement[0] = 5

                if event.type == pygame.KEYUP:
                    if event.key in (pygame.K_UP, pygame.K_DOWN):
                        object_movement[1] = 0
                    elif event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                        object_movement[0] = 0

            elif level_number == 2:
                complete_button = level2()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if complete_button and complete_button.collidepoint(event.pos):
                        complete_level(2)
                        current_screen = "level_select"

def main():
    """Main game loop."""
    load_game_data()  # Load progress at the start
    clock = pygame.time.Clock()
    while True:
        handle_events()

        if current_screen == "main_menu":
            main_menu()
        elif current_screen == "level_select":
            level_select()
        elif current_screen.startswith("level_"):
            level_number = int(current_screen.split("_")[1])

            if level_number == 1:
                level1()
            elif level_number == 2:
                level2()

        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()