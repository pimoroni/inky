"""Inky e-Ink Display Driver."""
import time
import struct

from PIL import Image
from . import eeprom, ssd1608

try:
    import numpy
except ImportError:
    raise ImportError('This library requires the numpy module\nInstall with: sudo apt install python-numpy')

WHITE = 0
BLACK = 1
RED = YELLOW = 2

RESET_PIN = 27
BUSY_PIN = 17
DC_PIN = 22

MOSI_PIN = 10
SCLK_PIN = 11
CS0_PIN = 0

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

_RESOLUTION = {
    (600, 448): (600, 448, 0, 0, 0)
}


class Inky:
    """Inky e-Ink Display Driver."""

    WHITE = 0
    BLACK = 1
    RED = 2
    YELLOW = 2

    def __init__(self, resolution=(600, 448), colour='multi', cs_pin=CS0_PIN, dc_pin=DC_PIN, reset_pin=RESET_PIN, busy_pin=BUSY_PIN, h_flip=False, v_flip=False, spi_bus=None, i2c_bus=None, gpio=None):  # noqa: E501
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

        if resolution not in _RESOLUTION.keys():
            raise ValueError('Resolution {}x{} not supported!'.format(*resolution))

        self.resolution = resolution
        self.width, self.height = resolution
        self.cols, self.rows, self.rotation, self.offset_x, self.offset_y = _RESOLUTION[resolution]

        if colour not in ('multi'):
            raise ValueError('Colour {} is not supported!'.format(colour))

        self.colour = colour
        self.eeprom = eeprom.read_eeprom(i2c_bus=i2c_bus)
        self.lut = colour

        # The EEPROM is used to disambiguate the variants of wHAT and pHAT
        # 1   Red pHAT (High-Temp)
        # 2   Yellow wHAT (1_E)
        # 3   Black wHAT (1_E)
        # 4   Black pHAT (Normal)
        # 5   Yellow pHAT (DEP0213YNS75AFICP)
        # 6   Red wHAT (Regular)
        # 7   Red wHAT (High-Temp)
        # 8   Red wHAT (DEPG0420RWS19AF0HP)
        # 10  BW pHAT (ssd1608) (DEPG0213BNS800F13CP)
        # 11  Red pHAT (ssd1608)
        # 12  Yellow pHAT (ssd1608)
        # if self.eeprom is not None:
        #    # Only support new-style variants
        #    if self.eeprom.display_variant not in (10, 11, 12):
        #        raise RuntimeError('This driver is not compatible with your board.')
        #    if self.eeprom.width != self.width or self.eeprom.height != self.height:
        #        pass
        #        # TODO flash correct heights to new EEPROMs
        #        # raise ValueError('Supplied width/height do not match Inky: {}x{}'.format(self.eeprom.width, self.eeprom.height))

        self.buf = numpy.zeros((self.cols, self.rows), dtype=numpy.uint8)

        self.border_colour = 0

        self.dc_pin = dc_pin
        self.reset_pin = reset_pin
        self.busy_pin = busy_pin
        self.cs_pin = cs_pin
        self.h_flip = h_flip
        self.v_flip = v_flip

        self._gpio = gpio
        self._gpio_setup = False

        self._luts = None

    def setup(self):
        """Set up Inky GPIO and reset display."""
        if not self._gpio_setup:
            if self._gpio is None:
                try:
                    import RPi.GPIO as GPIO
                    self._gpio = GPIO
                except ImportError:
                    raise ImportError('This library requires the RPi.GPIO module\nInstall with: sudo apt install python-rpi.gpio')
            self._gpio.setmode(self._gpio.BCM)
            self._gpio.setwarnings(False)
            self._gpio.setup(self.dc_pin, self._gpio.OUT, initial=self._gpio.LOW, pull_up_down=self._gpio.PUD_OFF)
            self._gpio.setup(self.reset_pin, self._gpio.OUT, initial=self._gpio.HIGH, pull_up_down=self._gpio.PUD_OFF)
            self._gpio.setup(self.busy_pin, self._gpio.IN, pull_up_down=self._gpio.PUD_OFF)

            if self._spi_bus is None:
                import spidev
                self._spi_bus = spidev.SpiDev()

            self._spi_bus.open(0, self.cs_pin)
            self._spi_bus.max_speed_hz = 488000

            self._gpio_setup = True

        self._gpio.output(self.reset_pin, self._gpio.LOW)
        time.sleep(0.1)
        self._gpio.output(self.reset_pin, self._gpio.HIGH)
        time.sleep(0.1)

        self._busy_wait()

        self._send_command(
            UC8159_TRES,
            struct.pack(">HH", self.width, self.height))

        """
        eink_data[0] |= 1<<5;
	    eink_data[0] |= 0b11<<2; # ROTATE_0
	    eink_data[0] |= 0x01<<1 # BOOSTER_ON
	    eink_data[0] |= 0x01; # /* Add the soft reset bit */
	    eink_data[1] = 0x08; # display_colours == UC8159_7C
        """

        self._send_command(
            UC8159_PSR,
            [
                0b11101111,  # See above for more magic numbers
                0x08         # display_colours == UC8159_7C
            ]
        )

        self._send_command(
            UC8159_PWR,
            [
                (0x06 << 3) |  # ???
                (0x01 << 2) |  # SOURCE_INTERNAL_DC_DC
                (0x01 << 1) |  # GATE_INTERNAL_DC_DC
                (0x01),        # LV_SOURCE_INTERNAL_DC_DC
                0x00,          # VGx_20V
                0x23,          # UC8159_7C
                0x23           # UC8159_7C
            ]
        )

        # Set the PLL clock frequency to 50Hz
        self._send_command(UC8159_PLL, [0x3C])  # ref code writes 3 bytes here??

        # Send the TSE register to the display
        self._send_command(UC8159_TSE, [0x00])  # Colour

        self._send_command(UC8159_CDI, [0x37])  # ???

        self._send_command(UC8159_TCON, [0x22])

        # Disable external flash
        self._send_command(UC8159_DAM, [0x00])

        # UC8159_7C
        self._send_command(UC8159_PWS, [0xAA])

        self._send_command(
            UC8159_PFS, [0x00]  # PFS_1_FRAME
        )


    def _busy_wait(self, timeout=15.0):
        """Wait for busy/wait pin."""
        t_start = time.time()
        while not self._gpio.input(self.busy_pin):
            time.sleep(0.01)
            if time.time() - t_start >= timeout:
                raise RuntimeError("Timeout waiting for busy signal to clear.")

    def _update(self, buf, busy_wait=True):
        """Update display.

        Dispatches display update to correct driver.

        :param buf_a: Black/White pixels
        :param buf_b: Yellow/Red pixels

        """
        self.setup()

        self._send_command(UC8159_DTM1, buf)
        self._busy_wait()

        self._send_command(UC8159_PON)
        self._busy_wait()

        self._send_command(UC8159_DRF)
        self._busy_wait()

        self._send_command(UC8159_POF)
        self._busy_wait()

    def set_pixel(self, x, y, v):
        """Set a single pixel.

        :param x: x position on display
        :param y: y position on display
        :param v: colour to set

        """
        self.buf[y][x] = v & 0x0F

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

        #buf = numpy.packbits()

        #buf = []
        #for i in range(self.width * self.height // 2):
        #    buf.append(
        #        region[i * 2] << 4) + (region[index * 2 + 1] & 0x0F)
        #    )

        buf = region.flatten()

        buf = ((buf[::2] << 4) & 0xF0) | (buf[1::2] & 0x0F)

        self._update(buf.astype('uint8').tolist(), busy_wait=busy_wait)

    def set_border(self, colour):
        """Set the border colour."""
        raise NotImplemented
        #if colour in (WHITE, BLACK, RED):
        #    self.border_colour = colour

    def set_image(self, image):
        """Copy an image to the display."""
        palette = Image.new("P", (16, 16))
        palette.putpalette([
            0, 0, 0,
            255, 255, 255,
            0, 255, 0,
            0, 0, 255,
            255, 0, 0,
            255,255,0,
            255,140,0,
            255, 255, 255
        ] * 32)
        image.load()
        palette.load()
        #canvas = Image.new("P", (self.rows, self.cols))
        result = image.im.convert("P", True, palette.im)
        #canvas.paste(result, (self.offset_x, self.offset_y))
        self.buf = numpy.array(result, dtype=numpy.uint8).reshape((self.cols, self.rows))

    def _spi_write(self, dc, values):
        """Write values over SPI.

        :param dc: whether to write as data or command
        :param values: list of values to write

        """
        self._gpio.output(self.dc_pin, dc)
        try:
            self._spi_bus.xfer3(values)
        except AttributeError:
            for x in range(((len(values) - 1) // _SPI_CHUNK_SIZE) + 1):
                offset = x * _SPI_CHUNK_SIZE
                self._spi_bus.xfer(values[offset:offset + _SPI_CHUNK_SIZE])

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
