#!/usr/bin/env python3

import argparse
from PIL import Image
from inky.auto import auto

print("""Inky wHAT: Dither image

Converts and displays dithered images on Inky wHAT.
""")

# Set up the inky wHAT display and border colour

inky_display = auto(ask_user=True, verbose=True)
inky_display.set_border(inky_display.WHITE)

# Grab the image argument from the command line

parser = argparse.ArgumentParser()
parser.add_argument('--image', '-i', type=str, required=True, help="Input image to be converted/displayed")
args, _ = parser.parse_known_args()

img_file = args.image

# Open our image file that was passed in from the command line

img = Image.open(img_file)

# Get the width and height of the image

w, h = img.size

# Calculate the new height and width of the image

h_new = 300
w_new = int((float(w) / h) * h_new)
w_cropped = 400

# Resize the image with high-quality resampling

img = img.resize((w_new, h_new), resample=Image.LANCZOS)

# Calculate coordinates to crop image to 400 pixels wide

x0 = (w_new - w_cropped) / 2
x1 = x0 + w_cropped
y0 = 0
y1 = h_new

# Crop image

img = img.crop((x0, y0, x1, y1))

# Convert the image to use a white / black / red colour palette

pal_img = Image.new("P", (1, 1))
pal_img.putpalette((255, 255, 255, 0, 0, 0, 255, 0, 0) + (0, 0, 0) * 252)

img = img.convert("RGB").quantize(palette=pal_img)

# Display the final image on Inky wHAT

inky_display.set_image(img)
inky_display.show()
