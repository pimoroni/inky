"""Inky e-Ink Display Driver."""
import time
import struct

try:
    from PIL import Image
except ImportError:
    Image = None

from . import eeprom

try:
    import numpy
except ImportError:
    raise ImportError('This library requires the numpy module\nInstall with: sudo apt install python-numpy')

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

RESET_PIN = 27
BUSY_PIN = 17
DC_PIN = 22

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

_RESOLUTION = {
    (600, 448): (600, 448, 0, 0, 0, 0b11),
    (640, 400): (640, 400, 0, 0, 0, 0b10)
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
        self.border_colour = WHITE
        self.cols, self.rows, self.rotation, self.offset_x, self.offset_y, self.resolution_setting = _RESOLUTION[resolution]

        if colour not in ('multi'):
            raise ValueError('Colour {} is not supported!'.format(colour))

        self.colour = colour
        self.eeprom = eeprom.read_eeprom(i2c_bus=i2c_bus)
        self.lut = colour

        # Check for supported display variant and select the correct resolution
        # Eg: 600x480 and 640x400
        if self.eeprom is not None and self.eeprom.display_variant in (14, 15):
            eeprom_resolution = _RESOLUTION.keys[self.eeprom.display_variant - 14]
            self.resolution = eeprom_resolution
            self.width, self.height = eeprom_resolution
            self.cols, self.rows, self.rotation, self.offset_x, self.offset_y, self.resolution_setting = _RESOLUTION[eeprom_resolution]

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

    def _palette_blend(self, saturation, dtype='uint8'):
        saturation = float(saturation)
        palette = []
        for i in range(7):
            rs, gs, bs = [c * saturation for c in SATURATED_PALETTE[i]]
            rd, gd, bd = [c * (1.0 - saturation) for c in DESATURATED_PALETTE[i]]
            if dtype == 'uint8':
                palette += [int(rs + rd), int(gs + gd), int(bs + bd)]
            if dtype == 'uint24':
                palette += [(int(rs + rd) << 16) | (int(gs + gd) << 8) | int(bs + bd)]
        if dtype == 'uint8':
            palette += [255, 255, 255]
        if dtype == 'uint24':
            palette += [0xffffff]
        return palette

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
            self._gpio.setup(self.cs_pin, self._gpio.OUT, initial=self._gpio.HIGH)
            self._gpio.setup(self.dc_pin, self._gpio.OUT, initial=self._gpio.LOW, pull_up_down=self._gpio.PUD_OFF)
            self._gpio.setup(self.reset_pin, self._gpio.OUT, initial=self._gpio.HIGH, pull_up_down=self._gpio.PUD_OFF)
            self._gpio.setup(self.busy_pin, self._gpio.IN, pull_up_down=self._gpio.PUD_OFF)

            if self._spi_bus is None:
                import spidev
                self._spi_bus = spidev.SpiDev()

            self._spi_bus.open(0, self.cs_channel)
            self._spi_bus.no_cs = True
            self._spi_bus.max_speed_hz = 3000000

            self._gpio_setup = True

        self._gpio.output(self.reset_pin, self._gpio.LOW)
        time.sleep(0.1)
        self._gpio.output(self.reset_pin, self._gpio.HIGH)
        time.sleep(0.1)

        self._busy_wait()

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
                (0x06 << 3) |  # ??? - not documented in UC8159 datasheet
                (0x01 << 2) |  # SOURCE_INTERNAL_DC_DC
                (0x01 << 1) |  # GATE_INTERNAL_DC_DC
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

    def _busy_wait(self, timeout=30.0):
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

        self._update(buf.astype('uint8').tolist(), busy_wait=busy_wait)

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
            if Image is None:
                raise RuntimeError("PIL is required for converting images: sudo apt install python-pil python3-pil")
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
        self._gpio.output(self.cs_pin, 0)
        self._gpio.output(self.dc_pin, dc)

        if type(values) is str:
            values = [ord(c) for c in values]

        try:
            self._spi_bus.xfer3(values)
        except AttributeError:
            for x in range(((len(values) - 1) // _SPI_CHUNK_SIZE) + 1):
                offset = x * _SPI_CHUNK_SIZE
                self._spi_bus.xfer(values[offset:offset + _SPI_CHUNK_SIZE])
        self._gpio.output(self.cs_pin, 1)

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
