#!/usr/bin/env python

import os
from PIL import Image
from inky.auto import auto


print("""Inky pHAT/wHAT: Logo

Displays the Inky pHAT/wHAT logo.

""")

# Get the current path
PATH = os.path.dirname(__file__)

# Set up the Inky display
try:
    inky_display = auto(ask_user=True, verbose=True)
except TypeError:
    raise TypeError("You need to update the Inky library to >= v1.1.0")

try:
    inky_display.set_border(inky_display.BLACK)
except NotImplementedError:
    pass

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

elif inky_display.resolution in ((400, 300), ):
    if inky_display.colour == 'black':
        img = Image.open(os.path.join(PATH, "what/resources/InkywHAT-400x300-bw.png"))
    else:
        img = Image.open(os.path.join(PATH, "what/resources/InkywHAT-400x300.png"))

elif inky_display.resolution in ((600, 448), ):
    img = Image.open(os.path.join(PATH, "what/resources/InkywHAT-400x300.png"))
    img = img.resize(inky_display.resolution)

# Display the logo image

inky_display.set_image(img)
inky_display.show()
