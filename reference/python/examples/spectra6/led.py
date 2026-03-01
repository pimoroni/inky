#!/usr/bin/env python3

import time

import gpiod
import gpiodevice
from gpiod.line import Bias, Direction, Value

print(
    """\nled.py - Blink the LED!

Press Ctrl+C to exit!

"""
)

LED_PIN = 13

# Find the gpiochip device we need, we'll use
# gpiodevice for this, since it knows the right device
# for its supported platforms.
chip = gpiodevice.find_chip_by_platform()

# Setup for the LED pin
led = chip.line_offset_from_id(LED_PIN)
gpio = chip.request_lines(consumer="inky", config={led: gpiod.LineSettings(direction=Direction.OUTPUT, bias=Bias.DISABLED)})

while True:
    gpio.set_value(led, Value.ACTIVE)
    time.sleep(1)
    gpio.set_value(led, Value.INACTIVE)
    time.sleep(1)
