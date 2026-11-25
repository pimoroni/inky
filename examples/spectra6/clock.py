#!/usr/bin/env python3

import datetime
import pathlib
import time

from font_fredoka_one import FredokaOne
from PIL import Image, ImageDraw, ImageFont, ImageOps

from inky.auto import auto

print(
    """clock.py - A painting with a clock along the bottom

This example demonstrates how to:
 1. show a painting with a clock bar underneath it,
 2. use set_region() so only the time is refreshed each minute

The whole display refreshes when the example starts and then once an hour.
Every other minute only the time refreshes, and the painting stays as it is.

Hang your Inky Impression in portrait, turned a quarter turn clockwise.
Press Ctrl+C to exit!

"""
)

inky = auto(ask_user=True, verbose=True)

if not hasattr(inky, "set_region"):
    raise SystemExit("This example needs an Inky Impression with a Spectra 6 display!")

# Speed for the minute-by-minute clock updates.
# FAST refreshes quicker, but the colours are less vivid.
# Try inky.MEDIUM or inky.NORMAL to compare
CLOCK_SPEED = inky.FAST

# The painting to show, from the images folder next to this example
IMAGE = pathlib.Path(__file__).parent / "images" / "vincent-van-gogh-inky13.jpg"

# We draw in portrait, so the width and height are swapped.
# The picture is turned to suit the display just before it's shown
WIDTH, HEIGHT = inky.height, inky.width

# The bar, text and line sizes scale with the display, so the example fits every size
BAR_HEIGHT = HEIGHT // 8
BAR_TOP = HEIGHT - BAR_HEIGHT
BAR_MIDDLE = BAR_TOP + BAR_HEIGHT // 2
PADDING = BAR_HEIGHT // 4
LINE_WIDTH = max(2, BAR_HEIGHT // 40)

font_time = ImageFont.truetype(FredokaOne, int(BAR_HEIGHT * 0.6))
font_date = ImageFont.truetype(FredokaOne, int(BAR_HEIGHT * 0.25))

# Work out the width of the widest time we could draw, such as "00:00" or "88:88".
# The time area is made that wide, so it stays put as the digits change
widest_time = max(font_time.getlength(f"{digit}{digit}:{digit}{digit}") for digit in "0123456789")
TIME_AREA_WIDTH = min(WIDTH, int(widest_time) + PADDING * 2)

# Areas to refresh as (x, y, width, height), in portrait
BAR_AREA = (0, BAR_TOP, WIDTH, BAR_HEIGHT)
TIME_AREA = (0, BAR_TOP, TIME_AREA_WIDTH, BAR_HEIGHT)

# Saturation of the palette used to dither the painting. set_image() uses the same by default
SATURATION = 0.5

# The bundled painting is stored on its side. Stand it up and crop it to fit
painting = Image.open(IMAGE).transpose(Image.Transpose.ROTATE_270)
painting = ImageOps.fit(painting, (WIDTH, HEIGHT))

# Dither the painting into the display's six colours once, at the start.
# It then comes out exactly the same every time we draw the clock over it
palette = Image.new("P", (1, 1))
palette.putpalette(inky._palette_blend(SATURATION))
painting = painting.quantize(6, palette=palette, dither=Image.Dither.FLOYDSTEINBERG)


def set_portrait_region(x, y, width, height):
    # The picture is turned a quarter turn before it's shown.
    # This turns a portrait area the same way, to match it on the display
    display_x = y
    display_y = WIDTH - x - width
    inky.set_region(display_x, display_y, height, width)


# The day of the last refresh, so we can tell when the date changes
last_day = None

while True:
    now = datetime.datetime.now()

    # Start from a copy of the painting and draw the clock bar over it
    frame = painting.copy()
    draw = ImageDraw.Draw(frame)

    # Draw text without anti-aliasing to keep it to the display's six colours
    draw.fontmode = "1"

    # A black bar with a yellow line along its top
    draw.rectangle((0, BAR_TOP, WIDTH, HEIGHT), fill=inky.BLACK)
    draw.line((0, BAR_TOP, WIDTH, BAR_TOP), fill=inky.YELLOW, width=LINE_WIDTH)

    # The time on the left, and the day and date on the right
    draw.text((PADDING, BAR_MIDDLE), f"{now:%H:%M}", inky.YELLOW, font_time, anchor="lm")
    draw.text((WIDTH - PADDING, BAR_MIDDLE), f"{now:%A}", inky.WHITE, font_date, anchor="rd")
    draw.text((WIDTH - PADDING, BAR_MIDDLE), f"{now.day} {now:%B}", inky.WHITE, font_date, anchor="ra")

    # Turn the picture to suit the display and copy it across
    inky.set_image(frame.transpose(Image.Transpose.ROTATE_90))

    if last_day is None or now.minute == 0:
        # Refresh everything at the start and on the hour to keep the colours fresh.
        # Faster speeds lose some colour, so the painting always gets a normal refresh
        kind = "full"
        inky.speed = inky.NORMAL
        inky.reset_region()
    elif now.date() != last_day:
        # The day has changed, so refresh the whole bar to update the date too
        kind = "time and date"
        inky.speed = CLOCK_SPEED
        set_portrait_region(*BAR_AREA)
    else:
        # Only the time has changed
        kind = "time"
        inky.speed = CLOCK_SPEED
        set_portrait_region(*TIME_AREA)

    last_day = now.date()

    start = time.monotonic()
    inky.show()
    print(f"{now:%H:%M} {kind} refresh took {time.monotonic() - start:.1f}s")

    # Wait for the next minute, unless the refresh has already run into it
    if f"{datetime.datetime.now():%H:%M}" == f"{now:%H:%M}":
        time.sleep(60 - time.time() % 60)
