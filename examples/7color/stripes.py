#!/usr/bin/env python3

from inky.inky_uc8159 import Inky

inky = Inky()

for y in range(inky.height - 1):
    color = y // (inky.height // 7)
    for x in range(inky.width - 1):
        inky.set_pixel(x, y, color)

inky.show()
