#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import time
import calendar
import sys

from PIL import Image, ImageFont, ImageDraw

sys.path.insert(0, '../../library')

from inky import what as inkywhat

print("""Inky pHAT: Calendar

Draws a calendar for the current month to your Inky pHAT.

This example uses a sprite sheet of numbers and month names which are
composited over the background in a couple of different ways.

""")

image = Image.new('P', (400, 300))
draw = ImageDraw.Draw(image)

if len(sys.argv) < 2:
    print("""Usage: {} <colour>
       Valid colours: red, yellow, black
""".format(sys.argv[0]))
    sys.exit(0)

colour = sys.argv[1]
inkywhat.set_colour(colour)

inkywhat.set_border(inkywhat.BLACK)
#inkywhat.set_rotation(180)

# Load our sprite sheet and prepare a mask
text = Image.open("resources/calendar.png")

tw, th = text.size
text = text.resize((tw*2, th*2), Image.NEAREST)
text_mask = text.convert("1")


# Note: The mask determines which pixels from our sprite sheet we want
# to actually use when calling inkywhat.paste
# which uses PIL's Image.paste() method,
# See: http://pillow.readthedocs.io/en/3.1.x/reference/Image.html?highlight=paste#PIL.Image.Image.paste

# Load our backdrop image
backdrop = Image.open("resources/empty-backdrop.png")
bw, bh = backdrop.size
backdrop = backdrop.resize((bw*2, bh*2), Image.NEAREST)
draw.rectangle(((0, 0), (400, 60)), 1)
image.paste(backdrop, (-12, 60))

# Grab the current date, and prepare our calendar
cal = calendar.Calendar()
now = datetime.datetime.now()
dates = cal.monthdatescalendar(now.year, now.month)

col_w = 40
col_h = 23

cols = 7
rows = len(dates) + 1

cal_w = 1 + ((col_w + 1) * cols)
cal_h = 1 + ((col_h + 1) * rows)

cal_x = 400 - cal_w - 2
cal_y = 2


def print_digit(position, digit, colour):
    """Print a single digit using the sprite sheet.

    Each number is grabbed from the masked sprite sheet,
    and then used as a mask to paste the desired colour
    onto Inky pHATs image buffer.

    """
    o_x, o_y = position
    
    num_margin = 4
    num_width = 12
    num_height = 14

    s_y = 22
    s_x = num_margin + (digit * (num_width + num_margin))

    sprite = text_mask.crop((s_x, s_y, s_x + num_width, s_y + num_height))

    image.paste(colour, (o_x, o_y), sprite)

def print_number(position, number, colour):
    """Prints a number using the sprite sheet."""

    for digit in str(number):
        print_digit(position, int(digit), colour)
        position = (position[0] + 16, position[1])

# Paint out a black rectangle onto which we'll draw our canvas
draw.rectangle((cal_x, cal_y, cal_x + cal_w - 1, cal_y + cal_h - 1), fill=inkywhat.BLACK, outline=inkywhat.WHITE)

# The starting position of the months in our spritesheet
months_x = 2
months_y = 20

# Number of months per row
months_cols = 3

# The width/height of each month in our spritesheet
month_w = 46
month_h = 18

# Figure out where the month is in the spritesheet
month_col = (now.month - 1) % months_cols
month_row = (now.month - 1) // months_cols

# Convert that location to usable X/Y coordinates
month_x = months_x + (month_col * month_w)
month_y = months_y + (month_row * month_h)

crop_region = (month_x, month_y, month_x + month_w, month_y + month_h)

month = text.crop(crop_region)
month_mask = text_mask.crop(crop_region)

monthyear_x = 42

# Paste in the month name we grabbed from our sprite sheet
image.paste(inkywhat.WHITE, (monthyear_x, cal_y + 4), month_mask)

# Print the year right below the month
print_number((monthyear_x, cal_y + 5 + col_h), now.year, inkywhat.WHITE)



# Draw the vertical lines which separate the columns
# and also draw the day names into the table header
for x in range(cols):
    # Figure out the left edge of the column
    o_x = (col_w + 1) * x
    o_x += cal_x

    crop_x = 2 + (32 * x)

    # Crop the relevant day name from our text image
    crop_region = ((crop_x, 0, crop_x + 32, 18))
    day_mask = text_mask.crop(crop_region)
    image.paste(inkywhat.WHITE, (o_x + 4, cal_y + 2), day_mask)

    # Offset to the right side of the column and draw the vertical line
    o_x += col_w + 1
    draw.line((o_x, cal_y, o_x, cal_h))

# Draw the horizontal lines which separate the rows
for y in range(rows):
    o_y = (col_h + 1) * y
    o_y += cal_y + col_h + 1
    draw.line((cal_x, o_y, cal_w + cal_x - 1, o_y))

# Step through each week
for row, week in enumerate(dates):
    y = (col_h + 1) * (row + 1)
    y += cal_y + 1

    # And each day in the week
    for col, day in enumerate(week):
        x = (col_w + 1) * col
        x += cal_x + 1

        # Draw in the day name.
        # If it's the current day, invert the calendar background and text
        if (day.day, day.month) == (now.day, now.month):
            draw.rectangle((x, y, x + col_w - 1, y + col_h - 1), fill=inkywhat.WHITE)
            print_number((x+3, y+3), day.day, inkywhat.BLACK)

        # If it's any other day, paint in as white if it's in the current month
        # and red if it's in the previous or next month
        else:
            print_number((x+3, y+3), day.day, inkywhat.WHITE if day.month == now.month else inkywhat.RED)

inkywhat.set_image(image)

# And show it!
inkywhat.show()
