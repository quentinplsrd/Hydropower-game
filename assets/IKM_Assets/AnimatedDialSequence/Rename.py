import os

# Supported image extensions
image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp']

# List all files in the current directory
files = os.listdir('.')

# Filter and sort image files
image_files = sorted(f for f in files if os.path.splitext(f)[1].lower() in image_extensions)

# Rename each file
for idx, filename in enumerate(image_files):
    ext = os.path.splitext(filename)[1].lower()
    new_name = f'Dial_{idx}{ext}'
    os.rename(filename, new_name)
    print(f'Renamed {filename} -> {new_name}')
