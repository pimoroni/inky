#!/usr/bin/env python3

# To simulate:
# from inky.mock import InkyMockImpression as Inky
from inky.auto import auto

inky = auto(ask_user=True, verbose=True)

for y in range(inky.height - 1):
    color = y // (inky.height // 7)
    for x in range(inky.width - 1):
        inky.set_pixel(x, y, color * 0x11)

inky.show()
# To simulate:
# inky.wait_for_window_close()
