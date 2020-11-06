#!/usr/bin/env python3
import time

from inky.inky_uc8159 import Inky


inky = Inky()

colors = ['Black', 'White', 'Green', 'Blue', 'Red', 'Yellow', 'Orange']

for color in range(7):
    print("Color: {}".format(colors[color]))
    for y in range(inky.height - 1):
        for x in range(inky.width - 1):
            inky.set_pixel(x, y, color)
    inky.show()
    time.sleep(5.0)
