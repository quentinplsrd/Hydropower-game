import pygame
import sys
import os
import cv2
import numpy as np
import random

pygame.init()

# Constants
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 30
FACE_PATH_TEMPLATE = "assets2/CYC_Assets/Faces/F{}.jpg"
BODY_PATH_TEMPLATE = "assets2/CYC_Assets/Bodies/B{}.jpg"
NUM_CHARACTERS = 9  # Includes the center "Random"

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 200, 0)

# Screen setup
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Character Select")
clock = pygame.time.Clock()

# Fonts
font_size = int(SCREEN_HEIGHT * 0.03)
font = pygame.font.SysFont("Arial", font_size, bold=True)
label = font.render("Random", True, WHITE)
title_font = pygame.font.SysFont("Arial", int(SCREEN_HEIGHT * 0.05), bold=True)
title_text = title_font.render("Choose your character!", True, WHITE)
confirm_font = pygame.font.SysFont("Arial", int(SCREEN_HEIGHT * 0.025), bold=True)
confirm_text = confirm_font.render("Confirm", True, WHITE)

# State
selected_index = 4
hovered_index = None
current_preview_index = 4
face_rects = []
ignore_mouse_hover_until_move = False
block_hover_if_random = False
random_selection_active = False
random_selection_start_time = 0
random_highlight_index = None
last_interval_step = -1
confirm_button_rect = None
confirm_clicked = False

# Name input
name_input_active = False
player_name = ""
max_name_length = 16
name_input_rect = None


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
        path = resource_path(path_template.format(i))
        try:
            frame = pygame.image.load(path).convert_alpha()
            frames.append(frame)
        except pygame.error as e:
            print(f"Error loading frame {i}: {e}")
            sys.exit(1)
    return frames


