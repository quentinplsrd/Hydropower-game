import sys
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

# Build the OR-Tools optimization model
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

# --------------------------
# Pygame-based GUI with dynamic layout (resizable window) and integrated overlay.
# --------------------------
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

        # Flag to control whether instructions overlay is shown.
        self.show_instructions = False

        # The message string will be used both for check/optimize messages and for instructions.
        self.message = ""

        # Initialize layout areas and UI objects.
        self.update_layout()

        # Initial hourly releases.
        self.y_values = (TARGET / N_timesteps) * np.ones(N_timesteps)
        self.selected_bar = None
        self.dragging = False
        self.last_mouse_y = None

        self.start_time = time.time()
        self.solution_checked = False
        self.try_again_button_rect = None
        self.close_instructions_button_rect = None

    def update_layout(self):
        self.window_width, self.window_height = self.screen.get_size()
        
        # Recalculate fonts based on the smaller dimension.
        new_font_size = max(12, int(min(self.window_width, self.window_height) / 50))
        new_large_font_size = max(16, int(min(self.window_width, self.window_height) / 35))
        self.font = pygame.font.SysFont(None, new_font_size)
        self.large_font = pygame.font.SysFont(None, new_large_font_size)
        
        # Use relative values for layout:
        self.instructions_area = pygame.Rect(int(self.window_width * 0.04), int(self.window_height * 0.01),
                                               int(self.window_width * 0.92), int(self.window_height * 0.06))
        self.bar_graph_area = pygame.Rect(int(self.window_width * 0.08), int(self.window_height * 0.15),
                                          int(self.window_width * 0.83), int(self.window_height * 0.45))
        self.button_area = pygame.Rect(self.bar_graph_area.x, int(self.window_height * 0.08),
                                       self.bar_graph_area.width, int(self.window_height * 0.07))
        self.total_panel_area = pygame.Rect(int(self.window_width * 0.08), int(self.window_height * 0.69),
                                            int(self.window_width * 0.83), int(self.window_height * 0.15))
        self.credit_area = pygame.Rect(int(self.window_width * 0.04), int(self.window_height * 0.87),
                                       int(self.window_width * 0.92), int(self.window_height * 0.05))
        
        # Update buttons (now 4 buttons: "Start", "Check solution", "Optimize", "Instructions")
        button_width = int(150 * self.window_width / 1200)
        button_height = int(40 * self.window_height / 900)
        gap = int(50 * self.window_width / 1200)
        total_buttons_width = 4 * button_width + 3 * gap
        start_x = self.button_area.x + (self.button_area.width - total_buttons_width) // 2
        button_y = self.button_area.y + (self.button_area.height - button_height) // 2
        self.buttons = {
            "Start": pygame.Rect(start_x, button_y, button_width, button_height),
            "Check solution": pygame.Rect(start_x + button_width + gap, button_y, button_width, button_height),
            "Optimize": pygame.Rect(start_x + 2 * (button_width + gap), button_y, button_width, button_height),
            "Instructions": pygame.Rect(start_x + 3 * (button_width + gap), button_y, button_width, button_height),
        }
        
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
        ramp_rate = np.roll(self.y_values, -1) - self.y_values
        self.maximum_ramp_up_rate = np.max(ramp_rate)
        self.maximum_ramp_down_rate = np.max(-ramp_rate)
        self.feasible_total_sum = abs(self.total_sum - TARGET) <= target_tol
        self.feasible_min_release = self.minimum_release_rate >= (min_release - 0.1 * target_tol)
        self.feasible_ramp_up = self.maximum_ramp_up_rate <= (max_ramp_up + 0.1 * target_tol)
        self.feasible_ramp_down = self.maximum_ramp_down_rate <= (max_ramp_down + 0.1 * target_tol)
        self.feasible_solution = (self.feasible_total_sum and self.feasible_min_release and
                                  self.feasible_ramp_up and self.feasible_ramp_down)

    def draw_timer(self):
        elapsed = time.time() - self.start_time
        timer_text = self.font.render(f"Time: {int(elapsed)}s", True, (0, 0, 0))
        timer_rect = timer_text.get_rect(topright=(self.window_width - 20, 20))
        self.screen.blit(timer_text, timer_rect)
        revenue_pct = 0
        if optimal_value:
            revenue_pct = 100 * self.total_revenue / optimal_value
        color = (0, 200, 0) if revenue_pct >= 85 else (200, 0, 0)
        pct_text = self.font.render(f"Optimality: {revenue_pct:.0f}%", True, color)
        pct_rect = pct_text.get_rect(topright=(self.window_width - 20, timer_rect.bottom + 5))
        self.screen.blit(pct_text, pct_rect)
        feasible_bottom = self.feasible_total_sum and self.feasible_min_release and self.feasible_ramp_up and self.feasible_ramp_down
        feas_text = "Feasible!" if feasible_bottom else "Infeasible"
        feas_color = (0, 200, 0) if feasible_bottom else (200, 0, 0)
        feas_line = self.font.render(f"{feas_text}", True, feas_color)
        feas_rect = feas_line.get_rect(topright=(self.window_width - 20, pct_rect.bottom + 5))
        self.screen.blit(feas_line, feas_rect)

    def draw_bar_graph(self):
        pygame.draw.rect(self.screen, (200, 200, 200), self.bar_graph_area, 2)
        bar_width = self.bar_graph_area.width / N_timesteps
        max_value = 2.5
        pygame.draw.line(self.screen, (0, 0, 0),
                         (self.bar_graph_area.x, self.bar_graph_area.y),
                         (self.bar_graph_area.x, self.bar_graph_area.y + self.bar_graph_area.height), 2)
        tick_interval = 0.5
        num_ticks = int(max_value / tick_interval) + 1
        for i in range(num_ticks):
            tick_value = i * tick_interval
            y = self.bar_graph_area.y + self.bar_graph_area.height - (tick_value / max_value) * self.bar_graph_area.height
            pygame.draw.line(self.screen, (0, 0, 0),
                             (self.bar_graph_area.x - 5, y),
                             (self.bar_graph_area.x, y), 2)
            tick_label = self.font.render(f"{tick_value:.1f}", True, (0, 0, 0))
            self.screen.blit(tick_label, (self.bar_graph_area.x - 35, y - 10))
        pygame.draw.line(self.screen, (0, 0, 0),
                         (self.bar_graph_area.x, self.bar_graph_area.y + self.bar_graph_area.height),
                         (self.bar_graph_area.x + self.bar_graph_area.width, self.bar_graph_area.y + self.bar_graph_area.height), 2)
        x_ticks = [0, 5, 10, 15, 20]
        for tick in x_ticks:
            tick_x = self.bar_graph_area.x + (tick + 0.5) * bar_width
            pygame.draw.line(self.screen, (0, 0, 0),
                             (tick_x, self.bar_graph_area.y + self.bar_graph_area.height),
                             (tick_x, self.bar_graph_area.y + self.bar_graph_area.height + 5), 2)
            tick_label = self.font.render(str(tick), True, (0, 0, 0))
            self.screen.blit(tick_label, (tick_x - tick_label.get_width() // 2,
                                          self.bar_graph_area.y + self.bar_graph_area.height + 8))
        x_axis_title = self.font.render("Hours", True, (0, 0, 0))
        x_title_rect = x_axis_title.get_rect(center=(self.bar_graph_area.centerx,
                                                       self.bar_graph_area.y + self.bar_graph_area.height + 30))
        self.screen.blit(x_axis_title, x_title_rect)
        y_axis_title = self.font.render("Hourly release (AF/hr)", True, (0, 0, 0))
        y_axis_title_rotated = pygame.transform.rotate(y_axis_title, 90)
        y_title_rect = y_axis_title_rotated.get_rect(center=(self.bar_graph_area.x - 50,
                                                             self.bar_graph_area.centery))
        self.screen.blit(y_axis_title_rotated, y_title_rect)
        for i in range(N_timesteps):
            x = self.bar_graph_area.x + i * bar_width
            value = self.y_values[i]
            bar_height = (value / max_value) * self.bar_graph_area.height
            y = self.bar_graph_area.y + self.bar_graph_area.height - bar_height
            color = (31, 119, 180)
            pygame.draw.rect(self.screen, color, (x, y, bar_width - 2, bar_height))
            text = self.font.render(f"{value:.2f}", True, (0, 0, 0))
            text_rect = text.get_rect(center=(x + bar_width / 2, y - 10))
            self.screen.blit(text, text_rect)
        price_points = []
        for i in range(N_timesteps):
            x = self.bar_graph_area.x + (i + 0.5) * bar_width
            y = self.bar_graph_area.y + self.bar_graph_area.height - (price_values[i] / max_value) * self.bar_graph_area.height
            price_points.append((x, y))
        if len(price_points) >= 2:
            pygame.draw.lines(self.screen, (0, 0, 0), False, price_points, 2)
        legend_rect = pygame.Rect(self.bar_graph_area.right - 160, self.bar_graph_area.y + 10, 150, 50)
        pygame.draw.rect(self.screen, (240, 240, 240), legend_rect)
        pygame.draw.rect(self.screen, (0, 0, 0), legend_rect, 2)
        dash_start = (legend_rect.x + 10, legend_rect.y + 15)
        dash_end = (legend_rect.x + 30, legend_rect.y + 15)
        draw_dashed_line(self.screen, (0, 0, 0), dash_start, dash_end, width=2, dash_length=4, space_length=3)
        price_text = self.font.render("Price ($/AF)", True, (0, 0, 0))
        self.screen.blit(price_text, (legend_rect.x + 40, legend_rect.y + 10))
        pygame.draw.rect(self.screen, (31, 119, 180), (legend_rect.x + 10, legend_rect.y + 30, 20, 12.5))
        rel_text = self.font.render("Releases (AF)", True, (0, 0, 0))
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
            pygame.draw.rect(self.screen, (200, 200, 200), rect, 2)
            max_display = target_value * 1.5 if target_value != 0 else 1
            calculated_bar_height = (value / max_display) * rect.height
            bar_height = min(calculated_bar_height, rect.height)
            bar_y = rect.y + rect.height - bar_height
            bar_rect = pygame.Rect(rect.x + 10, bar_y, rect.width - 20, bar_height)
            color = (31, 119, 180)
            if key == "Total revenue ($)" and abs(value - target_value) <= target_tol:
                color = (0, 200, 0)
            if key == "Total release (AF)" and abs(value - target_value) <= target_tol:
                color = (0, 200, 0)
            if key == "Minimum release (AF/hr)" and value >= (target_value - 0.1 * target_tol):
                color = (0, 200, 0)
            if key in ["Maximum ramp up", "Maximum ramp down"] and value <= (target_value + 0.1 * target_tol):
                color = (0, 200, 0)
            pygame.draw.rect(self.screen, color, bar_rect)
            axis_y = rect.y + rect.height - (target_value / max_display) * rect.height
            draw_dashed_line(self.screen, (0, 0, 0), (rect.x, axis_y), (rect.x + rect.width, axis_y), width=2, dash_length=10, space_length=5)
            label = self.font.render(f"{key}", True, (0, 0, 0))
            label_rect = label.get_rect(center=(rect.centerx, rect.y - 10))
            self.screen.blit(label, label_rect)
            target_label = self.font.render(target_name, True, (0, 0, 0))
            target_label_rect = target_label.get_rect(center=(rect.centerx, rect.y + rect.height - 75))
            self.screen.blit(target_label, target_label_rect)

    def draw_buttons(self):
        for label, rect in self.buttons.items():
            pygame.draw.rect(self.screen, (180, 180, 180), rect)
            pygame.draw.rect(self.screen, (0, 0, 0), rect, 2)
            text = self.font.render(label, True, (0, 0, 0))
            text_rect = text.get_rect(center=rect.center)
            self.screen.blit(text, text_rect)


    def draw_credit(self):
        credit_text = ("A WPTO-funded ANL-NREL outreach project: Quentin Ploussard, Elise DeGeorge, Lukas Livengood, "
                       "Amr Elseweifi, Cathy Milostan, Jonghwan Kwon 'JK', Matt Mahalik, Tom Veselka, Bree Mendlin")
        wrapped_lines = textwrap.wrap(credit_text, width=80)
        y = self.credit_area.y
        for line in wrapped_lines:
            text = self.font.render(line, True, (0, 0, 0))
            self.screen.blit(text, (self.credit_area.x, y))
            y += text.get_height() + 2

    def draw_message(self):
        # Integrate both general messages and instructions overlay here.
        if self.message:
            overlay = pygame.Surface((self.window_width, self.window_height), pygame.SRCALPHA)
            # Use alpha=128 for a more transparent overlay
            overlay.fill((0, 0, 0, 128))
            self.screen.blit(overlay, (0, 0))
            lines = self.message.split("\n")
            for i, line in enumerate(lines):
                text = self.large_font.render(line, True, (255, 255, 255))
                text_rect = text.get_rect(center=(self.window_width // 2, self.window_height // 2 - 50 + i * 40))
                self.screen.blit(text, text_rect)
            # Draw a button depending on whether this is the instructions overlay or a message.
            if self.show_instructions:
                btn_label = "Close"
            else:
                btn_label = "Try again"
            btn_width = int(150 * self.window_width / 1200)
            btn_height = int(40 * self.window_height / 900)
            btn_x = (self.window_width - btn_width) // 2
            btn_y = self.window_height // 2 + 50
            self.try_again_button_rect = pygame.Rect(btn_x, btn_y, btn_width, btn_height)
            pygame.draw.rect(self.screen, (180, 180, 180), self.try_again_button_rect)
            pygame.draw.rect(self.screen, (0, 0, 0), self.try_again_button_rect, 2)
            btn_text = self.font.render(btn_label, True, (0, 0, 0))
            btn_text_rect = btn_text.get_rect(center=self.try_again_button_rect.center)
            self.screen.blit(btn_text, btn_text_rect)

    def handle_button_click(self, pos):
        for label, rect in self.buttons.items():
            if rect.collidepoint(pos):
                if label == "Start":
                    self.start_action()
                elif label == "Check solution":
                    self.check_action()
                elif label == "Optimize":
                    self.optimize_action()
                elif label == "Instructions":
                    self.show_instructions = True
                    self.message = "\n".join(textwrap.wrap(
                        "Find the best hydropower revenue by changing the hourly releases. "
                        "Ensure all environmental rules are met: daily target, minimum release, "
                        "maximum ramp up, and maximum ramp down.", width=80))

                    
    def start_action(self):
        self.y_values = (TARGET / N_timesteps) * np.ones(N_timesteps)
        self.solution_checked = False
        self.start_time = time.time()
        self.message = ""
        self.show_instructions = False

    def check_action(self):
        self.update_metrics()
        percent_solution = 100 * self.total_revenue / optimal_value if optimal_value != 0 else 0
        time_to_find = time.time() - self.start_time
        if percent_solution >= 85:
            self.message = (f"Solution is feasible!\n"
                            f"You are {percent_solution:.0f}% close to the optimal solution.\n"
                            f"Time to find: {time_to_find:.0f}s")
        else:
            self.message = (f"Solution is not feasible, try again...\n"
                            f"You are only {percent_solution:.0f}% close to the optimal solution.\n"
                            f"Time to find: {time_to_find:.0f}s")
        self.solution_checked = True
        self.start_time = time.time()

    def optimize_action(self):
        if self.solution_checked:
            if result.termination.reason == mathopt.TerminationReason.OPTIMAL:
                self.y_values = np.array([result.variable_values()[release[h]] for h in hours])
                self.message = ""
            else:
                self.message = "The model was infeasible."
        else:
            self.message = ("Try to find the solution by yourself first!\n"
                            "Click 'Check solution' then 'Optimize'.")
            

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
                    if self.message:
                        # If an overlay is showing, check the overlay button.
                        if hasattr(self, "try_again_button_rect") and self.try_again_button_rect.collidepoint(pos):
                            # If instructions overlay, close it; otherwise reset game.
                            if self.show_instructions:
                                self.show_instructions = False
                                self.message = ""
                            else:
                                self.start_action()
                                self.message = ""
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

    def run(self):
        while self.running:
            self.window_width, self.window_height = self.screen.get_size()
            self.update_layout()
            self.handle_events()
            self.update_metrics()
            self.screen.fill((255, 255, 255))
            self.draw_buttons()
            self.draw_bar_graph()
            self.draw_total_bars()
            self.draw_credit()
            self.draw_timer()
            self.draw_message()
            pygame.display.flip()
            self.clock.tick(60)
        pygame.quit()

def main():
    game = HydropowerGame()
    game.run()

if __name__ == "__main__":
    main()

