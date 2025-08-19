"""
In need of a creative way to say no? Look no further! Powered by the No As A Service API - find out more here: https://github.com/hotheadhacker/no-as-a-service

Requires the Manrope font (pip install font_manrope)

This example is written for the new four colour Inky pHAT/wHAT display so uses both yellow and red, but it should be easy to modify if you have an older Inky with fewer colours.
"""

import requests
from font_manrope import ManropeExtraBold, ManropeSemiBold
from PIL import Image, ImageDraw, ImageFont

from inky.auto import auto


def wrap_text(text, font, max_width, draw):
    """Wrap text to fit within the specified width - returns a list of lines"""
    lines = []
    for word in text.split():
        if not lines:
            lines.append(word)
        else:
            test_line = lines[-1] + " " + word
            w = draw.textbbox((0, 0), test_line, font=font)[2] - draw.textbbox((0, 0), test_line, font=font)[0]
            if w <= max_width:
                lines[-1] = test_line
            else:
                lines.append(word)
    return lines


# Fetch a No Reason from the API
try:
    response = requests.get("https://naas.isalman.dev/no")
    response.raise_for_status()
    reason = response.json().get("reason", "No reason provided")
except Exception:
    reason = "Error fetching reason"

# Initialize the Inky display and create a blank image
inky_display = auto()
img = Image.new("P", (inky_display.WIDTH, inky_display.HEIGHT), inky_display.WHITE)
draw = ImageDraw.Draw(img)

# Load fonts for the main message and the reason text
font = ImageFont.truetype(ManropeExtraBold, 34)
font_small = ImageFont.truetype(ManropeSemiBold, 18)

# Draw a yellow border around the display
border_thickness = 3
for i in range(border_thickness):
    draw.line([(i, i), (inky_display.WIDTH-1-i, i)], fill=inky_display.YELLOW)
    draw.line([(i, inky_display.HEIGHT-1-i), (inky_display.WIDTH-1-i, inky_display.HEIGHT-1-i)], fill=inky_display.YELLOW)
    draw.line([(i, i), (i, inky_display.HEIGHT-1-i)], fill=inky_display.YELLOW)
    draw.line([(inky_display.WIDTH-1-i, i), (inky_display.WIDTH-1-i, inky_display.HEIGHT-1-i)], fill=inky_display.YELLOW)

# Draw "NO" message centered at the top
message = "NO"
bbox = draw.textbbox((0, 0), message, font=font)
x = (inky_display.WIDTH - (bbox[2] - bbox[0])) // 2
y = 0
draw.text((x, y), message, inky_display.RED, font=font)

# Wrap the reason text to fit the display width
border = 10
wrap_width = inky_display.WIDTH - 2 * border
wrapped_reason = wrap_text(reason, font_small, wrap_width, draw)
# Calculate line height for the reason text
line_height = draw.textbbox((0, 0), "A", font=font_small)[3] - draw.textbbox((0, 0), "A", font=font_small)[1]
# Start drawing reason text below the "NO" message
ry = y + (bbox[3] - bbox[1]) + 10
for line in wrapped_reason:
    draw.text((border, ry), line, inky_display.BLACK, font=font_small)
    ry += line_height + 4

# Send the image to the display
inky_display.set_image(img)
inky_display.show()
