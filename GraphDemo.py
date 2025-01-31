import pygame
import matplotlib.pyplot as plt
import numpy as np

# Initialize Pygame
pygame.init()

# Constants
WINDOW_WIDTH, WINDOW_HEIGHT = 800, 600
FPS = 60
WAVE_SPEED = 0.1  
# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)

# Initialize screen
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Sine Wave Animation")

# Function to update and save the graph
def update_graph(x_start, x_end, filename='graph.png'):
    x = np.linspace(x_start, x_end, 1000)
    y = np.sin(x)
    
    plt.figure(figsize=(6, 4))
    plt.plot(x, y)
    plt.xlim(x_start, x_end)
    plt.ylim(-1.5, 1.5)
    plt.title('Sine Wave')
    plt.xlabel('X')
    plt.ylabel('Sin(X)')
    plt.savefig(filename)
    plt.close()

# Load graph image
def load_graph_image(filename='graph.png'):
    try:
        return pygame.image.load(filename)
    except pygame.error as e:
        print(f"Unable to load image: {e}")
        return None

# Draw button
def draw_button(screen, rect, text, color):
    pygame.draw.rect(screen, color, rect)
    font = pygame.font.Font(None, 36)
    text_surf = font.render(text, True, BLACK)
    text_rect = text_surf.get_rect(center=rect.center)
    screen.blit(text_surf, text_rect)

# Main game loop
def main():
    clock = pygame.time.Clock()
    running = True
    animation_started = False
    x_start = 0  # Starting x value for the sine wave
    x_end = 4 * np.pi  # Ending x value for the sine wave

    # Button properties
    button_rect = pygame.Rect(WINDOW_WIDTH // 2 - 50, WINDOW_HEIGHT // 2 - 25, 100, 50)

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if button_rect.collidepoint(event.pos):
                    animation_started = True

        # Clear the screen
        screen.fill(WHITE)

        if animation_started:
            # Update the x range to simulate movement
            x_start += WAVE_SPEED
            x_end += WAVE_SPEED

            # Update the graph with new x range
            update_graph(x_start, x_end)

            # Load and display the graph
            graph_image = load_graph_image()
            if graph_image:
                screen.blit(graph_image, (50, 50))
        else:
            # Draw the start button
            draw_button(screen, button_rect, "Start", GRAY)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()