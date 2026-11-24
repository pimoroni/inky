#!/usr/bin/env python3

import time
from datetime import timedelta

import gpiod
import gpiodevice
from font_fredoka_one import FredokaOne
from gpiod.line import Bias, Direction, Edge, Value
from PIL import Image, ImageDraw, ImageFont

from inky.auto import auto

print(
    """partial_refresh_buttons.py - Refresh one part of the display at a time

This example demonstrates how to:
 1. draw a strip on the display for each button,
 2. use set_region() so a button press only refreshes its own strip

Only the strip next to the button you press will refresh.
The rest of the display stays as it is.
The LED lights up while the display is busy.

Press Ctrl+C to exit!

"""
)

inky = auto(ask_user=True, verbose=True)

if not hasattr(inky, "set_region"):
    raise SystemExit("This example needs an Inky Impression with a Spectra 6 display!")

# FAST refreshes quicker, but the colours are less vivid.
# Try inky.MEDIUM or inky.NORMAL to compare
inky.speed = inky.FAST

# GPIO pins for each button (from top to bottom)
# These will vary depending on platform and the ones
# below should be correct for Raspberry Pi 5.
# Run "gpioinfo" to find out what yours might be.
#
# Raspberry Pi 5 Header pins used by Inky Impression:
#    PIN29, PIN31, PIN36, PIN18.
# These header pins correspond to BCM GPIO numbers:
#    GPIO05, GPIO06, GPIO16, GPIO24.
# These GPIO numbers are what is used below and not the
# header pin numbers.
#
# The 13.3" Impression uses GPIO16 for the display,
# so its button C is on GPIO25 (PIN22) instead.
SW_A = 5
SW_B = 6
SW_C = 25 if inky.resolution == (1600, 1200) else 16
SW_D = 24

BUTTONS = [SW_A, SW_B, SW_C, SW_D]

# These correspond to buttons A, B, C and D respectively
LABELS = ["A", "B", "C", "D"]

# The LED is on GPIO13 (PIN33)
LED_PIN = 13

# Create settings for the button pins, we want them to be inputs
# with a pull-up and a falling edge detection.
# The debounce period stops one press being seen as several.
BUTTON_SETTINGS = gpiod.LineSettings(direction=Direction.INPUT, bias=Bias.PULL_UP, edge_detection=Edge.FALLING, debounce_period=timedelta(milliseconds=20))

# The LED pin is an output
LED_SETTINGS = gpiod.LineSettings(direction=Direction.OUTPUT, bias=Bias.DISABLED)

# Find the gpiochip device we need.
# gpiodevice looks up the right one for each supported platform.
chip = gpiodevice.find_chip_by_platform()

# Build our config for each pin/line we want to use
OFFSETS = [chip.line_offset_from_id(pin) for pin in BUTTONS]
LED = chip.line_offset_from_id(LED_PIN)
line_config = dict.fromkeys(OFFSETS, BUTTON_SETTINGS)
line_config[LED] = LED_SETTINGS

# Request the lines, *whew*
request = chip.request_lines(consumer="spectra6-partial-refresh", config=line_config)

# The display is split into one strip per button.
# The text and border sizes scale with the strip, so the example fits every size of display
STRIP_HEIGHT = inky.height // len(BUTTONS)
BORDER = max(2, STRIP_HEIGHT // 40)
PADDING = STRIP_HEIGHT // 4

font_letter = ImageFont.truetype(FredokaOne, int(STRIP_HEIGHT * 0.7))
font_text = ImageFont.truetype(FredokaOne, int(STRIP_HEIGHT * 0.3))

# The colours each strip moves through, one step per press
COLOURS = [inky.WHITE, inky.YELLOW, inky.RED, inky.GREEN, inky.BLUE, inky.BLACK]

# How many times each button has been pressed
presses = [0] * len(BUTTONS)

# Create a new PIL image with a white background to draw the strips on
image = Image.new("P", (inky.width, inky.height), inky.WHITE)
draw = ImageDraw.Draw(image)


def draw_strip(index):
    top = index * STRIP_HEIGHT
    middle = top + STRIP_HEIGHT // 2

    # Each strip starts on a different colour and moves one colour along with every press
    step = index + presses[index]
    colour = COLOURS[step % len(COLOURS)]

    # Black text is easiest to read on white and yellow, white text on the rest
    text_colour = inky.BLACK if colour in (inky.WHITE, inky.YELLOW) else inky.WHITE

    text = f"Presses: {presses[index]}" if presses[index] else f"Press button {LABELS[index]}"

    # Draw the strip with a black border, its letter on the left and the count on the right
    draw.rectangle((0, top, inky.width - 1, top + STRIP_HEIGHT - 1), fill=colour, outline=inky.BLACK, width=BORDER)
    draw.text((PADDING, middle), LABELS[index], text_colour, font_letter, anchor="lm")
    draw.text((inky.width - PADDING, middle), text, text_colour, font_text, anchor="rm")


def refresh_display():
    # Light the LED while the display is busy refreshing
    request.set_value(LED, Value.ACTIVE)
    start = time.monotonic()
    inky.show()
    request.set_value(LED, Value.INACTIVE)
    print(f"Done in {time.monotonic() - start:.1f}s")


# "handle_button" will be called every time a button is pressed
# It receives one argument: the associated gpiod event object.
def handle_button(event):
    index = OFFSETS.index(event.line_offset)
    presses[index] += 1
    print(f"Button {LABELS[index]} pressed, refreshing its strip...")

    # Redraw this button's strip and copy the image to the display
    draw_strip(index)
    inky.set_image(image)

    # Only the strip for this button will be refreshed
    inky.set_region(0, index * STRIP_HEIGHT, inky.width, STRIP_HEIGHT)
    refresh_display()

    # Ignore any presses made while the display was refreshing.
    # Otherwise they'd queue up and refresh one after another
    while request.wait_edge_events(0):
        request.read_edge_events()


# Draw every strip and do one full refresh to start with
for index in range(len(BUTTONS)):
    draw_strip(index)

inky.set_image(image)
refresh_display()

print("Ready! Press a button.")

while True:
    for event in request.read_edge_events():
        handle_button(event)
