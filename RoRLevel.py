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
WINDOW_MODE = 2
NUM_FRAMES = 62
WATER_PATH_TEMPLATE = 'assets2/RoRWaterFrames/RoRLoopFrame_{}.jpg'
TUBE_PATH_TEMPLATE = 'assets2/RoRTubeFrames/RoRLoopFrame_{}.jpg'
LEVEL_DURATION = 60
MAX_ROTATION = 80
MAX_RELEASE = 100
ROTATION_ANGLE = 10
NUM_OVALS = 16
BACKGROUND_COLOR = (30, 30, 30)
REDI_ISLAND_URL = "https://www1.eere.energy.gov/apps/water/redi_island/#/large-island/"


screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Run of River Level")
font = pygame.font.SysFont(None, 24)

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def load_image(filename):
    try:
        return pygame.image.load(resource_path(filename)).convert_alpha()
    except pygame.error as e:
        print(f"Unable to load image: {e}")
        return None

def load_frames(num_frames, path_template):
    frames = []
    for i in range(0, num_frames):
        try:
            frame_path = resource_path(path_template.format(i))
            frame = pygame.image.load(frame_path).convert()
            frame = pygame.transform.scale(frame, (frame.get_size()[0]*SCREEN_WIDTH/1920, frame.get_size()[1]*SCREEN_HEIGHT/1080))
            frames.append(frame)
        except pygame.error as e:
            print(f"Error loading frame {i}: {e}")
            sys.exit(1)
    return frames

def truncate_float(value, decimal_places):
    factor = 10.0 ** decimal_places
    return int(value * factor) / factor

def change_screen_size(width, height):
    global screen
    screen = pygame.display.set_mode((width, height))

def reset_game():
    return {
        'rotation': 0,
        'release': 0.0,
        'power_data': [],
        'x_start': 0,
        'x_end': 5,
        'level_complete': False,
        'angles': [],
        'center_x': 0,
        'center_y': 0,
        'positions': []
    }

def update_graph(x_start, x_end, power_data):
    x = np.linspace(x_start, x_end, 1000)
    y_sine = 11 * np.sin(0.75*x+1) + 14
    power_x = np.linspace(x_start, x_start + 0.5, len(power_data))

    plt.figure(figsize=(4, 3), facecolor=(0, 0, 0, 0))
    ax = plt.gca()
    ax.set_facecolor((0, 0, 0, 0))
    plt.plot(power_x, power_data, label='Power Generated', color='deepskyblue')
    plt.plot(x, y_sine, label='Load Curve', color='white')
    plt.xlim(x_start, x_end)
    plt.ylim(-0.8, 30.5)
    plt.axis('off')

    legend = plt.legend(loc='upper right', facecolor='none', edgecolor='none', fontsize=14)
    for text in legend.get_texts():
        text.set_color('white')

    plt.tight_layout()
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    plt.savefig(temp_file.name, dpi=400, transparent=True)
    plt.close()
    return temp_file.name


# Load assets
static_image = load_image('assets2/RoRStatics/RoRStatic.jpg')
control_panel_image = load_image('assets2/IKM_Assets/ControlPanel.png')
up_active_image = load_image('assets2/IKM_Assets/UpButtonActive.png')
up_inactive_image = load_image('assets2/IKM_Assets/UpButtonInactive.png')
down_active_image = load_image('assets2/IKM_Assets/DownButtonActive.png')
down_inactive_image = load_image('assets2/IKM_Assets/DownButtonInactive.png')
border_frame_image = load_image('assets2/IKM_Assets/BorderFrame.png')
gate_image = load_image('assets2/RoRStatics/Wicket_gate.png')

