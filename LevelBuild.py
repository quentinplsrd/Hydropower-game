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
import textwrap
from ortools.math_opt.python import mathopt

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
LEVEL_DURATION = 60
WEBPAGE_URL = "https://www1.eere.energy.gov/apps/water/redi_island/#/large-island/"


# Environment Level setup
# Global simulation parameters and OR-Tools model setup.
N_timesteps = 24
hours = np.arange(N_timesteps)
TARGET = 16  # Daily release value
min_release = 0.2
max_ramp_up = 0.2
max_ramp_down = 0.3
target_tol = 0.1
price_values = 0.02 * np.array(
    [20, 18, 17, 16, 18, 25, 30, 35, 32, 30, 28, 27,
     28, 30, 32, 35, 40, 45, 42, 38, 35, 30, 25, 22]
)

model = mathopt.Model(name="game")
release = [model.add_variable(lb=0.0) for _ in hours]
model.maximize(sum([release[h] * price_values[h] for h in hours]))
model.add_linear_constraint(sum([release[h] for h in hours]) == TARGET)
for h in hours:
    model.add_linear_constraint(release[h] >= min_release)
    model.add_linear_constraint(release[h] - release[h - 1] <= max_ramp_up)
    model.add_linear_constraint(release[h] - release[h - 1] >= -max_ramp_down)

params = mathopt.SolveParameters(enable_output=False)
result = mathopt.solve(model, mathopt.SolverType.GLOP, params=params)
optimal_value = 0
if result.termination.reason == mathopt.TerminationReason.OPTIMAL:
    optimal_value = result.objective_value()

def get_bg_color(game):
    return (30, 30, 30) if game['dark_mode'] else (255, 255, 255)

def get_text_color(game):
    return (255, 255, 255) if game['dark_mode'] else (0, 0, 0)

def get_panel_color(game):
    return (80, 80, 80) if game['dark_mode'] else (200, 200, 200)

def get_button_color(game):
    return (100, 100, 100) if game['dark_mode'] else (180, 180, 200)

def get_button_outline_color(game):
    return (255, 255, 255) if game['dark_mode'] else (0, 0, 0)

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
#preload dam frames
frames = load_frames(NUM_FRAMES, FRAME_PATH_TEMPLATE)

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

def reset_level1():
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
def reset_level2():
    return {
        'window_width': 800,
        'window_height': 600,
        'screen': 0,
        'clock': 0, 
        'running': True,
        'font': pygame.font.SysFont(None, 24),
        'large_font': pygame.font.SysFont(None, 32),
    # Flags and messages.
        'show_instructions': False,
        'message': "",
        'dark_mode': False,
        'level_complete': False,
        'best_optimality': 0,
    # Button animation settings.
        'button_anim_duration': 0.2,
        'button_animations': {},
    # Initial hourly releases.
        'y_values': 0.2 * np.ones(24),
        'selected_bar': None,
        'dragging': False,
        'last_mouse_y': None,
        'start_time': time.time(),
        'solution_checked': False,
        'try_again_button_rect': None,
    # Metrics placeholders.
        'total_sum': 0,
        'total_revenue': 0,
        'maximum_ramp_up_rate': 0,
        'maximum_ramp_down_rate': 0,
        'feasible_solution': False
    }

def draw_dashed_line(surface, color, start_pos, end_pos, width=1, dash_length=10, space_length=5):
    x1, y1 = start_pos
    x2, y2 = end_pos
    dx = x2 - x1
    dy = y2 - y1
    line_length = (dx**2 + dy**2) ** 0.5
    dash_gap = dash_length + space_length
    num_dashes = int(line_length / dash_gap)
    for i in range(num_dashes + 1):
        start_fraction = i * dash_gap / line_length
        end_fraction = min((i * dash_gap + dash_length) / line_length, 1)
        start_x = x1 + dx * start_fraction
        start_y = y1 + dy * start_fraction
        end_x = x1 + dx * end_fraction
        end_y = y1 + dy * end_fraction
        pygame.draw.line(surface, color, (start_x, start_y), (end_x, end_y), width)