def tint_surface(surface, tint_color):
    tinted = surface.copy()
    tint = pygame.Surface(tinted.get_size(), pygame.SRCALPHA)
    tint.fill(tint_color + (150,))
    tinted.blit(tint, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
    return tinted


def trigger_random_selection():
    global random_selection_active, random_selection_start_time, last_interval_step
    random_selection_active = True
    random_selection_start_time = pygame.time.get_ticks()
    last_interval_step = -1


def handle_arrow_keys(key):
    global selected_index, current_preview_index
    row = selected_index // 3
    col = selected_index % 3

    if key == pygame.K_LEFT and col > 0:
        selected_index -= 1
    elif key == pygame.K_RIGHT and col < 2:
        selected_index += 1
    elif key == pygame.K_UP and row > 0:
        selected_index -= 3
    elif key == pygame.K_DOWN and row < 2:
        selected_index += 3

    current_preview_index = selected_index


def draw_character_grid(face_frames, face_size, border_frame, green_border_frame, player_name, name_input_active):
    global face_rects, confirm_button_rect
    face_rects = []

    grid_size = 3
    margin = int(SCREEN_WIDTH * 0.01)
    total_grid_width = grid_size * face_size + (grid_size - 1) * margin
    total_grid_height = grid_size * face_size + (grid_size - 1) * margin
    start_x = int(SCREEN_WIDTH * 0.05)
    start_y = (SCREEN_HEIGHT - total_grid_height) // 2

    # Title
    title_x = start_x + (total_grid_width - title_text.get_width()) // 2
    screen.blit(title_text, (title_x, start_y - face_size * 0.8))

    # Name input box
    name_box_width = int(face_size * 2.5)
    name_box_height = int(face_size * 0.3)
    name_x = start_x + (total_grid_width - name_box_width) // 2
    name_y = start_y - face_size // 2
    name_input_rect = pygame.Rect(name_x, name_y, name_box_width, name_box_height)
    name_border = pygame.transform.smoothscale(border_frame, (name_box_width + 4, name_box_height + 4))
    screen.blit(name_border, (name_x - 2, name_y - 2))

    name_surface = font.render(player_name or "Enter name...", True, WHITE if player_name else (180, 180, 180))
    name_text_x = name_x + 10
    name_text_y = name_y + (name_box_height - name_surface.get_height()) // 2
    screen.blit(name_surface, (name_text_x, name_text_y))

    index = 0
    for row in range(grid_size):
        for col in range(grid_size):
            if index >= len(face_frames):
                continue

            x = start_x + col * (face_size + margin)
            y = start_y + row * (face_size + margin)
            rect = pygame.Rect(x, y, face_size, face_size)

            center_x = x + face_size // 2
            center_y = y + face_size // 2
            border_x = center_x - border_frame.get_width() // 2
            border_y = center_y - border_frame.get_height() // 2

            if random_selection_active:
                if index == random_highlight_index and index != 4:
                    screen.blit(green_border_frame, (border_x, border_y))
                else:
                    screen.blit(border_frame, (border_x, border_y))
            else:
                if index == selected_index:
                    screen.blit(green_border_frame, (border_x, border_y))
                else:
                    screen.blit(border_frame, (border_x, border_y))

            screen.blit(face_frames[index], (x, y))
            face_rects.append((rect, index))

            if index == 4:
                screen.blit(label, (
                    rect.centerx - label.get_width() // 2,
                    rect.bottom + int(SCREEN_HEIGHT * 0.005)
                ))

            index += 1

    # Confirm Button
    confirm_width = int(face_size * 0.6)
    confirm_height = int(face_size * 0.2)
    confirm_border = pygame.transform.smoothscale(border_frame, (confirm_width + 4, confirm_height + 4))
    confirm_x = start_x + (total_grid_width - confirm_width) // 2
    confirm_y = start_y + total_grid_height + face_size // 4
    confirm_button_rect = pygame.Rect(confirm_x, confirm_y, confirm_width, confirm_height)
    border_center_x = confirm_x + confirm_width // 2
    border_center_y = confirm_y + confirm_height // 2
    border_x = border_center_x - confirm_border.get_width() // 2
    border_y = border_center_y - confirm_border.get_height() // 2

    # Determine if Confirm button should be enabled
    button_enabled = selected_index != 4 and player_name.strip() != ""

    if not button_enabled:
        # Tint confirm button gray when disabled
        gray_border = tint_surface(confirm_border, (100, 100, 100))
        screen.blit(gray_border, (border_x, border_y))
    else:
        screen.blit(confirm_border, (border_x, border_y))

    screen.blit(confirm_text, (
        confirm_x + (confirm_width - confirm_text.get_width()) // 2,
        confirm_y + (confirm_height - confirm_text.get_height()) // 2
    ))

    return name_input_rect


def draw_body_preview(body_frames, index, border_frame):
    if index is None or index >= len(body_frames):
        return
    body_img = body_frames[index]
    x = SCREEN_WIDTH - body_img.get_width() - int(SCREEN_WIDTH * 0.05)
    y = (SCREEN_HEIGHT - body_img.get_height()) // 2
    border_w, border_h = border_frame.get_size()
    center_x = x + body_img.get_width() // 2
    center_y = y + body_img.get_height() // 2
    border_x = center_x - border_w // 2
    border_y = center_y - border_h // 2
    screen.blit(border_frame, (border_x, border_y))
    screen.blit(body_img, (x, y))


def main():
    global hovered_index, selected_index, current_preview_index
    global ignore_mouse_hover_until_move, block_hover_if_random
    global random_selection_active, random_highlight_index, random_selection_start_time, last_interval_step
    global confirm_button_rect, confirm_clicked, name_input_rect, name_input_active, player_name

    face_frames_raw = load_frames(NUM_CHARACTERS, FACE_PATH_TEMPLATE)
    border_frame_raw = load_image("assets2/IKM_Assets/BorderFrame.png")
    body_frames_raw = load_frames(NUM_CHARACTERS, BODY_PATH_TEMPLATE)

    max_body_height = int(SCREEN_HEIGHT * 0.8)
    body_frames = []
    for img in body_frames_raw:
        scale_factor = max_body_height / img.get_height()
        new_size = (int(img.get_width() * scale_factor), int(img.get_height() * scale_factor))
        body_frames.append(pygame.transform.smoothscale(img, new_size))

    grid_size = 3
    target_area_fraction = 0.2
    face_size = int((SCREEN_WIDTH * SCREEN_HEIGHT * target_area_fraction / (grid_size * grid_size)) ** 0.5)
    face_frames = [pygame.transform.smoothscale(f, (face_size, face_size)) for f in face_frames_raw]
    border_size = (face_size + 4, face_size + 4)
    border_frame = pygame.transform.smoothscale(border_frame_raw, border_size)
    green_border_frame = tint_surface(border_frame, GREEN)

    body_border_frames = []
    for body_img in body_frames:
        border_size = (body_img.get_width() + 4, body_img.get_height() + 4)
        body_border = pygame.transform.smoothscale(border_frame_raw, border_size)
        body_border_frames.append(body_border)

    video_path = resource_path("assets2/CYC_Assets/Background.mp4")
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Failed to open video.")
        sys.exit(1)

    running = True
    while running:
        ret, frame = cap.read()
        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.resize(frame, (SCREEN_WIDTH, SCREEN_HEIGHT))
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_surface = pygame.surfarray.make_surface(np.flipud(np.rot90(frame)))
        screen.blit(frame_surface, (0, 0))

        current_time = pygame.time.get_ticks()

        if random_selection_active:
            duration = 1000
            interval = 100
            elapsed = current_time - random_selection_start_time
            interval_step = elapsed // interval

            if interval_step != last_interval_step:
                while True:
                    temp = random.randint(0, 8)
                    if temp != 4 and temp != random_highlight_index:
                        break
                random_highlight_index = temp
                last_interval_step = interval_step

            if elapsed >= duration:
                random_selection_active = False
                selected_index = random_highlight_index
                current_preview_index = selected_index
                hovered_index = 4
                block_hover_if_random = True
                random_highlight_index = None

        mouse_pos = pygame.mouse.get_pos()
        if not ignore_mouse_hover_until_move and not random_selection_active:
            hovered_index = None
            for rect, index in face_rects:
                if rect.collidepoint(mouse_pos):
                    hovered_index = index
                    break

            if block_hover_if_random:
                if hovered_index is None or hovered_index == 4:
                    hovered_index = 4
                else:
                    block_hover_if_random = False

            if not block_hover_if_random and hovered_index is not None and hovered_index != current_preview_index:
                current_preview_index = hovered_index

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if name_input_rect and name_input_rect.collidepoint(event.pos):
                    name_input_active = True
                else:
                    name_input_active = False

                if hovered_index is not None and not random_selection_active:
                    if hovered_index == 4:
                        trigger_random_selection()
                    else:
                        selected_index = hovered_index
                        current_preview_index = selected_index

                if confirm_button_rect and confirm_button_rect.collidepoint(event.pos):
                    # Only accept confirm if valid selection and name entered
                    if selected_index != 4 and player_name.strip() != "":
                        if selected_index < 4:
                            print(f"Character {selected_index + 1} confirmed. Name: {player_name}")
                        else:
                            print(f"Character {selected_index} confirmed. Name: {player_name}")
                        confirm_clicked = True

            elif event.type == pygame.MOUSEMOTION:
                ignore_mouse_hover_until_move = False
            elif event.type == pygame.KEYDOWN and name_input_active:
                if event.key == pygame.K_BACKSPACE:
                    player_name = player_name[:-1]
                elif event.key == pygame.K_RETURN:
                    name_input_active = False
                elif len(player_name) < max_name_length:
                    char = event.unicode
                    if char.isprintable():
                        player_name += char
            elif event.type == pygame.KEYDOWN and not random_selection_active:
                handle_arrow_keys(event.key)
                ignore_mouse_hover_until_move = True

        name_input_rect = draw_character_grid(
            face_frames, face_size, border_frame, green_border_frame,
            player_name, name_input_active
        )
        draw_body_preview(body_frames, current_preview_index, body_border_frames[current_preview_index])

        pygame.display.flip()
        clock.tick(FPS)

    cap.release()
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
