import sys
import numpy

from unittest.mock import Mock

mock_mod_list = ['spidev', 'RPi', 'RPi.GPIO', 'smbus2']
for m in mock_mod_list:
    sys.modules[m] = Mock()


class MockSMBus:
    """Mock a Python SMBus instance.
    Redirects read/write operations to self.regs.
    """

    def __init__(self, i2c_bus):
        """Initialize mock SMBus class.
        :param i2c_bus: unused, maintains compatibility with smbus.SMBus(n)
        """
        self.regs = [0 for _ in range(255)]

    def write_i2c_block_data(self, i2c_address, register, values):
        """Write a block of i2c data bytes."""
        raise IOError("Pretending there's no EEPROM to talk to.")
        # self.regs[register:register + len(values)] = values

    def read_i2c_block_data(self, i2c_address, register, length):
        """Read a block of i2c data bytes."""
        return self.regs[register:register + length]


sys.modules['smbus2'].SMBus = MockSMBus


from . import inky

try:
    import matplotlib
    from matplotlib import pyplot
except ImportError:
    sys.exit('Simulation requires the matplotlib package\nInstall with: pip install matplotlib')

# try:
#     from PIL import Image
# except ImportError:
#     sys.exit('Simulation requires the pillow package\nInstall with: pip install pillow')


class InkyMockW(inky.Inky):

    """Inky wHAT e-Ink Display Driver."""

    WIDTH = 400
    HEIGHT = 300

    WHITE = 0
    BLACK = 1
    RED = 2
    YELLOW = 2

    def __init__(self, colour, h_flip=False, v_flip=False):
        """Initialise an Inky pHAT Display.

        :param colour: one of red, black or yellow, default: black

        """
        inky.Inky.__init__(
            self,
            resolution=(self.WIDTH, self.HEIGHT),
            colour=colour,
            h_flip=h_flip,
            v_flip=v_flip)

    def _send_command(self, command, data=None):
        pass

    def _simulate(self, region):
        region = numpy.rot90(region, self.rotation // 90)
        # region = numpy.fliplr(region) # bug? hack?
        region = region.reshape(300,400) # bug? hack?
        region = numpy.flipud(region) # bug? hack? 

        colordicts = {
            'red': {'red': ((0.0, 1, 1), (0.5, 0, 0), (1.0, 1, 1)),
                    'green': ((0.0, 1, 1), (0.5, 0, 0), (1.0, 0, 0)),
                    'blue': ((0.0, 1, 1), (0.5, 0, 0), (1.0, 0, 0))},
            'yellow': {'red': ((0.0, 1, 1), (0.5, 0.35, 0), (1.0, 0.7, 0.7)),
                       'green': ((0.0, 1, 1), (0.5, 0.27, 0), (1.0, 0.54, 0.54)),
                       'blue': ((0.0, 1, 1), (0.5, 0, 0), (1.0, 0, 0))},
            'black': {'red': ((0.0, 1, 1), (0.5, 0, 0), (1.0, 0, 0)),
                      'green': ((0.0, 1, 1), (0.5, 0, 0), (1.0, 0, 0)),
                      'blue': ((0.0, 1, 1), (0.5, 0, 0), (1.0, 0, 0))}
        }

        colormap = matplotlib.colors.LinearSegmentedColormap('einky_colormap', colordicts[self.colour], 3)

        pyplot.figure(figsize=(self.WIDTH/100.0, self.HEIGHT/100.0))
        pyplot.axis('off')
        pyplot.pcolor(region, cmap=colormap)
        pyplot.show()

    def show(self, busy_wait=True):
        """Show buffer on display.

        :param busy_wait: If True, wait for display update to finish before returning.

        """
        print(">>simulating...")

        region = self.buf

        if self.v_flip:
            region = numpy.fliplr(region)

        if self.h_flip:
            region = numpy.flipud(region)

        if self.rotation:
            region = numpy.rot90(region, self.rotation // 90)

        self._simulate(region)
