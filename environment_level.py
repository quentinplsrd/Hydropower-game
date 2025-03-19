import time
import numpy as np
import pygame
import textwrap
from ortools.math_opt.python import mathopt

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

# Global simulation parameters and OR-Tools model setup.
N_timesteps = 24
hours = np.arange(N_timesteps)
TARGET = 4.8  # Daily release value
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

# Helper functions for colors.
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

# Initialize game state in a dictionary.
def init_game():
    pygame.init()
    game = {}
    game['window_width'] = 800
    game['window_height'] = 600
    game['screen'] = pygame.display.set_mode((game['window_width'], game['window_height']), pygame.RESIZABLE)
    pygame.display.set_caption("Hydropower Game")
    game['clock'] = pygame.time.Clock()
    game['running'] = True

    # Initialize fonts.
    game['font'] = pygame.font.SysFont(None, 24)
    game['large_font'] = pygame.font.SysFont(None, 32)

    # Flags and messages.
    game['show_instructions'] = False
    game['message'] = ""
    game['dark_mode'] = False
    game['level_complete'] = False  # New flag
    game['best_optimality'] = 0     # Track best optimality score

    # Remove credits-related items.

    # Button animation settings.
    game['button_anim_duration'] = 0.2  # seconds
    game['button_animations'] = {}

    update_layout(game)

    # Initial hourly releases.
    game['y_values'] = (TARGET / N_timesteps) * np.ones(N_timesteps)
    game['selected_bar'] = None
    game['dragging'] = False
    game['last_mouse_y'] = None

    game['start_time'] = time.time()
    game['solution_checked'] = False
    game['try_again_button_rect'] = None

    # Metrics placeholders.
    game['total_sum'] = 0
    game['total_revenue'] = 0
    game['minimum_release_rate'] = 0
    game['maximum_ramp_up_rate'] = 0
    game['maximum_ramp_down_rate'] = 0
    game['feasible_solution'] = False

    return game

def update_layout(game):
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
    # Removed credit_area.
    
    button_width = int(150 * game['window_width'] / 1200)
    gap = int(50 * game['window_width'] / 1200)
    # Removed "Optimize" from the list.
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
    # Remove the "Minimum release (AF/hr)" bar by excluding it from the labels.
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
    game['feasible_min_release'] = game['minimum_release_rate'] >= (min_release - 0.1 * target_tol)
    game['feasible_ramp_up'] = game['maximum_ramp_up_rate'] <= (max_ramp_up + 0.1 * target_tol)
    game['feasible_ramp_down'] = game['maximum_ramp_down_rate'] <= (max_ramp_down + 0.1 * target_tol)
    game['feasible_solution'] = (game['feasible_total_sum'] and game['feasible_min_release'] and
                                 game['feasible_ramp_up'] and game['feasible_ramp_down'])

