"""Inky e-Ink Display Driver."""
import struct
import time
import warnings
from datetime import timedelta

import gpiod
import gpiodevice
import numpy
from gpiod.line import Bias, Direction, Edge, Value
from PIL import Image

from . import eeprom

BLACK = 0
WHITE = 1
GREEN = 2
BLUE = 3
RED = 4
YELLOW = 5
ORANGE = 6
CLEAN = 7

DESATURATED_PALETTE = [
    [0, 0, 0],
    [255, 255, 255],
    [0, 255, 0],
    [0, 0, 255],
    [255, 0, 0],
    [255, 255, 0],
    [255, 140, 0],
    [255, 255, 255]
]

SATURATED_PALETTE = [
    [57, 48, 57],
    [255, 255, 255],
    [58, 91, 70],
    [61, 59, 94],
    [156, 72, 75],
    [208, 190, 71],
    [177, 106, 73],
    [255, 255, 255]
]

RESET_PIN = 27  # PIN13
BUSY_PIN = 17   # PIN11
DC_PIN = 22     # PIN15

MOSI_PIN = 10
SCLK_PIN = 11
CS0_PIN = 8

UC8159_PSR = 0x00
UC8159_PWR = 0x01
UC8159_POF = 0x02
UC8159_PFS = 0x03
UC8159_PON = 0x04
UC8159_BTST = 0x06
UC8159_DSLP = 0x07
UC8159_DTM1 = 0x10
UC8159_DSP = 0x11
UC8159_DRF = 0x12
UC8159_IPC = 0x13
UC8159_PLL = 0x30
UC8159_TSC = 0x40
UC8159_TSE = 0x41
UC8159_TSW = 0x42
UC8159_TSR = 0x43
UC8159_CDI = 0x50
UC8159_LPD = 0x51
UC8159_TCON = 0x60
UC8159_TRES = 0x61
UC8159_DAM = 0x65
UC8159_REV = 0x70
UC8159_FLG = 0x71
UC8159_AMV = 0x80
UC8159_VV = 0x81
UC8159_VDCS = 0x82
UC8159_PWS = 0xE3
UC8159_TSSET = 0xE5

_SPI_CHUNK_SIZE = 4096
_SPI_COMMAND = 0
_SPI_DATA = 1

_RESOLUTION_5_7_INCH = (600, 448)  # Inky Impression 5.7"
_RESOLUTION_4_INCH = (640, 400)    # Inky Impression 4"

