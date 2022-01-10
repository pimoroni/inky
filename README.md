# Inky

[![Build Status](https://travis-ci.com/pimoroni/inky.svg?branch=master)](https://travis-ci.com/pimoroni/inky)
[![Coverage Status](https://coveralls.io/repos/github/pimoroni/inky/badge.svg?branch=master)](https://coveralls.io/github/pimoroni/inky?branch=master)
[![PyPi Package](https://img.shields.io/pypi/v/inky.svg)](https://pypi.python.org/pypi/inky)
[![Python Versions](https://img.shields.io/pypi/pyversions/inky.svg)](https://pypi.python.org/pypi/inky)

Python library for [Inky pHAT](https://shop.pimoroni.com/products/inky-phat), [Inky wHAT](https://shop.pimoroni.com/products/inky-what) and [Inky Impression](https://shop.pimoroni.com/?q=inky+impression) e-paper displays for Raspberry Pi.

## Inky pHAT

[Inky pHAT](https://shop.pimoroni.com/products/inky-phat) is a 250x122 pixel e-paper display, available in red/black/white, yellow/black/white and black/white. It's great for nametags and displaying very low frequency information such as a daily calendar or weather overview.


## Inky wHAT

[Inky wHAT](https://shop.pimoroni.com/products/inky-what) is a 400x300 pixel e-paper display available in red/black/white, yellow/black/white and black/white. It's got tons of resolution for detailed daily to-do lists, multi-day weather forecasts, bus timetables and more.

## Inky Impression

[Inky Impression](https://shop.pimoroni.com/?q=inky+impression) is our line of glorious 7 colour eInk displays, available in [4"](https://shop.pimoroni.com/products/inky-impression-4) (640 x 400 pixel) and [5.7"](https://shop.pimoroni.com/products/inky-impression-5-7) (600 x 448 pixel) flavours. They're packed with strong colours and perfect for displaying striking graphics or lots of data.

# Installation

First, make sure you have I2C and SPI enabled in `sudo raspi-config`.

The Python pip package is named inky, on the Raspberry Pi install with:

```
pip3 install inky[rpi,example-depends]
```

This will install Inky along with dependencies for the Raspberry Pi, plus fonts used by the examples.

If you want to simulate Inky on your desktop, use:

```
pip3 install inky
```

You may need to use `sudo pip3` or `sudo pip` depending on your environment and Python version.

# Usage

The library should be run with Python 3.

## Auto Setup

Inky can try to automatically identify your board (from the information stored on its EEPROM) and set up accordingly. This is the easiest way to work with recent Inky displays.

```python
from inky.auto import auto
display = auto()
```

You can then get the colour and resolution from the board:

```python
display.colour
display.resolution
```

## Manual Setup

If you have an older Inky without an EEPROM, you can specify the type manually. The Inky library contains modules for both the pHAT and wHAT, load the Inky pHAT one as follows:

```python
from inky import InkyPHAT
```

You'll then need to pick your colour, one of 'red', 'yellow' or 'black' and instantiate the class:

```python
display = InkyPHAT('red')
```

If you're using the wHAT you'll need to load the InkyWHAT class from the Inky library like so:

```python
from inky import InkyWHAT
display = InkyWHAT('red')
```

Once you've initialised Inky, there are only three methods you need to be concerned with:

## Set Image

Set a PIL image, numpy array or list to Inky's internal buffer. The image dimensions should match the dimensions of the pHAT or wHAT you're using.

```python
display.set_image(image)
```

You should use `PIL` to create an image. `PIL` provides an `ImageDraw` module which allow you to draw text, lines and shapes over your image. See: https://pillow.readthedocs.io/en/stable/reference/ImageDraw.html

## Set Border

Set the border colour of you pHAT or wHAT.

```python
display.set_border(colour)
```

`colour` should be one of `inky.RED`, `inky.YELLOW`, `inky.WHITE` or `inky.BLACK` with available colours depending on your display type.

## Update The Display

Once you've prepared and set your image, and chosen a border colour, you can update your e-ink display with:

```python
display.show()
```


# Migrating

If you're migrating code from the old `inkyphat` library you'll find that much of the drawing and image manipulation functions have been removed from Inky. These functions were always supplied by PIL, and the recommended approach is to use PIL to create and prepare your image before setting it to Inky with `set_image()`.
