import pygame
import sys
import numpy as np
import matplotlib.pyplot as plt
import tempfile
import os
import webbrowser

pygame.init()

# Constants
SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 900
FPS = 30
NUM_FLOW_FRAMES = 37
FLOW_PATH_TEMPLATE = 'assets2/DamSequences/Flow Cuts/Flow1_frame_{}.jpg'
FLOW2_PATH_TEMPLATE = 'assets2/DamSequences/Flow Cuts 2/Flow2_frame_{}.jpg'
FLOW3_PATH_TEMPLATE = 'assets2/DamSequences/Flow Cuts 3/Flow3_frame_{}.jpg'
FLOW4_PATH_TEMPLATE = 'assets2/DamSequences/Flow Cuts 4/Flow4_frame_{}.jpg'
NUM_TURBINE_FRAMES = 34
TURBINE_PATH_TEMPLATE = 'assets2/DamSequences/Turbine Cuts/Turbine1_frame_{}.jpg'
TURBINE2_PATH_TEMPLATE = 'assets2/DamSequences/Turbine Cuts 2/Turbine2_frame_{}.jpg'
TURBINE3_PATH_TEMPLATE = 'assets2/DamSequences/Turbine Cuts 3/Turbine3_frame_{}.jpg'
TURBINE4_PATH_TEMPLATE = 'assets2/DamSequences/Turbine Cuts 4/Turbine4_frame_{}.jpg'
NUM_WATER_FRAMES = 127
WATER_PATH_TEMPLATE = 'assets2/DamSequences/WaterLevels/WaterLevel_{}.jpg'
NUM_SPILLWAY_FRAMES = 25
SPILLWAY_PATH_TEMPLATE = 'assets2/DamSequences/Spillway Cuts/Spillway_frame_{}.jpg'
MAX_WATER_LEVEL = 4  # Maximum water level for game over
WATER_LEVEL_THRESHOLD = 0.01 * MAX_WATER_LEVEL  # 1% of the max water level
WINDOW_MODE = 2  # Default window mode (1: small, 2: medium, 3: large)
LEVEL_DURATION = 360 # Duration of the level in seconds
BAR_IMAGE_PATH_TEMPLATE = 'assets2/IKM_Assets/AnimatedBarSequence/Bar_{}.png'
BAR_IMAGE_COUNT = 101 # Bar_0 to Bar_100

# URL to open
WEBPAGE_URL = "https://www1.eere.energy.gov/apps/water/redi_island/#/large-island/"

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Hydropower Dam Simulation")
font = pygame.font.SysFont(None, 24)

def load_bar_frames():
    frames = []
    for i in range(BAR_IMAGE_COUNT):
        try:
            path = resource_path(BAR_IMAGE_PATH_TEMPLATE.format(i))
            image = pygame.image.load(path).convert_alpha()
            rotated_bar_image = pygame.transform.rotate(image, 90)
            image = pygame.transform.scale(rotated_bar_image, ((image.get_size()[0]*SCREEN_WIDTH/1920)/2, (image.get_size()[1]*SCREEN_HEIGHT/1080)))
            frames.append(image)
        except pygame.error as e:
            print(f"Error loading bar frame {i}: {e}")
            sys.exit(1)
    return frames

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
    for i in range(0, num_frames):
        try:
            frame_path = resource_path(path_template.format(i))
            frame = pygame.image.load(frame_path).convert()
            frame = pygame.transform.scale(frame, (int(frame.get_size()[0]*SCREEN_WIDTH/1920), int(frame.get_size()[1]*SCREEN_HEIGHT/1080)))
            frames.append(frame)
        except pygame.error as e:
            print(f"Error loading frame {i}: {e}")
            sys.exit(1)
    return frames

def update_graph(x_start, x_end, power_data):
    x = np.linspace(x_start, x_end, 1000)
    y_sine = -4*np.cos(x) + 4.5

    # Calculate x-values for power data
    power_x = np.linspace(x_start, x_start + 0.5, len(power_data))

    plt.figure(figsize=(4, 3), facecolor=(0, 0, 0, 0))
    ax = plt.gca()
    ax.set_facecolor((0, 0, 0, 0))
    plt.plot(power_x, power_data, label='Power Generated', color='deepskyblue')
    plt.plot(x, y_sine, label='Load Curve', color='white')
    plt.xlim(x_start, x_end)
    plt.ylim(-0.5, 10)
    plt.axis('off')

    legend = plt.legend(loc='upper right', facecolor='none', edgecolor='none', fontsize=14)
    for text in legend.get_texts():
        text.set_color('white')

    plt.tight_layout()
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    plt.savefig(temp_file.name, dpi=300, transparent=True)
    plt.close()
    return temp_file.name

