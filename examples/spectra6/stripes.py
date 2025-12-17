#!/usr/bin/env python3

from inky.auto import auto

inky = auto(ask_user=True, verbose=True)

COLOURS = [0, 1, 2, 3, 5, 6]

for y in range(inky.height - 1):
    c = min(y // (inky.height // 6), 5)
    for x in range(inky.width - 1):
        inky.set_pixel(x, y, COLOURS[c])

inky.show()
