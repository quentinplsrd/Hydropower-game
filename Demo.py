import cv2
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
    base_path = sys._MEIPASS
else:
    base_path = os.path.abspath(".")

# Load the image
intro_image_path = os.path.join(base_path, 'Dam.png')
try:
    intro_image = pygame.image.load(intro_image_path)
except pygame.error as e:
    print(f"Unable to load image: {e}")
    pygame.quit()
    sys.exit()
scale_factor = 2
original_size = intro_image.get_size()
new_size = (int(original_size[0] * scale_factor), int(original_size[1] * scale_factor))
scaled_intro_image = pygame.transform.scale(intro_image, new_size)

levelx_image_path = os.path.join(base_path, 'LevelDiagram.png')
try:
    levelx_image = pygame.image.load(levelx_image_path)
except pygame.error as e:
    print(f"Unable to load image: {e}")
    pygame.quit()
    sys.exit()
levelx_image = pygame.transform.scale(levelx_image, (800, 600))

# Game state
accessible_levels = [True] + [False] * (LEVELS - 1)
level_best_times = [float('inf')] * LEVELS
current_screen = "main_menu"

# Level 1 objects
level1_initial_positions = [
    pygame.Rect(200, 200, 50, 50),
    pygame.Rect(300, 300, 50, 50),
]
level1_objects = level1_initial_positions.copy()
selected_object = None
object_movement = [0, 0]

# Level 3 globals
current_text_box = None
clicked_objects = set()

# Level 4 globals
has_played = False

# Timer variables
level1_start_time = None
level1_current_time = 0

def load_game_data():
    global accessible_levels, level_best_times
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, 'r') as file:
            data = json.load(file)
            accessible_levels = data.get('accessible_levels', accessible_levels)
            level_best_times = data.get('level_best_times', level_best_times)

def save_game_data():
    data = {
        'accessible_levels': accessible_levels,
        'level_best_times': level_best_times
    }
    with open(SAVE_FILE, 'w') as file:
        json.dump(data, file)

def reset_level1():
    global level1_objects, selected_object, object_movement, level1_start_time
    level1_objects = [pygame.Rect(obj.x, obj.y, obj.width, obj.height) for obj in level1_initial_positions]
    selected_object = None
    object_movement = [0, 0]
    level1_start_time = time.time()

def reset_level3():
    global current_text_box, clicked_objects
    current_text_box = None
    clicked_objects.clear()

def reset_level4():
    global has_played
    has_played = False

def draw_text(text, x, y, color=BLACK):
    label = FONT.render(text, True, color)
    screen.blit(label, (x, y))

def main_menu():
    screen.fill(BACKGROUND_COLOR)
    screen.blit(scaled_intro_image, (40, -10))
    draw_text(TITLE, 270, 100, BLUE)
    draw_text("Click to select a level", 280, 200, BLACK)

    button_rect = pygame.Rect(325, 300, 150, 50)
    pygame.draw.rect(screen, GREEN, button_rect)
    draw_text("Level Select", 328, 310, WHITE)
    return button_rect

def level_select():
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
    global selected_object, level_complete, level1_current_time
    screen.fill(WHITE)
    draw_text("Level 1: Complete this to unlock Level 2", 150, 50, BLACK)
    level_complete = False

    if level1_start_time is not None and not level_complete:
        level1_current_time = time.time() - level1_start_time
    draw_text(f"Current Time: {level1_current_time:.2f}s", 570, 10, BLACK)
    if level_best_times[0] != float('inf'):
        draw_text(f"Best Time: {level_best_times[0]:.2f}s", 570, 40, BLACK)

    for obj in level1_objects:
        pygame.draw.rect(screen, BLUE, obj)

    level1_objects[1].x += object_movement[0]
    level1_objects[1].y += object_movement[1]

    if level1_objects[0].colliderect(level1_objects[1]):
        level_complete = True

    if level_complete:
        draw_text("Level Complete!", 300, 150, GREEN)
        complete_button = pygame.Rect(325, 500, 175, 30)
        pygame.draw.rect(screen, GREEN, complete_button)
        draw_text("Back to Levels", 330, 500, WHITE)

        if level1_current_time < level_best_times[0]:
            level_best_times[0] = level1_current_time
            save_game_data()

        return complete_button
    else:
        exit_button = pygame.Rect(15, 10, 120, 50)
        pygame.draw.rect(screen, RED, exit_button)
        draw_text("Exit Level", 15, 20, WHITE)
        return exit_button

