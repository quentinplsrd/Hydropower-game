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
FRAME_PATH_TEMPLATE = 'assets/scene{}.png'
FONT_SIZE = 24
FONT = pygame.font.Font(None, FONT_SIZE)
BUBBLEFONT = pygame.font.SysFont('comicsansms', FONT_SIZE * 2)
MAX_WATER_LEVEL = 3  # Maximum water level for game over
GATE_WIDTH = 8
GATE_HEIGHT = 100
GATE_MOVE_DISTANCE = 2.5  # Distance the gate moves per frame
FADE_IN_DURATION = 2.0  # Duration of fade-in effect in seconds
WATER_LEVEL_THRESHOLD = 0.01 * MAX_WATER_LEVEL  # 1% of the max water level

# URL to open
WEBPAGE_URL = "https://www1.eere.energy.gov/apps/water/redi_island/#/large-island/"

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Hydropower Dam Simulation")
font = pygame.font.SysFont(None, FONT_SIZE)

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
            frame = pygame.image.load(frame_path)
            frame = pygame.transform.scale(frame, (SCREEN_WIDTH, SCREEN_HEIGHT))
            frames.append(frame)
        except pygame.error as e:
            print(f"Error loading frame {i}: {e}")
            sys.exit(1)
    return frames

def update_graph(x_start, x_end, power_data):
    x = np.linspace(x_start, x_end, 1000)
    y_sine = 4 * np.sin(x) + 5

    # Calculate x-values for power data
    power_x = np.linspace(x_start, x_start + 0.5, len(power_data))

    plt.figure(figsize=(4, 3))  # Adjusted figure size
    plt.plot(power_x, power_data, label='Power Generated', color='red')
    plt.plot(x, y_sine, label='Load Curve')
    plt.xlim(x_start, x_end)
    plt.ylim(0, 10)
    plt.title('Power Output vs Load Curve')
    plt.xlabel('Time')
    plt.ylabel('Power')
    plt.legend(loc='upper right')
    plt.tight_layout()  # Automatically adjust subplot parameters

    # Use a temporary file for the graph image
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    plt.savefig(temp_file.name, dpi=100)
    plt.close()
    return temp_file.name

def load_graph_image(filename):
    try:
        return pygame.image.load(filename)
    except pygame.error as e:
        print(f"Unable to load image: {e}")
        return None

def reset_game():
    """Reset game variables to initial conditions."""
    return {
        'water_level': 0.0,
        'water_volume': 0.0,
        'intake_rate': 1.0,
        'base_outer_flow': 1.75,
        'gates': [
            {'x': 320, 'initial_y': 275, 'y': 275, 'target_y': 275, 'open_y': 225},
            {'x': 350, 'initial_y': 300, 'y': 300, 'target_y': 300, 'open_y': 250},
            {'x': 380, 'initial_y': 320, 'y': 320, 'target_y': 320, 'open_y': 270}
        ],
        'power_data': [],
        'x_start': 0,
        'x_end': 5,
        'game_over': False,
        'fade_in_alpha': 0,
        'fade_in_time': 0.0,
        'fade_in_alpha_boss': 0,
        'fade_in_time_boss': 0.0,
        'fade_in_alpha_bubble': 0,
        'fade_in_time_bubble': 0.0
    }

