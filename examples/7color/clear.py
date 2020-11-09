#!/usr/bin/env python3
import time

from inky.inky_uc8159 import Inky, CLEAN


inky = Inky()

for _ in range(2):
    for y in range(inky.height - 1):
        for x in range(inky.width - 1):
            inky.set_pixel(x, y, CLEAN)

    inky.show()
    time.sleep(1.0)
