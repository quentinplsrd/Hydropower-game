import pygame
import sys
import numpy as np
#import matplotlib.pyplot as plt
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
ROTATION_ANGLE = 10
NUM_OVALS = 16
circle_radius = 80
BACKGROUND_COLOR = (30, 30, 30)

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

def load_image(filename):
    try:
        return pygame.image.load(filename).convert()
    except pygame.error as e:
        print(f"Unable to load image: {e}")
        return None

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

def truncate_float(value, decimal_places):
    """Truncate a float to a specified number of decimal places."""
    factor = 10.0 ** decimal_places
    return int(value * factor) / factor

def change_screen_size(width, height):
    global screen
    screen = pygame.display.set_mode((width, height))

def reset_game():
    return {
        'rotation' : 0,
        'release' : 0.0,
        'power_data' : [],
        'x_start': 0,
        'x_end': 5,
        'level_complete': False,
        'angles': [],
        'center_x': 0,
        'center_y': 0,
        'positions': []
    }

def get_pointer_rotation(power_generated):
    """Calculate the rotation angle for the pointer based on power generated."""
    clamped_power = min(max(power_generated, 0), 25)
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

try:
    gate_image_path = resource_path('assets2/Wicket_gate.png')
    gate_image = pygame.image.load(gate_image_path).convert_alpha()
except pygame.error as e:
    print(f"Error loading pointer image: {e}")
    sys.exit(1)

"""
def update_graph(x_start, x_end, power_data):
    x = np.linspace(x_start, x_end, 1000)
    y_sine = 11*np.sin(x) + 14

    # Calculate x-values for power data
    power_x = np.linspace(x_start, x_start + 0.5, len(power_data))

    plt.figure(figsize=(4, 3), facecolor='black')  # Set figure background color to black
    ax = plt.gca()  # Get current axes
    ax.set_facecolor('black') 
    plt.plot(power_x, power_data, label='Power Generated', color='red')
    plt.plot(x, y_sine, label='Load Curve', color='white')  # Change line color for visibility
    plt.xlim(x_start, x_end)
    plt.ylim(-0.5, 30)
    #plt.fill_between(power_x,power_data,y_sine[0:len(power_data)])

    # Set legend with white text
    legend = plt.legend(loc='upper right', facecolor='black', edgecolor='white', fontsize=14)
    for text in legend.get_texts():
        text.set_color('white')  # Set legend text color to white

    plt.axis('off')  
    plt.tight_layout()  # Automatically adjust subplot parameters

    # Use a temporary file for the graph image
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    plt.savefig(temp_file.name, dpi=200, facecolor='black')  
    plt.close()
    return temp_file.name
"""
def main():
    frames = load_frames(NUM_FRAMES, FRAME_PATH_TEMPLATE)
    SCREEN_HEIGHT = screen.get_height()
    SCREEN_WIDTH = screen.get_width()
    global WINDOW_MODE
    global gate_image
    running = True
    game_state = reset_game()
    clock = pygame.time.Clock()
    IMAGE_WIDTH, IMAGE_HEIGHT = gate_image.get_size()
    game_state['angles'] = [220-i*360/NUM_OVALS for i in range(NUM_OVALS)]

    while running:
        SCREEN_HEIGHT = screen.get_height()
        SCREEN_WIDTH = screen.get_width()
        global circle_radius
        active_circle_radius = circle_radius * (SCREEN_WIDTH/800)
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
                    change_screen_size(1920, 1440)
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    if game_state['rotation'] < 90:
                        game_state['angles'] = [angle + ROTATION_ANGLE for angle in game_state['angles']]
                        game_state['rotation'] +=  ROTATION_ANGLE
                elif event.key == pygame.K_DOWN:
                    if game_state['rotation'] > 0:
                        game_state['angles'] = [angle - ROTATION_ANGLE for angle in game_state['angles']]
                        game_state['rotation'] -= ROTATION_ANGLE
        active_gate_image = pygame.transform.smoothscale(gate_image,(IMAGE_WIDTH*0.0001*SCREEN_WIDTH,IMAGE_HEIGHT*0.00015*SCREEN_HEIGHT))
        game_state['center_x'],game_state['center_y'] = SCREEN_WIDTH*.15, SCREEN_HEIGHT*.2
        game_state['positions'] = [
            (game_state['center_x'] + active_circle_radius * np.cos(2 * np.pi * i / NUM_OVALS),
            game_state['center_y'] + active_circle_radius * np.sin(2 * np.pi * i / NUM_OVALS))
            for i in range(NUM_OVALS)
        ]
        frame_index = int((game_state['rotation'] / 10))
        frame_index = max(0, min(NUM_FRAMES - 1, frame_index))  # Clamp to valid range
        active_frame = pygame.transform.scale(frames[frame_index], (SCREEN_WIDTH, SCREEN_HEIGHT))
        screen.blit(active_frame, (0, 0))
        if WINDOW_MODE == 1:
            performance_font = pygame.font.Font(None, 24)
        elif WINDOW_MODE == 2:
            performance_font = pygame.font.Font(None, 36)
        elif WINDOW_MODE == 3:
            performance_font = pygame.font.Font(None, 48)
        rotation_status = f"Rotation: {game_state['rotation']} degrees"
        rotation_label = performance_font.render(rotation_status, True, (255,255,255))
        screen.blit(rotation_label, (0,0))
        game_state['release'] = int((1-(game_state['rotation']/90))*MAX_RELEASE)
        release_status = f"Current Release: {game_state['release']} cfs"
        release_label = performance_font.render(release_status, True, (255,255,255))
        screen.blit(release_label, (SCREEN_WIDTH*0.4,0))
        power_generated = 0.25*game_state['release']
        power_status = f"Power Generated: {power_generated} MW/s"
        power_label = performance_font.render(power_status, True, (255,255,255))
        screen.blit(power_label,(SCREEN_WIDTH*0.045,SCREEN_HEIGHT*0.77))
        game_state['power_data'].append(power_generated)

        """graph_filename = update_graph(game_state['x_start'], game_state['x_end'], game_state['power_data'])
        graph_image = load_image(graph_filename)
        if graph_image:
            scaled_graph_image = pygame.transform.scale(graph_image, (SCREEN_WIDTH * 0.28, SCREEN_HEIGHT * 0.25))
            screen.blit(scaled_graph_image, (SCREEN_WIDTH * 0.725, SCREEN_HEIGHT * 0.12))
        os.remove(graph_filename) """

        # Trim power data to match the visible window
        if len(game_state['power_data']) > 10:
            game_state['power_data'] = game_state['power_data'][-10:]

        # Update the x range to simulate movement
        game_state['x_start'] += 0.05
        game_state['x_end'] += 0.05

        draw_dial_and_pointer(screen, power_generated,SCREEN_WIDTH,SCREEN_HEIGHT)

        square_size = active_circle_radius * 2.7
        square_position = (SCREEN_WIDTH*.018, SCREEN_HEIGHT*.025)
        pygame.draw.rect(screen, BACKGROUND_COLOR, (*square_position, square_size, square_size))

        for i, (pos_x, pos_y) in enumerate(game_state['positions']):
            rotated_image = pygame.transform.rotozoom(active_gate_image, game_state['angles'][i],1.0)
            rect = rotated_image.get_rect(center=(pos_x, pos_y))
            screen.blit(rotated_image, rect.topleft)
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()