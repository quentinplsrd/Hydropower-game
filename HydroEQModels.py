import pygame
import sys
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg

# Constants
g = 9.81  # Gravity
pygame.init()

# Display resolution
WIDTH, HEIGHT = 800, 600
window = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Hydropower Visualization")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
BLUE = (0, 0, 255)

# Global figure handles
fig_3d, ax_3d, canvas_3d, scatter = None, None, None, None
fig_colormap, ax_colormap, canvas_colormap, red_dot = None, None, None, None

# Slider class
class Slider:
    def __init__(self, x_frac, y_frac, w_frac, h_frac, min_val, max_val, start_val, label):
        self.x_frac = x_frac
        self.y_frac = y_frac
        self.w_frac = w_frac
        self.h_frac = h_frac
        self.rect = pygame.Rect(0, 0, 0, 0)
        self.update_rect()
        self.min_val = min_val
        self.max_val = max_val
        self.value = start_val
        self.label = label
        self.dragging = False

    def update_rect(self):
        self.rect.x = int(self.x_frac * WIDTH)
        self.rect.y = int(self.y_frac * HEIGHT)
        self.rect.w = int(self.w_frac * WIDTH)
        self.rect.h = int(self.h_frac * HEIGHT)

    def draw(self, surface):
        self.update_rect()
        pygame.draw.rect(surface, GRAY, self.rect)
        handle_x = self.rect.x + (self.rect.w * ((self.value - self.min_val) / (self.max_val - self.min_val)))
        handle_rect = pygame.Rect(handle_x - 5, self.rect.y, 10, self.rect.h)
        pygame.draw.rect(surface, BLUE, handle_rect)
        font = pygame.font.Font(None, int(0.04 * HEIGHT))
        text = font.render(f"{self.label}: {self.value:.2f}", True, BLACK)
        surface.blit(text, (self.rect.x, self.rect.y - int(0.05 * HEIGHT)))

    def update(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                rel_x = event.pos[0] - self.rect.x
                self.value = self.min_val + (rel_x / self.rect.w) * (self.max_val - self.min_val)
                self.value = max(self.min_val, min(self.max_val, self.value))

Q_slider = Slider(0.15, 0.9, 0.3, 0.04, 0, 100, 10, 'Flow Rate Q (cfs)')
h_slider = Slider(0.55, 0.9, 0.3, 0.04, 0, 100, 10, 'Head h (ft)')

azim_angle = 225
elev_angle = 30
last_mouse_pos = (0, 0)
is_dragging = False
show_3d_plot = True

def mouse_over_slider(pos):
    return Q_slider.rect.collidepoint(pos) or h_slider.rect.collidepoint(pos)

def draw_3d_surface(Q_val, h_val, azim, elev):
    global fig_3d, ax_3d, canvas_3d, scatter
    if fig_3d:
        plt.close(fig_3d)
    fig_3d = plt.figure(figsize=(5, 4), dpi=100)
    ax_3d = fig_3d.add_subplot(111, projection='3d')
    fig_3d.subplots_adjust(left=0.15, right=0.85, bottom=0.2)
    Q = np.linspace(0, 100, 50)
    h = np.linspace(0, 100, 50)
    Q_grid, h_grid = np.meshgrid(Q, h)
    P_grid = (Q_grid * g * h_grid)/1000
    ax_3d.plot_surface(Q_grid, h_grid, P_grid, cmap='Blues', alpha=0.9)
    P_val = (Q_val * g * h_val)/1000
    scatter = ax_3d.scatter(Q_val, h_val, P_val, color='red', s=50)
    ax_3d.set_xlabel("Flow Rate Q (cfs)", labelpad=10)
    ax_3d.set_ylabel("Head h (ft)", labelpad=10)
    ax_3d.set_zlabel("Power P (kW)", labelpad=10)
    ax_3d.set_xlim(0, 100)
    ax_3d.set_ylim(0, 100)
    ax_3d.set_zlim(0, 100)
    ax_3d.view_init(elev=elev, azim=azim)
    canvas_3d = FigureCanvasAgg(fig_3d)
    canvas_3d.draw()
    raw_data = canvas_3d.get_renderer().buffer_rgba()
    size = canvas_3d.get_width_height()
    return pygame.image.frombuffer(raw_data, size, "RGBA")

def update_3d_surface(Q_val, h_val, azim, elev):
    global scatter, canvas_3d, ax_3d, fig_3d
    scatter.remove()
    P_val = (Q_val * g * h_val)/1000
    scatter = ax_3d.scatter(Q_val, h_val, P_val, color='red', s=50)
    ax_3d.view_init(elev=elev, azim=azim)
    canvas_3d.draw()
    raw_data = canvas_3d.get_renderer().buffer_rgba()
    size = canvas_3d.get_width_height()
    return pygame.image.frombuffer(raw_data, size, "RGBA")

def draw_colormap(Q_val, h_val):
    global fig_colormap, ax_colormap, canvas_colormap, red_dot
    if fig_colormap:
        plt.close(fig_colormap)
    fig_colormap, ax_colormap = plt.subplots(figsize=(4, 3), dpi=100)
    Q = np.linspace(0, 100, 200)
    h = np.linspace(0, 100, 200)
    Q_grid, h_grid = np.meshgrid(Q, h)
    P_grid = (Q_grid * g * h_grid)/1000
    cmap = plt.get_cmap('viridis')
    c = ax_colormap.pcolormesh(Q_grid, h_grid, P_grid, shading='auto', cmap=cmap)
    fig_colormap.colorbar(c, ax=ax_colormap, label="Power (kW)")
    red_dot = ax_colormap.plot(Q_val, h_val, 'ro')[0]
    ax_colormap.set_xlabel("Flow Rate Q (cfs)")
    ax_colormap.set_ylabel("Head h (ft)")
    fig_colormap.tight_layout()
    canvas_colormap = FigureCanvasAgg(fig_colormap)
    canvas_colormap.draw()
    raw_data = canvas_colormap.get_renderer().buffer_rgba()
    size = canvas_colormap.get_width_height()
    return pygame.image.frombuffer(raw_data, size, "RGBA")

def update_colormap(Q_val, h_val):
    global red_dot, canvas_colormap
    red_dot.set_data([Q_val], [h_val])
    canvas_colormap.draw()
    raw_data = canvas_colormap.get_renderer().buffer_rgba()
    size = canvas_colormap.get_width_height()
    return pygame.image.frombuffer(raw_data, size, "RGBA")

running = True
first_run = True
slow_run = 0
UPDATE_INTERVAL = 4
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        Q_slider.update(event)
        h_slider.update(event)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            is_dragging = not mouse_over_slider(event.pos)
            last_mouse_pos = event.pos
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            is_dragging = False
        elif event.type == pygame.MOUSEMOTION and is_dragging:
            dx = event.pos[0] - last_mouse_pos[0]
            dy = event.pos[1] - last_mouse_pos[1]
            azim_angle -= dx * 0.5
            elev_angle += dy * 0.5
            elev_angle = max(-90, min(90, elev_angle))
            last_mouse_pos = event.pos
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_TAB:
                show_3d_plot = not show_3d_plot
                if show_3d_plot and fig_colormap:
                    plt.close(fig_colormap)
                elif not show_3d_plot and fig_3d:
                    plt.close(fig_3d)
                first_run = True
            elif event.key == pygame.K_r:
                azim_angle = 225
                elev_angle = 30

    Q = Q_slider.value
    h = h_slider.value
    P = Q * g * h/1000

    window.fill(WHITE)

    # Draw equation and variable labels at the top
    font_small = pygame.font.Font(None, int(0.045 * HEIGHT))
    font_large = pygame.font.Font(None, int(0.06 * HEIGHT))
    view_mode = "3D Surface Plot" if show_3d_plot else "2D Colormap"
    window.blit(font_small.render(f"{view_mode} (TAB to toggle, R to reset view)", True, BLACK), (int(0.25 * WIDTH), int(0.01 * HEIGHT)))
    window.blit(font_small.render("η: Turbine efficiency, ρ: Water density, Q: Flow Rate, g: Gravity, h: Head", True, BLACK), (int(0.1 * WIDTH), int(0.11 * HEIGHT)))
    window.blit(font_small.render("Explore the fundamental equation of Hydropower by adjusting the flow rate and head!", True, BLACK), (int(0.03 * WIDTH), int(0.145 * HEIGHT)))
    window.blit(font_small.render("Click and drag sliders to adjust parameters.", True, BLACK), (int(0.25 * WIDTH), int(0.95 * HEIGHT)))
    if (show_3d_plot): window.blit(font_small.render("Click and hold anywhere other than the sliders to rotate 3D-plot.", True, BLACK), (int(0.15 * WIDTH), int(0.18 * HEIGHT))) 
    window.blit(font_large.render("P = ηρQgh", True, BLACK), (int(0.32 * WIDTH), int(0.055 * HEIGHT)))
    window.blit(font_large.render(f"P = {P:.2f} kW", True, BLACK), (int(0.52 * WIDTH), int(0.055 * HEIGHT)))

    # Draw/update plot in the middle
    if first_run:
        plot_surface = draw_3d_surface(Q, h, azim_angle, elev_angle) if show_3d_plot else draw_colormap(Q, h)
        plot_rect = plot_surface.get_rect(center=(WIDTH // 2, int(0.55 * HEIGHT)))
        first_run = False
    else:
        if slow_run % UPDATE_INTERVAL == 0:
            plot_surface = update_3d_surface(Q, h, azim_angle, elev_angle) if show_3d_plot else update_colormap(Q, h)
    slow_run += 1

    window.blit(plot_surface, plot_rect)

    # Draw sliders at bottom
    Q_slider.draw(window)
    h_slider.draw(window)

    pygame.display.flip()

if fig_3d: plt.close(fig_3d)
if fig_colormap: plt.close(fig_colormap)
pygame.quit()
sys.exit()