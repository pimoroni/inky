#!/usr/bin/env python3

import sys

from PIL import Image
from inky.inky_uc8159 import Inky

inky = Inky()
saturation = 0.5

if len(sys.argv) == 1:
    print("""
Usage: {file} image-file
""".format(file=sys.argv[0]))
    sys.exit(1)

image = Image.open(sys.argv[1])

if len(sys.argv) > 2:
    saturation = float(sys.argv[2])

inky.set_image(image, saturation=saturation)
inky.show()