_RESOLUTION = {
    _RESOLUTION_5_7_INCH: (_RESOLUTION_5_7_INCH[0], _RESOLUTION_5_7_INCH[1], 0, 0, 0, 0b11),
    _RESOLUTION_4_INCH: (_RESOLUTION_4_INCH[0], _RESOLUTION_4_INCH[1], 0, 0, 0, 0b10)
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

    WIDTH = 600
    HEIGHT = 448

    DESATURATED_PALETTE = [
        [0, 0, 0],
        [255, 255, 255],
        [0, 255, 0],
        [0, 0, 255],
        [255, 0, 0],
        [255, 255, 0],
        [255, 140, 0],
        [255, 255, 255]]

    SATURATED_PALETTE = [
        [57, 48, 57],
        [255, 255, 255],
        [58, 91, 70],
        [61, 59, 94],
        [156, 72, 75],
        [208, 190, 71],
        [177, 106, 73],
        [255, 255, 255]]

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
                resolution = [_RESOLUTION_5_7_INCH, None, _RESOLUTION_4_INCH][self.eeprom.display_variant - 14]
            else:
                resolution = _RESOLUTION_5_7_INCH

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
                        self.cs_pin: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.ACTIVE, bias=Bias.DISABLED),
                        self.dc_pin: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.INACTIVE, bias=Bias.DISABLED),
                        self.reset_pin: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.ACTIVE, bias=Bias.DISABLED),
                        self.busy_pin: gpiod.LineSettings(direction=Direction.INPUT, edge_detection=Edge.RISING, debounce_period=timedelta(milliseconds=10), bias=Bias.DISABLED)
                    })

            if self._spi_bus is None:
                import spidev
                self._spi_bus = spidev.SpiDev()

            self._spi_bus.open(0, self.cs_channel)
            try:
                self._spi_bus.no_cs = True
            except OSError:
                warnings.warn("SPI: Cannot disable chip-select!")
            self._spi_bus.max_speed_hz = 3000000

            self._gpio_setup = True

        self._gpio.set_value(self.reset_pin, Value.INACTIVE)
        time.sleep(0.1)
        self._gpio.set_value(self.reset_pin, Value.ACTIVE)
        time.sleep(0.1)

        self._busy_wait(1.0)

        # Resolution Setting
        # 10bit horizontal followed by a 10bit vertical resolution
        # we'll let struct.pack do the work here and send 16bit values
        # life is too short for manual bit wrangling
        self._send_command(
            UC8159_TRES,
            struct.pack(">HH", self.width, self.height))

        # Panel Setting
        # 0b11000000 = Resolution select, 0b00 = 640x480, our panel is 0b11 = 600x448
        # 0b00100000 = LUT selection, 0 = ext flash, 1 = registers, we use ext flash
        # 0b00010000 = Ignore
        # 0b00001000 = Gate scan direction, 0 = down, 1 = up (default)
        # 0b00000100 = Source shift direction, 0 = left, 1 = right (default)
        # 0b00000010 = DC-DC converter, 0 = off, 1 = on
        # 0b00000001 = Soft reset, 0 = Reset, 1 = Normal (Default)
        # 0b11 = 600x448
        # 0b10 = 640x400
        self._send_command(
            UC8159_PSR,
            [
                (self.resolution_setting << 6) | 0b101111,  # See above for more magic numbers
                0x08                                        # display_colours == UC8159_7C
            ]
        )

        # Power Settings
        self._send_command(
            UC8159_PWR,
            [
                (0x06 << 3) |  # ??? - not documented in UC8159 datasheet  # noqa: W504
                (0x01 << 2) |  # SOURCE_INTERNAL_DC_DC                     # noqa: W504
                (0x01 << 1) |  # GATE_INTERNAL_DC_DC                       # noqa: W504
                (0x01),        # LV_SOURCE_INTERNAL_DC_DC
                0x00,          # VGx_20V
                0x23,          # UC8159_7C
                0x23           # UC8159_7C
            ]
        )

        # Set the PLL clock frequency to 50Hz
        # 0b11000000 = Ignore
        # 0b00111000 = M
        # 0b00000111 = N
        # PLL = 2MHz * (M / N)
        # PLL = 2MHz * (7 / 4)
        # PLL = 2,800,000 ???
        self._send_command(UC8159_PLL, [0x3C])  # 0b00111100

        # Send the TSE register to the display
        self._send_command(UC8159_TSE, [0x00])  # Colour

        # VCOM and Data Interval setting
        # 0b11100000 = Vborder control (0b001 = LUTB voltage)
        # 0b00010000 = Data polarity
        # 0b00001111 = Vcom and data interval (0b0111 = 10, default)
        cdi = (self.border_colour << 5) | 0x17
        self._send_command(UC8159_CDI, [cdi])  # 0b00110111

        # Gate/Source non-overlap period
        # 0b11110000 = Source to Gate (0b0010 = 12nS, default)
        # 0b00001111 = Gate to Source
        self._send_command(UC8159_TCON, [0x22])  # 0b00100010

        # Disable external flash
        self._send_command(UC8159_DAM, [0x00])

        # UC8159_7C
        self._send_command(UC8159_PWS, [0xAA])

        # Power off sequence
        # 0b00110000 = power off sequence of VDH and VDL, 0b00 = 1 frame (default)
        # All other bits ignored?
        self._send_command(
            UC8159_PFS, [0x00]  # PFS_1_FRAME
        )

    def _busy_wait(self, timeout=40.0):
        """Wait for busy/wait pin."""
        # If the busy_pin is *high* (pulled up by host)
        # then assume we're not getting a signal from inky
        # and wait the timeout period to be safe.
        if self._gpio.get_value(self.busy_pin) == Value.ACTIVE:
            warnings.warn(f"Busy Wait: Held high. Waiting for {timeout:0.2f}s")
            time.sleep(timeout)
            return

        event = self._gpio.wait_edge_events(timedelta(seconds=timeout))
        if not event:
            warnings.warn(f"Busy Wait: Timed out after {timeout:0.2f}s")
            return

        for event in self._gpio.read_edge_events():
            if event.Type == Edge.RISING:
                return

    def _update(self, buf):
        """Update display.

        Dispatches display update to correct driver.

        """
        self.setup()
        self._send_command(UC8159_DTM1, buf)

        self._send_command(UC8159_PON)
        self._busy_wait(0.2)

        self._send_command(UC8159_DRF)
        self._busy_wait(32.0)

        self._send_command(UC8159_POF)
        self._busy_wait(0.2)

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
            raise ValueError(f"Image must be ({self.width}x{self.height}) pixels!")
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

        try:
            self._spi_bus.xfer3(values)
        except AttributeError:
            for x in range(((len(values) - 1) // _SPI_CHUNK_SIZE) + 1):
                offset = x * _SPI_CHUNK_SIZE
                self._spi_bus.xfer(values[offset : offset + _SPI_CHUNK_SIZE])

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
