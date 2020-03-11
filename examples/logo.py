#!/usr/bin/env python

import os
import argparse
from PIL import Image


print("""Inky pHAT/wHAT: Logo

Displays the Inky pHAT/wHAT logo.

""")

# Get the current path

PATH = os.path.dirname(__file__)

# Command line arguments to set display type and colour

parser = argparse.ArgumentParser()
parser.add_argument('--mock', '-m', required=False, action='store_true', help="Simulate Inky using MatPlotLib")
parser.add_argument('--type', '-t', type=str, required=True, choices=["what", "phat"], help="type of display")
parser.add_argument('--colour', '-c', type=str, required=True, choices=["red", "black", "yellow"], help="ePaper display colour")
args = parser.parse_args()

if args.mock:
    from inky import InkyMockPHAT as InkyPHAT
    from inky import InkyMockWHAT as InkyWHAT
else:
    from inky import InkyWHAT, InkyPHAT

colour = args.colour

# Set up the correct display and scaling factors

if args.type == "phat":
    inky_display = InkyPHAT(colour)
elif args.type == "what":
    inky_display = InkyWHAT(colour)

inky_display.set_border(inky_display.BLACK)

# Pick the correct logo image to show depending on display type/colour

if args.type == "phat":
    if colour == 'black':
        img = Image.open(os.path.join(PATH, "phat/resources/InkypHAT-212x104-bw.png"))
    else:
        img = Image.open(os.path.join(PATH, "phat/resources/InkypHAT-212x104.png"))
elif args.type == "what":
    if colour == 'black':
        img = Image.open(os.path.join(PATH, "what/resources/InkywHAT-400x300-bw.png"))
    else:
        img = Image.open(os.path.join(PATH, "what/resources/InkywHAT-400x300.png"))

# Display the logo image

inky_display.set_image(img)
inky_display.show()

if args.mock:
    print("Press Ctrl+C or close window to exit...")
    inky_display.wait_for_window_close()
