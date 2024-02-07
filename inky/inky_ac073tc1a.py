"""Inky e-Ink Display Driver."""
import time
import warnings
from datetime import timedelta

import gpiod
import gpiodevice
from gpiod.line import Direction, Edge, Value
from PIL import Image

from . import eeprom

try:
    import numpy
except ImportError:
    raise ImportError("This library requires the numpy module\nInstall with: sudo apt install python-numpy")

BLACK = 0
WHITE = 1
GREEN = 2
BLUE = 3
RED = 4
YELLOW = 5
ORANGE = 6
CLEAN = 7

RESET_PIN = 27  # PIN13
BUSY_PIN = 17   # PIN11
DC_PIN = 22     # PIN15

MOSI_PIN = 10
SCLK_PIN = 11
CS0_PIN = 8

AC073TC1_PSR = 0x00
AC073TC1_PWR = 0x01
AC073TC1_POF = 0x02
AC073TC1_POFS = 0x03
AC073TC1_PON = 0x04
AC073TC1_BTST1 = 0x05
AC073TC1_BTST2 = 0x06
AC073TC1_DSLP = 0x07
AC073TC1_BTST3 = 0x08
AC073TC1_DTM = 0x10
AC073TC1_DSP = 0x11
AC073TC1_DRF = 0x12
AC073TC1_IPC = 0x13
AC073TC1_PLL = 0x30
AC073TC1_TSC = 0x40
AC073TC1_TSE = 0x41
AC073TC1_TSW = 0x42
AC073TC1_TSR = 0x43
AC073TC1_CDI = 0x50
AC073TC1_LPD = 0x51
AC073TC1_TCON = 0x60
AC073TC1_TRES = 0x61
AC073TC1_DAM = 0x65
AC073TC1_REV = 0x70
AC073TC1_FLG = 0x71
AC073TC1_AMV = 0x80
AC073TC1_VV = 0x81
AC073TC1_VDCS = 0x82
AC073TC1_T_VDCS = 0x84
AC073TC1_AGID = 0x86
AC073TC1_CMDH = 0xAA
AC073TC1_CCSET = 0xE0
AC073TC1_PWS = 0xE3
AC073TC1_TSSET = 0xE6

_SPI_CHUNK_SIZE = 4096
_SPI_COMMAND = 0
_SPI_DATA = 1

_RESOLUTION_7_3_INCH = (800, 480)  # Inky Impression 7.3"


_RESOLUTION = {
    _RESOLUTION_7_3_INCH: (_RESOLUTION_7_3_INCH[0], _RESOLUTION_7_3_INCH[1], 0, 0, 0, 0b11),
}


