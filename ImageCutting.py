from PIL import Image
import os
 
def crop_images(image_dir, output_dir, crop_box):
    """
    Crops multiple images in a directory using the same rectangular selection.

    Args:
        image_dir (str): Path to the directory containing the images.
        output_dir (str): Path to the directory where cropped images will be saved.
        crop_box (tuple): A tuple representing the crop box (left, upper, right, lower).
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for filename in os.listdir(image_dir):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            image_path = os.path.join(image_dir, filename)
            try:
                img = Image.open(image_path)
                cropped_img = img.crop(crop_box)
                output_path = os.path.join(output_dir, filename)
                cropped_img.save(output_path)
                print(f"Cropped and saved: {filename}")
            except Exception as e:
                print(f"Error processing {filename}: {e}")

if __name__ == '__main__':
    image_directory = "."  # Replace with your image directory
    output_directory = "./Cropped/"  # Replace with your output directory
    crop_rectangle = (860, 100, 1000, 355)  # Example crop box (left, upper, right, lower)
    #Gate 1: crop_rectangle = (450, 200, 610, 600)
    #Gate 2: crop_rectangle = (600, 200, 750, 500)
    #Gate 3: crop_rectangle = (740, 150, 860, 450)
    #Gate 4: crop_rectangle = (860, 100, 1000, 355)
    crop_images(image_directory, output_directory, crop_rectangle)