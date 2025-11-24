"""Inky e-Ink Display Driver."""
import time
import warnings

import gpiod
import gpiodevice
import numpy
from gpiod.line import Bias, Direction, Value
from PIL import Image

from . import eeprom

BLACK = 0
WHITE = 1
YELLOW = 2
RED = 3
BLUE = 5
GREEN = 6

DESATURATED_PALETTE = [
    [0, 0, 0],
    [255, 255, 255],
    [255, 255, 0],
    [255, 0, 0],
    [0, 0, 255],
    [0, 255, 0],
    [255, 255, 255]]

SATURATED_PALETTE = [
    [0, 0, 0],
    [161, 164, 165],
    [208, 190, 71],
    [156, 72, 75],
    [61, 59, 94],
    [58, 91, 70],
    [255, 255, 255]]

RESET_PIN = 27  # PIN13
BUSY_PIN = 17   # PIN11
DC_PIN = 22     # PIN15

MOSI_PIN = 10
SCLK_PIN = 11
CS0_PIN = 8

EL673_PSR = 0x00
EL673_PWR = 0x01
EL673_POF = 0x02
EL673_POFS = 0x03
EL673_PON = 0x04
EL673_BTST1 = 0x05
EL673_BTST2 = 0x06
EL673_DSLP = 0x07
EL673_BTST3 = 0x08
EL673_DTM1 = 0x10
EL673_DSP = 0x11
EL673_DRF = 0x12
EL673_PLL = 0x30
EL673_CDI = 0x50
EL673_TCON = 0x60
EL673_TRES = 0x61
EL673_REV = 0x70
EL673_VDCS = 0x82
EL673_PWS = 0xE3

_SPI_CHUNK_SIZE = 4096

_RESOLUTION_7_3_INCH = (800, 480)  # Inky Impression 7.3 (Spectra 6)"

_RESOLUTION = {
    _RESOLUTION_7_3_INCH: (_RESOLUTION_7_3_INCH[0], _RESOLUTION_7_3_INCH[1], 0, 0, 0, 0b01),
}


