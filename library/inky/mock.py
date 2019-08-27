import sys
import numpy


from . import inky


class InkyMock(inky.Inky):

    def __init__(self, colour, h_flip=False, v_flip=False):
        """Initialise an Inky pHAT Display.

        :param colour: one of red, black or yellow, default: black

        """
        global Mock, matplotlib, pyplot

        from unittest.mock import Mock

        try:
            import matplotlib
            from matplotlib import pyplot
        except ImportError:
            sys.exit('Simulation requires the matplotlib package\nInstall with: pip install matplotlib')

        resolution = (self.WIDTH, self.HEIGHT)

        if resolution not in inky._RESOLUTION.keys():
            raise ValueError('Resolution {}x{} not supported!'.format(*resolution))

        self.resolution = resolution
        self.width, self.height = resolution
        self.cols, self.rows, self.rotation = inky._RESOLUTION[resolution]

        if colour not in ('red', 'black', 'yellow'):
            raise ValueError('Colour {} is not supported!'.format(colour))

        self.colour = colour

        self.h_flip = h_flip
        self.v_flip = v_flip

        self._colordicts = {
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

    def _send_command(self, command, data=None):
        pass

    def _simulate(self, region):
        pass

    def _display(self, region):
        colormap = matplotlib.colors.LinearSegmentedColormap('einky_colormap', self._colordicts[self.colour], 3)

        pyplot.figure(figsize=(self.WIDTH / 100.0, self.HEIGHT / 100.0))
        pyplot.axis('off')
        pyplot.pcolor(region, cmap=colormap)
        pyplot.show()

    def show(self, busy_wait=True):
        """Show buffer on display.

        :param busy_wait: Ignored. Updates are simulated and instant.

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


class InkyMockPHAT(InkyMock):

    """Inky wHAT e-Ink Display Driver."""

    WIDTH = 212
    HEIGHT = 104

    WHITE = 0
    BLACK = 1
    RED = 2
    YELLOW = 2

    def _simulate(self, region):
        region = numpy.rot90(region, self.rotation // 90)
        region = numpy.fliplr(region)

        self._display(region)


class InkyMockWHAT(InkyMock):

    """Inky wHAT e-Ink Display Driver."""

    WIDTH = 400
    HEIGHT = 300

    WHITE = 0
    BLACK = 1
    RED = 2
    YELLOW = 2

    def _simulate(self, region):
        region = numpy.rot90(region, self.rotation // 90)
        region = region.reshape(300, 400)  # bug? hack?
        region = numpy.flipud(region)  # bug? hack?

        self._display(region)