def draw_timer(game):
    elapsed = time.time() - game['start_time']
    timer_text = game['font'].render(f"Time: {int(elapsed)}s", True, get_text_color(game))
    timer_rect = timer_text.get_rect(topright=(game['window_width'] - 20, 20))
    game['screen'].blit(timer_text, timer_rect)
    revenue_pct = 0
    if optimal_value:
        revenue_pct = 100 * game['total_revenue'] / optimal_value
    pct_text = game['font'].render(f"Optimality: {revenue_pct:.0f}%", True, get_text_color(game))
    pct_rect = pct_text.get_rect(topright=(game['window_width'] - 20, timer_rect.bottom + 5))
    game['screen'].blit(pct_text, pct_rect)
    # Display best optimality score.
    best_text = game['font'].render(f"Best: {game.get('best_optimality', 0):.0f}%", True, get_text_color(game))
    best_rect = best_text.get_rect(topright=(game['window_width'] - 20, pct_rect.bottom + 5))
    game['screen'].blit(best_text, best_rect)
    feas_text = "Feasible!" if game['feasible_solution'] else "Infeasible"
    feas_color = (0, 200, 0) if game['feasible_solution'] else (200, 0, 0)
    feas_line = game['font'].render(feas_text, True, feas_color)
    feas_rect = feas_line.get_rect(topright=(game['window_width'] - 20, best_rect.bottom + 5))
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
                         (bar_graph_area.x - 5, y),
                         (bar_graph_area.x, y), 2)
        tick_label = game['font'].render(f"{tick_value:.1f}", True, get_text_color(game))
        screen.blit(tick_label, (bar_graph_area.x - 35, y - 10))
    pygame.draw.line(screen, get_text_color(game),
                     (bar_graph_area.x, bar_graph_area.y + bar_graph_area.height),
                     (bar_graph_area.x + bar_graph_area.width, bar_graph_area.y + bar_graph_area.height), 2)
    
    # Add dashed horizontal lines at data value 0.2 and 2.0.
    dashed_y_0_2 = bar_graph_area.y + bar_graph_area.height - (0.2 / max_value) * bar_graph_area.height
    dashed_y_2_0 = bar_graph_area.y + bar_graph_area.height - (2.0 / max_value) * bar_graph_area.height
    draw_dashed_line(screen, get_text_color(game), (bar_graph_area.x, dashed_y_0_2), (bar_graph_area.x+bar_graph_area.width, dashed_y_0_2), width=2, dash_length=5, space_length=3)
    draw_dashed_line(screen, get_text_color(game), (bar_graph_area.x, dashed_y_2_0), (bar_graph_area.x+bar_graph_area.width, dashed_y_2_0), width=2, dash_length=5, space_length=3)
    
    left_margin = 5
    available_width = bar_graph_area.width - left_margin
    bar_width = available_width / N_timesteps
    x_ticks = [0, 5, 10, 15, 20]
    for tick in x_ticks:
        tick_x = bar_graph_area.x + left_margin + (tick + 0.5) * bar_width
        pygame.draw.line(screen, get_text_color(game),
                         (tick_x, bar_graph_area.y + bar_graph_area.height),
                         (tick_x, bar_graph_area.y + bar_graph_area.height + 5), 2)
        tick_label = game['font'].render(str(tick), True, get_text_color(game))
        screen.blit(tick_label, (tick_x - tick_label.get_width() // 2,
                                  bar_graph_area.y + bar_graph_area.height + 8))
    x_axis_title = game['font'].render("Hours", True, get_text_color(game))
    x_title_rect = x_axis_title.get_rect(center=(bar_graph_area.centerx,
                                                   bar_graph_area.y + bar_graph_area.height + 30))
    screen.blit(x_axis_title, x_title_rect)
    y_axis_title = game['font'].render("Hourly release (AF/hr)", True, get_text_color(game))
    y_axis_title_rotated = pygame.transform.rotate(y_axis_title, 90)
    y_title_rect = y_axis_title_rotated.get_rect(center=(bar_graph_area.x - 50,
                                                         bar_graph_area.centery))
    screen.blit(y_axis_title_rotated, y_title_rect)
    for i in range(N_timesteps):
        x = int(bar_graph_area.x + left_margin + i * bar_width)
        value = game['y_values'][i]
        bar_height = int((value / max_value) * bar_graph_area.height)
        y = int(bar_graph_area.y + bar_graph_area.height - bar_height)
        color = (31, 119, 180)
        pygame.draw.rect(screen, color, (x, y, int(bar_width) - 2, bar_height))
        text = game['font'].render(f"{value:.2f}", True, get_text_color(game))
        text_rect = text.get_rect(center=(x + bar_width / 2, y - 10))
        screen.blit(text, text_rect)
    price_points = []
    for i in range(N_timesteps):
        x = bar_graph_area.x + left_margin + (i + 0.5) * bar_width
        y = bar_graph_area.y + bar_graph_area.height - (price_values[i] / max_value) * bar_graph_area.height
        price_points.append((x, y))
    if len(price_points) >= 2:
        pygame.draw.lines(screen, get_text_color(game), False, price_points, 2)
    legend_rect = pygame.Rect(bar_graph_area.right - 160, bar_graph_area.y + 10, 150, 50)
    pygame.draw.rect(screen, get_panel_color(game), legend_rect)
    pygame.draw.rect(screen, get_text_color(game), legend_rect, 2)
    dash_start = (legend_rect.x + 10, legend_rect.y + 15)
    dash_end = (legend_rect.x + 30, legend_rect.y + 15)
    draw_dashed_line(screen, get_text_color(game), dash_start, dash_end, width=2, dash_length=4, space_length=3)
    price_text = game['font'].render("Price ($/AF)", True, get_text_color(game))
    screen.blit(price_text, (legend_rect.x + 40, legend_rect.y + 10))
    pygame.draw.rect(screen, (31, 119, 180), (legend_rect.x + 10, legend_rect.y + 30, 20, 12.5))
    rel_text = game['font'].render("Releases (AF)", True, get_text_color(game))
    screen.blit(rel_text, (legend_rect.x + 40, legend_rect.y + 30))
    draw_timer(game)

def draw_total_bars(game):
    screen = game['screen']
    total_bar_graphs = game['total_bar_graphs']
    # Remove "Minimum release (AF/hr)" from the metrics.
    metrics = {
        "Total revenue ($)": (game['total_revenue'], optimal_value, "Optimal value"),
        "Total release (AF)": (game['total_sum'], TARGET, "Daily target"),
        "Maximum ramp up": (game['maximum_ramp_up_rate'], max_ramp_up, "Ramp up limit"),
        "Maximum ramp down": (game['maximum_ramp_down_rate'], max_ramp_down, "Ramp down limit"),
    }
    for key, rect in total_bar_graphs.items():
        # Only process keys that exist in the metrics dictionary.
        if key not in metrics:
            continue
        value, target_value, target_name = metrics[key]
        pygame.draw.rect(screen, get_panel_color(game), rect, 2)
        max_display = target_value * 1.5 if target_value != 0 else 1
        calculated_bar_height = (value / max_display) * rect.height
        bar_height = min(calculated_bar_height, rect.height)
        bar_bottom_y = rect.y + rect.height
        bar_rect = pygame.Rect(rect.x + 10, bar_bottom_y - bar_height, rect.width - 20, bar_height)
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
        label_rect = label.get_rect(center=(rect.centerx, rect.y - 10))
        screen.blit(label, label_rect)
        target_label = game['font'].render(target_name, True, get_text_color(game))
        target_label_rect = target_label.get_rect(center=(rect.centerx, axis_y - 10))
        screen.blit(target_label, target_label_rect)

