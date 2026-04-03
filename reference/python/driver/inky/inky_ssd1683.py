"""Inky e-Ink Display Driver."""
import time
from datetime import timedelta

import gpiod
import gpiodevice
import numpy
from gpiod.line import Bias, Direction, Edge, Value
from PIL import Image

from . import eeprom, ssd1683

WHITE = 0
BLACK = 1
RED = YELLOW = 2

RESET_PIN = 27  # PIN13
BUSY_PIN = 17   # PIN11
DC_PIN = 22     # PIN15

MOSI_PIN = 10
SCLK_PIN = 11
CS0_PIN = 8

SUPPORTED_DISPLAYS = 17, 18, 19

_SPI_CHUNK_SIZE = 4096
_SPI_COMMAND = 0
_SPI_DATA = 1

_RESOLUTION = {
    (400, 300): (400, 300, 0, 0, 0)
}


class Inky:
    """Inky e-Ink Display Driver."""

    WHITE = 0
    BLACK = 1
    RED = 2
    YELLOW = 2

    def __init__(self, resolution=(400, 300), colour="black", cs_pin=CS0_PIN, dc_pin=DC_PIN, reset_pin=RESET_PIN, busy_pin=BUSY_PIN, h_flip=False, v_flip=False, spi_bus=None, i2c_bus=None, gpio=None):  # noqa: E501
        """Initialise an Inky Display.

        :param resolution: (width, height) in pixels, default: (400, 300)
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

        if resolution not in _RESOLUTION.keys():
            raise ValueError("Resolution {}x{} not supported!".format(*resolution))

        self.resolution = resolution
        self.width, self.height = resolution
        self.cols, self.rows, self.rotation, self.offset_x, self.offset_y = _RESOLUTION[resolution]

        if colour not in ("red", "black", "yellow"):
            raise ValueError("Colour {} is not supported!".format(colour))

        self.colour = colour
        self.eeprom = eeprom.read_eeprom(i2c_bus=i2c_bus)
        self.lut = colour

        if self.eeprom is not None:
            # Only support SSD1683 variants
            if self.eeprom.display_variant not in SUPPORTED_DISPLAYS:
                raise RuntimeError("This driver is not compatible with your board.")
            if self.eeprom.width != self.width or self.eeprom.height != self.height:
                raise ValueError("Supplied width/height do not match Inky: {}x{}".format(self.eeprom.width, self.eeprom.height))

        self.buf = numpy.zeros((self.cols, self.rows), dtype=numpy.uint8)

        self.border_colour = 0

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

        self._luts = {
            "black": [
                0x02, 0x02, 0x01, 0x11, 0x12, 0x12, 0x22, 0x22, 0x66, 0x69,
                0x69, 0x59, 0x58, 0x99, 0x99, 0x88, 0x00, 0x00, 0x00, 0x00,
                0xF8, 0xB4, 0x13, 0x51, 0x35, 0x51, 0x51, 0x19, 0x01, 0x00
            ],
            "red": [
                0x02, 0x02, 0x01, 0x11, 0x12, 0x12, 0x22, 0x22, 0x66, 0x69,
                0x69, 0x59, 0x58, 0x99, 0x99, 0x88, 0x00, 0x00, 0x00, 0x00,
                0xF8, 0xB4, 0x13, 0x51, 0x35, 0x51, 0x51, 0x19, 0x01, 0x00
            ],
            "yellow": [
                0x02, 0x02, 0x01, 0x11, 0x12, 0x12, 0x22, 0x22, 0x66, 0x69,
                0x69, 0x59, 0x58, 0x99, 0x99, 0x88, 0x00, 0x00, 0x00, 0x00,
                0xF8, 0xB4, 0x13, 0x51, 0x35, 0x51, 0x51, 0x19, 0x01, 0x00
            ]
        }

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
                        self.cs_pin: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.INACTIVE, bias=Bias.DISABLED),
                        self.dc_pin: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.INACTIVE, bias=Bias.DISABLED),
                        self.reset_pin: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.ACTIVE, bias=Bias.DISABLED),
                        self.busy_pin: gpiod.LineSettings(direction=Direction.INPUT, edge_detection=Edge.FALLING, bias=Bias.DISABLED)
                    })

            if self._spi_bus is None:
                import spidev

                self._spi_bus = spidev.SpiDev()

            self._spi_bus.open(0, self.cs_channel)
            self._spi_bus.max_speed_hz = 10000000  # Should be good for 20MHz according to datasheet

            self._gpio_setup = True

        self._gpio.set_value(self.reset_pin, Value.INACTIVE)
        time.sleep(0.5)
        self._gpio.set_value(self.reset_pin, Value.ACTIVE)
        time.sleep(0.5)

        self._send_command(0x12)  # Soft Reset
        time.sleep(1.0)  # Required, or we'll miss buf_a (black)
        self._busy_wait()

    def _busy_wait(self, timeout=30.0):
        """Wait for busy/wait pin."""
        if self._gpio.get_value(self.busy_pin) == Value.ACTIVE:
            event = self._gpio.wait_edge_events(timedelta(seconds=timeout))
            if not event:
                raise RuntimeError("Timeout waiting for busy signal to clear.")
            for event in self._gpio.read_edge_events():
                pass

    def _update(self, buf_a, buf_b, busy_wait=True):
        """Update display.

        Dispatches display update to correct driver.

        :param buf_a: Black/White pixels
        :param buf_b: Yellow/Red pixels

        """
        self.setup()

        self._send_command(ssd1683.DRIVER_CONTROL, [self.rows - 1, (self.rows - 1) >> 8, 0x00])
        # Set dummy line period
        self._send_command(ssd1683.WRITE_DUMMY, [0x1B])
        # Set Line Width
        self._send_command(ssd1683.WRITE_GATELINE, [0x0B])
        # Data entry sequence (scan direction leftward and downward)
        self._send_command(ssd1683.DATA_MODE, [0x03])
        # Set ram X start and end position
        xposBuf = [0x00, self.cols // 8 - 1]
        self._send_command(ssd1683.SET_RAMXPOS, xposBuf)
        # Set ram Y start and end position
        yposBuf = [0x00, 0x00, (self.rows - 1) & 0xFF, (self.rows - 1) >> 8]
        self._send_command(ssd1683.SET_RAMYPOS, yposBuf)
        # VCOM Voltage
        self._send_command(ssd1683.WRITE_VCOM, [0x70])
        # Write LUT DATA
        # self._send_command(ssd1683.WRITE_LUT, self._luts[self.lut])

        if self.border_colour == self.BLACK:
            self._send_command(ssd1683.WRITE_BORDER, 0b00000000)
            # GS Transition + Waveform 00 + GSA 0 + GSB 0
        elif self.border_colour == self.RED and self.colour == "red":
            self._send_command(ssd1683.WRITE_BORDER, 0b00000110)
            # GS Transition + Waveform 01 + GSA 1 + GSB 0
        elif self.border_colour == self.YELLOW and self.colour == "yellow":
            self._send_command(ssd1683.WRITE_BORDER, 0b00001111)
            # GS Transition + Waveform 11 + GSA 1 + GSB 1
        elif self.border_colour == self.WHITE:
            self._send_command(ssd1683.WRITE_BORDER, 0b00000001)
            # GS Transition + Waveform 00 + GSA 0 + GSB 1

        # Set RAM address to 0, 0
        self._send_command(ssd1683.SET_RAMXCOUNT, [0x00])
        self._send_command(ssd1683.SET_RAMYCOUNT, [0x00, 0x00])

        for data in ((ssd1683.WRITE_RAM, buf_a), (ssd1683.WRITE_ALTRAM, buf_b)):
            cmd, buf = data
            self._send_command(cmd, buf)

        self._busy_wait()
        self._send_command(ssd1683.MASTER_ACTIVATE)

    def set_pixel(self, x, y, v):
        """Set a single pixel.

        :param x: x position on display
        :param y: y position on display
        :param v: colour to set

        """
        if v in (WHITE, BLACK, RED):
            self.buf[y][x] = v

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

        buf_a = numpy.packbits(numpy.where(region == BLACK, 0, 1)).tolist()
        buf_b = numpy.packbits(numpy.where(region == RED, 1, 0)).tolist()

        self._update(buf_a, buf_b, busy_wait=busy_wait)

    def set_border(self, colour):
        """Set the border colour."""
        if colour in (WHITE, BLACK, RED):
            self.border_colour = colour

    def set_image(self, image):
        """Copy an image to the display."""
        if not image.mode == "P":
            palette_image = Image.new("P", (1, 1))
            r, g, b = 0, 0, 0
            if self.colour == "red":
                r = 255
            if self.colour == "yellow":
                r = g = 255
            palette_image.putpalette([255, 255, 255, 0, 0, 0, r, g, b] + [0, 0, 0] * 252)
            image.load()
            image = image.im.convert("P", True, palette_image.im)

        canvas = Image.new("P", (self.cols, self.rows))
        width, height = image.size
        canvas.paste(image, (self.offset_x, self.offset_y, width, height))
        self.buf = numpy.array(canvas, dtype=numpy.uint8).reshape((self.rows, self.cols))

    def _spi_write(self, dc, values):
        """Write values over SPI.

        :param dc: whether to write as data or command
        :param values: list of values to write

        """
        self._gpio.set_value(self.cs_pin, Value.INACTIVE)
        self._gpio.set_value(self.dc_pin, Value.ACTIVE if dc else Value.INACTIVE)

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
