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
CS0_PIN = 26
CS1_PIN = 16

CS0_SEL = 0b01
CS1_SEL = 0b10
CS_BOTH_SEL = CS0_SEL | CS1_SEL

EL133UF1_PSR = 0x00
EL133UF1_PWR = 0x01
EL133UF1_POF = 0x02
EL133UF1_PON = 0x04
EL133UF1_BTST_N = 0x05
EL133UF1_BTST_P = 0x06
EL133UF1_DTM = 0x10
EL133UF1_DRF = 0x12
EL133UF1_PLL = 0x30
EL133UF1_TSC = 0x40
EL133UF1_TSE = 0x41
EL133UF1_TSW = 0x42
EL133UF1_TSR = 0x43
EL133UF1_CDI = 0x50
EL133UF1_LPD = 0x51
EL133UF1_TCON = 0x60
EL133UF1_TRES = 0x61
EL133UF1_DAM = 0x65
EL133UF1_REV = 0x70
EL133UF1_FLG = 0x71
EL133UF1_AMV = 0x80
EL133UF1_VV = 0x81
EL133UF1_VDCS = 0x82
EL133UF1_PTLW = 0x83
EL133UF1_ANTM = 0x74
EL133UF1_AGID = 0x86
EL133UF1_PWS = 0xE3
EL133UF1_TSSET = 0xE5
EL133UF1_CMD66 = 0xF0
EL133UF1_CCSET = 0xE0
EL133UF1_BOOST_VDDP_EN = 0xB7
EL133UF1_EN_BUF = 0xB6
EL133UF1_TFT_VCOM_POWER = 0xB1
EL133UF1_BUCK_BOOST_VDDN = 0xB0

_RESOLUTION_13_3_INCH = (1600, 1200)    # Inky Impression 13 (Spectra 6)"

