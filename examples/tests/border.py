#!/usr/bin/env python
import time
import sys
from PIL import Image
from inky import InkyPHAT

INKY_COLOUR = None

if len(sys.argv) > 1:
    INKY_COLOUR = sys.argv[1]

if INKY_COLOUR not in ['red', 'yellow', 'black']:
    print("Usage: {} <red, yellow, black>".format(sys.argv[0]))
    sys.exit(1)

phat = InkyPHAT(INKY_COLOUR)

white = Image.new('P', (212, 104), phat.WHITE)
black = Image.new('P', (212, 104), phat.BLACK)

while True:
    print("White")
    phat.set_border(phat.WHITE)
    phat.set_image(black)
    phat.show()
    time.sleep(1)

    if INKY_COLOUR == 'red':
        print("Red")
        phat.set_border(phat.RED)
        phat.set_image(white)
        phat.show()
        time.sleep(1)

    if INKY_COLOUR == 'yellow':
        print("Yellow")
        phat.set_border(phat.YELLOW)
        phat.set_image(white)
        phat.show()
        time.sleep(1)

    print("Black")
    phat.set_border(phat.BLACK)
    phat.set_image(white)
    phat.show()
    time.sleep(1)

    if INKY_COLOUR == 'red':
        print("Red")
        phat.set_border(phat.RED)
        phat.set_image(white)
        phat.show()
        time.sleep(1)

    if INKY_COLOUR == 'yellow':
        print("Yellow")
        phat.set_border(phat.YELLOW)
        phat.set_image(white)
        phat.show()
        time.sleep(1)
