import pygame
import sys
import numpy as np
import matplotlib.pyplot as plt
import tempfile
import os
import webbrowser

pygame.init()

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
NUM_FRAMES = 170  # Number of frames to load
FRAME_PATH_TEMPLATE = 'assets2/scene{}.png'
MAX_WATER_LEVEL = 4  # Maximum water level for game over
GATE_WIDTH = 0.01
GATE_HEIGHT = 0.1667
GATE_MOVE_DISTANCE = 0.08333  # Distance the gate moves per frame
FADE_IN_DURATION = 2.0  # Duration of fade-in effect in seconds
WATER_LEVEL_THRESHOLD = 0.01 * MAX_WATER_LEVEL  # 1% of the max water level
WINDOW_MODE = 1
LEVEL_DURATION = 60 # Duration of the level in seconds

# URL to open
WEBPAGE_URL = "https://www1.eere.energy.gov/apps/water/redi_island/#/large-island/"

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Hydropower Dam Simulation")
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

def update_graph(x_start, x_end, power_data):
    x = np.linspace(x_start, x_end, 1000)
    y_sine = 2*np.sin(x) + 6

    # Calculate x-values for power data
    power_x = np.linspace(x_start, x_start + 0.5, len(power_data))

    plt.figure(figsize=(4, 3), facecolor='black')  # Set figure background color to black
    ax = plt.gca()  # Get current axes
    ax.set_facecolor('black') 
    plt.plot(power_x, power_data, label='Power Generated', color='red')
    plt.plot(x, y_sine, label='Load Curve', color='white')  # Change line color for visibility
    plt.xlim(x_start, x_end)
    plt.ylim(-0.5, 12)
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

def load_image(filename):
    try:
        return pygame.image.load(filename).convert()
    except pygame.error as e:
        print(f"Unable to load image: {e}")
        return None

