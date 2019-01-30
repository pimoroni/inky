"""Inky e-Ink Display Driver."""
import sys
import time
import struct

import spidev

from . import eeprom

try:
    import RPi.GPIO as GPIO
except ImportError:
    sys.exit('This library requires the RPi.GPIO module\nInstall with: sudo apt install python-rpi.gpio')

try:
    import smbus
except ImportError:
    sys.exit('This library requires the SMBus module\nInstall with: sudo apt install python-smbus')

try:
    import numpy
except ImportError:
    sys.exit('This library requires the numpy module\nInstall with: sudo apt install python-numpy')

WHITE = 0
BLACK = 1
RED = YELLOW = 2

RESET_PIN = 27
BUSY_PIN = 17
DC_PIN = 22

MOSI_PIN = 10
SCLK_PIN = 11
CS0_PIN = 0

_SPI_CHUNK_SIZE = 4096
_SPI_COMMAND = GPIO.LOW
_SPI_DATA = GPIO.HIGH

_RESOLUTION = {
    (400, 300): (400, 300, 0),
    (212, 104): (104, 212, -90),
}


class Inky:
    """Inky e-Ink Display Driver."""

    WHITE = 0
    BLACK = 1
    RED = 2
    YELLOW = 2

    def __init__(self, resolution=(400, 300), colour='black', cs_pin=CS0_PIN, dc_pin=DC_PIN, reset_pin=RESET_PIN, busy_pin=BUSY_PIN, h_flip=False, v_flip=False):
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
        if resolution not in _RESOLUTION.keys():
            raise ValueError('Resolution {}x{} not supported!'.format(*resolution))

        self.resolution = resolution
        self.width, self.height = resolution
        self.cols, self.rows, self.rotation = _RESOLUTION[resolution]

        if colour not in ('red', 'black', 'yellow'):
            raise ValueError('Colour {} is not supported!'.format(colour))

        self.colour = colour
        self.eeprom = eeprom.read_eeprom()
        self.lut = colour

        if self.eeprom is not None:
            if self.eeprom.width != self.width or self.eeprom.height != self.height:
                raise ValueError('Supplied width/height do not match Inky: {}x{}'.format(self.eeprom.width, self.eeprom.height))
            if self.eeprom.display_variant == 1 and self.eeprom.get_color() == 'red':
                self.lut = 'red_ht'

        self.buf = numpy.zeros((self.height, self.width), dtype=numpy.uint8)
        self.border_colour = 0

        self.dc_pin = dc_pin
        self.reset_pin = reset_pin
        self.busy_pin = busy_pin
        self.cs_pin = cs_pin
        self.h_flip = h_flip
        self.v_flip = v_flip

        self._gpio_setup = False

        self._luts = {
            'black': [
            # Phase 0     Phase 1     Phase 2     Phase 3     Phase 4     Phase 5     Phase 6
            # A B C D     A B C D     A B C D     A B C D     A B C D     A B C D     A B C D
            0b01001000, 0b10100000, 0b00010000, 0b00010000, 0b00010011, 0b00000000, 0b00000000,  # LUT0 - Black
            0b01001000, 0b10100000, 0b10000000, 0b00000000, 0b00000011, 0b00000000, 0b00000000,  # LUTT1 - White
            0b00000000, 0b00000000, 0b00000000, 0b00000000, 0b00000000, 0b00000000, 0b00000000,  # IGNORE
            0b01001000, 0b10100101, 0b00000000, 0b10111011, 0b00000000, 0b00000000, 0b00000000,  # LUT3 - Red
            0b00000000, 0b00000000, 0b00000000, 0b00000000, 0b00000000, 0b00000000, 0b00000000,  # LUT4 - VCOM

            # Duration            |  Repeat
            # A   B     C     D   |
            16,   4,    4,    4,     4,   # 0 Flash
            16,   4,    4,    4,     4,   # 1 clear
            4,    8,    8,    16,    16,  # 2 bring in the black
            0,    0,    0,    0,     0,   # 3 time for red
            0,    0,    0,    0,     0,   # 4 final black sharpen phase
            0,    0,    0,    0,     0,   # 5
            0,    0,    0,    0,     0,   # 6
            ],
            'red': [
            # Phase 0     Phase 1     Phase 2     Phase 3     Phase 4     Phase 5     Phase 6
            # A B C D     A B C D     A B C D     A B C D     A B C D     A B C D     A B C D
            0b01001000, 0b10100000, 0b00010000, 0b00010000, 0b00010011, 0b00000000, 0b00000000,  # LUT0 - Black
            0b01001000, 0b10100000, 0b10000000, 0b00000000, 0b00000011, 0b00000000, 0b00000000,  # LUTT1 - White
            0b00000000, 0b00000000, 0b00000000, 0b00000000, 0b00000000, 0b00000000, 0b00000000,  # IGNORE
            0b01001000, 0b10100101, 0b00000000, 0b10111011, 0b00000000, 0b00000000, 0b00000000,  # LUT3 - Red
            0b00000000, 0b00000000, 0b00000000, 0b00000000, 0b00000000, 0b00000000, 0b00000000,  # LUT4 - VCOM

            # Duration            |  Repeat
            # A   B     C     D   |
            67,   10,   31,   10,    4,   # 0 Flash
            16,   8,    4,    4,     6,   # 1 clear
            4,    8,    8,    16,    16,  # 2 bring in the black
            2,    4,    4,    64,    32,  # 3 time for red
            6,    6,    6,    2,     2,   # 4 final black sharpen phase
            0,    0,    0,    0,     0,   # 5
            0,    0,    0,    0,     0    # 6
            ],
            'red_ht': [
            # Phase 0     Phase 1     Phase 2     Phase 3     Phase 4     Phase 5     Phase 6
            # A B C D     A B C D     A B C D     A B C D     A B C D     A B C D     A B C D
            0b01001000, 0b10100000, 0b00010000, 0b00010000, 0b00010011, 0b00000000, 0b00000000,  # LUT0 - Black
            0b01001000, 0b10100000, 0b10000000, 0b00000000, 0b00000011, 0b00000000, 0b00000000,  # LUTT1 - White
            0b00000000, 0b00000000, 0b00000000, 0b00000000, 0b00000000, 0b00000000, 0b00000000,  # IGNORE
            0b01001000, 0b10100101, 0b00000000, 0b10111011, 0b00000000, 0b00000000, 0b00000000,  # LUT3 - Red
            0b00000000, 0b00000000, 0b00000000, 0b00000000, 0b00000000, 0b00000000, 0b00000000,  # LUT4 - VCOM

            # Duration            |  Repeat
            # A   B     C     D   |
            67,   10,   31,   10,    4,   # 0 Flash
            16,   8,    4,    4,     6,   # 1 clear
            4,    8,    8,    16,    16,  # 2 bring in the black
            2,    4,    4,    64,    32,  # 3 time for red
            6,    6,    6,    2,     2,   # 4 final black sharpen phase
            0,    0,    0,    0,     0,   # 5
            0,    0,    0,    0,     0    # 6
            ],
            'yellow': [
            # Phase 0     Phase 1     Phase 2     Phase 3     Phase 4     Phase 5     Phase 6
            # A B C D     A B C D     A B C D     A B C D     A B C D     A B C D     A B C D
            0b11111010, 0b10010100, 0b10001100, 0b11000000, 0b11010000,  0b00000000, 0b00000000,  # LUT0 - Black
            0b11111010, 0b10010100, 0b00101100, 0b10000000, 0b11100000,  0b00000000, 0b00000000,  # LUTT1 - White
            0b11111010, 0b00000000, 0b00000000, 0b00000000, 0b00000000,  0b00000000, 0b00000000,  # IGNORE
            0b11111010, 0b10010100, 0b11111000, 0b10000000, 0b01010000,  0b00000000, 0b11001100,  # LUT3 - Yellow (or Red)
            0b10111111, 0b01011000, 0b11111100, 0b10000000, 0b11010000,  0b00000000, 0b00010001,  # LUT4 - VCOM

            # Duration            | Repeat
            # A   B     C     D   |
            64,   16,   64,   16,   8,
            8,    16,   4,    4,    16,
            8,    8,    3,    8,    32,
            8,    4,    0,    0,    16,
            16,   8,    8,    0,    32,
            0,    0,    0,    0,    0,
            0,    0,    0,    0,    0,
            ]
        }

    def setup(self):
        """Set up Inky GPIO and reset display."""
        if not self._gpio_setup:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            GPIO.setup(self.dc_pin, GPIO.OUT, initial=GPIO.LOW, pull_up_down=GPIO.PUD_OFF)
            GPIO.setup(self.reset_pin, GPIO.OUT, initial=GPIO.HIGH, pull_up_down=GPIO.PUD_OFF)
            GPIO.setup(self.busy_pin, GPIO.IN, pull_up_down=GPIO.PUD_OFF)

            self._spi = spidev.SpiDev()
            self._spi.open(0, self.cs_pin)
            self._spi.max_speed_hz = 488000

            self._gpio_setup = True

        GPIO.output(self.reset_pin, GPIO.LOW)
        time.sleep(0.1)
        GPIO.output(self.reset_pin, GPIO.HIGH)
        time.sleep(0.1)

        self._send_command(0x12)  # Soft Reset
        self._busy_wait()

    def _busy_wait(self):
        """Wait for busy/wait pin."""
        while(GPIO.input(self.busy_pin) != GPIO.LOW):
            time.sleep(0.01)

    def _update(self, buf_a, buf_b):
        """Update display.

        :param buf_a: Black/White pixels
        :param buf_b: Yellow/Red pixels

        """
        self.setup()

        packed_height = list(struct.pack('<H', self.rows))

        if isinstance(packed_height[0], str):
            packed_height = map(ord, packed_height)

        self._send_command(0x74, 0x54)  # Set Analog Block Control
        self._send_command(0x7e, 0x3b)  # Set Digital Block Control

        self._send_command(0x01, packed_height + [0x00])  # Gate setting

        self._send_command(0x03, [0b10000, 0b0001])  # Gate Driving Voltage

        self._send_command(0x3a, 0x07)  # Dummy line period
        self._send_command(0x3b, 0x04)  # Gate line width
        self._send_command(0x11, 0x03)  # Data entry mode setting 0x03 = X/Y increment

        self._send_command(0x04)  # Power On
        self._send_command(0x2c, 0x3c)  # VCOM Register, 0x3c = -1.5v?

        self._send_command(0x3c, 0b00000000)
        if self.border_colour == self.BLACK:
            self._send_command(0x3c, 0b00000000)  # GS Transition Define A + VSS + LUT0
        elif self.border_colour == self.RED and self.colour == 'red':
            self._send_command(0x3c, 0b01110011)  # Fix Level Define A + VSH2 + LUT3
        elif self.border_colour == self.YELLOW and self.colour == 'yellow':
            self._send_command(0x3c, 0b00110011)  # GS Transition Define A + VSH2 + LUT3
        elif self.border_colour == self.WHITE:
            self._send_command(0x3c, 0b00110001)  # GS Transition Define A + VSH2 + LUT1

        if self.colour == 'yellow':
            self._send_command(0x04, 0x07)  # Set voltage of VSH and VSL

        self._send_command(0x32, self._luts[self.lut])  # Set LUTs

        self._send_command(0x44, [0x00, (self.cols // 8) - 1])  # Set RAM X Start/End
        self._send_command(0x45, [0x00, 0x00] + packed_height)  # Set RAM Y Start/End

        # 0x24 == RAM B/W, 0x26 == RAM Red/Yellow/etc
        for data in ((0x24, buf_a), (0x26, buf_b)):
            cmd, buf = data
            self._send_command(0x4e, 0x00)  # Set RAM X Pointer Start
            self._send_command(0x4f, [0x00, 0x00])  # Set RAM Y Pointer Start
            self._send_command(cmd, buf)

        self._send_command(0x22, 0xc7)  # Display Update Sequence
        self._send_command(0x20)  # Trigger Display Update
        time.sleep(0.05)
        self._busy_wait()
        self._send_command(0x10, 0x01)  # Enter Deep Sleep

    def set_pixel(self, x, y, v):
        """Set a single pixel.

        :param x: x position on display
        :param y: y position on display
        :param v: colour to set

        """
        if v in (WHITE, BLACK, RED):
            self.buf[y][x] = v

    def show(self):
        """Show buffer on display."""
        region = self.buf

        if self.v_flip:
            region = numpy.fliplr(region)

        if self.h_flip:
            region = numpy.flipud(region)

        if self.rotation:
            region = numpy.rot90(region, self.rotation // 90)

        buf_a = numpy.packbits(numpy.where(region == BLACK, 0, 1)).tolist()
        buf_b = numpy.packbits(numpy.where(region == RED, 1, 0)).tolist()

        self._update(buf_a, buf_b)

    def set_border(self, colour):
        """Set the border colour."""
        if colour in (WHITE, BLACK, RED):
            self.border_colour = colour

    def set_image(self, image):
        """Copy an image to the display."""
        if self.rotation % 180 == 0:
            self.buf = numpy.array(image, dtype=numpy.uint8).reshape((self.width, self.height))
        else:
            self.buf = numpy.array(image, dtype=numpy.uint8).reshape((self.height, self.width))

    def _spi_write(self, dc, values):
        """Write values over SPI.

        :param dc: whether to write as data or command
        :param values: list of values to write

        """
        GPIO.output(self.dc_pin, dc)
        try:
            self._spi.xfer3(values)
        except AttributeError:
            for x in range(((len(values) - 1) // _SPI_CHUNK_SIZE) + 1):
                offset = x * _SPI_CHUNK_SIZE
                self._spi.xfer(values[offset:offset + _SPI_CHUNK_SIZE])

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
