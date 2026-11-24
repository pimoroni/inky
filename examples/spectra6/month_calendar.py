#!/usr/bin/env python3

import calendar
import datetime
import time

from font_fredoka_one import FredokaOne
from PIL import Image, ImageDraw, ImageFont

from inky.auto import auto

print(
    """month_calendar.py - This month's calendar, with today picked out

This example demonstrates how to:
 1. draw a month calendar, with today's date in big on the left,
 2. use set_region() so only the parts that change refresh at midnight

The whole display refreshes at the start and when the month changes.

Press Ctrl+C to exit!

"""
)

inky = auto(ask_user=True, verbose=True)

if not hasattr(inky, "set_region"):
    raise SystemExit("This example needs an Inky Impression with a Spectra 6 display!")

GAP = max(6, inky.width // 60)
SHADOW = GAP // 2
LINE = max(2, inky.height // 160)

# The cards as (left, top, right, bottom), with today on the left and the month on the right
SPLIT = inky.width * 3 // 8
TODAY_CARD = (GAP, GAP, SPLIT, inky.height - GAP)
MONTH_CARD = (SPLIT + GAP, GAP, inky.width - GAP, inky.height - GAP)

# Drawn in the display's own colours, like inky.BLUE, so set_image() doesn't dither it
screen = Image.new("P", (inky.width, inky.height), inky.BLUE)
draw = ImageDraw.Draw(screen)
draw.fontmode = "1"


def font(size):
    return ImageFont.truetype(FredokaOne, max(8, int(size)))


def pill(centre, text, text_font, colour):
    left, top, right, bottom = draw.textbbox(centre, text, font=text_font, anchor="mm")
    padding = (bottom - top) * 0.45
    box = (left - padding * 2, top - padding, right + padding * 2, bottom + padding)
    draw.rounded_rectangle(box, radius=(box[3] - box[1]) / 2, fill=colour)
    draw.text(centre, text, inky.WHITE, text_font, anchor="mm")


def card(box):
    left, top, right, bottom = box
    radius = inky.height // 24
    draw.rounded_rectangle((left + SHADOW, top + SHADOW, right - 1, bottom - 1), radius=radius, fill=inky.BLACK)
    draw.rounded_rectangle((left, top, right - SHADOW - 1, bottom - SHADOW - 1), radius=radius, outline=inky.BLACK, width=LINE, fill=inky.WHITE)
    return left, top, right - SHADOW, bottom - SHADOW


def month_layout(today):
    # Every date in the month and where its cell goes, as {day: (left, top, right, bottom)}
    left, top, right, bottom = MONTH_CARD
    right, bottom = right - SHADOW, bottom - SHADOW
    weeks = calendar.Calendar().monthdayscalendar(today.year, today.month)
    grid_top = top + (bottom - top) * 0.25
    cell_width = (right - left - GAP * 2) / 7
    cell_height = (bottom - grid_top - GAP) / len(weeks)

    cells = {}
    for row, week in enumerate(weeks):
        for column, day in enumerate(week):
            if day:
                x = int(left + GAP + column * cell_width)
                y = int(grid_top + row * cell_height)
                cells[day] = (x, y, int(x + cell_width), int(y + cell_height))
    return cells, cell_width, grid_top


def draw_today(today):
    left, top, right, bottom = card(TODAY_CARD)
    middle_x = (left + right) // 2
    size = min((right - left) * 0.4, (bottom - top) * 0.3)

    # Everything on this card is 2.45 sizes tall, centred in the card
    block_top = top + (bottom - top - size * 2.45) / 2
    draw.text((middle_x, block_top + size * 0.45), str(today.day), inky.BLACK, font(size * 1.1), anchor="mm")
    draw.text((middle_x, block_top + size * 1.1), f"{today:%B}", inky.BLACK, font(size * 0.25), anchor="mm")
    pill((middle_x, block_top + size * 1.5), f"{today:%A}".upper(), font(size * 0.2), inky.BLACK)

    # The week number and day of the year, each with a coloured label
    days_in_year = 366 if calendar.isleap(today.year) else 365
    rows = (("WEEK", str(today.isocalendar().week), inky.BLUE), ("DAY", f"{today.timetuple().tm_yday}/{days_in_year}", inky.GREEN))
    text_font = font(size * 0.17)
    label_width = draw.textlength("WEEK", font=text_font) * 1.6
    text_width = max(draw.textlength(text, font=text_font) for _, text, _ in rows)
    row_left = middle_x - (label_width + text_width) / 2
    for row, (label, text, colour) in enumerate(rows):
        y = block_top + size * (1.95 + row * 0.38)
        pill((row_left + label_width * 0.4, y), label, text_font, colour)
        draw.text((row_left + label_width, y), text, inky.BLACK, text_font, anchor="lm")


def draw_month(today):
    left, top, right, _ = card(MONTH_CARD)
    cells, cell_width, grid_top = month_layout(today)
    middle_x = (left + right) // 2

    draw.text((middle_x, top + (grid_top - top) * 0.4), f"{today:%B %Y}", inky.BLACK, font((grid_top - top) * 0.38), anchor="mm")

    # Day names along the top, with the weekend in blue
    for column, name in enumerate(calendar.day_abbr):
        x = left + GAP + (column + 0.5) * cell_width
        colour = inky.BLUE if column >= 5 else inky.BLACK
        draw.text((x, grid_top - (grid_top - top) * 0.15), name.upper(), colour, font(cell_width * 0.22), anchor="mm")
    draw.line((left + GAP, grid_top, right - GAP, grid_top), fill=inky.BLACK, width=LINE)

    for day, (cell_left, cell_top, cell_right, cell_bottom) in cells.items():
        centre_x, centre_y = (cell_left + cell_right) / 2, (cell_top + cell_bottom) / 2
        size = min(cell_right - cell_left, cell_bottom - cell_top) * 0.42
        number_font = font(size)
        if day == today.day:
            # White on a red rounded square
            highlight = (centre_x - size, centre_y - size, centre_x + size, centre_y + size)
            draw.rounded_rectangle(highlight, radius=size / 2, fill=inky.RED)
            draw.text((centre_x, centre_y), str(day), inky.WHITE, number_font, anchor="mm")
        else:
            weekend = datetime.date(today.year, today.month, day).weekday() >= 5
            draw.text((centre_x, centre_y), str(day), inky.BLUE if weekend else inky.BLACK, number_font, anchor="mm")


def refresh(box=None):
    inky.set_image(screen)
    if box is None:
        inky.reset_region()
        inky.speed = inky.NORMAL
    else:
        # Only this part is refreshed, at medium speed. FAST is quicker but dulls greens
        left, top, right, bottom = box
        inky.set_region(left, top, right - left, bottom - top)
        inky.speed = inky.MEDIUM
    start = time.monotonic()
    inky.show()
    kind = "full" if box is None else "partial"
    print(f"{datetime.datetime.now():%Y-%m-%d %H:%M} {kind} refresh took {time.monotonic() - start:.1f}s")


shown = None

while True:
    today = datetime.date.today()

    if shown is None or (today.year, today.month) != (shown.year, shown.month):
        draw_today(today)
        draw_month(today)
        refresh()
    elif today != shown:
        draw_today(today)
        refresh(TODAY_CARD)

        # Only the old and new highlighted dates change, so refresh the area around both
        draw_month(today)
        cells, _, _ = month_layout(today)
        old, new = cells[shown.day], cells[today.day]
        left, top = min(old[0], new[0]), min(old[1], new[1])
        right, bottom = max(old[2], new[2]), max(old[3], new[3])
        refresh((left, top, right, bottom))

    shown = today

    # Check the date every minute, so it's right soon after the clock is set at boot
    time.sleep(60)
