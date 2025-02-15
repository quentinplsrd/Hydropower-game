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


class HydropowerGame:
    def __init__(self):
        pygame.init()
        self.window_width = 1200
        self.window_height = 900
        self.screen = pygame.display.set_mode((self.window_width, self.window_height), pygame.RESIZABLE)
        pygame.display.set_caption("Hydropower Game")
        self.clock = pygame.time.Clock()
        self.running = True

        # Initialize fonts (will be recalculated in update_layout)
        self.font = pygame.font.SysFont(None, 24)
        self.large_font = pygame.font.SysFont(None, 32)

        # Flags for overlay, dark mode, and credits overlay.
        self.show_instructions = False
        self.message = ""
        self.dark_mode = False
        self.show_credits = False

        # Credits data for the scrolling overlay.
        self.credits_list = [
            "Quentin Ploussard",
            "Elise DeGeorge",
            "Lukas Livengood",
            "Amr Elseweifi",
            "Cathy Milostan",
            "Jonghwan Kwon 'JK'",
            "Matt Mahalik",
            "Tom Veselka",
            "Bree Mendlin",
            "A WPTO-funded ANL-NREL outreach project"
        ]
        # Initialize credits_offset so that the block starts at the bottom.
        self.credits_offset = self.window_height

        # Animation settings for buttons
        self.button_anim_duration = 0.2  # seconds
        self.button_animations = {}       # dict to store animation start times keyed by button label

        self.update_layout()

        # Initial hourly releases.
        self.y_values = (TARGET / N_timesteps) * np.ones(N_timesteps)
        self.selected_bar = None
        self.dragging = False
        self.last_mouse_y = None

        self.start_time = time.time()
        self.solution_checked = False
        self.try_again_button_rect = None

    def get_bg_color(self):
        return (30, 30, 30) if self.dark_mode else (255, 255, 255)

    def get_text_color(self):
        return (255, 255, 255) if self.dark_mode else (0, 0, 0)

    def get_panel_color(self):
        return (80, 80, 80) if self.dark_mode else (200, 200, 200)

    def get_button_color(self):
        return (100, 100, 100) if self.dark_mode else (180, 180, 180)

    def get_button_outline_color(self):
        return (255, 255, 255) if self.dark_mode else (0, 0, 0)

    def update_layout(self):
        self.window_width, self.window_height = self.screen.get_size()
        
        new_font_size = max(12, int(min(self.window_width, self.window_height) / 50))
        new_large_font_size = max(16, int(min(self.window_width, self.window_height) / 35))
        self.font = pygame.font.SysFont(None, new_font_size)
        self.large_font = pygame.font.SysFont(None, new_large_font_size)
        
        self.instructions_area = pygame.Rect(int(self.window_width * 0.04),
                                               int(self.window_height * 0.01),
                                               int(self.window_width * 0.92),
                                               int(self.window_height * 0.06))
        self.bar_graph_area = pygame.Rect(int(self.window_width * 0.08),
                                          int(self.window_height * 0.15),
                                          int(self.window_width * 0.83),
                                          int(self.window_height * 0.45))
        self.button_area = pygame.Rect(self.bar_graph_area.x,
                                       int(self.window_height * 0.08),
                                       self.bar_graph_area.width,
                                       int(self.window_height * 0.07))
        self.total_panel_area = pygame.Rect(int(self.window_width * 0.08),
                                            int(self.window_height * 0.69),
                                            int(self.window_width * 0.83),
                                            int(self.window_height * 0.15))
        self.credit_area = pygame.Rect(int(self.window_width * 0.04),
                                       int(self.window_height * 0.87),
                                       int(self.window_width * 0.92),
                                       int(self.window_height * 0.05))
        
        credits_button_width = 150
        credits_button_height = 40
        margin = 20
        vertical_offset = 30  # Additional upward offset
        button_width = int(150 * self.window_width / 1200)
        gap = int(50 * self.window_width / 1200)
        button_labels = ["Restart", "Check Solution", "Optimize", "Instructions", "Dark Mode"]
        total_buttons_width = len(button_labels) * button_width + (len(button_labels) - 1) * gap
        start_x = self.button_area.x + (self.button_area.width - total_buttons_width) // 2
        
        self.credits_button_rect = pygame.Rect(
            start_x, 
            self.window_height - credits_button_height - margin - vertical_offset,
            credits_button_width, 
            credits_button_height
        )
        
        button_height = int(40 * self.window_height / 900)
        button_y = self.button_area.y + (self.button_area.height - button_height) // 2
        self.buttons = {}
        for i, label in enumerate(button_labels):
            self.buttons[label] = pygame.Rect(start_x + i * (button_width + gap),
                                              button_y, button_width, button_height)
        # Update panels for metrics.
        panel_margin = int(10 * self.window_width / 1200)
        panel_width = (self.total_panel_area.width - 4 * panel_margin) // 5
        panel_height = self.total_panel_area.height
        labels = ["Total revenue ($)", "Total release (AF)", "Minimum release (AF/hr)",
                  "Maximum ramp up", "Maximum ramp down"]
        self.total_bar_graphs = {}
        for i, label in enumerate(labels):
            x = self.total_panel_area.x + i * (panel_width + panel_margin)
            y = self.total_panel_area.y
            self.total_bar_graphs[label] = pygame.Rect(x, y, panel_width, panel_height)

    def update_metrics(self):
        self.total_sum = np.sum(self.y_values)
        self.total_revenue = np.sum(self.y_values * price_values)
        self.minimum_release_rate = np.min(self.y_values)
        if len(self.y_values) > 1:
            ramp_rate = self.y_values[1:] - self.y_values[:-1]
            self.maximum_ramp_up_rate = np.max(ramp_rate)
            self.maximum_ramp_down_rate = np.max(-ramp_rate)
        else:
            self.maximum_ramp_up_rate = 0
            self.maximum_ramp_down_rate = 0
        self.feasible_total_sum = abs(self.total_sum - TARGET) <= target_tol
        self.feasible_min_release = self.minimum_release_rate >= (min_release - 0.1 * target_tol)
        self.feasible_ramp_up = self.maximum_ramp_up_rate <= (max_ramp_up + 0.1 * target_tol)
        self.feasible_ramp_down = self.maximum_ramp_down_rate <= (max_ramp_down + 0.1 * target_tol)
        self.feasible_solution = (self.feasible_total_sum and self.feasible_min_release and
                                  self.feasible_ramp_up and self.feasible_ramp_down)

    def draw_timer(self):
        elapsed = time.time() - self.start_time
        timer_text = self.font.render(f"Time: {int(elapsed)}s", True, self.get_text_color())
        timer_rect = timer_text.get_rect(topright=(self.window_width - 20, 20))
        self.screen.blit(timer_text, timer_rect)
        revenue_pct = 0
        if optimal_value:
            revenue_pct = 100 * self.total_revenue / optimal_value
        pct_text = self.font.render(f"Optimality: {revenue_pct:.0f}%", True, self.get_text_color())
        pct_rect = pct_text.get_rect(topright=(self.window_width - 20, timer_rect.bottom + 5))
        self.screen.blit(pct_text, pct_rect)
        feas_text = "Feasible!" if self.feasible_solution else "Infeasible"
        feas_color = (0, 200, 0) if self.feasible_solution else (200, 0, 0)
        feas_line = self.font.render(feas_text, True, feas_color)
        feas_rect = feas_line.get_rect(topright=(self.window_width - 20, pct_rect.bottom + 5))
        self.screen.blit(feas_line, feas_rect)

    def draw_bar_graph(self):
        pygame.draw.rect(self.screen, self.get_panel_color(), self.bar_graph_area, 2)
        max_value = 2.5
        pygame.draw.line(self.screen, self.get_text_color(),
                         (self.bar_graph_area.x, self.bar_graph_area.y),
                         (self.bar_graph_area.x, self.bar_graph_area.y + self.bar_graph_area.height), 2)
        tick_interval = 0.5
        num_ticks = int(max_value / tick_interval) + 1
        for i in range(num_ticks):
            tick_value = i * tick_interval
            y = self.bar_graph_area.y + self.bar_graph_area.height - (tick_value / max_value) * self.bar_graph_area.height
            pygame.draw.line(self.screen, self.get_text_color(),
                             (self.bar_graph_area.x - 5, y),
                             (self.bar_graph_area.x, y), 2)
            tick_label = self.font.render(f"{tick_value:.1f}", True, self.get_text_color())
            self.screen.blit(tick_label, (self.bar_graph_area.x - 35, y - 10))
        pygame.draw.line(self.screen, self.get_text_color(),
                         (self.bar_graph_area.x, self.bar_graph_area.y + self.bar_graph_area.height),
                         (self.bar_graph_area.x + self.bar_graph_area.width, self.bar_graph_area.y + self.bar_graph_area.height), 2)
        left_margin = 5
        available_width = self.bar_graph_area.width - left_margin
        bar_width = available_width / N_timesteps
        x_ticks = [0, 5, 10, 15, 20]
        for tick in x_ticks:
            tick_x = self.bar_graph_area.x + left_margin + (tick + 0.5) * bar_width
            pygame.draw.line(self.screen, self.get_text_color(),
                             (tick_x, self.bar_graph_area.y + self.bar_graph_area.height),
                             (tick_x, self.bar_graph_area.y + self.bar_graph_area.height + 5), 2)
            tick_label = self.font.render(str(tick), True, self.get_text_color())
            self.screen.blit(tick_label, (tick_x - tick_label.get_width() // 2,
                                          self.bar_graph_area.y + self.bar_graph_area.height + 8))
        x_axis_title = self.font.render("Hours", True, self.get_text_color())
        x_title_rect = x_axis_title.get_rect(center=(self.bar_graph_area.centerx,
                                                       self.bar_graph_area.y + self.bar_graph_area.height + 30))
        self.screen.blit(x_axis_title, x_title_rect)
        y_axis_title = self.font.render("Hourly release (AF/hr)", True, self.get_text_color())
        y_axis_title_rotated = pygame.transform.rotate(y_axis_title, 90)
        y_title_rect = y_axis_title_rotated.get_rect(center=(self.bar_graph_area.x - 50,
                                                             self.bar_graph_area.centery))
        self.screen.blit(y_axis_title_rotated, y_title_rect)
        for i in range(N_timesteps):
            x = int(self.bar_graph_area.x + left_margin + i * bar_width)
            value = self.y_values[i]
            bar_height = int((value / max_value) * self.bar_graph_area.height)
            y = int(self.bar_graph_area.y + self.bar_graph_area.height - bar_height)
            color = (31, 119, 180)
            pygame.draw.rect(self.screen, color, (x, y, int(bar_width) - 2, bar_height))
            text = self.font.render(f"{value:.2f}", True, self.get_text_color())
            text_rect = text.get_rect(center=(x + bar_width / 2, y - 10))
            self.screen.blit(text, text_rect)
        price_points = []
        for i in range(N_timesteps):
            x = self.bar_graph_area.x + left_margin + (i + 0.5) * bar_width
            y = self.bar_graph_area.y + self.bar_graph_area.height - (price_values[i] / max_value) * self.bar_graph_area.height
            price_points.append((x, y))
        if len(price_points) >= 2:
            pygame.draw.lines(self.screen, self.get_text_color(), False, price_points, 2)
        legend_rect = pygame.Rect(self.bar_graph_area.right - 160, self.bar_graph_area.y + 10, 150, 50)
        pygame.draw.rect(self.screen, self.get_panel_color(), legend_rect)
        pygame.draw.rect(self.screen, self.get_text_color(), legend_rect, 2)
        dash_start = (legend_rect.x + 10, legend_rect.y + 15)
        dash_end = (legend_rect.x + 30, legend_rect.y + 15)
        draw_dashed_line(self.screen, self.get_text_color(), dash_start, dash_end, width=2, dash_length=4, space_length=3)
        price_text = self.font.render("Price ($/AF)", True, self.get_text_color())
        self.screen.blit(price_text, (legend_rect.x + 40, legend_rect.y + 10))
        pygame.draw.rect(self.screen, (31, 119, 180), (legend_rect.x + 10, legend_rect.y + 30, 20, 12.5))
        rel_text = self.font.render("Releases (AF)", True, self.get_text_color())
        self.screen.blit(rel_text, (legend_rect.x + 40, legend_rect.y + 30))
        self.draw_timer()

    def draw_total_bars(self):
        metrics = {
            "Total revenue ($)": (self.total_revenue, optimal_value, "Optimal value"),
            "Total release (AF)": (self.total_sum, TARGET, "Daily target"),
            "Minimum release (AF/hr)": (self.minimum_release_rate, min_release, "Minimum rate"),
            "Maximum ramp up": (self.maximum_ramp_up_rate, max_ramp_up, "Ramp up limit"),
            "Maximum ramp down": (self.maximum_ramp_down_rate, max_ramp_down, "Ramp down limit"),
        }
        for key, rect in self.total_bar_graphs.items():
            value, target_value, target_name = metrics[key]
            pygame.draw.rect(self.screen, self.get_panel_color(), rect, 2)
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
            elif key == "Minimum release (AF/hr)":
                color = (200, 0, 0)
                if value >= (target_value - 0.1 * target_tol):
                    color = (0, 200, 0)
            elif key in ["Maximum ramp up", "Maximum ramp down"]:
                color = (200, 0, 0)
                if value <= (target_value + 0.1 * target_tol):
                    color = (0, 200, 0)
            pygame.draw.rect(self.screen, color, bar_rect)
            axis_y = rect.y + rect.height - (target_value / max_display) * rect.height
            draw_dashed_line(self.screen, self.get_text_color(),
                             (rect.x, axis_y),
                             (rect.x + rect.width, axis_y),
                             width=2, dash_length=10, space_length=5)
            label = self.font.render(f"{key}", True, self.get_text_color())
            label_rect = label.get_rect(center=(rect.centerx, rect.y - 10))
            self.screen.blit(label, label_rect)
            target_label = self.font.render(target_name, True, self.get_text_color())
            target_label_rect = target_label.get_rect(center=(rect.centerx, axis_y - 10))
            self.screen.blit(target_label, target_label_rect)

    def draw_buttons(self):
        for label, rect in self.buttons.items():
            anim_scale = 1.0
            if label in self.button_animations:
                elapsed = time.time() - self.button_animations[label]
                if elapsed < self.button_anim_duration:
                    progress = elapsed / self.button_anim_duration
                    if progress < 0.5:
                        anim_scale = 1 - 0.1 * (progress / 0.5)
                    else:
                        anim_scale = 0.9 + 0.1 * ((progress - 0.5) / 0.5)
                else:
                    del self.button_animations[label]
            scaled_width = int(rect.width * anim_scale)
            scaled_height = int(rect.height * anim_scale)
            scaled_rect = pygame.Rect(0, 0, scaled_width, scaled_height)
            scaled_rect.center = rect.center
            pygame.draw.rect(self.screen, self.get_button_color(), scaled_rect)
            pygame.draw.rect(self.screen, self.get_button_outline_color(), scaled_rect, 2)
            display_label = label
            if label == "Dark Mode":
                display_label = f"Dark Mode: {'On' if self.dark_mode else 'Off'}"
            text = self.font.render(display_label, True, self.get_text_color())
            text_rect = text.get_rect(center=scaled_rect.center)
            self.screen.blit(text, text_rect)
            
        anim_scale = 1.0
        key = "Credits"
        if key in self.button_animations:
            elapsed = time.time() - self.button_animations[key]
            if elapsed < self.button_anim_duration:
                progress = elapsed / self.button_anim_duration
                if progress < 0.5:
                    anim_scale = 1 - 0.1 * (progress / 0.5)
                else:
                    anim_scale = 0.9 + 0.1 * ((progress - 0.5) / 0.5)
            else:
                del self.button_animations[key]
        scaled_width = int(self.credits_button_rect.width * anim_scale)
        scaled_height = int(self.credits_button_rect.height * anim_scale)
        scaled_rect = pygame.Rect(0, 0, scaled_width, scaled_height)
        scaled_rect.center = self.credits_button_rect.center
        pygame.draw.rect(self.screen, self.get_button_color(), scaled_rect)
        pygame.draw.rect(self.screen, self.get_button_outline_color(), scaled_rect, 2)

        button_label = "Close Credits" if self.show_credits else "Credits"
        credits_text = self.font.render(button_label, True, self.get_text_color())
        credits_text_rect = credits_text.get_rect(center=scaled_rect.center)
        self.screen.blit(credits_text, credits_text_rect)

    def draw_message(self):
        if self.message:
            overlay = pygame.Surface((self.window_width, self.window_height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 128))
            self.screen.blit(overlay, (0, 0))
            lines = self.message.split("\n")
            for i, line in enumerate(lines):
                text = self.large_font.render(line, True, (255, 255, 255))
                text_rect = text.get_rect(center=(self.window_width // 2, self.window_height // 2 - 50 + i * 40))
                self.screen.blit(text, text_rect)
            btn_label = "Close"
            btn_width = int(150 * self.window_width / 1200)
            btn_height = int(40 * self.window_height / 900)
            btn_x = (self.window_width - btn_width) // 2
            btn_y = self.window_height // 2 + 50
            self.try_again_button_rect = pygame.Rect(btn_x, btn_y, btn_width, btn_height)
            pygame.draw.rect(self.screen, self.get_button_color(), self.try_again_button_rect)
            pygame.draw.rect(self.screen, self.get_button_outline_color(), self.try_again_button_rect, 2)
            btn_text = self.font.render(btn_label, True, self.get_text_color())
            btn_text_rect = btn_text.get_rect(center=self.try_again_button_rect.center)
            self.screen.blit(btn_text, btn_text_rect)

    def draw_credits_overlay(self):
        credits_font = pygame.font.SysFont(None, 48)
        line_height = credits_font.get_linesize() * 2
        total_height = line_height * len(self.credits_list)
        
        overlay = pygame.Surface((self.window_width, self.window_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        self.screen.blit(overlay, (0, 0))
        
        y = self.credits_offset
        for line in self.credits_list:
            text = credits_font.render(line, True, (255, 255, 255))
            text_rect = text.get_rect(center=(self.window_width // 2, y))
            self.screen.blit(text, text_rect)
            y += line_height
        
        mid_index = len(self.credits_list) // 2.25
        middle_line_center = self.credits_offset + mid_index * line_height + line_height / 2
        if middle_line_center > self.window_height / 2:
            self.credits_offset -= 2  # Adjust scroll speed as needed

    def handle_button_click(self, pos):
        # Check the top buttons.
        for label, rect in self.buttons.items():
            if rect.collidepoint(pos):
                self.button_animations[label] = time.time()
                if label == "Restart":
                    self.start_action()
                elif label == "Check Solution":
                    self.check_action()
                elif label == "Optimize":
                    self.optimize_action()
                elif label == "Instructions":
                    self.show_instructions = True
                    self.message = "\n".join(textwrap.wrap(
                        "Find the best hydropower revenue by changing the hourly releases. "
                        "Ensure all environmental rules are met: daily target, minimum release, "
                        "maximum ramp up, and maximum ramp down.", width=80))
                elif label == "Dark Mode":
                    self.dark_mode = not self.dark_mode
                return

    def start_action(self):
        self.y_values = (TARGET / N_timesteps) * np.ones(N_timesteps)
        self.solution_checked = False
        self.start_time = time.time()
        self.message = ""
        self.show_instructions = False

    def check_action(self):
        self.update_metrics()
        time_to_find = time.time() - self.start_time
        if self.feasible_solution:
            self.message = f"Solution is feasible!\nTime to find: {time_to_find:.0f}s"
        else:
            self.message = f"Solution is not feasible, try again!\nTime to find: {time_to_find:.0f}s"
        self.solution_checked = True
        self.start_time = time.time()

    def optimize_action(self):
        if not self.solution_checked:
            self.message = ("Try to find the solution by yourself first!\nClick 'Check solution' then 'Optimize'.")
            return
        if result.termination.reason == mathopt.TerminationReason.OPTIMAL:
            self.y_values = np.array([result.variable_values()[release[h]] for h in hours])
            self.message = "Optimized solution applied!"
        else:
            self.message = "The model was infeasible."

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.VIDEORESIZE:
                self.window_width = event.w
                self.window_height = event.h
                self.screen = pygame.display.set_mode((self.window_width, self.window_height), pygame.RESIZABLE)
                self.update_layout()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    pos = event.pos

                    if self.credits_button_rect.collidepoint(pos):
                        self.button_animations["Credits"] = time.time()
                        self.show_credits = not self.show_credits
                        if self.show_credits:
                            self.credits_offset = self.window_height
                        continue
                    if self.message:
                        if hasattr(self, "try_again_button_rect") and self.try_again_button_rect.collidepoint(pos):
                            self.message = ""
                            self.show_instructions = False
                        continue
                    if self.button_area.collidepoint(pos):
                        self.handle_button_click(pos)
                    elif self.bar_graph_area.collidepoint(pos):
                        bar_width = self.bar_graph_area.width / N_timesteps
                        rel_x = pos[0] - self.bar_graph_area.x
                        bar_index = int(rel_x // bar_width)
                        if 0 <= bar_index < N_timesteps:
                            self.selected_bar = bar_index
                            self.dragging = True
                            self.last_mouse_y = pos[1]
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.dragging = False
                    self.selected_bar = None
            elif event.type == pygame.MOUSEMOTION:
                if self.dragging and self.selected_bar is not None:
                    dy = self.last_mouse_y - event.pos[1]
                    sensitivity = 0.005
                    delta = dy * sensitivity
                    new_value = np.clip(self.y_values[self.selected_bar] + delta, 0, 1.5)
                    self.y_values[self.selected_bar] = new_value
                    self.last_mouse_y = event.pos[1]
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.message = ""
                    self.show_instructions = False
                    self.show_credits = False

    def run(self):
        while self.running:
            self.window_width, self.window_height = self.screen.get_size()
            self.update_layout()
            self.handle_events()
            self.update_metrics()
            self.screen.fill(self.get_bg_color())
            self.draw_buttons()
            self.draw_bar_graph()
            self.draw_total_bars()
            self.draw_timer()
            self.draw_message()
            if self.show_credits:
                self.draw_credits_overlay()
            pygame.display.flip()
            self.clock.tick(60)
        pygame.quit()

def main():
    game = HydropowerGame()
    game.run()

if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()

