#!/usr/bin/env python

import argparse

from PIL import Image, ImageFont, ImageDraw
from fonts.ttf import AmaticSCBold

from inky import InkyPHAT

print("""Inky pHAT: Hello... my name is:

Use Inky pHAT as a personalised name badge!

""")

#inkyphat.set_rotation(180)

parser = argparse.ArgumentParser()
parser.add_argument('--colour', '-c', type=str, required=True, choices=["red", "black", "yellow"], help="ePaper display colour")
parser.add_argument('--name', '-n', type=str, required=True, help="Your name")
args = parser.parse_args()

colour = args.colour

inky_display = InkyPHAT(colour)

# Show the backdrop image

#inky_display.set_border(inky_display.RED)
img = Image.new("P", (inky_display.WIDTH, inky_display.HEIGHT))
draw = ImageDraw.Draw(img)

# Add the text

intuitive_font = ImageFont.truetype("/home/pi/fonts/intuitive.ttf", 24)
hanken_bold_font = ImageFont.truetype("/home/pi/fonts/HankenGrotesk-Bold.otf", 34)
hanken_regular_font = ImageFont.truetype("/home/pi/fonts/HankenGrotesk-Regular.otf", 16)

name = args.name

# Center the text and align it with the name strip

y_top = int(inky_display.HEIGHT * (5.0 / 10.0))
y_bottom = y_top + int(inky_display.HEIGHT * (4.0 / 10.0))

for y in range(0, y_top):
    for x in range(0, inky_display.width):
        img.putpixel((x, y), inky_display.RED)

for y in range(y_top, y_bottom):
    for x in range(0, inky_display.width):
        img.putpixel((x, y), inky_display.WHITE)

for y in range(y_bottom, inky_display.HEIGHT):
    for x in range(0, inky_display.width):
        img.putpixel((x, y), inky_display.RED)

hello_w, hello_h = hanken_bold_font.getsize("Hello")
hello_x = int((inky_display.WIDTH - hello_w) / 2)
hello_y = 0
draw.text((hello_x, hello_y), "Hello", inky_display.WHITE, font=hanken_bold_font)

mynameis_w, mynameis_h = hanken_regular_font.getsize("my name is")
mynameis_x = int((inky_display.WIDTH - mynameis_w) / 2)
mynameis_y = hello_h
draw.text((mynameis_x, mynameis_y), "my name is", inky_display.WHITE, font=hanken_regular_font)

name_w, name_h = intuitive_font.getsize(name)
name_x = int((inky_display.WIDTH - name_w) / 2)
name_y = int(y_top + ((y_bottom - y_top - name_h) / 2))
draw.text((name_x, name_y), name, inky_display.BLACK, font=intuitive_font)

inky_display.set_image(img)
inky_display.show()