def update_layout(game):
    # We calculate the window size from our fixed screen.
    game['window_width'], game['window_height'] = game['screen'].get_size()
    new_font_size = max(12, int(min(game['window_width'], game['window_height']) / 50))
    new_large_font_size = max(16, int(min(game['window_width'], game['window_height']) / 35))
    game['font'] = pygame.font.SysFont(None, new_font_size)
    game['large_font'] = pygame.font.SysFont(None, new_large_font_size)

    game['instructions_area'] = pygame.Rect(int(game['window_width'] * 0.04),
                                            int(game['window_height'] * 0.01),
                                            int(game['window_width'] * 0.92),
                                            int(game['window_height'] * 0.06))
    game['bar_graph_area'] = pygame.Rect(int(game['window_width'] * 0.08),
                                         int(game['window_height'] * 0.15),
                                         int(game['window_width'] * 0.83),
                                         int(game['window_height'] * 0.45))
    game['button_area'] = pygame.Rect(game['bar_graph_area'].x,
                                      int(game['window_height'] * 0.08),
                                      game['bar_graph_area'].width,
                                      int(game['window_height'] * 0.07))
    game['total_panel_area'] = pygame.Rect(int(game['window_width'] * 0.08),
                                           int(game['window_height'] * 0.69),
                                           int(game['window_width'] * 0.83),
                                           int(game['window_height'] * 0.15))

    button_width = int(150 * game['window_width'] / 1200)
    gap = int(50 * game['window_width'] / 1200)
    button_labels = ["Restart", "Check Solution", "Instructions", "Dark Mode"]
    total_buttons_width = len(button_labels) * button_width + (len(button_labels) - 1) * gap
    start_x = game['button_area'].x + (game['button_area'].width - total_buttons_width) // 2

    button_height = int(40 * game['window_height'] / 900)
    button_y = game['button_area'].y + (game['button_area'].height - button_height) // 2
    buttons = {}
    for i, label in enumerate(button_labels):
        buttons[label] = pygame.Rect(start_x + i * (button_width + gap),
                                     button_y, button_width, button_height)
    game['buttons'] = buttons

    panel_margin = int(10 * game['window_width'] / 1200)
    labels = ["Total revenue ($)", "Total release (AF)", "Maximum ramp up", "Maximum ramp down"]
    panel_count = len(labels)
    panel_width = (game['total_panel_area'].width - (panel_count - 1) * panel_margin) // panel_count
    panel_height = game['total_panel_area'].height
    total_bar_graphs = {}
    for i, label in enumerate(labels):
        x = game['total_panel_area'].x + i * (panel_width + panel_margin)
        y = game['total_panel_area'].y
        total_bar_graphs[label] = pygame.Rect(x, y, panel_width, panel_height)
    game['total_bar_graphs'] = total_bar_graphs

    # Define the exit button rectangle relative to the window size.
    exit_width = int(80 * game['window_width'] / 800)
    exit_height = int(40 * game['window_height'] / 600)
    game['exit_button_rect'] = pygame.Rect(int(game['window_width'] * 0.02),
                                             int(game['window_height'] * 0.02),
                                             exit_width, exit_height)
    
def update_metrics(game):
    game['total_sum'] = np.sum(game['y_values'])
    game['total_revenue'] = np.sum(game['y_values'] * price_values)
    game['minimum_release_rate'] = np.min(game['y_values'])
    if len(game['y_values']) > 1:
        ramp_rate = game['y_values'][1:] - game['y_values'][:-1]
        game['maximum_ramp_up_rate'] = np.max(ramp_rate)
        game['maximum_ramp_down_rate'] = np.max(-ramp_rate)
    else:
        game['maximum_ramp_up_rate'] = 0
        game['maximum_ramp_down_rate'] = 0
    game['feasible_total_sum'] = abs(game['total_sum'] - TARGET) <= target_tol
    game['feasible_ramp_up'] = game['maximum_ramp_up_rate'] <= (max_ramp_up + 0.1 * target_tol)
    game['feasible_ramp_down'] = game['maximum_ramp_down_rate'] <= (max_ramp_down + 0.1 * target_tol)
    game['feasible_solution'] = (game['feasible_total_sum'] and game['feasible_ramp_up'] and game['feasible_ramp_down'])

