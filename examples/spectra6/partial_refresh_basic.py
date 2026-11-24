#!/usr/bin/env python3

# This basic example draws the whole display, then refreshes one square with set_region()

from PIL import Image, ImageDraw

from inky.auto import auto

inky = auto(ask_user=True, verbose=True)

# Fill the whole display and refresh it
image = Image.new("P", (inky.width, inky.height), inky.WHITE)
draw = ImageDraw.Draw(image)
inky.set_image(image)
inky.show()

# Draw a red square, then refresh only that area
draw.rectangle((100, 100, 199, 199), fill=inky.RED)
inky.set_image(image)
inky.set_region(100, 100, 100, 100)
inky.show()