def load_image(filename):
    try:
        return pygame.image.load(resource_path(filename)).convert_alpha()
    except pygame.error as e:
        print(f"Unable to load image: {e}")
        return None

def reset_game():
    """Reset game variables to initial conditions."""
    return {
        'started' : False,
        'water_level': 0.0,
        'water_volume': 0.0,
        'intake_rate': 1.5,
        'base_outer_flow': 2.8,
        'active_outer_flow': 2.8,
        'spillway_rate': 0.0,
        'wasted_water': 0.0,
        'gates': [0,0,0,0],
        'power_data': [],
        'x_start': 0,
        'x_end': 5,
        'game_over': False,
        'score': 0.0,
        'elapsed_time': 0.0,
        'level_complete': False
    }

def truncate_float(value, decimal_places):
    """Truncate a float to a specified number of decimal places."""
    factor = 10.0 ** decimal_places
    return int(value * factor) / factor

def change_screen_size(width, height):
    global screen
    screen = pygame.display.set_mode((width, height))

def draw_start_screen(screen):
    """Draw the start screen with a start button."""
    screen.fill((0, 0, 0))  # Fill the screen with black

    # Define button properties
    start_text = "Start"
    start_font = pygame.font.SysFont(None, 48)
    start_label = start_font.render(start_text, True, (255, 255, 255))
    start_rect = start_label.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))

    # Draw the button
    pygame.draw.rect(screen, (100, 100, 100), start_rect.inflate(20, 10))  # Button background
    screen.blit(start_label, start_rect)

    # Draw the title
    title_text = "Hydropower Dam Level"
    title_font = pygame.font.SysFont(None, 72)
    title_label = title_font.render(title_text, True, (255, 255, 255))
    title_rect = title_label.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4))
    screen.blit(title_label, title_rect)

    pygame.display.flip()

    return start_rect

def start_screen(game_state):
    """Display the start screen and wait for the player to click the start button."""
    while True:
        start_rect = draw_start_screen(screen)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if start_rect.collidepoint(event.pos):
                    game_state['started'] = True
                    return  # Exit the start screen and begin the game