class Inky:
    """Inky e-Ink Display Driver."""

    BLACK = 0
    WHITE = 1
    YELLOW = 2
    RED = 3
    BLUE = 4
    GREEN = 5

    WIDTH = 0
    HEIGHT = 0

    DESATURATED_PALETTE = [
        [0, 0, 0],
        [255, 255, 255],
        [255, 255, 0],
        [255, 0, 0],
        [0, 0, 255],
        [0, 255, 0],
        [255, 255, 255]]

    SATURATED_PALETTE = [
        [0, 0, 0],
        [161, 164, 165],
        [208, 190, 71],
        [156, 72, 75],
        [61, 59, 94],
        [58, 91, 70],
        [255, 255, 255]]

    def __init__(self, resolution=None, colour="multi", cs_pin=CS0_PIN, dc_pin=DC_PIN, reset_pin=RESET_PIN, busy_pin=BUSY_PIN, h_flip=False, v_flip=False, spi_bus=None, i2c_bus=None, gpio=None):  # noqa: E501
        """Initialise an Inky Display.

        :param resolution: (width, height) in pixels, default: (800, 480)
        :param colour: one of red, black or yellow, default: black
        :param cs_pin: chip-select pin for SPI communication
        :param dc_pin: data/command pin for SPI communication
        :param reset_pin: device reset pin
        :param busy_pin: device busy/wait pin
        :param h_flip: enable horizontal display flip, default: False
        :param v_flip: enable vertical display flip, default: False

        """
        self._spi_bus = spi_bus
        self._i2c_bus = i2c_bus
        self.eeprom = eeprom.read_eeprom(i2c_bus=i2c_bus)

        # Check for supported display variant and select the correct resolution
        if resolution is None:
            resolution = _RESOLUTION_7_3_INCH

        if resolution not in _RESOLUTION.keys():
            raise ValueError(f"Resolution {resolution[0]}x{resolution[1]} not supported!")

        self.resolution = resolution
        self.width, self.height = resolution
        self.WIDTH, self.HEIGHT = resolution
        self.border_colour = WHITE
        self.cols, self.rows, self.rotation, self.offset_x, self.offset_y, self.resolution_setting = _RESOLUTION[resolution]

        if colour not in ("multi"):
            raise ValueError(f"Colour {colour} is not supported!")

        self.colour = colour
        self.lut = colour

        self.buf = numpy.zeros((self.rows, self.cols), dtype=numpy.uint8)

        self.dc_pin = dc_pin
        self.reset_pin = reset_pin
        self.busy_pin = busy_pin
        self.cs_pin = cs_pin
        try:
            self.cs_channel = [8, 7].index(cs_pin)
        except ValueError:
            self.cs_channel = 0
        self.h_flip = h_flip
        self.v_flip = v_flip

        self._gpio = gpio
        self._gpio_setup = False

        self._luts = None

    def _palette_blend(self, saturation, dtype="uint8"):
        saturation = float(saturation)
        palette = []
        for i in range(6):
            rs, gs, bs = [c * saturation for c in self.SATURATED_PALETTE[i]]
            rd, gd, bd = [c * (1.0 - saturation) for c in self.DESATURATED_PALETTE[i]]
            if dtype == "uint8":
                palette += [int(rs + rd), int(gs + gd), int(bs + bd)]
            if dtype == "uint24":
                palette += [(int(rs + rd) << 16) | (int(gs + gd) << 8) | int(bs + bd)]
        return palette

    def setup(self):
        """Set up Inky GPIO and reset display."""
        if not self._gpio_setup:
            if self._gpio is None:
                gpiochip = gpiodevice.find_chip_by_platform()
                gpiodevice.friendly_errors = True
                if gpiodevice.check_pins_available(gpiochip, {
                        "Chip Select": self.cs_pin,
                        "Data/Command": self.dc_pin,
                        "Reset": self.reset_pin,
                        "Busy": self.busy_pin
                }):
                    self.cs_pin = gpiochip.line_offset_from_id(self.cs_pin)
                    self.dc_pin = gpiochip.line_offset_from_id(self.dc_pin)
                    self.reset_pin = gpiochip.line_offset_from_id(self.reset_pin)
                    self.busy_pin = gpiochip.line_offset_from_id(self.busy_pin)
                    self._gpio = gpiochip.request_lines(consumer="inky", config={
                        self.cs_pin: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.ACTIVE, bias=Bias.DISABLED),
                        self.dc_pin: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.INACTIVE, bias=Bias.DISABLED),
                        self.reset_pin: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.ACTIVE, bias=Bias.DISABLED),
                        self.busy_pin: gpiod.LineSettings(direction=Direction.INPUT, bias=Bias.PULL_UP)
                    })

            if self._spi_bus is None:
                import spidev
                self._spi_bus = spidev.SpiDev()

            self._spi_bus.open(0, self.cs_channel)
            self._spi_bus.max_speed_hz = 1000000

            self._gpio_setup = True

        self._gpio.set_value(self.reset_pin, Value.INACTIVE)
        time.sleep(0.03)
        self._gpio.set_value(self.reset_pin, Value.ACTIVE)
        time.sleep(0.03)

        self._busy_wait(0.3)

        self._send_command(0xAA, [0x49, 0x55, 0x20, 0x08, 0x09, 0x18])
        self._send_command(EL673_PWR, [0x3F])
        self._send_command(EL673_PSR, [0x5F, 0x69])

        self._send_command(EL673_BTST1, [0x40, 0x1F, 0x1F, 0x2C])
        self._send_command(EL673_BTST3, [0x6F, 0x1F, 0x1F, 0x22])
        self._send_command(EL673_BTST2, [0x6F, 0x1F, 0x17, 0x17])

        self._send_command(EL673_POFS, [0x00, 0x54, 0x00, 0x44])
        self._send_command(EL673_TCON, [0x02, 0x00])
        self._send_command(EL673_PLL, [0x08])
        self._send_command(EL673_CDI, [0x3F])
        self._send_command(EL673_TRES, [0x03, 0x20, 0x01, 0xE0])
        self._send_command(EL673_PWS, [0x2F])
        self._send_command(EL673_VDCS, [0x01])

    def _busy_wait(self, timeout=40.0):
        """Wait for busy/wait pin."""
        # If the busy_pin is *high* (pulled up by host)
        # then assume we're not getting a signal from inky
        # and wait the timeout period to be safe.
        if self._gpio.get_value(self.busy_pin) == Value.ACTIVE:
            time.sleep(timeout)
            return

        t_start = time.time()
        while not self._gpio.get_value(self.busy_pin) == Value.ACTIVE:
            time.sleep(0.1)
            if time.time() - t_start > timeout:
                warnings.warn(f"Busy Wait: Timed out after {timeout:0.2f}s")
                return

    def _update(self, buf):
        """Update display.

        Dispatches display update to correct driver.

        """
        self.setup()

        self._send_command(EL673_DTM1, buf)
        self._send_command(EL673_PON)
        self._busy_wait(0.3)

        # second setting of the BTST2 register
        self._send_command(EL673_BTST2, [0x6F, 0x1F, 0x17, 0x49])

        self._send_command(EL673_DRF, [0x00])
        self._busy_wait(32.0)

        self._send_command(EL673_POF, [0x00])
        self._busy_wait(0.3)

    def set_pixel(self, x, y, v):
        """Set a single pixel.

        :param x: x position on display
        :param y: y position on display
        :param v: colour to set

        """
        self.buf[y][x] = v & 0x07

    def show(self, busy_wait=True):
        """Show buffer on display.

        :param busy_wait: If True, wait for display update to finish before returning.

        """
        region = self.buf

        if self.v_flip:
            region = numpy.fliplr(region)

        if self.h_flip:
            region = numpy.flipud(region)

        if self.rotation:
            region = numpy.rot90(region, self.rotation // 90)

        buf = region.flatten()

        buf = ((buf[::2] << 4) & 0xF0) | (buf[1::2] & 0x0F)

        self._update(buf.astype("uint8").tolist())

    def set_border(self, colour):
        """Set the border colour."""
        if colour in (BLACK, WHITE, GREEN, BLUE, RED, YELLOW):
            self.border_colour = colour

    def set_image(self, image, saturation=0.5):
        """Copy an image to the display.

        :param image: PIL image to copy, must be 800x480
        :param saturation: Saturation for quantization palette - higher value results in a more saturated image

        """
        if not image.size == (self.width, self.height):
            raise ValueError(f"Image must be ({self.width}x{self.height}) pixels!")

        dither = Image.Dither.FLOYDSTEINBERG

        # Image size doesn't matter since it's just the palette we're using
        palette_image = Image.new("P", (1, 1))

        if image.mode == "P":
            # Create a pure colour palette from DESATURATED_PALETTE
            palette = numpy.array(DESATURATED_PALETTE, dtype=numpy.uint8).flatten().tobytes()
            palette_image.putpalette(palette)

            # Assume that palette mode images with an unset palette use the
            # default colour order and "DESATURATED_PALETTE" pure colours
            if not image.palette.colors:
                image.putpalette(palette)

            # Assume that palette mode images with exactly six colours use
            # all the correct colours, but not exactly in the right order.
            if len(image.palette.colors) == 6:
                dither = Image.Dither.NONE
        else:
            # All other image should be quantized and dithered
            palette = self._palette_blend(saturation)
            palette_image.putpalette(palette)

        image = image.convert("RGB").quantize(6, palette=palette_image, dither=dither)

        # Remap our sequential palette colours to display native (missing colour 4)
        remap = numpy.array([0, 1, 2, 3, 5, 6])
        self.buf = remap[numpy.array(image, dtype=numpy.uint8).reshape((self.rows, self.cols))]

    def _spi_write(self, dc, values):
        """Write values over SPI.

        :param dc: whether to write as data or command
        :param values: list of values to write

        """
        self._gpio.set_value(self.cs_pin, Value.INACTIVE)
        self._gpio.set_value(self.dc_pin, Value.ACTIVE if dc else Value.INACTIVE)

        if isinstance(values, str):
            values = [ord(c) for c in values]

        try:
            self._spi_bus.xfer3(values)
        except AttributeError:
            for x in range(((len(values) - 1) // _SPI_CHUNK_SIZE) + 1):
                offset = x * _SPI_CHUNK_SIZE
                self._spi_bus.xfer(values[offset:offset + _SPI_CHUNK_SIZE])

        self._gpio.set_value(self.cs_pin, Value.ACTIVE)

    def _send_command(self, command, data=None):
        """Send command over SPI.
        :param command: command byte
        :param data: optional list of values
        """

        self._gpio.set_value(self.cs_pin, Value.INACTIVE)
        self._gpio.set_value(self.dc_pin, Value.INACTIVE)
        time.sleep(0.3)
        self._spi_bus.xfer3([command])

        if data is not None:
            self._gpio.set_value(self.dc_pin, Value.ACTIVE)
            self._spi_bus.xfer3(data)

        self._gpio.set_value(self.cs_pin, Value.ACTIVE)
        self._gpio.set_value(self.dc_pin, Value.INACTIVE)
