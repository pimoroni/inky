#!/usr/bin/env python3

import datetime
import math
import os
import socket
import time

import psutil
from font_fredoka_one import FredokaOne
from PIL import Image, ImageDraw, ImageFont

from inky.auto import auto

print(
    """system_stats.py - Your Raspberry Pi's stats in a grid of tiles

This example demonstrates how to:
 1. draw a grid of tiles with gauges for CPU, memory, swap, disk and temperature,
 2. use set_region() so each tile refreshes on its own, only when it needs to

CPU, memory, swap and temperature are checked every 5 minutes and the disk
every half hour. A tile only refreshes when its reading has changed.
The whole display refreshes once an hour.

Press Ctrl+C to exit!

"""
)

# CPU usage is measured between readings, so take a first one now
psutil.cpu_percent()

inky = auto(ask_user=True, verbose=True)

if not hasattr(inky, "set_region"):
    raise SystemExit("This example needs an Inky Impression with a Spectra 6 display!")

# Which tile goes where, as (column, row) in a 3 x 2 grid
TILES = {
    "cpu": (0, 0),
    "memory": (1, 0),
    "temperature": (2, 0),
    "disk": (0, 1),
    "swap": (1, 1),
    "system": (2, 1),
}

COLUMNS, ROWS = 3, 2
GAP = max(6, inky.width // 60)
SHADOW = GAP // 2
TILE_WIDTH = (inky.width - GAP * (COLUMNS + 1)) // COLUMNS
TILE_HEIGHT = (inky.height - GAP * (ROWS + 1)) // ROWS

SEGMENTS = 18

# The gap between dial segments, in degrees
SEGMENT_GAP = 3

TEMPERATURE_RANGE = (30, 85)

GIGABYTE = 1024 ** 3

# Drawn in the display's own colours, like inky.BLUE, so set_image() doesn't dither it
screen = Image.new("P", (inky.width, inky.height), inky.BLUE)


def font(size):
    return ImageFont.truetype(FredokaOne, max(8, int(size)))


def tile_position(name):
    column, row = TILES[name]
    return GAP + column * (TILE_WIDTH + GAP), GAP + row * (TILE_HEIGHT + GAP)


def level_colour(fraction):
    if fraction < 0.6:
        return inky.GREEN
    if fraction < 0.85:
        return inky.YELLOW
    return inky.RED


def cpu_temperature():
    for sensor in psutil.sensors_temperatures().get("cpu_thermal", []):
        return sensor.current
    return None


def ip_address():
    for interface, addresses in psutil.net_if_addrs().items():
        if interface == "lo":
            continue
        for address in addresses:
            if address.family == socket.AF_INET:
                return address.address
    return "no network"


def tile_content(name):
    if name == "cpu":
        # The average since the last reading
        percent = round(psutil.cpu_percent())
        return ("gauge", "CPU", percent / 100, f"{percent}%", f"load {os.getloadavg()[0]:.2f}")

    if name == "memory":
        memory = psutil.virtual_memory()
        used = memory.total - memory.available
        percent = round(used / memory.total * 100)
        return ("gauge", "MEMORY", percent / 100, f"{percent}%", f"{used / GIGABYTE:.1f}/{memory.total / GIGABYTE:.1f} GB")

    if name == "swap":
        swap = psutil.swap_memory()
        if swap.total == 0:
            return ("gauge", "SWAP", 0, "off", None)
        percent = round(swap.percent)
        return ("gauge", "SWAP", percent / 100, f"{percent}%", f"{swap.used / GIGABYTE:.1f}/{swap.total / GIGABYTE:.1f} GB")

    if name == "disk":
        disk = psutil.disk_usage("/")
        percent = round(disk.percent)
        return ("gauge", "DISK", percent / 100, f"{percent}%", f"{disk.free / GIGABYTE:.1f} GB free")

    if name == "temperature":
        temperature = cpu_temperature()
        if temperature is None:
            return ("gauge", "TEMP", 0, "n/a", None)
        low, high = TEMPERATURE_RANGE
        fraction = min(max((round(temperature) - low) / (high - low), 0), 1)
        return ("gauge", "TEMP", fraction, f"{round(temperature)}°C", None)

    # The system tile only changes on the hourly full refresh, so it shows whole hours
    uptime = int(time.time() - psutil.boot_time())
    days, hours = uptime // 86400, uptime % 86400 // 3600
    return ("system", socket.gethostname(), ip_address(), f"{days}d {hours}h")


def pill(draw, centre, text, text_font, colour):
    left, top, right, bottom = draw.textbbox(centre, text, font=text_font, anchor="mm")
    padding = (bottom - top) * 0.45
    box = (left - padding * 2, top - padding, right + padding * 2, bottom + padding)
    draw.rounded_rectangle(box, radius=(box[3] - box[1]) / 2, fill=colour)
    draw.text(centre, text, inky.WHITE, text_font, anchor="mm")


def draw_tile(name, content):
    line = max(2, TILE_HEIGHT // 80)
    card_width, card_height = TILE_WIDTH - SHADOW, TILE_HEIGHT - SHADOW
    tile = Image.new("P", (TILE_WIDTH, TILE_HEIGHT), inky.BLUE)
    draw = ImageDraw.Draw(tile)
    draw.fontmode = "1"
    radius = card_height // 10
    draw.rounded_rectangle((SHADOW, SHADOW, TILE_WIDTH - 1, TILE_HEIGHT - 1), radius=radius, fill=inky.BLACK)
    draw.rounded_rectangle((0, 0, card_width - 1, card_height - 1), radius=radius, outline=inky.BLACK, width=line, fill=inky.WHITE)

    middle_x = card_width // 2
    middle_y = card_height // 2
    radius = int(min(card_width, card_height) * 0.40)
    label_y = middle_y + radius * 0.9

    if content[0] == "gauge":
        _, label, fraction, value, detail = content
        thickness = int(radius * 0.3)
        outer = (middle_x - radius, middle_y - radius, middle_x + radius, middle_y + radius)
        inner = (outer[0] + line, outer[1] + line, outer[2] - line, outer[3] - line)

        # PIL measures angles clockwise from 3 o'clock, so 135° is the bottom left
        step = 270 / SEGMENTS
        outline = math.degrees(line / (radius - thickness / 2))
        lit = math.ceil(fraction * SEGMENTS)
        for segment in range(SEGMENTS):
            begin = 135 + segment * step + SEGMENT_GAP / 2
            end = begin + step - SEGMENT_GAP
            colour = level_colour((segment + 0.5) / SEGMENTS) if segment < lit else inky.WHITE
            draw.arc(outer, begin, end, fill=inky.BLACK, width=thickness)
            draw.arc(inner, begin + outline, end - outline, fill=colour, width=thickness - line * 2)

        draw.text((middle_x, middle_y), value, inky.BLACK, font(radius * 0.48), anchor="mm")
        if detail:
            draw.text((middle_x, middle_y + radius * 0.36), detail, inky.BLACK, font(radius * 0.17), anchor="mm")
        pill(draw, (middle_x, label_y), label, font(radius * 0.22), inky.BLACK)
    else:
        _, hostname, address, uptime = content
        size = radius * 0.3

        text_font = font(size)
        length = draw.textlength(hostname, font=text_font)
        if length > card_width * 0.85:
            text_font = font(size * card_width * 0.85 / length)
        draw.text((middle_x, middle_y - radius * 0.55), hostname, inky.BLACK, text_font, anchor="mm")

        rows = (("IP", address, inky.BLUE, middle_y - radius * 0.05), ("UP", uptime, inky.GREEN, middle_y + radius * 0.35))
        text_font = font(size * 0.6)
        label_width = draw.textlength("UP", font=text_font) * 2.4
        text_width = max(draw.textlength(text, font=text_font) for _, text, _, _ in rows)
        left = middle_x - (label_width + text_width) / 2
        for label, text, colour, y in rows:
            pill(draw, (left + label_width * 0.45, y), label, text_font, colour)
            draw.text((left + label_width, y), text, inky.BLACK, text_font, anchor="lm")

        pill(draw, (middle_x, label_y), "SYSTEM", font(radius * 0.22), inky.BLACK)

    screen.paste(tile, tile_position(name))


def tiles_due(minute):
    # Spread out, so no more than one tile refreshes in a minute
    names = []
    if minute % 5 == 1:
        names.append("cpu")
    if minute % 5 == 2:
        names.append("memory")
    if minute % 5 == 3:
        names.append("temperature")
    if minute % 5 == 4:
        names.append("swap")
    if minute == 30:
        names.append("disk")
    return names


# What each tile is showing, so a tile only refreshes when it would look different
shown = {}

while True:
    now = datetime.datetime.now()

    if not shown or now.minute == 0:
        # Refresh everything at normal speed at the start and hourly, to keep the colours fresh
        for name in TILES:
            shown[name] = tile_content(name)
            draw_tile(name, shown[name])

        inky.set_image(screen)
        inky.reset_region()
        inky.speed = inky.NORMAL
        start = time.monotonic()
        inky.show()
    else:
        for name in tiles_due(now.minute):
            content = tile_content(name)
            if content == shown[name]:
                continue

            shown[name] = content
            draw_tile(name, content)

            inky.set_image(screen)
            x, y = tile_position(name)
            inky.set_region(x, y, TILE_WIDTH, TILE_HEIGHT)
            inky.speed = inky.MEDIUM
            start = time.monotonic()
            inky.show()
            print(f"{now:%H:%M} {name} refresh took {time.monotonic() - start:.1f}s")

    # Wait for the next minute
    if datetime.datetime.now().minute == now.minute:
        time.sleep(60 - time.time() % 60)
