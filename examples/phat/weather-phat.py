#!/usr/bin/env python
# -*- coding: utf-8 -*-

import glob
import json
import time
import urllib
import argparse
from inky import InkyPHAT
from PIL import Image, ImageDraw, ImageFont
from font_fredoka_one import FredokaOne

try:
    import requests
except ImportError:
    exit("This script requires the requests module\nInstall with: sudo pip install requests")

print("""Inky pHAT: Weather

Displays weather information for a given location. The default location is Sheffield-on-Sea.

""")

parser = argparse.ArgumentParser()
parser.add_argument('--colour', '-c', type=str, required=True, choices=["red", "black", "yellow"], help="ePaper display colour")
args = parser.parse_args()

colour = args.colour
inky_display = InkyPHAT(colour)
inky_display.set_border(inky_display.BLACK)

CITY = "Sheffield"
COUNTRYCODE = "GB"
WARNING_TEMP = 25.0


def get_location():
    res = requests.get('http://ipinfo.io')
    if(res.status_code == 200):
        json_data = json.loads(res.text)
        return json_data
    return {}

# Python 2 vs 3 breaking changes.

def encode(qs):
    val = ""
    try:
        val = urllib.urlencode(qs).replace("+","%20")
    except:
        val = urllib.parse.urlencode(qs).replace("+", "%20")
    return val

def get_weather(address):
    base = "https://query.yahooapis.com/v1/public/yql?"
    query = "select * from weather.forecast where woeid in (select woeid from geo.places(1) where text=\""+address+"\")"
    qs={"q": query, "format": "json", "env": "store://datatables.org/alltableswithkeys"}

    uri = base + encode(qs)

    res = requests.get(uri)
    if(res.status_code==200):
        json_data = json.loads(res.text)
        return json_data

    return {}

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

icons = {}
masks = {}

location_string = "{city}, {countrycode}".format(city=CITY, countrycode=COUNTRYCODE)

weather = get_weather(location_string)

icon_map = {
	"snow": [5, 6, 7, 8, 10, 13, 14, 15, 16, 17, 18, 41, 42, 43, 46],
	"rain": [9, 11, 12],
	"cloud": [19, 20, 21, 22, 25, 26, 27, 28, 29, 30, 44],
	"sun": [32, 33, 34, 36],
	"storm": [0, 1, 2, 3, 4, 37, 38, 39, 45, 47],
        "wind": [23, 24]
}

pressure = 0
temperature = 0
weather_icon = None

if "channel" in weather["query"]["results"]:
    results = weather["query"]["results"]["channel"]
    pressure = results["atmosphere"]["pressure"]
    temperature = (int(results["item"]["forecast"][0]["high"]) - 32) * .5556
    code = int(results["item"]["forecast"][0]["code"])

    for icon in icon_map:
        if code in icon_map[icon]:
            weather_icon = icon
            break

else:
    print("Warning, no weather information found!")

# Create a new canvas to draw on

img = Image.open("resources/backdrop.png")
draw = ImageDraw.Draw(img)

# Load our icon files and generate masks
for icon in glob.glob("resources/icon-*.png"):
    icon_name = icon.split("icon-")[1].replace(".png", "")
    icon_image = Image.open(icon)
    icons[icon_name] = icon_image
    masks[icon_name] = create_mask(icon_image)

# Load the built-in FredokaOne font
font = ImageFont.truetype(FredokaOne, 22)

# Let's draw some lines!
draw.line((69, 36, 69, 81)) # Vertical line
draw.line((31, 35, 184, 35)) # Horizontal top line
draw.line((69, 58, 174, 58)) # Horizontal middle line
draw.line((169, 58, 169, 58), 2) # Red seaweed pixel :D

# And now some text

datetime = time.strftime("%d/%m %H:%M")

draw.text((36, 12), datetime, inky_display.WHITE, font=font)

draw.text((72, 34), "T", inky_display.WHITE, font=font)
draw.text((92, 34), u"{:.2f}°".format(temperature), inky_display.WHITE if temperature < WARNING_TEMP else inky_display.RED, font=font)

draw.text((72, 58), "P", inky_display.WHITE, font=font)
draw.text((92, 58), "{}".format(pressure), inky_display.WHITE, font=font)

# Draw the current weather icon over the backdrop
if weather_icon is not None:
    img.paste(icons[weather_icon], (28, 36), masks[weather_icon])

else:
    draw.text((28, 36), "?", inky_display.RED, font=font)

# And show it!
inky_display.set_image(img)
inky_display.show()