def main():
    global SCREEN_WIDTH, SCREEN_HEIGHT, screen
    clock = pygame.time.Clock()
    water_frames = load_frames(NUM_FRAMES, WATER_PATH_TEMPLATE)
    tube_frames = load_frames(NUM_FRAMES, TUBE_PATH_TEMPLATE)
    frame_index = 0
    window_mode = 2
    running = True
    game_state = reset_game()
    game_state['angles'] = [220 - i * 360 / NUM_OVALS for i in range(NUM_OVALS)]
    active_circle_radius = SCREEN_WIDTH * 0.0875

    statics_image = pygame.transform.smoothscale(static_image, (SCREEN_WIDTH, SCREEN_HEIGHT))

    box_width = int(SCREEN_WIDTH * 0.35)
    box_height = int(SCREEN_HEIGHT * 0.06)
    box_x = SCREEN_WIDTH - box_width - int(SCREEN_WIDTH * 0.02)
    box_y = SCREEN_HEIGHT - box_height - int(SCREEN_HEIGHT * 0.02)
    clickable_rect = pygame.Rect(box_x, box_y, box_width, box_height)

    graph_width = (1200*screen.get_size()[0] / 1920)/2.8
    graph_height = (900*screen.get_size()[1] / 1080)/2.8
    graph_x = SCREEN_WIDTH - graph_width - SCREEN_WIDTH * 0.02 
    graph_y = int(SCREEN_HEIGHT * 0.075) 
    graph_border = pygame.transform.smoothscale(border_frame_image, (int(graph_width*1.025), int(graph_height*1.025)))

    # Button positioning
    button_width = up_active_image.get_width() * SCREEN_WIDTH / 1920
    button_height = up_active_image.get_height() * SCREEN_HEIGHT / 1080
    button_x = SCREEN_WIDTH * 0.45
    up_button_y = SCREEN_HEIGHT * 0.83
    down_button_y = SCREEN_HEIGHT * 0.93

    # --- Draw Wicket Gate Frame and Label ---
    frame_size = int(active_circle_radius * 2.7)
    frame_x = int(SCREEN_WIDTH * 0.018)
    frame_y = int(SCREEN_HEIGHT * 0.043)

    
    scaled_frame = pygame.transform.smoothscale(border_frame_image, (frame_size, frame_size))

    scaled_panel = pygame.transform.smoothscale(control_panel_image, ((control_panel_image.get_size()[0] * SCREEN_WIDTH / 1920)/2, (control_panel_image.get_size()[1] * SCREEN_HEIGHT / 1080)/2))

    # Define gate size as a fraction of the frame
    gate_scale_factor = 0.18  # 20% of the frame size

    gate_size = int(frame_size * gate_scale_factor)
    active_gate_image = pygame.transform.smoothscale(gate_image, (gate_size, gate_size))

    game_state['center_x'], game_state['center_y'] = frame_x + frame_size / 2, frame_y + frame_size / 2
    game_state['positions'] = [
        (game_state['center_x'] + active_circle_radius * np.cos(2 * np.pi * i / NUM_OVALS),
            game_state['center_y'] + active_circle_radius * np.sin(2 * np.pi * i / NUM_OVALS))
        for i in range(NUM_OVALS)
    ]

    scaled_border = pygame.transform.smoothscale(border_frame_image, (box_width, box_height))
   
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    window_mode = 1
                    change_screen_size(800, 600)
                elif event.key == pygame.K_2:
                    window_mode = 2
                    change_screen_size(1024, 768)
                elif event.key == pygame.K_3:
                    window_mode = 3
                    change_screen_size(1600, 900)
                elif event.key == pygame.K_UP:
                    if game_state['rotation'] > 0:
                        game_state['angles'] = [angle - ROTATION_ANGLE for angle in game_state['angles']]
                        game_state['rotation'] -= ROTATION_ANGLE
                elif event.key == pygame.K_DOWN:
                    if game_state['rotation'] < 80:
                        game_state['angles'] = [angle + ROTATION_ANGLE for angle in game_state['angles']]
                        game_state['rotation'] += ROTATION_ANGLE
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                if clickable_rect.collidepoint(mouse_x, mouse_y):
                    webbrowser.open(REDI_ISLAND_URL)
                if up_button_rect.collidepoint(mouse_x, mouse_y):
                    if game_state['rotation'] > 0:
                        game_state['angles'] = [angle - ROTATION_ANGLE for angle in game_state['angles']]
                        game_state['rotation'] -= ROTATION_ANGLE
                elif down_button_rect.collidepoint(mouse_x, mouse_y):
                    if game_state['rotation'] < 80:
                        game_state['angles'] = [angle + ROTATION_ANGLE for angle in game_state['angles']]
                        game_state['rotation'] += ROTATION_ANGLE
            elif event.type == pygame.MOUSEWHEEL:
                if event.y > 0 and game_state['rotation'] > 0:  # Scroll up
                    game_state['angles'] = [angle - ROTATION_ANGLE for angle in game_state['angles']]
                    game_state['rotation'] -= ROTATION_ANGLE
                elif event.y < 0 and game_state['rotation'] < 80:  # Scroll down
                    game_state['angles'] = [angle + ROTATION_ANGLE for angle in game_state['angles']]
                    game_state['rotation'] += ROTATION_ANGLE

        active_water_frame = water_frames[frame_index]
        active_tube_frame = tube_frames[frame_index]
        frame_index = (frame_index + 1) % (NUM_FRAMES-1)
        screen.blit(statics_image, (0, 0))
        screen.blit(active_water_frame, (int(SCREEN_WIDTH*.5256), int(SCREEN_HEIGHT*.72779)))
        screen.blit(active_tube_frame, (1, SCREEN_HEIGHT*.3286))
        

        if window_mode == 1:
            performance_font = pygame.font.Font(None, 24)
        elif window_mode == 2:
            performance_font = pygame.font.Font(None, 36)
        elif window_mode == 3:
            performance_font = pygame.font.Font(None, 48)

        game_state['release'] = int((1 - (game_state['rotation'] / 80)) * MAX_RELEASE) + 10
        power_generated = 0.25 * game_state['release']
        game_state['power_data'].append(power_generated)

        graph_filename = update_graph(game_state['x_start'], game_state['x_end'], game_state['power_data'])
        graph_image = load_image(graph_filename)
        
        
        scaled_graph_image = pygame.transform.scale(graph_image, (graph_width, graph_height))
        screen.blit(graph_border, (graph_x, graph_y))
        screen.blit(scaled_graph_image, (graph_x, graph_y))
        if len(game_state['power_data']) > 10:
            game_state['power_data'] = game_state['power_data'][-10:]

        game_state['x_start'] += 0.05
        game_state['x_end'] += 0.05

       
        screen.blit(scaled_panel, (0, SCREEN_HEIGHT * .8))

        rotation_status = f"Rotation: {game_state['rotation']} degrees"
        release_status = f"Current Release: {game_state['release']} cfs"
        power_status = f"Power Generated: {power_generated} kW/s"

        screen.blit(performance_font.render(rotation_status, True, (255, 255, 255)), (SCREEN_WIDTH * 0.02, SCREEN_HEIGHT * 0.85))
        screen.blit(performance_font.render(release_status, True, (255, 255, 255)), (SCREEN_WIDTH * 0.02, SCREEN_HEIGHT * 0.90))
        screen.blit(performance_font.render(power_status, True, (255, 255, 255)), (SCREEN_WIDTH * 0.02, SCREEN_HEIGHT * 0.95))


        up_button = pygame.transform.scale(up_active_image if game_state['rotation'] > 0 else up_inactive_image, (int(button_width), int(button_height)))
        down_button = pygame.transform.scale(down_active_image if game_state['rotation'] < 80 else down_inactive_image, (int(button_width), int(button_height)))

        up_button_rect = up_button.get_rect(topleft=(button_x, up_button_y))
        down_button_rect = down_button.get_rect(topleft=(button_x, down_button_y))

        screen.blit(up_button, up_button_rect.topleft)
        screen.blit(down_button, down_button_rect.topleft)

        screen.blit(scaled_frame, (frame_x, frame_y))

        label_surface = performance_font.render("Wicket Gate Display", True, (255, 255, 255))
        label_rect = label_surface.get_rect(center=(frame_x + frame_size / 2, frame_y - SCREEN_HEIGHT * 0.015))
        screen.blit(label_surface, label_rect)

        
        # --- Draw the rotating gates ---
        for i, (pos_x, pos_y) in enumerate(game_state['positions']):
            rotated_image = pygame.transform.rotozoom(active_gate_image, game_state['angles'][i], 1.0)
            rect = rotated_image.get_rect(center=(pos_x, pos_y))
            screen.blit(rotated_image, rect.topleft)

        # --- Draw clickable REDi Island box ---
        screen.blit(scaled_border, (box_x, box_y))

        label_surface_small = performance_font.render("Click here to view REDi Island", True, (255, 255, 255))
        label_rect_small = label_surface_small.get_rect(center=(box_x + box_width / 2, box_y + box_height / 2))
        screen.blit(label_surface_small, label_rect_small)

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