def draw_timer(game):
    elapsed = time.time() - game['start_time']
    timer_text = game['font'].render(f"Time: {int(elapsed)}s", True, get_text_color(game))
    timer_rect = timer_text.get_rect(topright=(
        game['window_width'] - int((20/800)*game['window_width']),
        int((20/600)*game['window_height'])
    ))
    game['screen'].blit(timer_text, timer_rect)
    revenue_pct = 0
    if optimal_value:
        revenue_pct = 100 * game['total_revenue'] / optimal_value
    if game['feasible_solution'] and revenue_pct <= 100:
        pct_str = f"Optimality: {revenue_pct:.0f}%"
    else:
        pct_str = "Optimality: --"
    pct_text = game['font'].render(pct_str, True, get_text_color(game))
    pct_rect = pct_text.get_rect(topright=(
        game['window_width'] - int((20/800)*game['window_width']),
        timer_rect.bottom + int((5/600)*game['window_height'])
    ))
    game['screen'].blit(pct_text, pct_rect)
    # Only display "Best:" if solution is checked and feasible; otherwise show "--"
    if game['solution_checked'] and game['feasible_solution']:
        best_str = f"Best: {game.get('best_optimality', 0):.0f}%"
    else:
        best_str = "Best: --"
    best_text = game['font'].render(best_str, True, get_text_color(game))
    best_rect = best_text.get_rect(topright=(
        game['window_width'] - int((20/800)*game['window_width']),
        pct_rect.bottom + int((5/600)*game['window_height'])
    ))
    game['screen'].blit(best_text, best_rect)
    feas_text = "Feasible!" if (game['feasible_solution']) else "Infeasible"
    feas_color = (0, 200, 0) if (game['feasible_solution']) else (200, 0, 0)
    feas_line = game['font'].render(feas_text, True, feas_color)
    feas_rect = feas_line.get_rect(topright=(
        game['window_width'] - int((20/800)*game['window_width']),
        best_rect.bottom + int((5/600)*game['window_height'])
    ))
    game['screen'].blit(feas_line, feas_rect)