def main():
    global WINDOW_MODE
    spillway_index = 0
    spillway_frames = load_frames(NUM_SPILLWAY_FRAMES, SPILLWAY_PATH_TEMPLATE)
    water_frames = load_frames(NUM_WATER_FRAMES, WATER_PATH_TEMPLATE)
    flow1_index = 0
    flow2_index = 0
    flow3_index = 0
    flow4_index = 0
    flow1_frames = load_frames(NUM_FLOW_FRAMES, FLOW_PATH_TEMPLATE)
    flow2_frames = load_frames(NUM_FLOW_FRAMES, FLOW2_PATH_TEMPLATE)
    flow3_frames = load_frames(NUM_FLOW_FRAMES, FLOW3_PATH_TEMPLATE)
    flow4_frames = load_frames(NUM_FLOW_FRAMES, FLOW4_PATH_TEMPLATE)
    turbine1_index = 0
    turbine2_index = 0
    turbine3_index = 0
    turbine4_index = 0
    turbine1_frames = load_frames(NUM_TURBINE_FRAMES, TURBINE_PATH_TEMPLATE)
    turbine2_frames = load_frames(NUM_TURBINE_FRAMES, TURBINE2_PATH_TEMPLATE)
    turbine3_frames = load_frames(NUM_TURBINE_FRAMES, TURBINE3_PATH_TEMPLATE)
    turbine4_frames = load_frames(NUM_TURBINE_FRAMES, TURBINE4_PATH_TEMPLATE)
    bar_frames = load_bar_frames()
    static_background_image = load_image('assets2/DamSequences/DamStatics/DamStatics.jpg')
    static_tube_1_image = load_image('assets2/DamSequences/DamStatics/FullTube1.jpg')
    static_tube_2_image = load_image('assets2/DamSequences/DamStatics/FullTube2.jpg')
    open_gate_image = load_image('assets2/DamSequences/Gate Cuts/OpenGates.jpg')
    open_gate2_image = load_image('assets2/DamSequences/Gate Cuts 2/OpenGates2.jpg')
    open_gate3_image = load_image('assets2/DamSequences/Gate Cuts 3/OpenGates3.jpg')
    open_gate4_image = load_image('assets2/DamSequences/Gate Cuts 4/OpenGates4.jpg')
    closed_gate_image = load_image('assets2/DamSequences/Gate Cuts/ClosedGates.jpg')
    closed_gate2_image = load_image('assets2/DamSequences/Gate Cuts 2/ClosedGates2.jpg')
    closed_gate3_image = load_image('assets2/DamSequences/Gate Cuts 3/ClosedGates3.jpg')
    closed_gate4_image = load_image('assets2/DamSequences/Gate Cuts 4/ClosedGates4.jpg')
    border_frame_image = load_image('assets2/IKM_Assets/BorderFrame.png')
    control_panel_image = load_image('assets2/IKM_Assets/ControlPanel.png')
    up_active_image = load_image('assets2/IKM_Assets/UpButtonActive.png')
    up_inactive_image = load_image('assets2/IKM_Assets/UpButtonInactive.png')
    down_active_image = load_image('assets2/IKM_Assets/DownButtonActive.png')
    down_inactive_image = load_image('assets2/IKM_Assets/DownButtonInactive.png')

    static_background_image = pygame.transform.scale(static_background_image, (static_background_image.get_size()[0]*SCREEN_WIDTH/1920, static_background_image.get_size()[1]*SCREEN_HEIGHT/1080))
    static_tube_1_image = pygame.transform.scale(static_tube_1_image, (static_tube_1_image.get_size()[0]*SCREEN_WIDTH/1920, static_tube_1_image.get_size()[1]*SCREEN_HEIGHT/1080))
    static_tube_2_image = pygame.transform.scale(static_tube_2_image, (static_tube_2_image.get_size()[0]*SCREEN_WIDTH/1920, static_tube_2_image.get_size()[1]*SCREEN_HEIGHT/1080))
    open_gate_image = pygame.transform.scale(open_gate_image, (open_gate_image.get_size()[0]*SCREEN_WIDTH/1920, open_gate_image.get_size()[1]*SCREEN_HEIGHT/1080))
    open_gate2_image = pygame.transform.scale(open_gate2_image, (open_gate2_image.get_size()[0]*SCREEN_WIDTH/1920, open_gate2_image.get_size()[1]*SCREEN_HEIGHT/1080))
    open_gate3_image = pygame.transform.scale(open_gate3_image, (open_gate3_image.get_size()[0]*SCREEN_WIDTH/1920, open_gate3_image.get_size()[1]*SCREEN_HEIGHT/1080))
    open_gate4_image = pygame.transform.scale(open_gate4_image, (open_gate4_image.get_size()[0]*SCREEN_WIDTH/1920, open_gate4_image.get_size()[1]*SCREEN_HEIGHT/1080))
    closed_gate_image = pygame.transform.scale(closed_gate_image, (closed_gate_image.get_size()[0]*SCREEN_WIDTH/1920, closed_gate_image.get_size()[1]*SCREEN_HEIGHT/1080))
    closed_gate2_image = pygame.transform.scale(closed_gate2_image, (closed_gate2_image.get_size()[0]*SCREEN_WIDTH/1920, closed_gate2_image.get_size()[1]*SCREEN_HEIGHT/1080))
    closed_gate3_image = pygame.transform.scale(closed_gate3_image, (closed_gate3_image.get_size()[0]*SCREEN_WIDTH/1920, closed_gate3_image.get_size()[1]*SCREEN_HEIGHT/1080))
    closed_gate4_image = pygame.transform.scale(closed_gate4_image, (closed_gate4_image.get_size()[0]*SCREEN_WIDTH/1920, closed_gate4_image.get_size()[1]*SCREEN_HEIGHT/1080))

    # Initialize game state
    game_state = reset_game()
    start_screen(game_state)
    clock = pygame.time.Clock()

    # Button positioning
    button_width = up_active_image.get_width() * SCREEN_WIDTH / 1920
    button_height = up_active_image.get_height() * SCREEN_HEIGHT / 1080
    button_x = SCREEN_WIDTH * 0.45
    up_button_y = SCREEN_HEIGHT * 0.83
    down_button_y = SCREEN_HEIGHT * 0.93

    up_button_rect = pygame.Rect(button_x, up_button_y, button_width, button_height)
    down_button_rect = pygame.Rect(button_x, down_button_y, button_width, button_height)

    graph_width = (1200*screen.get_size()[0] / 1920)/2.8
    graph_height = (900*screen.get_size()[1] / 1080)/2.8
    graph_x = SCREEN_WIDTH - graph_width - SCREEN_WIDTH * 0.02
    graph_y = int(SCREEN_HEIGHT * 0.05) 
    graph_border = pygame.transform.smoothscale(border_frame_image, (int(graph_width*1.025), int(graph_height*1.025)))

    panel_width = (control_panel_image.get_size()[0] * SCREEN_WIDTH / 1920)/2
    panel_height = (control_panel_image.get_size()[1] * SCREEN_HEIGHT / 1080)/2
    scaled_panel = pygame.transform.smoothscale(control_panel_image, (panel_width, panel_height))
    panel_x = 0
    panel_y = int(SCREEN_HEIGHT * 0.8)

    # Set the font size relative to control panel height
    panel_font_size = int(panel_height * 0.15)
    panel_font = pygame.font.Font(None, panel_font_size)

    water_level_text = "Upper Reservoir Water Level"

    # REDi Island link box
    box_width = int(SCREEN_WIDTH * 0.35)
    box_height = int(SCREEN_HEIGHT * 0.06)
    box_x = SCREEN_WIDTH - box_width - int(SCREEN_WIDTH * 0.02)
    box_y = SCREEN_HEIGHT - box_height - int(SCREEN_HEIGHT * 0.02)
    clickable_rect = pygame.Rect(box_x, box_y, box_width, box_height)
    # Button linking to REDi Island
    
    scaled_border_redi = pygame.transform.smoothscale(border_frame_image, (box_width, box_height))

    label_surface = panel_font.render("Click here to view REDi Island", True, (255, 255, 255))
    label_rect = label_surface.get_rect(center=(box_x + box_width / 2, box_y + box_height / 2))

    level_surface = panel_font.render(water_level_text, True, (255, 255, 255))

    square_size = int(panel_height * 0.15)  # Adjust as needed
    spacing_between_squares = int(square_size * 0.3)

    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    for i in range(len(game_state['gates'])):
                        if game_state['gates'][i] == 0:
                            game_state['gates'][i] = 1
                            break
                elif event.key == pygame.K_DOWN:
                    for i in reversed(range(len(game_state['gates']))):
                        if game_state['gates'][i] == 1:
                            game_state['gates'][i] = 0
                            break
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if clickable_rect.collidepoint(event.pos):
                    webbrowser.open(WEBPAGE_URL)
                elif up_button_rect.collidepoint(event.pos):
                    for i in range(len(game_state['gates'])):
                        if game_state['gates'][i] == 0:
                            game_state['gates'][i] = 1
                            break
                elif down_button_rect.collidepoint(event.pos):
                    for i in reversed(range(len(game_state['gates']))):
                        if game_state['gates'][i] == 1:
                            game_state['gates'][i] = 0
                            break
            elif event.type == pygame.MOUSEWHEEL:
                if event.y > 0:
                    for i in range(len(game_state['gates'])):
                        if game_state['gates'][i] == 0:
                            game_state['gates'][i] = 1
                            break
                elif event.y < 0:
                    for i in reversed(range(len(game_state['gates']))):
                        if game_state['gates'][i] == 1:
                            game_state['gates'][i] = 0
                            break

 
        if game_state['level_complete']:
            screen.blit(static_background_image, (0,0))

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
        elif game_state['started']:
            delta_time = clock.tick(FPS) / 1000.0
            # Update elapsed time
            game_state['elapsed_time'] += delta_time
            # Check for level completion
            if game_state['elapsed_time'] >= LEVEL_DURATION:
                game_state['level_complete'] = True
            # Calculate the number of open gates
            open_gates = sum(game_state['gates'])
            game_state['active_outer_flow'] = (open_gates / 4) * game_state['base_outer_flow']
            # Update the water level
            if game_state['water_level'] > WATER_LEVEL_THRESHOLD and game_state['water_level'] < MAX_WATER_LEVEL:
                # Apply outflow only if water level is above the threshold
                game_state['spillway_rate'] = 0
                game_state['water_volume'] = max(0, game_state['water_volume'] + (game_state['intake_rate'] - game_state['active_outer_flow']) * delta_time)
            elif game_state['water_level'] >= MAX_WATER_LEVEL and game_state['active_outer_flow']<game_state['intake_rate']:
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

            #assume vol to elevation function by interpolation of set of points
            game_state['water_level'] = np.sqrt(game_state['water_volume'])

            bar_index = int((game_state['water_level']/MAX_WATER_LEVEL)*100)
            bar_index = min(100,bar_index)
            bar_image = bar_frames[bar_index]

            # Calculate wasted water via spillway
            game_state['wasted_water'] = game_state['wasted_water']+(game_state['spillway_rate']*delta_time)

            # Calculate power generated
            power_generated = 0.5 * (game_state['water_level'] + 3) * game_state['active_outer_flow']
            game_state['power_data'].append(power_generated)

            
            screen.blit(static_background_image, (0, 0))

            # Draw the static tubes
            water_index = min(int((game_state['water_level']/MAX_WATER_LEVEL) * (126)), 126)
            water_level_image = water_frames[water_index]
            screen.blit(water_level_image, (int(SCREEN_WIDTH*0.0255), 0))
            if game_state['spillway_rate'] > 0:
                spillway_index = spillway_index % 24
                spillway_index += 1
                spillway_image = spillway_frames[spillway_index]
                screen.blit(spillway_image, (int(SCREEN_WIDTH*.6172),int(SCREEN_HEIGHT*.1657)))
            else:
                spillway_index = 0
                screen.blit(spillway_frames[spillway_index], (int(SCREEN_WIDTH*.6172),int(SCREEN_HEIGHT*.1657)))
            screen.blit(static_tube_1_image, (int(SCREEN_WIDTH * 0.4025), int(SCREEN_HEIGHT * 0.3480)))
            screen.blit(static_tube_2_image, (int(SCREEN_WIDTH * 0.4737), int(SCREEN_HEIGHT * 0.5771)))
            
            if game_state['gates'][3] == 0:
                screen.blit(closed_gate4_image, (int(SCREEN_WIDTH * 0.553), int(SCREEN_HEIGHT * 0.3478)))
                screen.blit(flow4_frames[36], (int(SCREEN_WIDTH * 0.6881), int(SCREEN_HEIGHT * 0.7714)))
                screen.blit(turbine4_frames[turbine4_index], (int(SCREEN_WIDTH * 0.645), int(SCREEN_HEIGHT * 0.6223)))
            else:
                screen.blit(open_gate4_image, (int(SCREEN_WIDTH * 0.553), int(SCREEN_HEIGHT * 0.3478)))
                screen.blit(flow4_frames[flow4_index], (int(SCREEN_WIDTH * 0.6881), int(SCREEN_HEIGHT * 0.7714)))
                flow4_index += 1
                flow4_index = flow4_index % 35
                screen.blit(turbine4_frames[turbine4_index], (int(SCREEN_WIDTH * 0.645), int(SCREEN_HEIGHT * 0.6223)))
                turbine4_index += 1
                turbine4_index = turbine4_index % 33

            if game_state['gates'][2] == 0:
                screen.blit(closed_gate3_image, (int(SCREEN_WIDTH * 0.511), int(SCREEN_HEIGHT * 0.3611)))
                screen.blit(flow3_frames[36], (int(SCREEN_WIDTH * 0.6595), int(SCREEN_HEIGHT * 0.81805)))
                screen.blit(turbine3_frames[turbine3_index], (int(SCREEN_WIDTH * 0.6051), int(SCREEN_HEIGHT * 0.6486)))
            else:
                screen.blit(open_gate3_image, (int(SCREEN_WIDTH * 0.511), int(SCREEN_HEIGHT * 0.3611)))
                screen.blit(flow3_frames[flow3_index], (int(SCREEN_WIDTH * 0.6595), int(SCREEN_HEIGHT * 0.81805)))
                flow3_index += 1
                flow3_index = flow3_index % 35
                screen.blit(turbine3_frames[turbine3_index], (int(SCREEN_WIDTH * 0.6051), int(SCREEN_HEIGHT * 0.6486)))
                turbine3_index += 1
                turbine3_index = turbine3_index % 33

            if game_state['gates'][1] == 0:
                screen.blit(closed_gate2_image, (int(SCREEN_WIDTH * 0.4744), int(SCREEN_HEIGHT * 0.3767)))
                screen.blit(flow2_frames[36], (int(SCREEN_WIDTH * 0.6131), int(SCREEN_HEIGHT * 0.8406)))
                screen.blit(turbine2_frames[turbine2_index], (int(SCREEN_WIDTH * 0.564), int(SCREEN_HEIGHT * 0.6714)))
            else:
                screen.blit(open_gate2_image, (int(SCREEN_WIDTH * 0.4744), int(SCREEN_HEIGHT * 0.3767)))
                screen.blit(flow2_frames[flow2_index], (int(SCREEN_WIDTH * 0.6131), int(SCREEN_HEIGHT * 0.8406)))
                flow2_index += 1
                flow2_index = flow2_index % 35
                screen.blit(turbine2_frames[turbine2_index], (int(SCREEN_WIDTH * 0.564), int(SCREEN_HEIGHT * 0.6714)))
                turbine2_index += 1
                turbine2_index = turbine2_index % 33

            if game_state['gates'][0] == 0:
                screen.blit(closed_gate_image, (int(SCREEN_WIDTH * 0.4340), int(SCREEN_HEIGHT * 0.3914)))
                screen.blit(flow1_frames[36], (int(SCREEN_WIDTH * 0.5767), int(SCREEN_HEIGHT * 0.8764)))
                screen.blit(turbine1_frames[turbine1_index], (int(SCREEN_WIDTH * 0.5247), int(SCREEN_HEIGHT * 0.7006)))
            else:
                screen.blit(open_gate_image, (int(SCREEN_WIDTH * 0.4340), int(SCREEN_HEIGHT * 0.3914)))
                screen.blit(flow1_frames[flow1_index], (int(SCREEN_WIDTH * 0.5767), int(SCREEN_HEIGHT * 0.8764)))
                flow1_index += 1
                flow1_index = flow1_index % 35
                screen.blit(turbine1_frames[turbine1_index], (int(SCREEN_WIDTH * 0.5247), int(SCREEN_HEIGHT * 0.7006)))
                turbine1_index += 1
                turbine1_index = turbine1_index % 33

            # Update the graph with new x range and power data
            graph_filename = update_graph(game_state['x_start'], game_state['x_end'], game_state['power_data'])
            graph_image = load_image(graph_filename)

            scaled_graph_image = pygame.transform.scale(graph_image, (graph_width, graph_height))
            screen.blit(graph_border, (graph_x, graph_y))
            screen.blit(scaled_graph_image, (graph_x, graph_y))

             # Trim power data to match the visible window
            if len(game_state['power_data']) > 10:
                game_state['power_data'] = game_state['power_data'][-10:]

            # Update the x range to simulate movement
            game_state['x_start'] += 0.05
            game_state['x_end'] += 0.05

            # Set the font size based on the window mode
            if WINDOW_MODE == 1:
                performance_font = pygame.font.Font(None, 24)
            elif WINDOW_MODE == 2:
                performance_font = pygame.font.Font(None, 36)
            elif WINDOW_MODE == 3:
                performance_font = pygame.font.Font(None, 48)

            # Display the water wasted

            waste_status = f"Average Water Wasted: {(game_state['wasted_water']/game_state['elapsed_time']):.2f} cfs"
            waste_label = performance_font.render(waste_status, True, (255, 255, 255))
            screen.blit(waste_label, (SCREEN_WIDTH - waste_label.get_width() - SCREEN_WIDTH*0.0125, SCREEN_HEIGHT*0.0167))

            # Display elapsed time
            time_status = f"Time Elapsed: {int(game_state['elapsed_time'])} sec"
            time_max = f"Total Duration: {LEVEL_DURATION} sec"
            time_label = performance_font.render(time_status, True, (255, 255, 255))
            max_label = performance_font.render(time_max, True, (255, 255, 255))
            screen.blit(time_label, (SCREEN_WIDTH*0.0125, SCREEN_HEIGHT*0.0167))
            screen.blit(max_label, (SCREEN_WIDTH*0.0125, SCREEN_HEIGHT*0.0567))

            # Calculate the sine curve value at x_start + 0.5
            cos_value = -4*np.cos(game_state['x_start'] + 0.5) + 4.5

            # Calculate the load difference
            load_difference = truncate_float(power_generated - cos_value, 2)

            # Render the load difference text
            performance_text = f"Load Difference: {load_difference} MW"
            performance_label = performance_font.render(performance_text, True, (255, 255, 255))

            # Calculate the position to center the text at the top of the screen
            performance_x = (SCREEN_WIDTH - performance_label.get_width()) // 2
            performance_y = SCREEN_HEIGHT*0.0167  # Adjust the y-position as needed

            # Blit the performance label to the screen
            screen.blit(performance_label, (performance_x, performance_y))
            abs_load_difference = abs(load_difference)

            # Update the score
            game_state['score'] += abs_load_difference

            # Render the score text
            score_text = f"Average Power Imbalance: {int(game_state['score']/max(game_state['elapsed_time'],1))} MW"
            score_label = performance_font.render(score_text, True, (255, 255, 255))

            # Calculate the position to display the score
            score_x = (SCREEN_WIDTH - score_label.get_width()) // 2
            score_y = performance_y + performance_label.get_height() + SCREEN_HEIGHT*0.0167  # Position below the load difference

            # Blit the score label to the screen
            screen.blit(score_label, (score_x, score_y))
            
            # Draw the control panel
            screen.blit(scaled_panel, (panel_x, panel_y))

            # Prepare the lines
            outer_flow_text = f"Outer Flow: {game_state['active_outer_flow']:.2f} cfs"
            power_text = f"Power Generated: {power_generated:.2f} MW/s"  # Swapped order
            open_gates_text = f"Open Gates: {open_gates}"

            left_panel_lines = [outer_flow_text, power_text, open_gates_text]

            # Layout calculations
            left_spacing = (panel_height / (len(left_panel_lines) + 1)) / 1.75

            # Draw left column of text
            for i, line in enumerate(left_panel_lines):
                text_surface = panel_font.render(line, True, (255, 255, 255))
                text_x = panel_x + panel_width * 0.05  # Left margin
                text_y = panel_y + left_spacing * (i + 1) + SCREEN_HEIGHT*0.01
                screen.blit(text_surface, (text_x, text_y))

            screen.blit(level_surface, (SCREEN_WIDTH * 0.235, SCREEN_HEIGHT * 0.82))

            # Compute starting position
            start_x = panel_x + panel_width * 0.05
            start_y = panel_y + left_spacing * (len(left_panel_lines) + 1)

            for i in range(4):
                gate_open = game_state['gates'][i] == 1
                alpha = 255 if gate_open else 64  # Full opacity if open, transparent if closed

                # Create a surface with per-pixel alpha
                gate_surface = pygame.Surface((square_size, square_size), pygame.SRCALPHA)
                gate_surface.fill((0, 206, 244, alpha))  # Blue with variable transparency

                x = start_x + i * (square_size + spacing_between_squares)
                screen.blit(gate_surface, (x, start_y))

            screen.blit(bar_image, (int(SCREEN_WIDTH * 0.315), int(SCREEN_HEIGHT * 0.83)))

            # Decide whether buttons should be active
            all_open = all(g == 1 for g in game_state['gates'])
            all_closed = all(g == 0 for g in game_state['gates'])

            up_image = up_inactive_image if all_open else up_active_image
            down_image = down_inactive_image if all_closed else down_active_image

            # Scale and draw buttons
            up_scaled = pygame.transform.scale(up_image, (int(button_width), int(button_height)))
            down_scaled = pygame.transform.scale(down_image, (int(button_width), int(button_height)))

            screen.blit(up_scaled, up_button_rect.topleft)
            screen.blit(down_scaled, down_button_rect.topleft)

            screen.blit(scaled_border_redi, (box_x, box_y))
            screen.blit(label_surface, label_rect)

            # Clean up the temporary file
            os.remove(graph_filename)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()