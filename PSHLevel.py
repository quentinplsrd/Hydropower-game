import pygame
import sys
import os
import webbrowser
import matplotlib.pyplot as plt
import numpy as np
import tempfile


pygame.init()

# Constants
SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 900
NUM_FRAMES = 278
FRAME_PATH_TEMPLATE = 'assets2/PSHSequences/PSHLevelFramesCut/Generating_Frame_{}.jpg'
TURBINE_PATH_TEMPLATE = 'assets2/PSHSequences/PSHTurbineCut/Turbine_frame_{}.jpg'
REDI_ISLAND_URL = "https://www1.eere.energy.gov/apps/water/redi_island/#/large-island/"
MAX_RELEASE = 150
MIN_RELEASE = -150
RELEASE_STEP = 10


UPPER_RESERVOIR_NUM_FRAMES = 278
UPPER_RESERVOIR_PATH_TEMPLATE = 'assets2/PSHSequences/PSHUpperReservoirFramesCut/UpperReservoir_frame_{}.jpg'
BAR_IMAGE_PATH_TEMPLATE = 'assets2/IKM_Assets/AnimatedBarSequence/Bar_{}.png'
BAR_IMAGE_COUNT = 101  # Bar_0 to Bar_100

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("PSH Level Loop")
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
    for i in range(num_frames):
        try:
            frame_path = resource_path(path_template.format(i))
            frame = pygame.image.load(frame_path).convert_alpha()
            frame = pygame.transform.scale(frame, (int(frame.get_size()[0]*SCREEN_WIDTH/1920), int(frame.get_size()[1]*SCREEN_HEIGHT/1080)))
            frames.append(frame)
        except pygame.error as e:
            print(f"Error loading frame {i}: {e}")
            sys.exit(1)
    return frames

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

def load_upper_reservoir_frames(num_frames, path_template):
    frames = []
    for i in range(num_frames):
        try:
            frame_path = resource_path(path_template.format(i))
            frame = pygame.image.load(frame_path).convert_alpha()
            frame = pygame.transform.scale(frame, (int(frame.get_size()[0]*SCREEN_WIDTH/1920)/2.5, int(frame.get_size()[1]*SCREEN_HEIGHT/1080)/2.5))
            frames.append(frame)
        except pygame.error as e:
            print(f"Error loading upper reservoir frame {i}: {e}")
            sys.exit(1)
    return frames

def update_graph(x_start, x_end, power_data):
    x = np.linspace(x_start, x_end, 2000)
    y_sine = 37 * np.sin(0.75*x)
    power_x = np.linspace(x_start, x_start + 0.5, len(power_data))

    plt.figure(figsize=(4, 3), facecolor=(0, 0, 0, 0))
    ax = plt.gca()
    ax.set_facecolor((0, 0, 0, 0))
    plt.plot(power_x, power_data, label='Power Generated', color='deepskyblue')
    plt.plot(x, y_sine, label='Load Curve', color='white')
    plt.xlim(x_start, x_end)
    plt.ylim(-40, 40)
    plt.axis('off')

    legend = plt.legend(loc='upper right', facecolor='none', edgecolor='none', fontsize=14)
    for text in legend.get_texts():
        text.set_color('white')

    plt.tight_layout()
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    plt.savefig(temp_file.name, dpi=400, transparent=True)
    plt.close()
    return temp_file.name

def reset_game():
    return {
        'release': 0.0,
        'power_data': [],
        'imbalances': [],
        'x_start': 0,
        'x_end': 5,
        'level_complete': False,
    }

