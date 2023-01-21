#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import glob
import os
import time
import json
from sys import exit

from font_fredoka_one import FredokaOne
from inky.auto import auto
from PIL import Image, ImageDraw, ImageFont

"""
To run this example on Python 2.x you should:
    sudo apt install python-lxml
    sudo pip install geocoder requests font-fredoka-one

On Python 3.x:
    sudo apt install python3-lxml
    sudo pip3 install geocoder requests font-fredoka-one
"""

try:
    import requests
except ImportError:
    exit("This script requires the requests module\nInstall with: sudo pip install requests")

try:
    import geocoder
except ImportError:
    exit("This script requires the geocoder module\nInstall with: sudo pip install geocoder")

print("""Inky pHAT: Weather

Displays weather information for a given location. The default location is Sheffield-on-Sea.

""")

# Get the current path
PATH = os.path.dirname(__file__)

# Set up the display
try:
    inky_display = auto(ask_user=True, verbose=True)
except TypeError:
    raise TypeError("You need to update the Inky library to >= v1.1.0")

if inky_display.resolution not in ((212, 104), (250, 122)):
    w, h = inky_display.resolution
    raise RuntimeError("This example does not support {}x{}".format(w, h))

inky_display.set_border(inky_display.BLACK)

# Details to customise your weather display

CITY = "Sheffield"
COUNTRYCODE = "GB"
WARNING_TEMP = 25.0


# Convert a city name and country code to latitude and longitude
def get_coords(address):
    g = geocoder.arcgis(address)
    coords = g.latlng
    return coords


# Query OpenMeteo (https://open-meteo.com) to get current weather data
def get_weather(address):
    coords = get_coords(address)
    weather = {}
    res = requests.get("https://api.open-meteo.com/v1/forecast?latitude=" + str(coords[0]) + "&longitude=" + str(coords[1]) + "&current_weather=true")
    if res.status_code == 200:
        j = json.loads(res.text)
        current = j["current_weather"]
        weather["temperature"] = current["temperature"]
        weather["windspeed"] = current["windspeed"]
        weather["weathercode"] = current["weathercode"]
        return weather
    else:
        return weather


def create_mask(source, mask=(inky_display.WHITE, inky_display.BLACK, inky_display.RED)):
    """Create a transparency mask.

    Takes a paletized source image and converts it into a mask
    permitting all the colours supported by Inky pHAT (0, 1, 2)
    or an optional list of allowed colours.

    :param mask: Optional list of Inky pHAT colours to allow.

    """
    mask_image = Image.new("1", source.size)
    w, h = source.size
    for x in range(w):
        for y in range(h):
            p = source.getpixel((x, y))
            if p in mask:
                mask_image.putpixel((x, y), 255)

    return mask_image


# Dictionaries to store our icons and icon masks in
icons = {}
masks = {}

# Get the weather data for the given location
location_string = "{city}, {countrycode}".format(city=CITY, countrycode=COUNTRYCODE)
weather = get_weather(location_string)

# This maps the weather code from Open Meteo
# to the appropriate weather icons
# Weather codes from https://open-meteo.com/en/docs
icon_map = {
    "snow": [71, 73, 75, 77, 85, 86],
    "rain": [51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82],
    "cloud": [1, 2, 3, 45, 48],
    "sun": [0],
    "storm": [95, 96, 99],
    "wind": []
}

# Placeholder variables
windspeed = 0.0
temperature = 0.0
weather_icon = None

if weather:
    temperature = weather["temperature"]
    windspeed = weather["windspeed"]
    weathercode = weather["weathercode"]

    for icon in icon_map:
        if weathercode in icon_map[icon]:
            weather_icon = icon
            break

else:
    print("Warning, no weather information found!")

# Create a new canvas to draw on
img = Image.open(os.path.join(PATH, "resources/backdrop.png")).resize(inky_display.resolution)
draw = ImageDraw.Draw(img)

# Load our icon files and generate masks
for icon in glob.glob(os.path.join(PATH, "resources/icon-*.png")):
    icon_name = icon.split("icon-")[1].replace(".png", "")
    icon_image = Image.open(icon)
    icons[icon_name] = icon_image
    masks[icon_name] = create_mask(icon_image)

# Load the FredokaOne font
font = ImageFont.truetype(FredokaOne, 22)

# Draw lines to frame the weather data
draw.line((69, 36, 69, 81))       # Vertical line
draw.line((31, 35, 184, 35))      # Horizontal top line
draw.line((69, 58, 174, 58))      # Horizontal middle line
draw.line((169, 58, 169, 58), 2)  # Red seaweed pixel :D

# Write text with weather values to the canvas
datetime = time.strftime("%d/%m %H:%M")

draw.text((41, 12), datetime, inky_display.WHITE, font=font)

draw.text((72, 34), "T", inky_display.WHITE, font=font)
draw.text((92, 34), "{}°C".format(temperature), inky_display.WHITE if temperature < WARNING_TEMP else inky_display.RED, font=font)

draw.text((72, 58), "W", inky_display.WHITE, font=font)
draw.text((92, 58), "{}kmh".format(windspeed), inky_display.WHITE, font=font)

# Draw the current weather icon over the backdrop
if weather_icon is not None:
    img.paste(icons[weather_icon], (28, 36), masks[weather_icon])

else:
    draw.text((28, 36), "?", inky_display.RED, font=font)

# Display the weather data on Inky pHAT
inky_display.set_image(img)
inky_display.show()
