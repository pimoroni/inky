#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import random

from inky import InkyWHAT

from PIL import Image, ImageFont, ImageDraw
# from font_hanken_grotesk import HankenGroteskBold, HankenGroteskMedium

print("""Inky wHAT: Quotes

Display quotes on Inky wHAT

""")

try:
    import wikiquotes
except ImportError:
    exit("This script requires the wikiquotes module\nInstall with: sudo pip install wikiquotes")

# Command line arguments to set display type and colour, and enter your name

parser = argparse.ArgumentParser()
parser.add_argument('--colour', '-c', type=str, required=True, choices=["red", "black", "yellow"], help="ePaper display colour")
args = parser.parse_args()

colour = args.colour

def reflow_quote(quote, width, font):
    words = quote.split(" ")
    reflowed = '"'
    line_length = 0

    for i in range(len(words)):
        word = words[i] + " "
        word_length = font.getsize(word)[0]
        line_length += word_length

        if line_length < width:
            reflowed  += word
        else:
            line_length = word_length
            reflowed = reflowed[:-1] + "\n  " + word

    reflowed = reflowed.rstrip() + '"'

    return reflowed

# Set up the correct display and scaling factors

inky_display = InkyWHAT(colour)
inky_display.set_border(inky_display.WHITE)

w = inky_display.WIDTH
h = inky_display.HEIGHT

# Create a new canvas to draw on

img = Image.new("P", (inky_display.WIDTH, inky_display.HEIGHT))
draw = ImageDraw.Draw(img)

# Load the fonts

font_size = 24

author_font = ImageFont.truetype("/home/pi/fonts/SourceSerifPro-Semibold.ttf", font_size)
quote_font = ImageFont.truetype("/home/pi/fonts/SourceSansPro-Semibold.ttf", font_size)

people = [
    "Ada Lovelace",
    "Carl Sagan",
    "Grace Hopper",
    "Isaac Newton",
    "Marie Curie",
    "Michael Faraday",
    "Niels Bohr",
    "Rosalind Franklin"
]

padding = 30
max_width = w - padding
max_height = h - padding - author_font.getsize("ABCD ")[1]

below_max_length = False

while not below_max_length:
    person = random.choice(people)
    quote = wikiquotes.random_quote(person, "english")

    reflowed = reflow_quote(quote, max_width, quote_font)
    p_w, p_h = quote_font.getsize(reflowed)
    p_h = p_h * (reflowed.count("\n") + 1)

    if p_h < max_height:
        below_max_length = True

    else:
        continue

quote_x = (w - max_width) / 2
quote_y = ((h - max_height) + (max_height - p_h - author_font.getsize("ABCD ")[1])) / 2

author_x = quote_x
author_y = quote_y + p_h

author = "- " + person

draw.multiline_text((quote_x, quote_y), reflowed, fill=inky_display.BLACK, font=quote_font, align="left")
draw.multiline_text((author_x, author_y), author, fill=inky_display.RED, font=author_font, align="left")

h_line_length = int(w / 4.0)
v_line_length = int(h / 20.0)

draw.rectangle((padding / 4, padding / 4, w - (padding / 4), quote_y - (padding / 4)), fill=inky_display.RED)
draw.rectangle((padding / 4, author_y + author_font.getsize("ABCD ")[1] + (padding / 4) + 5, w - (padding / 4), h - (padding / 4)), fill=inky_display.RED)

inky_display.set_image(img)
inky_display.show()