def main():
    SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()
    clock = pygame.time.Clock()
    frames = load_frames(NUM_FRAMES, FRAME_PATH_TEMPLATE)
    turbine_frames = load_frames(NUM_FRAMES, TURBINE_PATH_TEMPLATE)
    upper_reservoir_frames = load_upper_reservoir_frames(UPPER_RESERVOIR_NUM_FRAMES, UPPER_RESERVOIR_PATH_TEMPLATE)
    bar_frames = load_bar_frames()
    game_state = reset_game()

    

    static_background_image = load_image('assets2/PSHSequences/PSHStatics/PSHStatics.jpg')
    static_background_image = pygame.transform.scale(static_background_image, (static_background_image.get_width() * SCREEN_WIDTH / 1920, static_background_image.get_height() * SCREEN_HEIGHT / 1080))
    upper_reservoir_image = load_image('assets2/PSHSequences/PSHStatics/UpperReservoirStatics.jpg')
    upper_reservoir_image = pygame.transform.scale(upper_reservoir_image, ((upper_reservoir_image.get_width() * SCREEN_WIDTH / 1920)/2.5, (upper_reservoir_image.get_height() * SCREEN_HEIGHT / 1080)/2.5))
    border_frame_image = load_image('assets2/IKM_Assets/BorderFrame.png')
    control_panel_image = load_image('assets2/IKM_Assets/ControlPanel.png')


    up_active_image = load_image('assets2/IKM_Assets/UpButtonActive.png')
    up_inactive_image = load_image('assets2/IKM_Assets/UpButtonInactive.png')
    down_active_image = load_image('assets2/IKM_Assets/DownButtonActive.png')
    down_inactive_image = load_image('assets2/IKM_Assets/DownButtonInactive.png')

    upper_reservoir_frame_index = 100
    running = True
    # REDi Island link box
    box_width = int(SCREEN_WIDTH * 0.35)
    box_height = int(SCREEN_HEIGHT * 0.06)
    box_x = SCREEN_WIDTH - box_width - int(SCREEN_WIDTH * 0.02)
    box_y = SCREEN_HEIGHT - box_height - int(SCREEN_HEIGHT * 0.02)
    clickable_rect = pygame.Rect(box_x, box_y, box_width, box_height)

    # Button positioning
    button_width = up_active_image.get_width() * SCREEN_WIDTH / 1920
    button_height = up_active_image.get_height() * SCREEN_HEIGHT / 1080
    button_x = SCREEN_WIDTH * 0.45
    up_button_y = SCREEN_HEIGHT * 0.83
    down_button_y = SCREEN_HEIGHT * 0.93

    up_button_rect = pygame.Rect(button_x, up_button_y, button_width, button_height)
    down_button_rect = pygame.Rect(button_x, down_button_y, button_width, button_height)

    # PSH Upper Reservoir Frame Positioning (LEFT)
    upper_edge_y = int(SCREEN_HEIGHT * 0.03)
    left_edge_x = int(SCREEN_WIDTH * 0.03)
    border_width = upper_reservoir_image.get_width()*1.005
    border_height = upper_reservoir_image.get_height()*1.01
    border_x = left_edge_x*0.975
    border_y = upper_edge_y*0.975

    scaled_border = pygame.transform.smoothscale(border_frame_image, (border_width, border_height))

    scaled_border_redi = pygame.transform.smoothscale(border_frame_image, (box_width, box_height))

    panel_width = (control_panel_image.get_size()[0] * SCREEN_WIDTH / 1920)/2
    panel_height = (control_panel_image.get_size()[1] * SCREEN_HEIGHT / 1080)/2
    scaled_panel = pygame.transform.smoothscale(control_panel_image, (panel_width, panel_height))

    panel_font_size = int(panel_height * 0.15)
    panel_font = pygame.font.Font(None, panel_font_size)

    label_text = panel_font.render("Upper Reservoir Water Level", True, (255, 255, 255))
    label_x = SCREEN_WIDTH * 0.235
    label_y = SCREEN_HEIGHT * 0.82

    graph_width = (1200*screen.get_size()[0] / 1920)/2.8
    graph_height = (900*screen.get_size()[1] / 1080)/2.8
    graph_x = SCREEN_WIDTH - graph_width - SCREEN_WIDTH * 0.02
    graph_y = int(SCREEN_HEIGHT * 0.05) 
    graph_border = pygame.transform.smoothscale(border_frame_image, (int(graph_width*1.025), int(graph_height*1.025)))

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                if clickable_rect.collidepoint(mx, my):
                    webbrowser.open(REDI_ISLAND_URL)
                elif up_button_rect.collidepoint(mx, my):
                    if game_state['release'] < MAX_RELEASE and allow_release:
                        game_state['release'] += RELEASE_STEP
                elif down_button_rect.collidepoint(mx, my):
                    if game_state['release'] > MIN_RELEASE and allow_pump:
                        game_state['release'] -= RELEASE_STEP
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    if game_state['release'] < MAX_RELEASE and allow_release:
                        game_state['release'] += RELEASE_STEP
                elif event.key == pygame.K_DOWN:
                    if game_state['release'] > MIN_RELEASE and allow_pump:
                        game_state['release'] -= RELEASE_STEP
            elif event.type == pygame.MOUSEWHEEL:
                if event.y > 0:
                    if game_state['release'] < MAX_RELEASE and allow_release:
                        game_state['release'] += RELEASE_STEP
                elif event.y < 0:
                    if game_state['release'] > MIN_RELEASE and allow_pump:
                        game_state['release'] -= RELEASE_STEP

        screen.blit(static_background_image, (0, 0))

        # Draw main background (unaffected by release scaling)
        #if game_state['release'] > 0:
            #active_frame = frames[frame_index]
            #screen.blit(active_frame, (0, 0))
            #frame_index = (frame_index + 1) % NUM_FRAMES
        #else:
            #if no_release_image:
                #paused_frame = pygame.transform.scale(no_release_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
                #screen.blit(paused_frame, (0, 0))
           # frame_index = 0

        # Update upper reservoir frame index scaled by release %
        release_factor = abs(game_state['release']) / 50.0
        previous_upper_reservoir_index = upper_reservoir_frame_index

        if game_state['release'] > 0 and upper_reservoir_frame_index < UPPER_RESERVOIR_NUM_FRAMES - 1:
            upper_reservoir_frame_index += release_factor
            if upper_reservoir_frame_index > UPPER_RESERVOIR_NUM_FRAMES - 1:
                upper_reservoir_frame_index = UPPER_RESERVOIR_NUM_FRAMES - 1
        elif game_state['release'] < 0 and upper_reservoir_frame_index > 0:
            upper_reservoir_frame_index -= release_factor
            if upper_reservoir_frame_index < 0:
                upper_reservoir_frame_index = 0

        # Convert to int for indexing frames
        upper_reservoir_frame_index_int = int(upper_reservoir_frame_index)
        # Convert to int for index comparison
        current_index_int = int(upper_reservoir_frame_index)
        previous_index_int = int(previous_upper_reservoir_index)

        # If we just overflowed the reservoir
        if previous_index_int < UPPER_RESERVOIR_NUM_FRAMES - 1 and current_index_int >= UPPER_RESERVOIR_NUM_FRAMES - 1:
            game_state['release'] = 0  # Stop the flow
        # If we just emptied the reservoir
        elif previous_index_int > 0 and current_index_int <= 0:
            game_state['release'] = 0  # Stop the flow
        
        if current_index_int >= UPPER_RESERVOIR_NUM_FRAMES - 1:
            allow_release = False
            allow_pump = True
        elif current_index_int <= 0:
            allow_release = True
            allow_pump = False
        else:
            allow_release = True
            allow_pump = True
        
        screen.blit(turbine_frames[upper_reservoir_frame_index_int], (SCREEN_WIDTH*0.3868, SCREEN_HEIGHT*0.5389))
        screen.blit(frames[upper_reservoir_frame_index_int], (SCREEN_WIDTH*0.5953, SCREEN_HEIGHT*0.4382))
        screen.blit(scaled_border, (border_x, border_y))
        screen.blit(upper_reservoir_image, (left_edge_x, upper_edge_y))
        screen.blit(upper_reservoir_frames[upper_reservoir_frame_index_int], (left_edge_x, upper_edge_y+SCREEN_HEIGHT*0.09))

        # REDi Island link box
        screen.blit(scaled_border_redi, (box_x, box_y))

        label_surface = panel_font.render("Click here to view REDi Island", True, (255, 255, 255))
        label_rect = label_surface.get_rect(center=(box_x + box_width / 2, box_y + box_height / 2))
        screen.blit(label_surface, label_rect)

        # Control panel
        screen.blit(scaled_panel, (0, SCREEN_HEIGHT * 0.8))

        # Text displays
        if game_state['release'] > 0:
            power_generated = 0.25 * game_state['release']
            game_state['power_data'].append(power_generated)
            release_status = f"Current Release Rate: {game_state['release']} cfs"
        elif game_state['release'] < 0:
            power_generated = 0
            excess_power = 0.25 * game_state['release']
            game_state['power_data'].append(excess_power)
            release_status = f"Current Pump Rate: {abs(game_state['release'])} cfs"
        else:
            power_generated = 0
            game_state['power_data'].append(power_generated)
            release_status = f"No Current Flow"
        
        power_status = f"Power Generated: {power_generated:.1f} MW/s"
        graph_filename = update_graph(game_state['x_start'], game_state['x_end'], game_state['power_data'])
        graph_image = load_image(graph_filename)

        scaled_graph_image = pygame.transform.scale(graph_image, (graph_width, graph_height))
        screen.blit(graph_border, (graph_x, graph_y))
        screen.blit(scaled_graph_image, (graph_x, graph_y))

        if len(game_state['power_data']) > 10:
            game_state['power_data'] = game_state['power_data'][-10:]

        game_state['x_start'] += 0.05
        game_state['x_end'] += 0.05

        screen.blit(panel_font.render(release_status, True, (255, 255, 255)), (SCREEN_WIDTH * 0.02, SCREEN_HEIGHT * 0.85))
        screen.blit(panel_font.render(power_status, True, (255, 255, 255)), (SCREEN_WIDTH * 0.02, SCREEN_HEIGHT * 0.90))

        # Upper Reservoir Water Level bar
        bar_index = int((300 - upper_reservoir_frame_index_int) * (1/3))
        bar_index = min(100,bar_index)
        bar_image = bar_frames[bar_index]
        screen.blit(bar_image, (int(SCREEN_WIDTH * 0.315), int(SCREEN_HEIGHT * 0.83)))

        # Label
        screen.blit(label_text, (label_x, label_y))

        # Buttons
        up_image = up_active_image if game_state['release'] < MAX_RELEASE and allow_release else up_inactive_image
        down_image = down_active_image if game_state['release'] > MIN_RELEASE and allow_pump else down_inactive_image

        up_scaled = pygame.transform.scale(up_image, (int(button_width), int(button_height)))
        down_scaled = pygame.transform.scale(down_image, (int(button_width), int(button_height)))

        screen.blit(up_scaled, up_button_rect.topleft)
        screen.blit(down_scaled, down_button_rect.topleft)

        # Get target load value from sine wave at this point in time
        current_x = game_state['x_start'] + 0.5
        target_load = 37 * np.sin(0.75*current_x)

        # Actual power is power_generated or pumping (negative power)
        actual_power = 0.25 * game_state['release']

        # Calculate imbalance and store
        imbalance = abs(actual_power - target_load)
        game_state['imbalances'].append(imbalance)

        avg_imbalance = sum(game_state['imbalances']) / len(game_state['imbalances'])
        imbalance_text = f"Avg Power Imbalance: {avg_imbalance:.2f} MW"
        text_surface = font.render(imbalance_text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, int(SCREEN_HEIGHT * 0.01)))
        screen.blit(text_surface, text_rect)

        clock.tick(30)
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
