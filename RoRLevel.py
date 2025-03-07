import pygame
import sys
import numpy as np
import matplotlib.pyplot as plt
import tempfile
import os

pygame.init()

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
NUM_FRAMES = 10  # Number of frames to load
FRAME_PATH_TEMPLATE = 'assets2/Level1/RoRF{}.png'
WINDOW_MODE = 1
LEVEL_DURATION = 60 # Duration of the level in seconds
MAX_ROTATION = 90
MAX_RELEASE = 100

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Run of River Simulation")
font = pygame.font.SysFont(None, 24)

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def load_frames(num_frames, path_template):
    """Load and scale frames for animation."""
    frames = []
    for i in range(1, num_frames + 1):
        try:
            frame_path = resource_path(path_template.format(i))
            frame = pygame.image.load(frame_path).convert()
            frames.append(frame)
        except pygame.error as e:
            print(f"Error loading frame {i}: {e}")
            sys.exit(1)
    return frames

def change_screen_size(width, height):
    global screen
    screen = pygame.display.set_mode((width, height))

def reset_game():
    return {
        'rotation' : 0,
        'release' : 0.0
    }

def get_pointer_rotation(power_generated):
    """Calculate the rotation angle for the pointer based on power generated."""
    clamped_power = min(max(power_generated, 0), 25)  # Clamp power to a maximum of 10
    return (clamped_power / 25) * 120  # Calculate rotation angle (0 to 120 degrees)

def draw_dial_and_pointer(screen, power_generated, WIDTH, HEIGHT):
    """Draw the dial and pointer on the screen."""
    dial_size = (int(WIDTH * 0.3), int(HEIGHT * 0.2))
    dial_image_scaled = pygame.transform.scale(dial_image, dial_size)
    pointer_size = (WIDTH*0.1, HEIGHT*0.1)
    pointer_image_scaled = pygame.transform.scale(pointer_image, pointer_size)

    dial_position = (WIDTH*0.01, HEIGHT*0.8)

    rotation_angle = get_pointer_rotation(power_generated)
    pointer_rotated = pygame.transform.rotate(pointer_image_scaled, -rotation_angle)

    pointer_rect = pointer_rotated.get_rect(center=dial_image_scaled.get_rect(topleft=dial_position).center)

    screen.blit(dial_image_scaled, dial_position)
    screen.blit(pointer_rotated, pointer_rect.topleft)

try:
    dial_image_path = resource_path('assets2/dial.png')
    dial_image = pygame.image.load(dial_image_path).convert_alpha()
except pygame.error as e:
    print(f"Error loading dial image: {e}")
    sys.exit(1)

try:
    pointer_image_path = resource_path('assets2/pointer.png')
    pointer_image = pygame.image.load(pointer_image_path).convert_alpha()
except pygame.error as e:
    print(f"Error loading pointer image: {e}")
    sys.exit(1)

def main():
    frames = load_frames(NUM_FRAMES, FRAME_PATH_TEMPLATE)
    SCREEN_HEIGHT = screen.get_height()
    SCREEN_WIDTH = screen.get_width()
    global WINDOW_MODE
    running = True
    game_state = reset_game()
    clock = pygame.time.Clock()

    while running:
        SCREEN_HEIGHT = screen.get_height()
        SCREEN_WIDTH = screen.get_width()
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    WINDOW_MODE = 1
                    change_screen_size(800, 600)
                elif event.key == pygame.K_2:
                    WINDOW_MODE = 2
                    change_screen_size(1024, 768)
                elif event.key == pygame.K_3:
                    WINDOW_MODE = 3
                    change_screen_size(1920, 1080)
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    if game_state['rotation'] < 90:
                        game_state['rotation'] = game_state['rotation'] + 10
                elif event.key == pygame.K_DOWN:
                    if game_state['rotation'] > 0:
                        game_state['rotation'] = game_state['rotation'] - 10
        frame_index = int((game_state['rotation'] / 10))
        frame_index = max(0, min(NUM_FRAMES - 1, frame_index))  # Clamp to valid range
        frames[frame_index] = pygame.transform.scale(frames[frame_index], (SCREEN_WIDTH, SCREEN_HEIGHT))
        screen.blit(frames[frame_index], (0, 0))
        if WINDOW_MODE == 1:
            performance_font = pygame.font.Font(None, 24)
        elif WINDOW_MODE == 2:
            performance_font = pygame.font.Font(None, 36)
        elif WINDOW_MODE == 3:
            performance_font = pygame.font.Font(None, 48)
        rotation_status = f"Rotation Angle: {game_state['rotation']}"
        rotation_label = performance_font.render(rotation_status, True, (255,255,255))
        screen.blit(rotation_label, (0,0))
        game_state['release'] = int((game_state['rotation']/90)*MAX_RELEASE)
        release_status = f"Current Release: {game_state['release']} cfs"
        release_label = performance_font.render(release_status, True, (255,255,255))
        screen.blit(release_label, (SCREEN_WIDTH*0.4,0))
        power_generated = 0.25*game_state['release']
        power_status = f"Power Generated: {power_generated} MW"
        power_label = performance_font.render(power_status, True, (255,255,255))
        screen.blit(power_label,(SCREEN_WIDTH*0.045,SCREEN_HEIGHT*0.77))
        draw_dial_and_pointer(screen, power_generated,SCREEN_WIDTH,SCREEN_HEIGHT)
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()