def draw_buttons(game):
    screen = game['screen']
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
        
    # Removed Credits button and related code.
    
def draw_message(game):
    if game['message']:
        overlay = pygame.Surface((game['window_width'], game['window_height']), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        game['screen'].blit(overlay, (0, 0))
        lines = game['message'].split("\n")
        for i, line in enumerate(lines):
            text = game['large_font'].render(line, True, (255, 255, 255))
            text_rect = text.get_rect(center=(game['window_width'] // 2, game['window_height'] // 2 - 50 + i * 40))
            game['screen'].blit(text, text_rect)
        # Draw the "Close" button.
        btn_label = "Close"
        btn_width = int(150 * game['window_width'] / 1200)
        btn_height = int(40 * game['window_height'] / 900)
        btn_x = (game['window_width'] - btn_width) // 2
        btn_y = game['window_height'] // 2 + 90
        game['try_again_button_rect'] = pygame.Rect(btn_x, btn_y, btn_width, btn_height)
        pygame.draw.rect(game['screen'], get_button_color(game), game['try_again_button_rect'])
        pygame.draw.rect(game['screen'], get_button_outline_color(game), game['try_again_button_rect'], 2)
        btn_text = game['font'].render(btn_label, True, get_text_color(game))
        btn_text_rect = btn_text.get_rect(center=game['try_again_button_rect'].center)
        game['screen'].blit(btn_text, btn_text_rect)
        # If level complete flag is set, draw a Level Complete button below.
        if game.get('level_complete'):
            lc_label = "Level Complete"
            lc_btn_width = int(150 * game['window_width'] / 1200)
            lc_btn_height = int(40 * game['window_height'] / 900)
            lc_btn_x = (game['window_width'] - lc_btn_width) // 2
            lc_btn_y = btn_y + lc_btn_height + 10  # positioned below the Close button
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
                    "both a feasible solution and 90% optimality.", width=80))
            elif label == "Dark Mode":
                game['dark_mode'] = not game['dark_mode']
            return

def start_action(game):
    game['y_values'] = (TARGET / N_timesteps) * np.ones(N_timesteps)
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
        game['message'] = f"Solution is feasible!\nTime: {time_to_find:.0f}s\nOptimality: {revenue_pct:.0f}%"
        if revenue_pct > game.get('best_optimality', 0):
            game['best_optimality'] = revenue_pct
    else:
        game['message'] = f"Solution is not feasible, try again!\nTime: {time_to_find:.0f}s\nOptimality: {revenue_pct:.0f}%"
    
    game['solution_checked'] = True
    # Only set level complete if the solution is feasible and optimality is at least 90%.
    game['level_complete'] = game['feasible_solution'] and (revenue_pct >= 90)

def handle_events(game):
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            game['running'] = False
        elif event.type == pygame.VIDEORESIZE:
            game['window_width'] = event.w
            game['window_height'] = event.h
            game['screen'] = pygame.display.set_mode((game['window_width'], game['window_height']), pygame.RESIZABLE)
            update_layout(game)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                pos = event.pos
                # If a message overlay is shown, check for its buttons.
                if game['message']:
                    if game.get('try_again_button_rect') and game['try_again_button_rect'].collidepoint(pos):
                        game['message'] = ""
                        game['show_instructions'] = False
                        continue
                    if game.get('level_complete_button_rect') and game['level_complete_button_rect'].collidepoint(pos):
                        # Level complete button clicked: display a congratulatory message
                        game['level_complete'] = False
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
                # Enforce bar values remain between 0.2 and 2.0
                new_value = np.clip(game['y_values'][game['selected_bar']] + delta, 0.2, 2.0)
                game['y_values'][game['selected_bar']] = new_value
                game['last_mouse_y'] = event.pos[1]
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                game['message'] = ""
                game['show_instructions'] = False

def run_game(game):
    while game['running']:
        game['window_width'], game['window_height'] = game['screen'].get_size()
        update_layout(game)
        handle_events(game)
        update_metrics(game)
        game['screen'].fill(get_bg_color(game))
        draw_buttons(game)
        draw_bar_graph(game)
        draw_total_bars(game)
        draw_timer(game)
        draw_message(game)
        pygame.display.flip()
        game['clock'].tick(60)
    pygame.quit()

def main():
    game = init_game()
    run_game(game)

if __name__ == "__main__":
    main()