def draw_bar_graph(game):
    screen = game['screen']
    bar_graph_area = game['bar_graph_area']
    pygame.draw.rect(screen, get_panel_color(game), bar_graph_area, 2)
    max_value = 2.5
    pygame.draw.line(screen, get_text_color(game),
                     (bar_graph_area.x, bar_graph_area.y),
                     (bar_graph_area.x, bar_graph_area.y + bar_graph_area.height), 2)
    tick_interval = 0.5
    num_ticks = int(max_value / tick_interval) + 1
    for i in range(num_ticks):
        tick_value = i * tick_interval
        y = bar_graph_area.y + bar_graph_area.height - (tick_value / max_value) * bar_graph_area.height
        pygame.draw.line(screen, get_text_color(game),
                         (bar_graph_area.x - int((5/800)*game['window_width']), y),
                         (bar_graph_area.x, y), 2)
        tick_label = game['font'].render(f"{tick_value:.1f}", True, get_text_color(game))
        screen.blit(tick_label, (bar_graph_area.x - int((35/800)*game['window_width']), y - int((10/600)*game['window_height'])))
    pygame.draw.line(screen, get_text_color(game),
                     (bar_graph_area.x, bar_graph_area.y + bar_graph_area.height),
                     (bar_graph_area.x + bar_graph_area.width, bar_graph_area.y + bar_graph_area.height), 2)
    # Draw the bars.
    left_margin = int((5/800)*game['window_width'])
    available_width = bar_graph_area.width - left_margin
    bar_width = available_width / N_timesteps
    for i in range(N_timesteps):
        x = int(bar_graph_area.x + left_margin + i * bar_width)
        value = game['y_values'][i]
        bar_height = int((value / max_value) * bar_graph_area.height)
        y = int(bar_graph_area.y + bar_graph_area.height - bar_height)
        color = (31, 119, 180)
        pygame.draw.rect(screen, color, (x, y, int(bar_width) - 2, bar_height))
        text = game['font'].render(f"{value:.2f}", True, get_text_color(game))
        text_rect = text.get_rect(center=(x + bar_width / 2, y - int((10/600)*game['window_height'])))
        screen.blit(text, text_rect)

    # Draw price points.
    price_points = []
    for i in range(N_timesteps):
        x = bar_graph_area.x + left_margin + (i + 0.5) * bar_width
        y = bar_graph_area.y + bar_graph_area.height - (price_values[i] / max_value) * bar_graph_area.height
        price_points.append((x, y))
    if len(price_points) >= 2:
        pygame.draw.lines(screen, get_text_color(game), False, price_points, 2)

    # Draw dashed lines (thresholds) after drawing bars & price points so they appear on top.
    dashed_y_0_2 = bar_graph_area.y + bar_graph_area.height - (0.2 / max_value) * bar_graph_area.height
    dashed_y_2_0 = bar_graph_area.y + bar_graph_area.height - (2.0 / max_value) * bar_graph_area.height
    draw_dashed_line(screen, get_text_color(game),
                     (bar_graph_area.x, dashed_y_0_2),
                     (bar_graph_area.x + bar_graph_area.width, dashed_y_0_2),
                     width=2, dash_length=5, space_length=3)
    draw_dashed_line(screen, get_text_color(game),
                     (bar_graph_area.x, dashed_y_2_0),
                     (bar_graph_area.x + bar_graph_area.width, dashed_y_2_0),
                     width=2, dash_length=5, space_length=3)
    
    # Dynamically size the legend based on the bar graph dimensions.
    legend_width = int(game['bar_graph_area'].width * 0.2)
    legend_height = int(game['bar_graph_area'].height * 0.15)
    legend_x = game['bar_graph_area'].right - legend_width - int((0.02)*game['window_width'])
    legend_y = game['bar_graph_area'].y + int((0.02)*game['window_height'])
    legend_rect = pygame.Rect(legend_x, legend_y, legend_width, legend_height)
    pygame.draw.rect(screen, get_panel_color(game), legend_rect)
    pygame.draw.rect(screen, get_text_color(game), legend_rect, 2)
    dash_start = (legend_rect.x + int((0.07)*legend_width), legend_rect.y + int((0.3)*legend_height))
    dash_end = (legend_rect.x + int((0.2)*legend_width), legend_rect.y + int((0.3)*legend_height))
    draw_dashed_line(screen, get_text_color(game), dash_start, dash_end, width=2, dash_length=4, space_length=3)
    price_text = game['font'].render("Release limit (AF/hr)", True, get_text_color(game))
    screen.blit(price_text, (legend_rect.x + int((0.3)*legend_width), legend_rect.y + int((0.2)*legend_height)))
    pygame.draw.rect(screen, (31, 119, 180), (legend_rect.x + int((0.07)*legend_width), legend_rect.y + int((0.6)*legend_height), int((0.15)*legend_width), int((0.3)*legend_height)))
    rel_text = game['font'].render("Releases (AF)", True, get_text_color(game))
    screen.blit(rel_text, (legend_rect.x + int((0.3)*legend_width), legend_rect.y + int((0.7)*legend_height)))
    
    # Draw x-axis ticks and labels.
    x_ticks = [0, 5, 10, 15, 20]
    for tick in x_ticks:
        tick_x = bar_graph_area.x + left_margin + (tick + 0.5) * bar_width
        pygame.draw.line(screen, get_text_color(game),
                         (tick_x, bar_graph_area.y + bar_graph_area.height),
                         (tick_x, bar_graph_area.y + bar_graph_area.height + int((5/600)*game['window_height'])), 2)
        tick_label = game['font'].render(str(tick), True, get_text_color(game))
        screen.blit(tick_label, (tick_x - tick_label.get_width() // 2,
                                  bar_graph_area.y + bar_graph_area.height + int((8/600)*game['window_height'])))

    x_axis_title = game['font'].render("Hours", True, get_text_color(game))
    x_title_rect = x_axis_title.get_rect(center=(bar_graph_area.centerx,
                                                 bar_graph_area.y + bar_graph_area.height + int((30/600)*game['window_height'])))
    screen.blit(x_axis_title, x_title_rect)
    y_axis_title = game['font'].render("Hourly release (AF/hr)", True, get_text_color(game))
    y_axis_title_rotated = pygame.transform.rotate(y_axis_title, 90)
    y_title_rect = y_axis_title_rotated.get_rect(center=(bar_graph_area.x - int((50/800)*game['window_width']),
                                                         bar_graph_area.centery))
    screen.blit(y_axis_title_rotated, y_title_rect)