def main():
    clock = pygame.time.Clock()
    frames = load_frames(NUM_FRAMES, FRAME_PATH_TEMPLATE)

    # Load the flooded town image
    try:
        flooded_town_image_path = resource_path('assets/FloodedTown.jpg')
        flooded_town_image = pygame.image.load(flooded_town_image_path)
        flooded_town_image = pygame.transform.scale(flooded_town_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
    except pygame.error as e:
        print(f"Error loading flooded town image: {e}")
        sys.exit(1)

    # Load the angry boss image and set the color key
    try:
        angry_boss_image_path = resource_path('assets/Angry_Boss.png')
        angry_boss_image = pygame.image.load(angry_boss_image_path).convert_alpha()
    except pygame.error as e:
        print(f"Error loading angry boss image: {e}")
        sys.exit(1)

    # Load the speech bubble image
    try:
        bubble_image_path = resource_path('assets/bubble.png')
        bubble_image = pygame.image.load(bubble_image_path).convert_alpha()
        scale_factor = 0.75
        original_size = bubble_image.get_size()
        new_size = (int(original_size[0] * scale_factor), int(original_size[1] * scale_factor))
        bubble_image = pygame.transform.scale(bubble_image, new_size)
    except pygame.error as e:
        print(f"Error loading bubble image: {e}")
        sys.exit(1)

    # Initialize game state
    game_state = reset_game()

    # Define button properties
    button_text = "Click to view REDi Island Webpage"
    button_font = pygame.font.SysFont(None, 28)
    button_label = button_font.render(button_text, True, (255, 255, 255))
    button_rect = button_label.get_rect(topleft=(450, 550))

    # Retry button properties
    retry_text = "Retry"
    retry_label = button_font.render(retry_text, True, (255, 255, 255))
    retry_rect = retry_label.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))

    running = True

    while running:
        # Calculate the time since the last frame
        delta_time = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
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
                elif retry_rect.collidepoint(event.pos) and game_state['game_over']:
                    game_state = reset_game()  # Reset the game state

        if not game_state['game_over']:
            # Calculate the number of open gates
            open_gates = sum(gate['target_y'] == gate['open_y'] for gate in game_state['gates'])
            outer_flow = (open_gates / 3) * game_state['base_outer_flow']

            # Update the water level
            if game_state['water_level'] > WATER_LEVEL_THRESHOLD:
                # Apply outflow only if water level is above the threshold
                game_state['water_volume'] = max(0, game_state['water_volume'] + (game_state['intake_rate'] - outer_flow) * delta_time)
            else:
                # Ignore outflow if water level is below the threshold
                game_state['water_volume'] = max(0, game_state['water_volume'] + game_state['intake_rate'] * delta_time)

            game_state['water_level'] = np.sqrt(game_state['water_volume'])

            # Calculate power generated
            power_generated = game_state['water_level'] * outer_flow
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
            graph_image = load_graph_image(graph_filename)

            # Check for game over condition
            if game_state['water_level'] >= MAX_WATER_LEVEL:
                game_state['game_over'] = True
                game_state['fade_in_alpha'] = 0  # Reset alpha for fade-in
                game_state['fade_in_time'] = 0.0  # Reset fade-in timer

            # Update gate positions
            for gate in game_state['gates']:
                if gate['y'] < gate['target_y']:
                    gate['y'] += GATE_MOVE_DISTANCE  # Move gate down
                elif gate['y'] > gate['target_y']:
                    gate['y'] -= GATE_MOVE_DISTANCE  # Move gate up

        screen.fill((0, 0, 0))

        if game_state['game_over']:
            # Play fade-in to game over screen
            game_state['fade_in_time'] += delta_time
            game_state['fade_in_alpha'] = min(255, int((game_state['fade_in_time'] / FADE_IN_DURATION) * 255))
            flooded_town_image.set_alpha(game_state['fade_in_alpha'])
            screen.blit(flooded_town_image, (0, 0))
            # Display the angry boss image once the fade-in is complete
            if game_state['fade_in_alpha'] == 255:
                scale_factor = 0.6
                original_size = angry_boss_image.get_size()
                new_size = (int(original_size[0] * scale_factor), int(original_size[1] * scale_factor))
                scaled_boss_image = pygame.transform.scale(angry_boss_image, new_size)
                game_state['fade_in_time_boss'] += delta_time
                game_state['fade_in_alpha_boss'] = min(255, int((2 * game_state['fade_in_time_boss'] / FADE_IN_DURATION) * 255))
                scaled_boss_image.set_alpha(game_state['fade_in_alpha_boss'])
                screen.blit(scaled_boss_image, ((SCREEN_WIDTH // 2 - scaled_boss_image.get_width() // 2) - 220, (SCREEN_HEIGHT // 2 - scaled_boss_image.get_height() // 2) + 100))
                if game_state['fade_in_alpha_boss'] == 255:
                    game_state['fade_in_time_bubble'] += delta_time
                    game_state['fade_in_alpha_bubble'] = min(255, int((2 * game_state['fade_in_time_bubble'] / FADE_IN_DURATION) * 255))
                    bubble_image.set_alpha(game_state['fade_in_alpha_bubble'])
                    # Display the speech bubble and text
                    bubble_position = ((SCREEN_WIDTH * 3 // 4 - bubble_image.get_width() // 2) - 150, (SCREEN_HEIGHT // 4 - bubble_image.get_height() // 2) + 100)
                    screen.blit(bubble_image, bubble_position)
                    # bubble_text = BUBBLEFONT.render("You flooded the town, you're fired!", True, (0, 0, 0))
                    if game_state['fade_in_alpha_bubble'] == 255:
                        # Draw the retry button
                        pygame.draw.rect(screen, (0, 0, 0), retry_rect.inflate(10, 10))
                        screen.blit(retry_label, retry_rect)
        else:
            # Normalize the water level to a range of 0 to NUM_FRAMES - 1
            frame_index = int((game_state['water_level'] / MAX_WATER_LEVEL) * (NUM_FRAMES - 1))
            frame_index = max(0, min(NUM_FRAMES - 1, frame_index))  # Clamp to valid range

            screen.blit(frames[frame_index], (0, 0))

            # Draw the gates
            for gate in game_state['gates']:
                gate_rect = pygame.Rect(gate['x'], gate['y'], GATE_WIDTH, GATE_HEIGHT)
                pygame.draw.rect(screen, (169, 169, 169), gate_rect)

            # Display the outer flow status
            flow_status = f"Outer Flow: {outer_flow:.2f}"
            label = FONT.render(flow_status, True, (0, 0, 0))
            screen.blit(label, (SCREEN_WIDTH - label.get_width() - 10, 10))

            # Display the number of open gates
            open_gates_status = f"Open Gates: {open_gates}"
            open_gates_label = FONT.render(open_gates_status, True, (0, 0, 0))
            screen.blit(open_gates_label, (SCREEN_WIDTH - open_gates_label.get_width() - 10, 40))

            # Display the power generated
            power_status = f"Power Generated: {power_generated:.2f} MW"
            power_label = FONT.render(power_status, True, (0, 0, 0))
            screen.blit(power_label, (SCREEN_WIDTH - power_label.get_width() - 10, 70))

            # Button linking to REDi Island
            pygame.draw.rect(screen, (0, 0, 0), button_rect.inflate(10, 10))
            screen.blit(button_label, button_rect)

            # Display of the power generated vs load graph
            if graph_image:
                scale_factor = 0.75
                original_size = graph_image.get_size()
                new_size = (int(original_size[0] * scale_factor), int(original_size[1] * scale_factor))
                scaled_graph_image = pygame.transform.scale(graph_image, new_size)
                screen.blit(scaled_graph_image, (500, 100))

            # Clean up the temporary file
            os.remove(graph_filename)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()