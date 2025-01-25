from PIL import Image

INPUT_IMG_NAME = 'ex_1.png'
OUTPUT_IMG_NAME = 'output.png'

def resize_to_fixed_w_h():
    w = 24                                  # fixed
    h = 24                                  # fixed
    img = Image.open(INPUT_IMG_NAME)
    img = img.resize((w, h), resample=Image.LANCZOS)
    img.save(OUTPUT_IMG_NAME)

def resize_by_scale():
    scale_percentage = 0.5
    img = Image.open(INPUT_IMG_NAME)
    width, height = img.size
    w = int(width * scale_percentage)
    h = int(height * scale_percentage)
    img = img.resize((w, h), resample=Image.LANCZOS)
    img.save(OUTPUT_IMG_NAME)

def resize_by_w_same_ratio():
    img = Image.open(INPUT_IMG_NAME)
    width, height = img.size
    w = 600                                 # fixed
    scale_percentage = w / width
    h = int(height * scale_percentage)
    img = img.resize((w, h), resample=Image.LANCZOS)
    img.save(OUTPUT_IMG_NAME)

def resize_by_h_same_ratio():
    img = Image.open(INPUT_IMG_NAME)
    width, height = img.size
    h = 750                                 # fixed
    scale_percentage = h / height
    w = int(width * scale_percentage)
    img = img.resize((w, h), resample=Image.LANCZOS)
    img.save(OUTPUT_IMG_NAME)

resize_by_w_same_ratio()