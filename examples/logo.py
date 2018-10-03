#!/usr/bin/env python

import argparse
from PIL import Image
from inky import InkyWHAT


print("""Inky pHAT/wHAT: Logo

Displays the Inky pHAT/wHAT logo.

""")

parser = argparse.ArgumentParser()
parser.add_argument('--type', '-t', type=str, required=True, choices=["what", "phat"], help="type of display")
parser.add_argument('--colour', '-c', type=str, required=True, choices=["red", "black", "yellow"], help="ePaper display colour")
args = parser.parse_args()

colour = args.colour

if args.type == "phat":
    from inky import InkyPHAT
    inky_display = InkyPHAT(colour)
elif args.type == "what":
    from inky import InkyWHAT
    inky_display = InkyWHAT(colour)

inky_display.set_border(inky_display.BLACK)

if args.type == "phat":
    if colour == 'black':
        img = Image.open("phat/resources/InkyPhat-212x104-bw.png")
    else:
        img = Image.open("phat/resources/InkyPhat-212x104.png")
elif args.type == "what":
    img = Image.open("what/resources/InkywHAT-400x300.png")

inky_display.set_image(img)

inky_display.show()