class Inky:
    """Inky e-Ink Display Driver."""

    BLACK = 0
    WHITE = 1
    GREEN = 2
    BLUE = 3
    RED = 4
    YELLOW = 5
    ORANGE = 6
    CLEAN = 7

    WIDTH = 800
    HEIGHT = 480

    DESATURATED_PALETTE = [
        [0, 0, 0],        # Black
        [255, 255, 255],  # White
        [0, 255, 0],      # Green
        [0, 0, 255],      # Blue
        [255, 0, 0],      # Red
        [255, 255, 0],    # Yellow
        [255, 140, 0],    # Orange
        [255, 255, 255]   # Clear
    ]

    SATURATED_PALETTE = [
        [0, 0, 0],        # Black
        [217, 242, 255],  # White
        [3, 124, 76],     # Green
        [27, 46, 198],    # Blue
        [245, 80, 34],    # Red
        [255, 255, 68],   # Yellow
        [239, 121, 44],   # Orange
        [255, 255, 255]   # Clear
    ]

    def __init__(self, resolution=None, colour="multi", cs_pin=CS0_PIN, dc_pin=DC_PIN, reset_pin=RESET_PIN, busy_pin=BUSY_PIN, h_flip=False, v_flip=False, spi_bus=None, i2c_bus=None, gpio=None):  # noqa: E501
        """Initialise an Inky Display.

        :param resolution: (width, height) in pixels, default: (600, 448)
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
        # Eg: 600x480 and 640x400
        if resolution is None:
            if self.eeprom is not None and self.eeprom.display_variant in (14, 15, 16):
                resolution = [_RESOLUTION_7_3_INCH, None, _RESOLUTION_7_3_INCH][self.eeprom.display_variant - 14]
            else:
                resolution = _RESOLUTION_7_3_INCH

        if resolution not in _RESOLUTION.keys():
            raise ValueError("Resolution {}x{} not supported!".format(*resolution))

        self.resolution = resolution
        self.width, self.height = resolution
        self.border_colour = WHITE
        self.cols, self.rows, self.rotation, self.offset_x, self.offset_y, self.resolution_setting = _RESOLUTION[resolution]

        if colour not in ("multi"):
            raise ValueError("Colour {} is not supported!".format(colour))

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
        for i in range(7):
            rs, gs, bs = [c * saturation for c in self.SATURATED_PALETTE[i]]
            rd, gd, bd = [c * (1.0 - saturation) for c in self.DESATURATED_PALETTE[i]]
            if dtype == "uint8":
                palette += [int(rs + rd), int(gs + gd), int(bs + bd)]
            if dtype == "uint24":
                palette += [(int(rs + rd) << 16) | (int(gs + gd) << 8) | int(bs + bd)]
        if dtype == "uint8":
            palette += [255, 255, 255]
        if dtype == "uint24":
            palette += [0xFFFFFF]
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
                        self.cs_pin: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.ACTIVE),
                        self.dc_pin: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.INACTIVE),
                        self.reset_pin: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.ACTIVE),
                        self.busy_pin: gpiod.LineSettings(direction=Direction.INPUT, edge_detection=Edge.RISING, debounce_period=timedelta(milliseconds=10))
                    })

            if self._spi_bus is None:
                import spidev
                self._spi_bus = spidev.SpiDev()

            self._spi_bus.open(0, self.cs_channel)
            try:
                self._spi_bus.no_cs = True
            except OSError:
                warnings.warn("SPI: Cannot disable chip-select!")
            self._spi_bus.max_speed_hz = 5000000

            self._gpio_setup = True

        self._gpio.set_value(self.reset_pin, Value.INACTIVE)
        time.sleep(0.1)
        self._gpio.set_value(self.reset_pin, Value.ACTIVE)
        time.sleep(0.1)

        self._gpio.set_value(self.reset_pin, Value.INACTIVE)
        time.sleep(0.1)
        self._gpio.set_value(self.reset_pin, Value.ACTIVE)

        self._busy_wait(1.0)

        # Sending init commands to display
        self._send_command(AC073TC1_CMDH, [0x49, 0x55, 0x20, 0x08, 0x09, 0x18])

        self._send_command(AC073TC1_PWR, [0x3F, 0x00, 0x32, 0x2A, 0x0E, 0x2A])

        self._send_command(AC073TC1_PSR, [0x5F, 0x69])

        self._send_command(AC073TC1_POFS, [0x00, 0x54, 0x00, 0x44])

        self._send_command(AC073TC1_BTST1, [0x40, 0x1F, 0x1F, 0x2C])

        self._send_command(AC073TC1_BTST2, [0x6F, 0x1F, 0x16, 0x25])

        self._send_command(AC073TC1_BTST3, [0x6F, 0x1F, 0x1F, 0x22])

        self._send_command(AC073TC1_IPC, [0x00, 0x04])

        self._send_command(AC073TC1_PLL, [0x02])

        self._send_command(AC073TC1_TSE, [0x00])

        self._send_command(AC073TC1_CDI, [0x3F])

        self._send_command(AC073TC1_TCON, [0x02, 0x00])

        self._send_command(AC073TC1_TRES, [0x03, 0x20, 0x01, 0xE0])

        self._send_command(AC073TC1_VDCS, [0x1E])

        self._send_command(AC073TC1_T_VDCS, [0x00])

        self._send_command(AC073TC1_AGID, [0x00])

        self._send_command(AC073TC1_PWS, [0x2F])

        self._send_command(AC073TC1_CCSET, [0x00])

        self._send_command(AC073TC1_TSSET, [0x00])

    def _busy_wait(self, timeout=40.0):
        """Wait for busy/wait pin."""
        # If the busy_pin is *high* (pulled up by host)
        # then assume we're not getting a signal from inky
        # and wait the timeout period to be safe.
        if self._gpio.get_value(self.busy_pin) == Value.ACTIVE:
            warnings.warn("Busy Wait: Held high. Waiting for {:0.2f}s".format(timeout))
            time.sleep(timeout)
            return

        event = self._gpio.wait_edge_events(timedelta(seconds=timeout))
        if not event:
            warnings.warn(f"Busy Wait: Timed out after {timeout:0.2f}s")
            return

        for event in self._gpio.read_edge_events():
            print(timeout, event)

    def _update(self, buf):
        """Update display.

        Dispatches display update to correct driver.

        :param buf_a: Black/White pixels
        :param buf_b: Yellow/Red pixels

        """

        self.setup()

        # TODO there has to be a better way to force the white colour to be used instead of clear...

        for i in range(len(buf)):
            if buf[i] & 0xF == 7:
                buf[i] = (buf[i] & 0xF0) + 1
                # print buf[i]
            if buf[i] & 0xF0 == 0x70:
                buf[i] = (buf[i] & 0xF) + 0x10
                # print buf[i]

        self._send_command(AC073TC1_DTM, buf)

        self._send_command(AC073TC1_PON)
        self._busy_wait(0.4)

        self._send_command(AC073TC1_DRF, [0x00])
        self._busy_wait(45.0)  # 41 seconds in testing

        self._send_command(AC073TC1_POF, [0x00])
        self._busy_wait(0.4)

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
        if colour in (BLACK, WHITE, GREEN, BLUE, RED, YELLOW, ORANGE, CLEAN):
            self.border_colour = colour

    def set_image(self, image, saturation=0.5):
        """Copy an image to the display.

        :param image: PIL image to copy, must be 600x448
        :param saturation: Saturation for quantization palette - higher value results in a more saturated image

        """
        if not image.size == (self.width, self.height):
            raise ValueError("Image must be ({}x{}) pixels!".format(self.width, self.height))
        if not image.mode == "P":
            palette = self._palette_blend(saturation)
            # Image size doesn't matter since it's just the palette we're using
            palette_image = Image.new("P", (1, 1))
            # Set our 7 colour palette (+ clear) and zero out the other 247 colours
            palette_image.putpalette(palette + [0, 0, 0] * 248)
            # Force source image data to be loaded for `.im` to work
            image.load()
            image = image.im.convert("P", True, palette_image.im)
        self.buf = numpy.array(image, dtype=numpy.uint8).reshape((self.rows, self.cols))

    def _spi_write(self, dc, values):
        """Write values over SPI.

        :param dc: whether to write as data or command
        :param values: list of values to write

        """
        self._gpio.set_value(self.cs_pin, Value.INACTIVE)
        self._gpio.set_value(self.dc_pin, Value.ACTIVE if dc else Value.INACTIVE)

        if isinstance(values, str):
            values = [ord(c) for c in values]

        for byte_value in values:
            self._spi_bus.xfer([byte_value])

        self._gpio.set_value(self.cs_pin, Value.ACTIVE)

    def _send_command(self, command, data=None):
        """Send command over SPI.

        :param command: command byte
        :param data: optional list of values

        """
        self._spi_write(_SPI_COMMAND, [command])
        if data is not None:
            self._send_data(data)

    def _send_data(self, data):
        """Send data over SPI.

        :param data: list of values

        """
        if isinstance(data, int):
            data = [data]
        self._spi_write(_SPI_DATA, data)