def draw_total_bars(game):
    screen = game['screen']
    total_bar_graphs = game['total_bar_graphs']
    metrics = {
        "Total revenue ($)": (game['total_revenue'], optimal_value, "Optimal value"),
        "Total release (AF)": (game['total_sum'], TARGET, "Daily target"),
        "Maximum ramp up": (game['maximum_ramp_up_rate'], max_ramp_up, "Ramp up limit"),
        "Maximum ramp down": (game['maximum_ramp_down_rate'], max_ramp_down, "Ramp down limit"),
    }
    for key, rect in total_bar_graphs.items():
        if key not in metrics:
            continue
        value, target_value, target_name = metrics[key]
        pygame.draw.rect(screen, get_panel_color(game), rect, 2)
        max_display = target_value * 1.5 if target_value != 0 else 1
        calculated_bar_height = (value / max_display) * rect.height
        bar_height = min(calculated_bar_height, rect.height)
        bar_bottom_y = rect.y + rect.height
        bar_rect = pygame.Rect(
            rect.x + int((10/800)*game['window_width']),
            bar_bottom_y - bar_height,
            rect.width - int((20/800)*game['window_width']),
            bar_height
        )

        if key == "Total revenue ($)":
            color = (31, 119, 180)
            if abs(value - target_value) <= target_tol:
                color = (0, 200, 0)
        elif key == "Total release (AF)":
            color = (0, 200, 0) if abs(value - target_value) <= target_tol else (200, 0, 0)
        elif key == "Maximum ramp up":
            color = (200, 0, 0)
            if value <= (target_value + 0.1 * target_tol):
                color = (0, 200, 0)
        elif key == "Maximum ramp down":
            color = (200, 0, 0)
            if value <= (target_value + 0.1 * target_tol):
                color = (0, 200, 0)

        pygame.draw.rect(screen, color, bar_rect)
        axis_y = rect.y + rect.height - (target_value / max_display) * rect.height
        draw_dashed_line(screen, get_text_color(game),
                         (rect.x, axis_y),
                         (rect.x + rect.width, axis_y),
                         width=2, dash_length=10, space_length=5)
        label = game['font'].render(f"{key}", True, get_text_color(game))
        label_rect = label.get_rect(center=(rect.centerx, rect.y - int((10/600)*game['window_height'])))
        screen.blit(label, label_rect)
        target_label = game['font'].render(target_name, True, get_text_color(game))
        target_label_rect = target_label.get_rect(center=(rect.centerx, axis_y - int((10/600)*game['window_height'])))
        screen.blit(target_label, target_label_rect)

def draw_buttons(game):
    screen = game['screen']
    # Draw standard buttons.
    for label, rect in game['buttons'].items():
        anim_scale = 1.0
        if label in game['button_animations']:
            elapsed = time.time() - game['button_animations'][label]
            if elapsed < game['button_anim_duration']:
                progress = elapsed / game['button_anim_duration']
                if progress < 0.5:
                    anim_scale = 1 - 0.1 * (progress / 0.5)
                else:
                    anim_scale = 0.9 + 0.1 * ((progress - 0.5) / 0.5)
            else:
                del game['button_animations'][label]
        scaled_width = int(rect.width * anim_scale)
        scaled_height = int(rect.height * anim_scale)
        scaled_rect = pygame.Rect(0, 0, scaled_width, scaled_height)
        scaled_rect.center = rect.center
        pygame.draw.rect(screen, get_button_color(game), scaled_rect)
        pygame.draw.rect(screen, get_button_outline_color(game), scaled_rect, 2)
        display_label = label
        if label == "Dark Mode":
            display_label = f"Dark Mode: {'On' if game['dark_mode'] else 'Off'}"
        text = game['font'].render(display_label, True, get_text_color(game))
        text_rect = text.get_rect(center=scaled_rect.center)
        screen.blit(text, text_rect)

    # Draw clickable red exit button with animation.
    if "Exit" in game['button_animations']:
        elapsed = time.time() - game['button_animations']["Exit"]
        if elapsed < game['button_anim_duration']:
            progress = elapsed / game['button_anim_duration']
            if progress < 0.5:
                exit_scale = 1 - 0.1 * (progress / 0.5)
            else:
                exit_scale = 0.9 + 0.1 * ((progress - 0.5) / 0.5)
        else:
            del game['button_animations']["Exit"]
            exit_scale = 1.0
    else:
        exit_scale = 1.0

    exit_rect_orig = game['exit_button_rect']
    scaled_exit_width = int(exit_rect_orig.width * exit_scale)
    scaled_exit_height = int(exit_rect_orig.height * exit_scale)
    scaled_exit_rect = pygame.Rect(0, 0, scaled_exit_width, scaled_exit_height)
    scaled_exit_rect.center = exit_rect_orig.center
    pygame.draw.rect(screen, (200, 0, 0), scaled_exit_rect)  # Red fill.
    pygame.draw.rect(screen, (255, 255, 255), scaled_exit_rect, 2)  # White outline.
    exit_text = game['font'].render("Exit", True, (255, 255, 255))
    exit_text_rect = exit_text.get_rect(center=scaled_exit_rect.center)
    screen.blit(exit_text, exit_text_rect)

