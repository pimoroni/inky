# Inky<!-- omit in toc -->

[![Build Status](https://img.shields.io/github/actions/workflow/status/pimoroni/inky/test.yml?branch=main)](https://github.com/pimoroni/inky/actions/workflows/test.yml)
[![Coverage Status](https://coveralls.io/repos/github/pimoroni/inky/badge.svg?branch=main)](https://coveralls.io/github/pimoroni/inky?branch=main)
[![PyPi Package](https://img.shields.io/pypi/v/inky.svg)](https://pypi.python.org/pypi/inky)
[![Python Versions](https://img.shields.io/pypi/pyversions/inky.svg)](https://pypi.python.org/pypi/inky)

Python library for [Inky pHAT](https://shop.pimoroni.com/products/inky-phat), [Inky wHAT](https://shop.pimoroni.com/products/inky-what) and [Inky Impression](https://shop.pimoroni.com/?q=inky+impression) e-paper displays for Raspberry Pi.

- [Get Inky](#get-inky)
- [Installation](#installation)
  - [Full install (recommended)](#full-install-recommended)
  - [Development](#development)
  - [Install stable library from PyPi and configure manually](#install-stable-library-from-pypi-and-configure-manually)
- [Usage](#usage)
  - [Auto Setup](#auto-setup)
  - [Manual Setup](#manual-setup)
  - [Set Image](#set-image)
  - [Set Border](#set-border)
  - [Update The Display](#update-the-display)
- [Migrating](#migrating)
- [Troubleshooting](#troubleshooting)
- [Other Resources](#other-resources)

## Get Inky

[Inky pHAT](https://shop.pimoroni.com/products/inky-phat) is a 250x122 pixel e-paper display, available in red/black/white, yellow/black/white and black/white. It's great for nametags and displaying very low frequency information such as a daily calendar or weather overview.

[Inky wHAT](https://shop.pimoroni.com/products/inky-what) is a 400x300 pixel e-paper display available in red/black/white, yellow/black/white and black/white. It's got tons of resolution for detailed daily to-do lists, multi-day weather forecasts, bus timetables and more.

[Inky Impression](https://shop.pimoroni.com/search?q=inky%20impression) is our line of glorious colour eInk displays, available in various sizes from the petite 4.0" up to the mighty 13.3". They're packed with strong colours and perfect for displaying striking graphics or lots of data.

## Installation

We'd recommend using this library with Raspberry Pi OS Bookworm or later. It requires Python ≥3.7.

### Full install (recommended)

We've created an easy installation script that will install all pre-requisites and get you up and running with minimal efforts. To run it, fire up Terminal which you'll find in Menu -> Accessories -> Terminal
on your Raspberry Pi desktop, as illustrated below:

![Finding the terminal](http://get.pimoroni.com/resources/github-repo-terminal.png)

In the new terminal window type the commands exactly as it appears below (check for typos) and follow the on-screen instructions:

```bash
git clone https://github.com/pimoroni/inky
cd inky
./install.sh
```

**Note** Libraries will be installed in the "pimoroni" virtual environment, you will need to activate it to run examples:

```
source ~/.virtualenvs/pimoroni/bin/activate
```

### Development

If you want to contribute, or like living on the edge of your seat by having the latest code, you can install the development version like so:

```bash
git clone https://github.com/pimoroni/inky
cd inky
./install.sh --unstable
```

### Install stable library from PyPi and configure manually

* Set up a virtual environment: `python3 -m venv --system-site-packages $HOME/.virtualenvs/pimoroni`
* Switch to the virtual environment: `source ~/.virtualenvs/pimoroni/bin/activate`
* Install the library: `pip install inky`

This will not make any configuration changes, so you may also need to enable:

* i2c: `sudo raspi-config nonint do_i2c 0`
* spi: `sudo raspi-config nonint do_spi 0`

You can optionally run `sudo raspi-config` or the graphical Raspberry Pi Configuration UI to enable interfaces.

Additionally you may need to disable SPI's chip-select to avoid the error:

```
Woah there, some pins we need are in use!
  ⚠️   Chip Select: (line 8, GPIO8) currently claimed by spi0 CS0
```

This requires the addition of `dtoverlay=spi0-0cs` to `/boot/firmware/config.txt`.

## Usage

The library should be run with Python 3.

### Auto Setup

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

### Manual Setup

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

### Set Image

Set a PIL image, numpy array or list to Inky's internal buffer. The image dimensions should match the dimensions of the pHAT or wHAT you're using.

```python
display.set_image(image)
```

You should use `PIL` to create an image. `PIL` provides an `ImageDraw` module which allow you to draw text, lines and shapes over your image. See: https://pillow.readthedocs.io/en/stable/reference/ImageDraw.html

### Set Border

Set the border colour of you pHAT or wHAT.

```python
display.set_border(colour)
```

`colour` should be one of `inky.RED`, `inky.YELLOW`, `inky.WHITE` or `inky.BLACK` with available colours depending on your display type.

### Update The Display

Once you've prepared and set your image, and chosen a border colour, you can update your e-ink display with:

```python
display.show()
```

## Migrating

If you're migrating code from the old `inkyphat` library you'll find that much of the drawing and image manipulation functions have been removed from Inky. These functions were always supplied by PIL, and the recommended approach is to use PIL to create and prepare your image before setting it to Inky with `set_image()`.

## Troubleshooting

### `ModuleNotFoundError: No module named 'inky'`<!-- omit in toc -->

Assuming you've run `./install.sh` already, make sure you have your virtual environment active. If you're using the one set up by our installer, that looks like this:

```
source ~/.virtualenvs/pimoroni/bin/activate
```

### `ModuleNotFoundError: No module named 'font_hanken_grotesk'`<!-- omit in toc -->

You're missing some dependencies that the example code needs to run. A list of dependencies can be found [here](https://github.com/pimoroni/inky/blob/main/requirements-examples.txt), and you can install them like this (make sure you have your virtual environment active):

```
pip install font-hanken-grotesk
```

### `RuntimeError: No EEPROM detected! You must manually initialise your Inky board.`<!-- omit in toc -->

Check that I2C and SPI are enabled. You can do this using `sudo raspi-config` - they're under 'Interfacing Options'. You may need to reboot your Pi after you've enabled them (`sudo reboot`).

### `Chip Select: (line 8, GPIO8) currently claimed by spi0 CS0`<!-- omit in toc -->

Check you have the following line present in your /boot/firmware/config.txt:

```
dtoverlay=spi0-0cs
```

You can edit the config file using `sudo nano boot/firmware/config.txt`, and it's Ctrl-X, then 'Y' and Enter to save your changes. You'll need to reboot your Pi after you've made this change (`sudo reboot`)

## Other Resources

Links to community projects and other resources that you might find helpful can be found below. Note that these code examples have not been written/tested by us and we're not able to offer support with them.

- InkyPi (customisable eInk display) - [Youtube](https://www.youtube.com/watch?v=L5PvQj1vfC4) / [Github](https://github.com/fatihak/InkyPi)
- [Using Pimoroni Inky displays with CircuitPython](https://github.com/bablokb/circuitpython-inky)
- [Inky Draw](https://github.com/jonothanhunt/inky-draw) - a fun drawing project for Inky pHAT using Flask and React
- [I built an E-Ink Calendar with a Raspberry Pi](https://www.youtube.com/watch?v=58QWxoFvtJY)
- [Spectra-Qualified Uncomplicated Inky Rendering Tools](https://github.com/fitoori/squirt) - one-shot Python scripts to display web content