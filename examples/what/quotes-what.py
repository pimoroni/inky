#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import random
import sys

from inky.auto import auto

from PIL import Image, ImageFont, ImageDraw
from font_source_serif_pro import SourceSerifProSemibold
from font_source_sans_pro import SourceSansProSemibold

print("""Inky wHAT: Quotes

Display quotes on Inky wHAT.
""")

try:
    import wikiquotes
except ImportError:
    print("""This script requires the wikiquotes module.

Install with:
    sudo apt install python3-lxml
    python3 -m pip install wikiquotes
""")
    sys.exit(1)

# Set up the correct display and scaling factors

inky_display = auto(ask_user=True, verbose=True)
inky_display.set_border(inky_display.WHITE)
# inky_display.set_rotation(180)

def getsize(font, text):
    _, _, right, bottom = font.getbbox(text)
    return (right, bottom)

# This function will take a quote as a string, a width to fit
# it into, and a font (one that's been loaded) and then reflow
# that quote with newlines to fit into the space required.
def reflow_quote(quote, width, font):
    words = quote.split(" ")
    reflowed = '"'
    line_length = 0

    for i in range(len(words)):
        word = words[i] + " "
        word_length = getsize(font, word)[0]
        line_length += word_length

        if line_length < width:
            reflowed += word
        else:
            line_length = word_length
            reflowed = reflowed[:-1] + "\n  " + word

    reflowed = reflowed.rstrip() + '"'

    return reflowed


WIDTH = inky_display.width
HEIGHT = inky_display.height

# Create a new canvas to draw on

img = Image.new("P", (WIDTH, HEIGHT))
draw = ImageDraw.Draw(img)

# Load the fonts

font_size = 24

author_font = ImageFont.truetype(SourceSerifProSemibold, font_size)
quote_font = ImageFont.truetype(SourceSansProSemibold, font_size)


# A list of famous scientists to search for quotes from
# on https://en.wikiquote.org. Change them to your
# favourite people, if you like!

people = [
    "Ada Lovelace",
    "Carl Sagan",
    "Charles Darwin",
    "Dorothy Hodgkin",
    "Edith Clarke",
    "Grace Hopper",
    "Hedy Lamarr",
    "Isaac Newton",
    "James Clerk Maxwell",
    "Margaret Hamilton",
    "Marie Curie",
    "Michael Faraday",
    "Niels Bohr",
    "Nikola Tesla",
    "Rosalind Franklin",
    "Stephen Hawking"
]

# The amount of padding around the quote. Note that
# a value of 30 means 15 pixels padding left and 15
# pixels padding right.
#
# Also define the max width and height for the quote.

padding = 50
max_width = WIDTH - padding
max_height = HEIGHT - padding - getsize(author_font, "ABCD ")[1]

below_max_length = False

# Only pick a quote that will fit in our defined area
# once rendered in the font and size defined.

while not below_max_length:
    person = random.choice(people)           # Pick a random person from our list
    quote = wikiquotes.random_quote(person, "english")

    reflowed = reflow_quote(quote, max_width, quote_font)
    p_w, p_h = getsize(quote_font, reflowed)  # Width and height of quote
    p_h = p_h * (reflowed.count("\n") + 1)   # Multiply through by number of lines

    if p_h < max_height:
        below_max_length = True              # The quote fits! Break out of the loop.

    else:
        continue

# x- and y-coordinates for the top left of the quote

quote_x = (WIDTH - max_width) / 2
quote_y = ((HEIGHT - max_height) + (max_height - p_h - getsize(author_font, "ABCD ")[1])) / 2

# x- and y-coordinates for the top left of the author

author_x = quote_x
author_y = quote_y + p_h

author = "- " + person

# Draw red rectangles top and bottom to frame quote

draw.rectangle(
    (
        padding / 4,
        padding / 4,
        WIDTH - (padding / 4),
        quote_y - (padding / 4)
    ), fill=inky_display.RED)

draw.rectangle(
    (
        padding / 4,
        author_y + getsize(author_font, "ABCD ")[1] + (padding / 4) + 5,
        WIDTH - (padding / 4),
        HEIGHT - (padding / 4)
    ), fill=inky_display.RED)

# Add some white hatching to the red rectangles to make
# it look a bit more interesting

hatch_spacing = 12

for x in range(0, 2 * WIDTH, hatch_spacing):
    draw.line((x, 0, x - WIDTH, HEIGHT), fill=inky_display.WHITE, width=3)

# Write our quote and author to the canvas

draw.multiline_text((quote_x, quote_y), reflowed, fill=inky_display.BLACK, font=quote_font, align="left")
draw.multiline_text((author_x, author_y), author, fill=inky_display.RED, font=author_font, align="left")

print(reflowed + "\n" + author + "\n")

# Display the completed canvas on Inky wHAT

inky_display.set_image(img)
inky_display.show()
