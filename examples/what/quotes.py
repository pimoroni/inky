#!/usr/bin/env python

import argparse
import random

from inky import InkyWHAT

from PIL import Image, ImageFont, ImageDraw
from font_hanken_grotesk import HankenGroteskBold, HankenGroteskMedium
from font_intuitive import Intuitive

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

def paginate_quote(quote, width, font):
    words = quote.split(" ")
    paginated = '"'
    line_length = 0

    for i in range(len(words)):
        word = words[i] + " "
        word_length = font.getsize(word)[0]
        line_length += word_length

        if line_length < width:
            paginated  += word
        else:
            line_length = word_length
            paginated = paginated[:-1] + "\n " + word

    paginated = paginated.rstrip() + '"'

    return paginated

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

author_font = ImageFont.truetype("/home/pi/fonts/caladea-italic.ttf", font_size)
quote_font = ImageFont.truetype(HankenGroteskBold, font_size)

people = [
    "Ada Lovelace",
    "Albert Einstein",
    "Carl Sagan",
    "Isaac Newton",
    "Marie Curie",
    "Michael Faraday",
    "Rosalind Franklin"
]

max_width = w - 30
max_height = h - font_size

suitable_quote = False

while not suitable_quote:
    person = random.choice(people)
    quote = wikiquotes.random_quote(person, "english")

    paginated = paginate_quote(quote, max_width, quote_font)
    p_w, p_h = quote_font.getsize(paginated)
    p_h = p_h * (paginated.count("\n") + 1)

    if p_h < max_height:
        suitable_quote = True

    else:
        continue

quote_x = (w - max_width) / 2
quote_y = ((h - max_height) + (max_height - p_h)) / 2

author_x = quote_x
author_y = quote_y + p_h

author = "- " + person

draw.multiline_text((quote_x, quote_y), paginated, fill=inky_display.BLACK, font=quote_font, align="left")
draw.multiline_text((author_x, author_y), author, fill=inky_display.RED, font=author_font, align="left")
inky_display.set_image(img)
inky_display.show()

