import sys
import numpy


from . import inky


class InkyMock(inky.Inky):

    def __init__(self, colour, h_flip=False, v_flip=False):
        """Initialise an Inky pHAT Display.

        :param colour: one of red, black or yellow, default: black

        """
        global tkinter, ttk, ImageTk, Image

        try:
            import tkinter
            from tkinter import ttk
            from PIL import ImageTk, Image
        except ImportError:
            sys.exit('Simulation requires tkinter')

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

        bw_inky_palette = [255, 255, 255,  # 0 = white
                           0, 0, 0]  # 1 = black

        red_inky_palette = [255, 255, 255,  # 0 = white
                            0, 0, 0,  # 1 = black
                            255, 0, 0]  # index 2 is red

        ylw_inky_palette = [255, 255, 255,  # 0 = white
                            0, 0, 0,  # 1 = black
                            223, 204, 16]  # index 2 is yellow
        # yellow color value: screen capture from
        # https://www.thoughtsmakethings.com/Pimoroni-Inky-pHAT

        self.c_palette = {"black": bw_inky_palette,
                          "red": red_inky_palette,
                          "yellow": ylw_inky_palette}

        self.tk_root = tkinter.Tk()
        self.tk_root.title("Inky Preview")
        self.tk_root.geometry('{}x{}'.format(self.WIDTH, self.HEIGHT))
        self.tk_root.aspect(self.WIDTH, self.HEIGHT, self.WIDTH, self.HEIGHT)

    def resize_image(self, event):
        # https://stackoverflow.com/questions/24061099/tkinter-resize-background-image-to-window-size
        new_width = event.width
        new_height = event.height
        image = self.disp_img_copy.resize((new_width, new_height))
        photo = ImageTk.PhotoImage(image)
        self.tk_label.config(image=photo)
        self.tk_label.image = photo  # avoid garbage collection

    def _send_command(self, command, data=None):
        pass

    def _simulate(self, region):
        pass

    def _display(self, region):
        im = Image.fromarray(region, "P")
        im.putpalette(self.c_palette[self.colour])

        self.disp_img_copy = im.copy()  # can be changed due to window resizing, so copy
        photo = ImageTk.PhotoImage(im)
        self.tk_label = ttk.Label(self.tk_root, image=photo)
        self.tk_label.bind('<Configure>', self.resize_image)
        self.tk_label.pack(fill=tkinter.BOTH, expand=tkinter.YES)

        self.tk_root.mainloop()

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
        region = numpy.flipud(region)  # spec: phat rotated -90
        region = numpy.fliplr(region)  # spec: phat rotated -90
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
        region = region.reshape(300, 400)  # for display
        self._display(region)
