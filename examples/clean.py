#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import argparse
from PIL import Image

print("""Inky pHAT: Clean

Displays solid blocks of red, black, and white to clean the Inky pHAT
display of any ghosting.

""")

parser = argparse.ArgumentParser()
parser.add_argument('--type', '-t', type=str, required=True, choices=["what", "phat"], help="type of display")
parser.add_argument('--colour', '-c', type=str, required=True, choices=["red", "black", "yellow"], help="ePaper display colour")
parser.add_argument('--number', '-n', type=int, required=False, help="number of cycles")
args = parser.parse_args()

colour = args.colour

if args.type == "phat":
    from inky import InkyPHAT
    inky_display = InkyPHAT(colour)
elif args.type == "what":
    from inky import InkyWHAT
    inky_display = InkyWHAT(colour)

if args.number:
    cycles = args.number
else:
    cycles = 3

colours = (inky_display.RED, inky_display.BLACK, inky_display.WHITE)
colour_names= (colour, "black", "white")

img = Image.new("P", (inky_display.WIDTH, inky_display.HEIGHT))

for i in range(cycles):
    print("Cleaning cycle %i\n" % (i + 1))
    for j, c in enumerate(colours):
        print("- updating with %s" % colour_names[j])
        inky_display.set_border(c)
        for x in range(inky_display.WIDTH):
            for y in range(inky_display.HEIGHT):
                img.putpixel((x, y), c)
        inky_display.set_image(img)
        inky_display.show()
        time.sleep(1)
    print("\n")

print("Cleaning complete!")
