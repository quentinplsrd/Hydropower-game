import cv2
import numpy as np
import os
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
import json

# Folder paths
input_folder = "assets2/PSHSequences/PSHLevelFrames"
output_folder = "assets2/PSHSequences/PSHTurbineCut"
os.makedirs(output_folder, exist_ok=True)

# Globals
crop_points = []
done_drawing = False
first_image = None
fig, ax = None, None
toolbar = None

def draw_rectangle():
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()

    ax.clear()
    ax.imshow(first_image)
    ax.set_title("Click two corners for rectangular crop. 'r' to reset.")

    if len(crop_points) == 1:
        ax.plot(*crop_points[0], 'go')
    elif len(crop_points) == 2:
        x1, y1 = crop_points[0]
        x2, y2 = crop_points[1]
        rect = plt.Rectangle((x1, y1), x2 - x1, y2 - y1,
                             linewidth=2, edgecolor='r', facecolor='none')
        ax.add_patch(rect)

    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    fig.canvas.draw()

def onclick(event):
    if toolbar.mode != '' or event.inaxes is None:
        return  # Ignore if zoom/pan is active

    if event.xdata is not None and event.ydata is not None:
        if len(crop_points) < 2:
            crop_points.append((int(event.xdata), int(event.ydata)))
            draw_rectangle()

def on_key(event):
    global crop_points
    if event.key == 'r':
        crop_points = []
        draw_rectangle()

def on_finish(event):
    global done_drawing
    if len(crop_points) == 2:
        done_drawing = True
        plt.close()
    else:
        print("You must select two corners before finishing.")

# --- Main ---

# Load image files
valid_exts = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff')
image_files = [f for f in sorted(os.listdir(input_folder)) if f.lower().endswith(valid_exts)]
if not image_files:
    print(f"No images found in {input_folder}.")
    exit()

# Load first image
first_image_path = os.path.join(input_folder, image_files[0])
first_image = cv2.cvtColor(cv2.imread(first_image_path), cv2.COLOR_BGR2RGB)

# Set up plot
fig, ax = plt.subplots()
plt.subplots_adjust(bottom=0.2)
ax.imshow(first_image)
ax.set_title("Click two corners for rectangular crop. 'r' to reset.")
toolbar = plt.get_current_fig_manager().toolbar

# Event connections
fig.canvas.mpl_connect('button_press_event', onclick)
fig.canvas.mpl_connect('key_press_event', on_key)

# Finish button
finish_ax = plt.axes([0.81, 0.05, 0.1, 0.075])
button = Button(finish_ax, 'Finish')
button.on_clicked(on_finish)

plt.show()

if done_drawing:
    print("Applying rectangular crop to all frames...")

    x1, y1 = crop_points[0]
    x2, y2 = crop_points[1]

    x_min, x_max = sorted([x1, x2])
    y_min, y_max = sorted([y1, y2])

    # Save top-left corner
    corner_data = {"top_left_x": x_min, "top_left_y": y_min}
    json_path = os.path.join(output_folder, "crop_coords.json")
    with open(json_path, "w") as f:
        json.dump(corner_data, f)
    print(f"Saved corner coordinates to: {json_path}")

    for filename in image_files:
        input_path = os.path.join(input_folder, filename)
        output_path = os.path.join(output_folder, filename)

        image = cv2.imread(input_path)
        cropped = image[y_min:y_max, x_min:x_max]

        cv2.imwrite(output_path, cropped)
        print(f"Saved: {output_path}")
else:
    print("Rectangle not fully defined — no crop applied.")