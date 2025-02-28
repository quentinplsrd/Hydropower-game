import cv2
import pygame
import sys
import time
import json
import os
import numpy as np
import matplotlib.pyplot as plt
import tempfile
import webbrowser

# Initialize Pygame
pygame.init()

# Constants
WINDOW_WIDTH, WINDOW_HEIGHT = 800, 600
TITLE = "The Hydropower Game"
FPS = 60
LEVELS = 10
FONT = pygame.font.Font(None, 36)
SAVE_FILE = 'game_save.json'
WINDOW_MODE = 1

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
intro_image_path = os.path.join(base_path, 'Dam.jpg')
try:
    intro_image = pygame.image.load(intro_image_path)
except pygame.error as e:
    print(f"Unable to load image: {e}")
    pygame.quit()
    sys.exit()
scaled_intro_image = pygame.transform.scale(intro_image, (WINDOW_WIDTH,WINDOW_HEIGHT))

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

# Level 3 globals
current_text_box = None
clicked_objects = set()

# Level 4 globals
has_played = False

# Hydropower Dam Level Constants
NUM_FRAMES = 170
FRAME_PATH_TEMPLATE = 'assets2/scene{}.png'
MAX_WATER_LEVEL = 4
GATE_WIDTH = 0.01
GATE_HEIGHT = 0.1666666
GATE_MOVE_DISTANCE = 0.08333
FADE_IN_DURATION = 2.0
WATER_LEVEL_THRESHOLD = 0.01 * MAX_WATER_LEVEL
LEVEL_DURATION = 30
WEBPAGE_URL = "https://www1.eere.energy.gov/apps/water/redi_island/#/large-island/"

# Load resources for the hydropower dam level
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def load_frames(num_frames, path_template):
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

def update_graph(x_start, x_end, power_data):
    x = np.linspace(x_start, x_end, 1000)
    y_sine = 2 * np.sin(x) + 6

    power_x = np.linspace(x_start, x_start + 0.5, len(power_data))

    plt.figure(figsize=(4, 3), facecolor='black')
    ax = plt.gca()
    ax.set_facecolor('black')
    plt.plot(power_x, power_data, label='Power Generated', color='red')
    plt.plot(x, y_sine, label='Load Curve', color='white')
    plt.xlim(x_start, x_end)
    plt.ylim(-0.5, 12)

    legend = plt.legend(loc='upper right', facecolor='black', edgecolor='white', fontsize=14)
    for text in legend.get_texts():
        text.set_color('white')

    plt.axis('off')
    plt.tight_layout()

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    plt.savefig(temp_file.name, dpi=200, facecolor='black')
    plt.close()
    return temp_file.name

def load_image(filename):
    try:
        return pygame.image.load(filename).convert()
    except pygame.error as e:
        print(f"Unable to load image: {e}")
        return None

def reset_hydropower_game():
    return {
        'water_level': 0.0,
        'water_volume': 0.0,
        'intake_rate': 2.0,
        'base_outer_flow': 2.8,
        'active_outer_flow': 2.8,
        'spillway_rate': 0.0,
        'wasted_water': 0.0,
        'gates': [
            {'x': 0.4, 'initial_y': 0.458, 'y': 0.458, 'target_y': 0.458, 'open_y': 0.37467},
            {'x': 0.4375, 'initial_y': 0.5, 'y': 0.5, 'target_y': 0.5, 'open_y': 0.41667},
            {'x': 0.475, 'initial_y': 0.533, 'y': 0.533, 'target_y': 0.533, 'open_y': 0.44967}
        ],
        'power_data': [],
        'x_start': 0,
        'x_end': 5,
        'game_over': False,
        'score': 0.0,
        'elapsed_time': 0.0,
        'level_complete': False
    }

def truncate_float(value, decimal_places):
    factor = 10.0 ** decimal_places
    return int(value * factor) / factor

def change_screen_size(width, height):
    global screen
    screen = pygame.display.set_mode((width, height))

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

