import cv2
import numpy as np
import os
import matplotlib.pyplot as plt
from matplotlib.widgets import Button

# Folder paths
input_folder = "Frames/DamTurbineLoopFrames"
output_folder = "Cropped Frames/DamTurbine4FlowFrames"
os.makedirs(output_folder, exist_ok=True)

# Globals
polygon_points = []
done_drawing = False
first_image = None
fig, ax = None, None
toolbar = None

# Draw the polygon on the image
def draw_polygon():
    # Preserve current zoom state
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()

    ax.clear()
    ax.imshow(first_image)
    ax.set_title("Click to draw polygon. Press 'Finish' when done.\n'u' to undo, zoom/pan with toolbar")

    if polygon_points:
        xs, ys = zip(*polygon_points)
        ax.plot(xs, ys, 'ro-')
        if len(polygon_points) > 2:
            ax.plot([xs[-1], xs[0]], [ys[-1], ys[0]], 'r-')

    # Restore zoom state
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    fig.canvas.draw()

# Handle click events
def onclick(event):
    if toolbar.mode != '' or event.inaxes is None:
        return  # Ignore if zoom/pan active or click outside image

    if event.xdata is not None and event.ydata is not None:
        x, y = int(event.xdata), int(event.ydata)
        if (x, y) != (0, 0):
            polygon_points.append((x, y))
            draw_polygon()
        else:
            print("Ignored click at (0, 0)")

# Handle keypress
def on_key(event):
    if event.key == 'u' and polygon_points:
        polygon_points.pop()
        draw_polygon()

# Handle Finish button
def on_finish(event):
    global done_drawing
    done_drawing = True
    plt.close()

# Create mask from polygon
def create_mask(image_shape, polygon_points):
    mask = np.zeros(image_shape[:2], dtype=np.uint8)
    pts = np.array(polygon_points, dtype=np.int32)
    cv2.fillPoly(mask, [pts], 255)
    return mask

# Apply mask to image
def apply_mask(image, mask):
    return cv2.bitwise_and(image, image, mask=mask)

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
img_artist = ax.imshow(first_image)
ax.set_title("Click to draw polygon. Press 'Finish' when done.\n'u' to undo, zoom/pan with toolbar")

# Grab the toolbar reference
toolbar = plt.get_current_fig_manager().toolbar

# Connect events
fig.canvas.mpl_connect('button_press_event', onclick)
fig.canvas.mpl_connect('key_press_event', on_key)

# Add Finish button
finish_ax = plt.axes([0.81, 0.05, 0.1, 0.075])
button = Button(finish_ax, 'Finish')
button.on_clicked(on_finish)

plt.show()

# Process if drawing was completed
if done_drawing and len(polygon_points) >= 3:
    print("Drawing complete. Applying crop to all frames...")

    mask = create_mask(first_image.shape, polygon_points)
    x, y, w, h = cv2.boundingRect(np.array(polygon_points))

    for filename in image_files:
        input_path = os.path.join(input_folder, filename)
        output_path = os.path.join(output_folder, filename)

        image = cv2.imread(input_path)
        masked_image = apply_mask(image, mask)
        cropped = masked_image[y:y+h, x:x+w]

        cv2.imwrite(output_path, cropped)
        print(f"Saved: {output_path}")
else:
    print("Polygon was not drawn or had fewer than 3 points.")
