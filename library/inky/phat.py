"""
`Inky pHAT`_ class and methods.

A getting started `tutorial`_ for the Inky pHAT is available on the pimoroni website.

The `pinout`_ for the Inky pHAT is documented on pinout.xyz

.. _`Inky pHAT`: https://shop.pimoroni.com/products/inky-phat
.. _`tutorial`: https://learn.pimoroni.com/tutorial/sandyj/getting-started-with-inky-phat
.. _`pinout`: https://pinout.xyz/pinout/inky_phat

"""
from . import inky


class InkyPHAT(inky.Inky):
    """Inky pHAT e-Ink Display Driver."""

    WIDTH = 212
    HEIGHT = 104

    WHITE = 0
    BLACK = 1
    RED = 2
    YELLOW = 2

    def __init__(self, colour='black'):
        """Initialise an Inky pHAT Display.

        :param str colour: one of 'red', 'black' or 'yellow', default: 'black'.
        """
        inky.Inky.__init__(
            self,
            resolution=(self.WIDTH, self.HEIGHT),
            colour=colour,
            h_flip=False,
            v_flip=False)
