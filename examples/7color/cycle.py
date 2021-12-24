#!/usr/bin/env python3
import time

from inky.auto import auto

inky = auto(ask_user=True, verbose=True)

colors = ['Black', 'White', 'Green', 'Blue', 'Red', 'Yellow', 'Orange']

for color in range(7):
    print("Color: {}".format(colors[color]))
    for y in range(inky.height):
        for x in range(inky.width):
            inky.set_pixel(x, y, color)
    inky.set_border(color)
    inky.show()
    time.sleep(5.0)
