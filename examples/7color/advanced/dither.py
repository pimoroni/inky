#!/usr/bin/env python3

import sys

import hitherdither
from inky.inky_uc8159 import Inky
from PIL import Image

print("""dither.py

Advanced dithering example using Hitherdither by Henrik Blidh:
https://github.com/hbldh/hitherdither

You should read the code, read the README ^ and edit accordingly.

Many of these dithering processes are slow, you might want to pre-prepare an image!

You will need to install hitherdither from GitHub:

sudo python3 -m pip install git+https://www.github.com/hbldh/hitherdither


usage: ./dither.py <image_file> <saturation>

- Image file should be RGB and can be a jpg, PNG or otherwise.

- Saturation should be from 0.0 to 1.0 and changes the palette that's used to dither the image.
  a higher saturation will generally result in a more saturated end image due to how colours are mixed.

""")

inky = Inky()
saturation = 0.5           # Saturation of palette
thresholds = [64, 64, 64]  # Threshold for snapping colours, I guess?

if len(sys.argv) == 1:
    print("""
Usage: {file} image-file
""".format(file=sys.argv[0]))
    sys.exit(1)

if len(sys.argv) > 2:
    saturation = float(sys.argv[2])

palette = hitherdither.palette.Palette(inky._palette_blend(saturation, dtype='uint24'))

image = Image.open(sys.argv[1]).convert("RGB")
# VERY slow (1m 40s on a Pi 4) - see https://github.com/hbldh/hitherdither for a list of methods
# image_dithered = hitherdither.diffusion.error_diffusion_dithering(image, palette, method="stucki", order=2)

# Usably quick, your vanilla dithering
# image_dithered = hitherdither.ordered.bayer.bayer_dithering(image, palette, thresholds, order=8)

# Usuably quick, half-tone comic-book feel, use order=4 for small dots and order=8 dot bigguns
image_dithered = hitherdither.ordered.cluster.cluster_dot_dithering(image, palette, thresholds, order=8)

# VERY slow
# image_dithered = hitherdither.ordered.yliluoma.yliluomas_1_ordered_dithering(image, palette, order=8)

inky.set_image(image_dithered.convert("P"))
inky.show()