def reset_game():
    """Reset game variables to initial conditions."""
    return {
        'started' : False,
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
    """Truncate a float to a specified number of decimal places."""
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
    """Calculate the rotation angle for the pointer based on power generated."""
    clamped_power = min(max(power_generated, 0), 10)  # Clamp power to a maximum of 10
    return (clamped_power / 10) * 120  # Calculate rotation angle (0 to 120 degrees)

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

def draw_start_screen(screen, font):
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
        start_rect = draw_start_screen(screen, font)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if start_rect.collidepoint(event.pos):
                    game_state['started'] = True
                    return  # Exit the start screen and begin the game

def main():
    frames = load_frames(NUM_FRAMES, FRAME_PATH_TEMPLATE)
    SCREEN_HEIGHT = screen.get_height()
    SCREEN_WIDTH = screen.get_width()
    global WINDOW_MODE

    # Load the monitor image
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

    # Initialize game state
    game_state = reset_game()
    start_screen(game_state)
    clock = pygame.time.Clock()

    # Define button properties
    button_text = "Click to view REDi Island"

    running = True

    while running:
        # Calculate the time since the last frame
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
            elif event.type == pygame.KEYDOWN and not game_state['game_over']:
                if event.key == pygame.K_UP:
                    # Open the next gate
                    for gate in game_state['gates']:
                        if gate['target_y'] == gate['initial_y']:
                            gate['target_y'] = gate['open_y']
                            break
                elif event.key == pygame.K_DOWN:
                    # Close the last open gate
                    for gate in reversed(game_state['gates']):
                        if gate['target_y'] == gate['open_y']:
                            gate['target_y'] = gate['initial_y']
                            break
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if button_rect.collidepoint(event.pos):
                    webbrowser.open(WEBPAGE_URL)

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

            # Draw the gates
            for gate in game_state['gates']:
                gate_rect = pygame.Rect(gate['x'] * SCREEN_WIDTH, gate['y'] * SCREEN_HEIGHT, GATE_WIDTH * SCREEN_WIDTH, GATE_HEIGHT * SCREEN_HEIGHT)
                pygame.draw.rect(screen, (169, 169, 169), gate_rect)

            # Display the monitor image behind the graph
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
        elif game_state['started']:
            delta_time = clock.tick(FPS) / 1000.0
            # Update elapsed time
            game_state['elapsed_time'] += delta_time
            # Check for level completion
            if game_state['elapsed_time'] >= LEVEL_DURATION and not game_state['game_over']:
                game_state['level_complete'] = True
            # Calculate the number of open gates
            open_gates = sum(gate['target_y'] == gate['open_y'] for gate in game_state['gates'])
            game_state['active_outer_flow'] = (open_gates / 3) * game_state['base_outer_flow']
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

            # Calculate wasted water via spillway
            game_state['wasted_water'] = game_state['wasted_water']+(game_state['spillway_rate']*delta_time)

            # Calculate power generated
            power_generated = 0.5 * (game_state['water_level'] + 3) * game_state['active_outer_flow']
            game_state['power_data'].append(power_generated)

            # Trim power data to match the visible window
            if len(game_state['power_data']) > 10:
                game_state['power_data'] = game_state['power_data'][-10:]

            # Update the x range to simulate movement
            game_state['x_start'] += 0.05
            game_state['x_end'] += 0.05

            # Update the graph with new x range and power data
            graph_filename = update_graph(game_state['x_start'], game_state['x_end'], game_state['power_data'])

            # Load and display the graph
            graph_image = load_image(graph_filename)

            # Update gate positions
            for gate in game_state['gates']:
                if gate['y'] < gate['target_y']:
                    gate['y'] += GATE_MOVE_DISTANCE  # Move gate down
                elif gate['y'] > gate['target_y']:
                    gate['y'] -= GATE_MOVE_DISTANCE  # Move gate up

            # Normalize the water level to a range of 0 to NUM_FRAMES - 1
            frame_index = int((game_state['water_level'] / MAX_WATER_LEVEL) * (NUM_FRAMES - 1))
            frame_index = max(0, min(NUM_FRAMES - 1, frame_index))  # Clamp to valid range
            frames[frame_index] = pygame.transform.scale(frames[frame_index], (SCREEN_WIDTH, SCREEN_HEIGHT))
            screen.blit(frames[frame_index], (0, 0))

            if game_state['active_outer_flow'] > 0:
                flow_image = pygame.transform.scale(flow_image, (SCREEN_WIDTH*0.2,SCREEN_HEIGHT*0.05))
                screen.blit(flow_image, (SCREEN_WIDTH*0.785,SCREEN_HEIGHT*0.765))

            # Draw the gates
            for gate in game_state['gates']:
                gate_rect = pygame.Rect(gate['x'] * SCREEN_WIDTH, gate['y'] * SCREEN_HEIGHT, GATE_WIDTH * SCREEN_WIDTH, GATE_HEIGHT * SCREEN_HEIGHT)
                pygame.draw.rect(screen, (169, 169, 169), gate_rect)

            # Display the monitor image behind the graph
            monitor_image_scaled = pygame.transform.scale(monitor_image, (int(SCREEN_WIDTH * 0.35), int(SCREEN_HEIGHT * 0.35)))
            screen.blit(monitor_image_scaled, (SCREEN_WIDTH * 0.62, SCREEN_HEIGHT * 0.18))

            # Display of the power generated vs load graph
            if graph_image:
                scaled_graph_image = pygame.transform.scale(graph_image, (SCREEN_WIDTH * 0.28, SCREEN_HEIGHT * 0.25))
                screen.blit(scaled_graph_image, (SCREEN_WIDTH * 0.65, SCREEN_HEIGHT * 0.22))

            # Set the font size based on the window mode
            if WINDOW_MODE == 1:
                performance_font = pygame.font.Font(None, 24)
            elif WINDOW_MODE == 2:
                performance_font = pygame.font.Font(None, 36)
            elif WINDOW_MODE == 3:
                performance_font = pygame.font.Font(None, 48)

            # Display the outer flow status
            flow_status = f"Outer Flow: {game_state['active_outer_flow']:.2f}"
            label = performance_font.render(flow_status, True, (0, 0, 0))
            screen.blit(label, (SCREEN_WIDTH - label.get_width() - SCREEN_WIDTH*0.0125, SCREEN_HEIGHT*0.0167))

            # Display the number of open gates
            open_gates_status = f"Open Gates: {open_gates}"
            open_gates_label = performance_font.render(open_gates_status, True, (0, 0, 0))
            screen.blit(open_gates_label, (SCREEN_WIDTH - open_gates_label.get_width() - SCREEN_WIDTH*0.0125, SCREEN_HEIGHT*0.0567))

            # Display the power generated
            power_status = f"Power Generated: {power_generated:.2f} MW"
            power_label = performance_font.render(power_status, True, (0, 0, 0))
            screen.blit(power_label, (SCREEN_WIDTH - power_label.get_width() - SCREEN_WIDTH*0.0125, SCREEN_HEIGHT*0.0967))

            # Display the water wasted

            waste_status = f"Average Water Wasted: {(game_state['wasted_water']/game_state['elapsed_time']):.2f} cfs"
            waste_label = performance_font.render(waste_status, True, (0, 0, 0))
            screen.blit(waste_label, (SCREEN_WIDTH - waste_label.get_width() - SCREEN_WIDTH*0.0125, SCREEN_HEIGHT*0.1267))

            # Display elapsed time
            time_status = f"Time Elapsed: {int(game_state['elapsed_time'])} sec"
            time_max = f"Total Duration: {LEVEL_DURATION} sec"
            time_label = performance_font.render(time_status, True, (0, 0, 0))
            max_label = performance_font.render(time_max, True, (0, 0, 0))
            screen.blit(time_label, (SCREEN_WIDTH*0.0125, SCREEN_HEIGHT*0.0167))
            screen.blit(max_label, (SCREEN_WIDTH*0.0125, SCREEN_HEIGHT*0.0567))

            # Calculate the sine curve value at x_start + 0.5
            sine_value = 2*np.sin(game_state['x_start'] + 0.5) + 6

            # Calculate the load difference
            load_difference = truncate_float(power_generated - sine_value, 2)

            # Render the load difference text
            performance_text = f"Load Difference: {load_difference} MW"
            performance_label = performance_font.render(performance_text, True, (0, 0, 0))

            # Calculate the position to center the text at the top of the screen
            performance_x = (SCREEN_WIDTH - performance_label.get_width()) // 2
            performance_y = SCREEN_HEIGHT*0.0167  # Adjust the y-position as needed

            # Blit the performance label to the screen
            screen.blit(performance_label, (performance_x, performance_y))
            abs_load_difference = abs(load_difference)

            # Update the score
            game_state['score'] += abs_load_difference

            # Render the score text
            score_text = f"Average Power Imbalance: {int(game_state['score']/game_state['elapsed_time'])} MW"
            score_label = performance_font.render(score_text, True, (0, 0, 0))

            # Calculate the position to display the score
            score_x = (SCREEN_WIDTH - score_label.get_width()) // 2
            score_y = performance_y + performance_label.get_height() + SCREEN_HEIGHT*0.0167  # Position below the load difference

            # Blit the score label to the screen
            screen.blit(score_label, (score_x, score_y))

            # Button linking to REDi Island
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

            # Draw the dial and pointer
            draw_dial_and_pointer(screen, power_generated,SCREEN_WIDTH,SCREEN_HEIGHT)

            # Clean up the temporary file
            os.remove(graph_filename)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()