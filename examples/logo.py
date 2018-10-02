#!/usr/bin/env python

from PIL import Image
import sys

sys.path.insert(0, '../library/')

from inky import InkyPHAT

print("""Inky pHAT: Logo

Displays the Inky pHAT logo.

""")

if len(sys.argv) < 2:
    print("""Usage: {} <colour>
       Valid colours: red, yellow, black
""".format(sys.argv[0]))
    sys.exit(0)

colour = sys.argv[1].lower()

inkyphat = InkyPHAT(colour)

inkyphat.set_border(inkyphat.BLACK)

if colour == 'black':
    img = Image.open("InkyPhat-212x104-bw.png")
else:
    img = Image.open("InkyPhat-212x104.png")

inkyphat.set_image(img)

inkyphat.show()
