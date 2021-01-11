#!/usr/bin/env python3
import signal

from inky.inky_uc8159 import Inky
# To simulate:
# from inky.mock import InkyMockImpression as Inky

inky = Inky()

for y in range(inky.height - 1):
    color = y // (inky.height // 7)
    for x in range(inky.width - 1):
        inky.set_pixel(x, y, color)

inky.show()
# To simulate:
# inky.wait_for_window_close()