def draw_message(game):
    if game['message']:
        overlay = pygame.Surface((game['window_width'], game['window_height']), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        game['screen'].blit(overlay, (0, 0))
        lines = game['message'].split("\n")
        text_rects = []
        for i, line in enumerate(lines):
            text = game['large_font'].render(line, True, (255, 255, 255))
            # Render each line with a vertical offset proportional to the window height.
            text_rect = text.get_rect(center=(game['window_width'] // 2,
                                              game['window_height'] // 2 - int((50/600)*game['window_height']) + i * int((40/600)*game['window_height'])))
            game['screen'].blit(text, text_rect)
            text_rects.append(text_rect)
        # Place the Close button below the message text block.
        if text_rects:
            btn_y = max(rect.bottom for rect in text_rects) + int((40/600)*game['window_height'])
        else:
            btn_y = game['window_height'] // 2 + int((90/600)*game['window_height'])
        btn_label = "Close"
        btn_width = int(150 * game['window_width'] / 1200)
        btn_height = int(40 * game['window_height'] / 900)
        btn_x = (game['window_width'] - btn_width) // 2
        game['try_again_button_rect'] = pygame.Rect(btn_x, btn_y, btn_width, btn_height)
        pygame.draw.rect(game['screen'], get_button_color(game), game['try_again_button_rect'])
        pygame.draw.rect(game['screen'], get_button_outline_color(game), game['try_again_button_rect'], 2)
        btn_text = game['font'].render(btn_label, True, get_text_color(game))
        btn_text_rect = btn_text.get_rect(center=game['try_again_button_rect'].center)
        game['screen'].blit(btn_text, btn_text_rect)
        if game.get('level_complete'):
            lc_label = "Level Complete"
            lc_btn_width = int(150 * game['window_width'] / 1200)
            lc_btn_height = int(40 * game['window_height'] / 900)
            lc_btn_x = (game['window_width'] - lc_btn_width) // 2
            lc_btn_y = btn_y + lc_btn_height + int((10/600)*game['window_height'])
            game['level_complete_button_rect'] = pygame.Rect(lc_btn_x, lc_btn_y, lc_btn_width, lc_btn_height)
            pygame.draw.rect(game['screen'], get_button_color(game), game['level_complete_button_rect'])
            pygame.draw.rect(game['screen'], get_button_outline_color(game), game['level_complete_button_rect'], 2)
            lc_text = game['font'].render(lc_label, True, get_text_color(game))
            lc_text_rect = lc_text.get_rect(center=game['level_complete_button_rect'].center)
            game['screen'].blit(lc_text, lc_text_rect)

def handle_button_click(game, pos):
    for label, rect in game['buttons'].items():
        if rect.collidepoint(pos):
            game['button_animations'][label] = time.time()
            if label == "Restart":
                start_action(game)
            elif label == "Check Solution":
                check_action(game)
            elif label == "Instructions":
                game['show_instructions'] = True
                game['message'] = "\n".join(textwrap.wrap(
                    "Find the best hydropower revenue by changing the hourly releases. "
                    "Ensure all environmental rules are met: daily target, minimum release, "
                    "maximum ramp up, and maximum ramp down. To complete the level, you must obtain "
                    "both a feasible solution and at least a 90% optimality.", width=80))
            elif label == "Dark Mode":
                game['dark_mode'] = not game['dark_mode']
            return
        
def start_action(game):
    game['y_values'] = 0.2 * np.ones(N_timesteps)
    game['solution_checked'] = False
    game['start_time'] = time.time()
    game['message'] = ""
    game['show_instructions'] = False
    game['level_complete'] = False

def check_action(game):
    update_metrics(game)
    time_to_find = time.time() - game['start_time']
    revenue_pct = 100 * game['total_revenue'] / optimal_value if optimal_value else 0
    if game['feasible_solution']:
        if revenue_pct >= 90:
            game['message'] = (f"Solution is feasible! You reached >90% optimality!\nTime: {time_to_find:.0f}s\nOptimality: {revenue_pct:.0f}%")
            if revenue_pct > game.get('best_optimality', 0):
                game['best_optimality'] = revenue_pct
        else:
            game['message'] = (f"Solution is feasible! However, you need to achieve at least a 90% optimality. Try again!\nTime: {time_to_find:.0f}s")
    else:
        game['message'] = (f"Solution is not feasible. Try again!\nTime: {time_to_find:.0f}s")
    
    game['solution_checked'] = True
    game['level_complete'] = game['feasible_solution'] and (revenue_pct >= 90)
    # Do not reset the timer here.

def change_screen_size_level2(game, width, height):
    game['window_width'] = width
    game['window_height'] = height
    game['screen'] = pygame.display.set_mode((width, height))
    update_layout(game)

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

def credits_screen():
    screen.fill(BACKGROUND_COLOR)
    
    # Create a semi-transparent overlay
    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
    overlay.set_alpha(200)  # Set transparency level
    overlay.fill(BLACK)
    screen.blit(overlay, (0, 0))
    
    # Display credits text
    credits_text = "credit to REDi Island, NREL, IKM, etc…"
    credits_label = FONT.render(credits_text, True, WHITE)
    screen.blit(credits_label, ((WINDOW_WIDTH - credits_label.get_width()) // 2, WINDOW_HEIGHT // 2))
    
    # Draw the exit button
    exit_button = pygame.Rect(0.0188*WINDOW_WIDTH, 0.0167*WINDOW_HEIGHT, 0.075*WINDOW_WIDTH, 0.0583*WINDOW_HEIGHT)
    pygame.draw.rect(screen, RED, exit_button)
    draw_text("Exit", 0.025*WINDOW_WIDTH, 0.0233*WINDOW_HEIGHT, WHITE)
    
    return exit_button

# Modify the main_menu function to add the "Credits" button
def main_menu():
    screen.fill(BACKGROUND_COLOR)
    screen.blit(scaled_intro_image, (0, 0))
    draw_text(TITLE, 270, 100, BLUE)

    level_select_button = pygame.Rect(325, 300, 150, 50)
    pygame.draw.rect(screen, GREEN, level_select_button)
    draw_text("Level Select", 328, 310, WHITE)

    credits_button = pygame.Rect(325, 370, 150, 50)  # Position below the level select button
    pygame.draw.rect(screen, BLUE, credits_button)
    draw_text("Credits", 348, 380, WHITE)

    return level_select_button, credits_button

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
    SCREEN_HEIGHT = screen.get_height()
    SCREEN_WIDTH = screen.get_width()
    global WINDOW_MODE, monitor_image, flow_image

    game_state = reset_level1()
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

            sine_value = 2 * np.sin(game_state['x_start'] + 0.5) + 6

            load_difference = truncate_float(power_generated - sine_value, 2)

            performance_text = f"Load Difference: {load_difference} MW"
            performance_label = performance_font.render(performance_text, True, (0, 0, 0))

            performance_x = (SCREEN_WIDTH - performance_label.get_width()) // 2
            performance_y = 10

            screen.blit(performance_label, (performance_x, performance_y))
            abs_load_difference = abs(load_difference)

            game_state['score'] += abs_load_difference

            # Render the score text
            score_text = f"Average Power Imbalance: {int(game_state['score']/game_state['elapsed_time'])} MW"
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
    game = reset_level2()
    game['screen'] = pygame.display.set_mode((game['window_width'], game['window_height']))
    game['clock'] =  pygame.time.Clock()
    if level_best_times[1] <= 100:
        game['best_optimality'] = level_best_times[1]
    while game['running']:
        update_layout(game) 
        handle_events_level2(game)
        update_metrics(game)
        game['screen'].fill(get_bg_color(game))
        draw_buttons(game)
        draw_bar_graph(game)
        draw_total_bars(game)
        draw_timer(game)
        draw_message(game)
        pygame.display.flip()
        game['clock'].tick(60)
    if game['level_complete']:
        complete_level(2)
        level_best_times[1] = game['best_optimality']

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

def handle_events_level2(game):
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                pos = event.pos
                # Check if the exit button was clicked.
                if game['exit_button_rect'].collidepoint(pos):
                    game['button_animations']["Exit"] = time.time()
                    game['running'] = False
                    break

                if game['message']:
                    if (game.get('try_again_button_rect')
                            and game['try_again_button_rect'].collidepoint(pos)):
                        game['message'] = ""
                        game['show_instructions'] = False
                        continue
                    if (game.get('level_complete_button_rect')
                            and game['level_complete_button_rect'].collidepoint(pos)):
                        game['level_complete'] = True
                        game['running'] = False
                        continue
                if game['button_area'].collidepoint(pos):
                    handle_button_click(game, pos)
                elif game['bar_graph_area'].collidepoint(pos):
                    bar_width = game['bar_graph_area'].width / N_timesteps
                    rel_x = pos[0] - game['bar_graph_area'].x
                    bar_index = int(rel_x // bar_width)
                    if 0 <= bar_index < N_timesteps:
                        game['selected_bar'] = bar_index
                        game['dragging'] = True
                        game['last_mouse_y'] = pos[1]

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                game['dragging'] = False
                game['selected_bar'] = None

        elif event.type == pygame.MOUSEMOTION:
            if game['dragging'] and game['selected_bar'] is not None:
                dy = game['last_mouse_y'] - event.pos[1]
                sensitivity = 0.005
                delta = dy * sensitivity
                new_value = np.clip(game['y_values'][game['selected_bar']] + delta, 0.2, 2.0)
                game['y_values'][game['selected_bar']] = new_value
                game['last_mouse_y'] = event.pos[1]

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1:
                change_screen_size_level2(game, 800, 600)
            elif event.key == pygame.K_2:
                change_screen_size_level2(game, 1024, 768)
            elif event.key == pygame.K_3:
                change_screen_size_level2(game, 1920, 1080)
            elif event.key == pygame.K_ESCAPE:
                game['message'] = ""
                game['show_instructions'] = False

def handle_events():
    global current_screen, current_text_box, clicked_objects
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            save_game_data()
            pygame.quit()
            sys.exit()

        if current_screen == "main_menu":
            if event.type == pygame.MOUSEBUTTONDOWN:
                level_select_button, credits_button = main_menu()
                if level_select_button.collidepoint(event.pos):
                    current_screen = "level_select"
                elif credits_button.collidepoint(event.pos):
                    current_screen = "credits"

        elif current_screen == "credits":
            if event.type == pygame.MOUSEBUTTONDOWN:
                exit_button = credits_screen()
                if exit_button.collidepoint(event.pos):
                    current_screen = "main_menu"

        elif current_screen == "level_select":
            if event.type == pygame.MOUSEBUTTONDOWN:
                buttons = level_select()
                for i, (button, accessible) in enumerate(buttons):
                    if button.collidepoint(event.pos) and accessible:
                        current_screen = f"level_{i + 1}"
                        reset_level3()
                        reset_level4()
                        break

        elif current_screen.startswith("level_"):
            level_number = int(current_screen.split("_")[1])

            if level_number == 3:
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
        elif current_screen == "credits":
            credits_screen()
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
                current_screen = "level_select"
            elif level_number == 3:
                level3()
            elif level_number == 4:
                level4()

        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()