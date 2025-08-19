# This basic example shows how to draw shapes and text on Inky pHAT using PIL.

from font_fredoka_one import FredokaOne
from PIL import Image, ImageDraw, ImageFont

from inky.auto import auto

inky_display = auto(ask_user=True, verbose=True)

WIDTH, HEIGHT = inky_display.width, inky_display.height

# Create new PIL image with a white background
image = Image.new("P", (WIDTH, HEIGHT), inky_display.WHITE)
draw = ImageDraw.Draw(image)

font = ImageFont.truetype(FredokaOne, 18)

# draw some shapes
draw.rectangle((100, 0, 170, 50), fill=inky_display.YELLOW)  # Rectangle
draw.ellipse((90, 90, 180, 180), fill=inky_display.RED)  # Circle (ellipse)


# draw some text
draw.text((80, 60), "Hello, World!", inky_display.BLACK, font)

inky_display.set_image(image)
inky_display.show()