def level2():
    screen.fill(WHITE)
    draw_text("Level 2: Click the button to complete", 150, 50, BLACK)

    complete_button = pygame.Rect(325, 300, 150, 50)
    pygame.draw.rect(screen, GREEN, complete_button)
    draw_text("Level Complete", 330, 310, WHITE)

    return complete_button

def level3():
    clickable_objects = [
        {"id": 1, "rect": pygame.Rect(100, 80, 50, 100), "description": "This is the gate.", "text_box_pos": (200, 100)},
        {"id": 2, "rect": pygame.Rect(150, 225, 200, 150), "description": "This is the penstock", "text_box_pos": (100, 400)},
        {"id": 3, "rect": pygame.Rect(510, 270, 50, 75), "description": "This is the generator.", "text_box_pos": (400, 150)},
        {"id": 4, "rect": pygame.Rect(510, 410, 60, 40), "description": "This is the turbine.", "text_box_pos": (350, 450)},
    ]

    screen.blit(levelx_image, (0, 0))
    exit_button = pygame.Rect(15, 10, 120, 50)
    pygame.draw.rect(screen, RED, exit_button)
    draw_text("Exit Level", 15, 20, WHITE)

    if current_text_box:
        display_text_box(current_text_box["description"], current_text_box["text_box_pos"])

    if len(clicked_objects) == len(clickable_objects):
        complete_button = pygame.Rect(600, 10, 190, 30)
        pygame.draw.rect(screen, GREEN, complete_button)
        draw_text("Level Complete", 605, 10, WHITE)
        return clickable_objects, exit_button, complete_button
    else:
        return clickable_objects, exit_button, None

def display_text_box(description, position):
    text_box_rect = pygame.Rect(position[0], position[1], 400, 100)
    pygame.draw.rect(screen, BLACK, text_box_rect)
    draw_text(description, text_box_rect.x + 10, text_box_rect.y + 10, WHITE)
    return text_box_rect

def play_video(video_path):
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print("Error: Could not open video.")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)

    # Define the target dimensions
    target_width, target_height = WINDOW_WIDTH, WINDOW_HEIGHT

    while cap.isOpened():
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                cap.release()
                pygame.quit()
                sys.exit()

        ret, frame = cap.read()
        if not ret:
            break

        # Resize the frame to fit the screen
        frame = cv2.resize(frame, (target_width, target_height))

        # Convert the frame to RGB (OpenCV uses BGR by default)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = pygame.surfarray.make_surface(frame.swapaxes(0, 1))

        screen.blit(frame, (0, 0))
        pygame.display.update()
        pygame.time.Clock().tick(fps)

    cap.release()

def level4():
    screen.fill(BLACK)
    draw_text("Level 4: Playing Video", 150, 50, WHITE)
    global has_played
    if not has_played:
        video_path = os.path.join(base_path, 'video.mp4')
        play_video(video_path)
        has_played = True
    exit_button = pygame.Rect(15, 10, 120, 50)
    pygame.draw.rect(screen, RED, exit_button)
    draw_text("Exit Level", 15, 20, WHITE)
    return exit_button

def complete_level(level):
    if level < LEVELS:
        accessible_levels[level] = True
        save_game_data()

def handle_events():
    global current_screen, selected_object, object_movement, current_text_box, clicked_objects
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            save_game_data()
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
                        reset_level1()
                        reset_level3()
                        reset_level4()
                        break

        elif current_screen.startswith("level_"):
            level_number = int(current_screen.split("_")[1])

            if level_number == 1:
                complete_button = level1()
                exit_button = pygame.Rect(15, 10, 120, 50)

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if exit_button.collidepoint(event.pos):
                        current_screen = "level_select"
                    elif complete_button and complete_button.collidepoint(event.pos):
                        complete_level(1)
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

            elif level_number == 3:
                clickable_objects, exit_button, complete_button = level3()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    for obj in clickable_objects:
                        if obj["rect"].collidepoint(event.pos):
                            current_text_box = obj
                            clicked_objects.add(obj["id"])
                            break
                        elif current_text_box:
                            text_box_rect = display_text_box(current_text_box["description"], current_text_box["text_box_pos"])
                            if not text_box_rect.collidepoint(event.pos):
                                current_text_box = None

                    if complete_button and complete_button.collidepoint(event.pos):
                        complete_level(3)
                        current_screen = "level_select"

                    if exit_button.collidepoint(event.pos):
                        current_screen = "level_select"

            elif level_number == 4:
                exit_button = level4()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if exit_button.collidepoint(event.pos):
                        current_screen = "level_select"

def main():
    load_game_data()
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
            elif level_number == 3:
                level3()
            elif level_number == 4:
                level4()

        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()