_RESOLUTION = {
    _RESOLUTION_13_3_INCH: (_RESOLUTION_13_3_INCH[0], _RESOLUTION_13_3_INCH[1], 0, 0, 0, 0b01)
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

    def __init__(self, resolution=None, colour="multi", cs_pin_0=CS0_PIN, cs_pin_1=CS1_PIN, dc_pin=DC_PIN, reset_pin=RESET_PIN, busy_pin=BUSY_PIN, h_flip=False, v_flip=False, spi_bus=None, i2c_bus=None, gpio=None):  # noqa: E501
        """Initialise an Inky Display.
        :param resolution: (width, height) in pixels, default: (1600, 1200)
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
            if self.eeprom is not None and self.eeprom.display_variant == 21:
                resolution = [_RESOLUTION_13_3_INCH, None, _RESOLUTION_13_3_INCH][self.eeprom.display_variant]
            else:
                resolution = _RESOLUTION_13_3_INCH

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
        self.cs_pin_0 = cs_pin_0
        self.cs_pin_1 = cs_pin_1

        try:
            self.cs_channel = [8, 7].index(cs_pin_0)
        except ValueError:
            self.cs_channel = 0

        self.h_flip = h_flip
        self.v_flip = v_flip

        self._gpio = gpio
        self._gpio_setup = False

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
                        "Chip Select 0": self.cs_pin_0,
                        "Chip Select 1": self.cs_pin_1,
                        "Data/Command": self.dc_pin,
                        "Reset": self.reset_pin,
                        "Busy": self.busy_pin
                }):

                    self.cs0_pin = gpiochip.line_offset_from_id(self.cs_pin_0)
                    self.cs1_pin = gpiochip.line_offset_from_id(self.cs_pin_1)
                    self.dc_pin = gpiochip.line_offset_from_id(self.dc_pin)
                    self.reset_pin = gpiochip.line_offset_from_id(self.reset_pin)
                    self.busy_pin = gpiochip.line_offset_from_id(self.busy_pin)
                    self._gpio = gpiochip.request_lines(consumer="inky", config={
                        self.cs0_pin: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.ACTIVE, bias=Bias.DISABLED),
                        self.cs1_pin: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.ACTIVE, bias=Bias.DISABLED),
                        self.dc_pin: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.INACTIVE, bias=Bias.DISABLED),
                        self.reset_pin: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.ACTIVE, bias=Bias.DISABLED),
                        self.busy_pin: gpiod.LineSettings(direction=Direction.INPUT, bias=Bias.PULL_UP)

                    })

            if self._spi_bus is None:
                import spidev
                self._spi_bus = spidev.SpiDev()

            self._spi_bus.open(0, self.cs_channel)
            self._spi_bus.max_speed_hz = 10000000

            self._gpio_setup = True

        self._gpio.set_value(self.reset_pin, Value.INACTIVE)
        time.sleep(0.03)
        self._gpio.set_value(self.reset_pin, Value.ACTIVE)
        time.sleep(0.03)

        self._busy_wait(0.3)

        self._send_command(EL133UF1_ANTM, CS0_SEL, [0xC0, 0x1C, 0x1C, 0xCC, 0xCC, 0xCC, 0x15, 0x15, 0x55])

        self._send_command(EL133UF1_CMD66, CS_BOTH_SEL, [0x49, 0x55, 0x13, 0x5D, 0x05, 0x10])
        self._send_command(EL133UF1_PSR, CS_BOTH_SEL, [0xDF, 0x69])
        self._send_command(EL133UF1_PLL, CS_BOTH_SEL, [0x08])
        self._send_command(EL133UF1_CDI, CS_BOTH_SEL, [0xF7])
        self._send_command(EL133UF1_TCON, CS_BOTH_SEL, [0x03, 0x03])
        self._send_command(EL133UF1_AGID, CS_BOTH_SEL, [0x10])
        self._send_command(EL133UF1_PWS, CS_BOTH_SEL, [0x22])
        self._send_command(EL133UF1_CCSET, CS_BOTH_SEL, [0x01])
        self._send_command(EL133UF1_TRES, CS_BOTH_SEL, [0x04, 0xB0, 0x03, 0x20])

        self._send_command(EL133UF1_PWR, CS0_SEL, [0x0F, 0x00, 0x28, 0x2C, 0x28, 0x38])
        self._send_command(EL133UF1_EN_BUF, CS0_SEL, [0x07])
        self._send_command(EL133UF1_BTST_P, CS0_SEL, [0xD8, 0x18])
        self._send_command(EL133UF1_BOOST_VDDP_EN, CS0_SEL, [0x01])
        self._send_command(EL133UF1_BTST_N, CS0_SEL, [0xD8, 0x18])
        self._send_command(EL133UF1_BUCK_BOOST_VDDN, CS0_SEL, [0x01])
        self._send_command(EL133UF1_TFT_VCOM_POWER, CS0_SEL, [0x02])

    def _busy_wait(self, timeout=40.0):
        """Wait for busy/wait pin."""
        # If the busy_pin is *high* (pulled up by host)
        # then assume we're not getting a signal from inky
        # and wait the timeout period to be safe.
        if self._gpio.get_value(self.busy_pin) == Value.ACTIVE:
            time.sleep(timeout)
            return

        t_start = time.time()
        while self._gpio.get_value(self.busy_pin) == Value.ACTIVE:
            time.sleep(0.1)
            if time.time() - t_start > timeout:
                warnings.warn(f"Busy Wait: Timed out after {timeout:0.2f}s")
                return

    def _update(self, buf_a, buf_b):
        """Update display.
        Dispatches display update to correct driver.
        """
        self.setup()

        self._send_command(EL133UF1_DTM, CS0_SEL, buf_a)
        self._send_command(EL133UF1_DTM, CS1_SEL, buf_b)

        self._send_command(EL133UF1_PON, CS_BOTH_SEL)
        self._busy_wait(0.2)

        self._send_command(EL133UF1_DRF, CS_BOTH_SEL, [0x00])
        self._busy_wait(32.0)

        self._send_command(EL133UF1_POF, CS_BOTH_SEL, [0x00])
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

        region = numpy.rot90(region, -1)
        buf_a = region[:, :600].flatten()
        buf_b = region[:, 600:].flatten()

        buf_a = (((buf_a[::2] << 4) & 0xF0) | (buf_a[1::2] & 0x0F)).astype("uint8").tolist()
        buf_b = (((buf_b[::2] << 4) & 0xF0) | (buf_b[1::2] & 0x0F)).astype("uint8").tolist()

        self._update(buf_a, buf_b)

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

    def _spi_write_bytes(self, data):
        for x in range(((len(data) - 1) // 4096) + 1):
            offset = x * 4096
            self._spi_bus.writebytes(data[offset:offset + 4096])

    def _send_command(self, command, cs_sel=None, data=None):
        """Send command over SPI.
        :param command: command byte
        :param data: optional list of values
        """
        if cs_sel is not None:
            if cs_sel & CS0_SEL:
                self._gpio.set_value(self.cs0_pin, Value.INACTIVE)
            if cs_sel & CS1_SEL:
                self._gpio.set_value(self.cs1_pin, Value.INACTIVE)

            self._gpio.set_value(self.dc_pin, Value.INACTIVE)
            time.sleep(0.3)
            self._spi_bus.xfer3([command])

            if data is not None:
                self._gpio.set_value(self.dc_pin, Value.ACTIVE)
                self._spi_bus.xfer3(data)

            self._gpio.set_value(self.cs0_pin, Value.ACTIVE)
            self._gpio.set_value(self.cs1_pin, Value.ACTIVE)
            self._gpio.set_value(self.dc_pin, Value.INACTIVE)