def get_pointer_rotation(power_generated):
    clamped_power = min(max(power_generated, 0), 10)
    return (clamped_power / 10) * 120

def draw_dial_and_pointer(screen, power_generated, WIDTH, HEIGHT):
    dial_size = (int(WIDTH * 0.3), int(HEIGHT * 0.2))
    dial_image_scaled = pygame.transform.scale(dial_image, dial_size)
    pointer_size = (WIDTH * 0.1, HEIGHT * 0.1)
    pointer_image_scaled = pygame.transform.scale(pointer_image, pointer_size)

    dial_position = (WIDTH * 0.01, HEIGHT * 0.8)

    rotation_angle = get_pointer_rotation(power_generated)
    pointer_rotated = pygame.transform.rotate(pointer_image_scaled, -rotation_angle)

    pointer_rect = pointer_rotated.get_rect(center=dial_image_scaled.get_rect(topleft=dial_position).center)

    screen.blit(dial_image_scaled, dial_position)
    screen.blit(pointer_rotated, pointer_rect.topleft)

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
    screen.blit(scaled_intro_image, (0,0))
    draw_text(TITLE, 270, 100, BLUE)

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

def hydropower_dam_level():
    frames = load_frames(NUM_FRAMES, FRAME_PATH_TEMPLATE)
    SCREEN_HEIGHT = screen.get_height()
    SCREEN_WIDTH = screen.get_width()
    global WINDOW_MODE

    try:
        monitor_image_path = resource_path('assets2/monitor.jpg')
        monitor_image = pygame.image.load(monitor_image_path).convert()
    except pygame.error as e:
        print(f"Error loading monitor image: {e}")
        sys.exit(1)

    try:
        flow_image_path = resource_path('assets2/flow.png')
        flow_image = pygame.image.load(flow_image_path).convert()
    except pygame.error as e:
        print(f"Error loading monitor image: {e}")
        sys.exit(1)

    game_state = reset_hydropower_game()
    clock = pygame.time.Clock()

    button_text = "Click to view REDi Island"
    level_complete_button = None

    running = True

    while running:
        SCREEN_HEIGHT = screen.get_height()
        SCREEN_WIDTH = screen.get_width()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN and not game_state['game_over']:
                if event.key == pygame.K_UP:
                    for gate in game_state['gates']:
                        if gate['target_y'] == gate['initial_y']:
                            gate['target_y'] = gate['open_y']
                            break
                elif event.key == pygame.K_DOWN:
                    for gate in reversed(game_state['gates']):
                        if gate['target_y'] == gate['open_y']:
                            gate['target_y'] = gate['initial_y']
                            break
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if button_rect.collidepoint(event.pos):
                    webbrowser.open(WEBPAGE_URL)
                elif level_complete_button and level_complete_button.collidepoint(event.pos):
                    complete_level(1)  
                    level_best_times[0] = game_state['score']  # Save the score
                    save_game_data()
                    return "level_select"  

        screen.fill((0, 0, 0))

        if game_state['level_complete']:
            # Draw the game environment as usual
            # Calculate the number of open gates
            open_gates = sum(gate['target_y'] == gate['open_y'] for gate in game_state['gates'])
            outer_flow = (open_gates / 3) * game_state['base_outer_flow']
            game_state['active_outer_flow'] = outer_flow

            # Normalize the water level to a range of 0 to NUM_FRAMES - 1
            frame_index = int((game_state['water_level'] / MAX_WATER_LEVEL) * (NUM_FRAMES - 1))
            frame_index = max(0, min(NUM_FRAMES - 1, frame_index))  # Clamp to valid range
            frames[frame_index] = pygame.transform.scale(frames[frame_index], (SCREEN_WIDTH, SCREEN_HEIGHT))
            screen.blit(frames[frame_index], (0, 0))

            if game_state['active_outer_flow'] > 0:
                flow_image = pygame.transform.scale(flow_image, (SCREEN_WIDTH*0.2, SCREEN_HEIGHT*0.05))
                screen.blit(flow_image, (SCREEN_WIDTH*0.785, SCREEN_HEIGHT*0.765))

            for gate in game_state['gates']:
                gate_rect = pygame.Rect(gate['x'] * SCREEN_WIDTH, gate['y'] * SCREEN_HEIGHT, GATE_WIDTH * SCREEN_WIDTH, GATE_HEIGHT * SCREEN_HEIGHT)
                pygame.draw.rect(screen, (169, 169, 169), gate_rect)

            monitor_image_scaled = pygame.transform.scale(monitor_image, (int(SCREEN_WIDTH * 0.35), int(SCREEN_HEIGHT * 0.35)))
            screen.blit(monitor_image_scaled, (SCREEN_WIDTH * 0.62, SCREEN_HEIGHT * 0.18))

            # Display the power generated vs load graph
            graph_filename = update_graph(game_state['x_start'], game_state['x_end'], game_state['power_data'])
            graph_image = load_image(graph_filename)
            if graph_image:
                scaled_graph_image = pygame.transform.scale(graph_image, (SCREEN_WIDTH * 0.28, SCREEN_HEIGHT * 0.25))
                screen.blit(scaled_graph_image, (SCREEN_WIDTH * 0.65, SCREEN_HEIGHT * 0.22))
            os.remove(graph_filename)

            # Draw the dial and pointer
            draw_dial_and_pointer(screen, power_generated, SCREEN_WIDTH, SCREEN_HEIGHT)

            # Draw the overlay
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(200)  # Semi-transparent
            overlay.fill((0, 0, 0))
            screen.blit(overlay, (0, 0))

            # Display level complete message
            if WINDOW_MODE == 1:
                complete_font = pygame.font.SysFont(None, 48)
            elif WINDOW_MODE == 2:
                complete_font = pygame.font.SysFont(None, 72)
            elif WINDOW_MODE == 3:
                complete_font = pygame.font.SysFont(None, 96)

            complete_text = "Level complete! Your score was:"
            complete_label = complete_font.render(complete_text, True, (255, 255, 255))
            score_text = f"{int(game_state['score'])}"
            score_label = complete_font.render(score_text, True, (255, 255, 255))

            screen.blit(complete_label, ((SCREEN_WIDTH - complete_label.get_width()) // 2, SCREEN_HEIGHT // 3))
            screen.blit(score_label, ((SCREEN_WIDTH - score_label.get_width()) // 2, SCREEN_HEIGHT // 2))
            # Draw the level complete button
            level_complete_button = pygame.Rect((SCREEN_WIDTH - 200) // 2, SCREEN_HEIGHT - 100, 200, 50)
            pygame.draw.rect(screen, GREEN, level_complete_button)
            draw_text("Level Complete", level_complete_button.x + 10, level_complete_button.y + 10, WHITE)

        else:
            delta_time = clock.tick(FPS) / 1000.0
            game_state['elapsed_time'] += delta_time
            if game_state['elapsed_time'] >= LEVEL_DURATION and not game_state['game_over']:
                game_state['level_complete'] = True
            open_gates = sum(gate['target_y'] == gate['open_y'] for gate in game_state['gates'])
            game_state['active_outer_flow'] = (open_gates / 3) * game_state['base_outer_flow']

            # Mass - balance equation conditional handling 
            if game_state['water_level'] > WATER_LEVEL_THRESHOLD and game_state['water_level'] < MAX_WATER_LEVEL:
                game_state['spillway_rate'] = 0
                game_state['water_volume'] = max(0, game_state['water_volume'] + (game_state['intake_rate'] - game_state['active_outer_flow']) * delta_time)
            elif game_state['water_level'] >= MAX_WATER_LEVEL and game_state['active_outer_flow'] < game_state['intake_rate']:
                game_state['spillway_rate'] = game_state['intake_rate'] - game_state['active_outer_flow']
                game_state['water_volume'] = MAX_WATER_LEVEL ** 2
            elif game_state['water_level'] >= MAX_WATER_LEVEL:
                game_state['spillway_rate'] = 0
                game_state['water_volume'] = game_state['water_volume'] + (game_state['intake_rate'] - game_state['active_outer_flow']) * delta_time
            elif game_state['water_level'] <= WATER_LEVEL_THRESHOLD and game_state['active_outer_flow'] > game_state['intake_rate']:
                game_state['spillway_rate'] = 0
                game_state['active_outer_flow'] = game_state['intake_rate']
                game_state['water_volume'] = max(0, game_state['water_volume'])
            else:
                game_state['spillway_rate'] = 0
                game_state['water_volume'] = max(0, game_state['water_volume'] + game_state['intake_rate'] * delta_time)

            game_state['water_level'] = np.sqrt(game_state['water_volume'])

            game_state['wasted_water'] = game_state['wasted_water'] + (game_state['spillway_rate'] * delta_time)

            power_generated = 0.5 * (game_state['water_level'] + 3) * game_state['active_outer_flow']
            game_state['power_data'].append(power_generated)

            if len(game_state['power_data']) > 10:
                game_state['power_data'] = game_state['power_data'][-10:]

            # Update the domain of the plot to simulate movement
            game_state['x_start'] += 0.05
            game_state['x_end'] += 0.05

            graph_filename = update_graph(game_state['x_start'], game_state['x_end'], game_state['power_data'])

            graph_image = load_image(graph_filename)

            # Moving the gates
            for gate in game_state['gates']:
                if gate['y'] < gate['target_y']:
                    gate['y'] += GATE_MOVE_DISTANCE
                elif gate['y'] > gate['target_y']:
                    gate['y'] -= GATE_MOVE_DISTANCE

            frame_index = int((game_state['water_level'] / MAX_WATER_LEVEL) * (NUM_FRAMES - 1))
            frame_index = max(0, min(NUM_FRAMES - 1, frame_index))
            frames[frame_index] = pygame.transform.scale(frames[frame_index], (SCREEN_WIDTH, SCREEN_HEIGHT))
            screen.blit(frames[frame_index], (0, 0))

            if game_state['active_outer_flow'] > 0:
                flow_image = pygame.transform.scale(flow_image, (SCREEN_WIDTH * 0.2, SCREEN_HEIGHT * 0.05))
                screen.blit(flow_image, (SCREEN_WIDTH * 0.785, SCREEN_HEIGHT * 0.765))

            for gate in game_state['gates']:
                gate_rect = pygame.Rect(gate['x'] * SCREEN_WIDTH, gate['y'] * SCREEN_HEIGHT, GATE_WIDTH * SCREEN_WIDTH, GATE_HEIGHT * SCREEN_HEIGHT)
                pygame.draw.rect(screen, (169, 169, 169), gate_rect)

            monitor_image_scaled = pygame.transform.scale(monitor_image, (int(SCREEN_WIDTH * 0.35), int(SCREEN_HEIGHT * 0.35)))
            screen.blit(monitor_image_scaled, (SCREEN_WIDTH * 0.62, SCREEN_HEIGHT * 0.18))

            if graph_image:
                scaled_graph_image = pygame.transform.scale(graph_image, (SCREEN_WIDTH * 0.28, SCREEN_HEIGHT * 0.25))
                screen.blit(scaled_graph_image, (SCREEN_WIDTH * 0.65, SCREEN_HEIGHT * 0.22))

            if WINDOW_MODE == 1:
                performance_font = pygame.font.Font(None, 24)
            elif WINDOW_MODE == 2:
                performance_font = pygame.font.Font(None, 36)
            elif WINDOW_MODE == 3:
                performance_font = pygame.font.Font(None, 48)

            flow_status = f"Outer Flow: {game_state['active_outer_flow']:.2f}"
            label = performance_font.render(flow_status, True, (0, 0, 0))
            screen.blit(label, (SCREEN_WIDTH - label.get_width() - SCREEN_WIDTH * 0.0125, SCREEN_HEIGHT * 0.0167))

            open_gates_status = f"Open Gates: {open_gates}"
            open_gates_label = performance_font.render(open_gates_status, True, (0, 0, 0))
            screen.blit(open_gates_label, (SCREEN_WIDTH - open_gates_label.get_width() - SCREEN_WIDTH * 0.0125, SCREEN_HEIGHT * 0.0567))

            power_status = f"Power Generated: {power_generated:.2f} MW"
            power_label = performance_font.render(power_status, True, (0, 0, 0))
            screen.blit(power_label, (SCREEN_WIDTH - power_label.get_width() - SCREEN_WIDTH * 0.0125, SCREEN_HEIGHT * 0.0967))

            waste_status = f"Water Wasted: {game_state['wasted_water']:.2f} cubic meters"
            waste_label = performance_font.render(waste_status, True, (0, 0, 0))
            screen.blit(waste_label, (SCREEN_WIDTH - waste_label.get_width() - SCREEN_WIDTH * 0.0125, SCREEN_HEIGHT * 0.1267))

            time_status = f"Time Elapsed: {game_state['elapsed_time']:.2f} seconds"
            time_label = performance_font.render(time_status, True, (0, 0, 0))
            screen.blit(time_label, (SCREEN_WIDTH * 0.0125, SCREEN_HEIGHT * 0.0167))

            sine_value = 2 * np.sin(game_state['x_start'] + 0.5) + 6

            load_difference = truncate_float(power_generated - sine_value, 2)

            performance_text = f"Load Difference: {load_difference} MW"
            performance_label = performance_font.render(performance_text, True, (0, 0, 0))

            performance_x = (SCREEN_WIDTH - performance_label.get_width()) // 2
            performance_y = 10

            screen.blit(performance_label, (performance_x, performance_y))
            abs_load_difference = abs(load_difference)

            game_state['score'] += abs_load_difference

            score_text = f"Score: {int(game_state['score'])}"
            score_label = performance_font.render(score_text, True, (0, 0, 0))

            score_x = (SCREEN_WIDTH - score_label.get_width()) // 2
            score_y = performance_y + performance_label.get_height() + SCREEN_HEIGHT * 0.0167

            screen.blit(score_label, (score_x, score_y))

            button_rect = pygame.Rect(SCREEN_WIDTH * 0.65, SCREEN_HEIGHT * 0.9, SCREEN_WIDTH * 0.32, SCREEN_HEIGHT * 0.05)
            if WINDOW_MODE == 1:
                button_font = pygame.font.SysFont(None, 30)
            elif WINDOW_MODE == 2:
                button_font = pygame.font.SysFont(None, 36)
            elif WINDOW_MODE == 3:
                button_font = pygame.font.SysFont(None, 40)
            button_label = button_font.render(button_text, True, (255, 255, 255))
            pygame.draw.rect(screen, (0, 0, 0), button_rect)
            screen.blit(button_label, button_rect)

            draw_dial_and_pointer(screen, power_generated, SCREEN_WIDTH, SCREEN_HEIGHT)

            os.remove(graph_filename)

        pygame.display.flip()

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

        frame = cv2.resize(frame, (target_width, target_height))
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
    global current_screen, current_text_box, clicked_objects
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
                        reset_hydropower_game()
                        reset_level3()
                        reset_level4()
                        break

        elif current_screen.startswith("level_"):
            level_number = int(current_screen.split("_")[1])

            if level_number == 1:
                hydropower_dam_level()
                current_screen = "level_select"

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
    global current_screen
    while True:
        handle_events()

        if current_screen == "main_menu":
            main_menu()
        elif current_screen == "level_select":
            level_select()
        elif current_screen.startswith("level_"):
            level_number = int(current_screen.split("_")[1])

            if level_number == 1:
                result = hydropower_dam_level()
                if result == "level_select":
                    current_screen = "level_select"
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