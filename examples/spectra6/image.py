#!/usr/bin/env python3

import argparse
import pathlib
import sys

from PIL import Image

from inky.auto import auto

parser = argparse.ArgumentParser()

parser.add_argument("--saturation", "-s", type=float, default=0.5, help="Colour palette saturation")
parser.add_argument("--file", "-f", type=pathlib.Path, help="Image file")

inky = auto(ask_user=True, verbose=True)

args, _ = parser.parse_known_args()

saturation = args.saturation

if not args.file:
    print(f"""Usage:
    {sys.argv[0]} --file image.png (--saturation 0.5)""")
    sys.exit(1)

image = Image.open(args.file)
resizedimage = image.resize(inky.resolution)

try:
    inky.set_image(resizedimage, saturation=saturation)
except TypeError:
    inky.set_image(resizedimage)

inky.show()
