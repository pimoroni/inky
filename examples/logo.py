#!/usr/bin/env python

import os
import argparse
from PIL import Image
from inky.auto import auto
from inky import InkyWHAT, InkyPHAT, InkyPHAT_SSD1608


print("""Inky pHAT/wHAT: Logo

Displays the Inky pHAT/wHAT logo.

""")

# Get the current path

PATH = os.path.dirname(__file__)

# Try to auto-detect the display from the EEPROM
try:
    inky_display = auto()
    print("Auto-detected {}".format(inky_display.eeprom.get_variant()))
except RuntimeError:
    inky_display = None

# Parse the command-line and try manual display setup
if inky_display is None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--type', '-t', type=str, required=False, default="auto", choices=["auto", "what", "phat", "phatssd1608"], help="type of display")
    parser.add_argument('--colour', '-c', type=str, required=False, choices=["red", "black", "yellow"], help="ePaper display colour")
    args = parser.parse_args()

    if args.type == "phat":
        inky_display = InkyPHAT(colour)
    elif args.type == "phatssd1608":
        inky_display = InkyPHAT_SSD1608(colour)
    elif args.type == "what":
        inky_display = InkyWHAT(colour)
    elif args.type == "auto":
        raise RuntimeError("Failed to auto-detect your Inky board type.")

inky_display.set_border(inky_display.BLACK)

# Pick the correct logo image to show depending on display resolution/colour

if inky_display.resolution in ((212, 104), (250, 122)):
    if inky_display.resolution == (250, 122):
        if inky_display.colour == 'black':
            img = Image.open(os.path.join(PATH, "phat/resources/InkypHAT-250x122-bw.png"))
        else:
            img = Image.open(os.path.join(PATH, "phat/resources/InkypHAT-250x122.png"))

    else:
        if inky_display.colour == 'black':
            img = Image.open(os.path.join(PATH, "phat/resources/InkypHAT-212x104-bw.png"))
        else:
            img = Image.open(os.path.join(PATH, "phat/resources/InkypHAT-212x104.png"))

elif inky_display.resolution in ((400, 300)):
    if inky_display.colour == 'black':
        img = Image.open(os.path.join(PATH, "what/resources/InkywHAT-400x300-bw.png"))
    else:
        img = Image.open(os.path.join(PATH, "what/resources/InkywHAT-400x300.png"))

# Display the logo image

inky_display.set_image(img)
inky_display.show()
