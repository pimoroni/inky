#!/usr/bin/env python
from inky.eeprom import read_eeprom

display = read_eeprom()

if display is None:
    print("""
No display EEPROM detected,
you might have an old Inky board that doesn't have an EEPROM - eg: early Inky pHAT boards.

Try running examples with --colour <black/red/yellow>

Or writing your code using:

from inky.phat import InkyPHAT

display = InkyPHAT("<black/red/yellow>")

""")
else:
    print("Found: {}".format(display.get_variant()))
    print(display)
