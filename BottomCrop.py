import cv2
import os

# Folder paths
input_folder = "assets2/RoRLoopFrames"
output_folder = "assets2/RoRBottom"
os.makedirs(output_folder, exist_ok=True)

# Supported image types
valid_exts = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff')

# Get list of images
image_files = [f for f in sorted(os.listdir(input_folder)) if f.lower().endswith(valid_exts)]
if not image_files:
    print(f"No valid image files found in {input_folder}.")
    exit()

# Process each image
for filename in image_files:
    input_path = os.path.join(input_folder, filename)
    output_path = os.path.join(output_folder, filename)

    image = cv2.imread(input_path)
    if image is None:
        print(f"Failed to read {filename}, skipping.")
        continue

    h = image.shape[0]
    cropped = image[h // 3:h]  # bottom two-thirds of the image

    cv2.imwrite(output_path, cropped)
    print(f"Saved: {output_path}")
