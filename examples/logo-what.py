#!/usr/bin/env python

from PIL import Image
import sys

sys.path.insert(0, '../library/')

from inky import what as inkywhat

inkywhat.set_colour('yellow')

print("""Inky wHAT: Logo

Displays the Inky wHAT logo.

""")

if len(sys.argv) < 2:
    print("""Usage: {} <colour>
       Valid colours: red, yellow, black
""".format(sys.argv[0]))
    sys.exit(0)

colour = sys.argv[1].lower()
inkywhat.set_colour(colour)

inkywhat.set_border(inkywhat.BLACK)

if colour == 'black':
    img = Image.open("InkyPhat-212x104-bw.png")
else:
    img = Image.open("InkyPhat-212x104.png")

inkywhat.set_image(img)

inkywhat.show()
