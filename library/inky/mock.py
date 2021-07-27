"""PIL/Tkinter based simulator for InkyWHAT and InkyWHAT."""
import numpy


from . import inky
from . import inky_uc8159


class InkyMock(inky.Inky):
    """Base simulator class for Inky."""

    def __init__(self, colour, h_flip=False, v_flip=False):
        """Initialise an Inky pHAT Display.

        :param colour: one of red, black or yellow, default: black

        """
        global tkinter, ImageTk, Image

        try:
            import tkinter
        except ImportError:
            raise ImportError('Simulation requires tkinter')

        try:
            from PIL import ImageTk, Image
        except ImportError:
            raise ImportError('Simulation requires PIL ImageTk and Image')

        resolution = (self.WIDTH, self.HEIGHT)

        if resolution not in inky._RESOLUTION.keys():
            raise ValueError('Resolution {}x{} not supported!'.format(*resolution))

        self.resolution = resolution
        self.width, self.height = resolution
        self.cols, self.rows, self.rotation = inky._RESOLUTION[resolution]

        self.buf = numpy.zeros((self.height, self.width), dtype=numpy.uint8)

        if colour not in ('red', 'black', 'yellow', 'multi'):
            raise ValueError('Colour {} is not supported!'.format(colour))

        self.colour = colour

        self.h_flip = h_flip
        self.v_flip = v_flip

        impression_palette = [57, 48, 57,     # black
                              255, 255, 255,  # white
                              58, 91, 70,     # green
                              61, 59, 94,     # blue
                              156, 72, 75,    # red
                              208, 190, 71,   # yellow
                              177, 106, 73,   # orange
                              255, 255, 255]  # clear

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

        self.c_palette = {'black': bw_inky_palette,
                          'red': red_inky_palette,
                          'yellow': ylw_inky_palette,
                          'multi': impression_palette}

        self._tk_done = False
        self.tk_root = tkinter.Tk()
        self.tk_root.title('Inky Preview')
        self.tk_root.geometry('{}x{}'.format(self.WIDTH, self.HEIGHT))
        self.tk_root.aspect(self.WIDTH, self.HEIGHT, self.WIDTH, self.HEIGHT)
        self.tk_root.protocol('WM_DELETE_WINDOW', self._close_window)
        self.cv = None
        self.cvh = self.HEIGHT
        self.cvw = self.WIDTH

    def wait_for_window_close(self):
        """Wait until the Tkinter window has closed."""
        while not self._tk_done:
            self.tk_root.update_idletasks()
            self.tk_root.update()

    def _close_window(self):
        self._tk_done = True
        self.tk_root.destroy()

    def resize(self, event):
        """Resize background image to window size."""
        # adapted from:
        # https://stackoverflow.com/questions/24061099/tkinter-resize-background-image-to-window-size
        # https://stackoverflow.com/questions/19838972/how-to-update-an-image-on-a-canvas
        self.cvw = event.width
        self.cvh = event.height
        self.cv.config(width=self.cvw, height=self.cvh)
        image = self.disp_img_copy.resize([self.cvw, self.cvh])
        self.photo = ImageTk.PhotoImage(image)
        self.cv.itemconfig(self.cvhandle, image=self.photo, anchor='nw')
        self.tk_root.update()

    def _send_command(self, command, data=None):
        pass

    def _simulate(self, region):
        pass

    def _display(self, region):
        im = Image.fromarray(region, 'P')
        im.putpalette(self.c_palette[self.colour])

        self.disp_img_copy = im.copy()  # can be changed due to window resizing, so copy
        image = self.disp_img_copy.resize([self.cvw, self.cvh])
        self.photo = ImageTk.PhotoImage(image)
        if self.cv is None:
            self.cv = tkinter.Canvas(self.tk_root, width=self.WIDTH, height=self.HEIGHT)
        self.cv.pack(side='top', fill='both', expand='yes')
        self.cvhandle = self.cv.create_image(0, 0, image=self.photo, anchor='nw')
        self.cv.bind('<Configure>', self.resize)
        self.tk_root.update()

    def show(self, busy_wait=True):
        """Show buffer on display.

        :param busy_wait: Ignored. Updates are simulated and instant.

        """
        print('>> Simulating {} {}x{}...'.format(self.colour, self.WIDTH, self.HEIGHT))

        region = self.buf

        if self.v_flip:
            region = numpy.fliplr(region)

        if self.h_flip:
            region = numpy.flipud(region)

        if self.rotation:
            region = numpy.rot90(region, self.rotation // 90)

        self._simulate(region)


class InkyMockPHAT(InkyMock):
    """Inky PHAT (212x104) e-Ink Display Simulator."""

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


class InkyMockPHATSSD1608(InkyMock):
    """Inky PHAT SSD1608 (250x122) e-Ink Display Simulator."""

    WIDTH = 250
    HEIGHT = 122

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
    """Inky wHAT e-Ink Display Simulator."""

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


class InkyMockImpression(InkyMock):
    """Inky Impression e-Ink Display Simulator."""

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

    def __init__(self):
        """Initialize a new mock Inky Impression."""
        InkyMock.__init__(self, 'multi')

    def _simulate(self, region):
        self._display(region)

    def set_pixel(self, x, y, v):
        """Set a single pixel on the display."""
        self.buf[y][x] = v & 0xf

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
            palette = inky_uc8159.Inky._palette_blend(self, saturation)
            # Image size doesn't matter since it's just the palette we're using
            palette_image = Image.new("P", (1, 1))
            # Set our 7 colour palette (+ clear) and zero out the other 247 colours
            palette_image.putpalette(palette + [0, 0, 0] * 248)
            # Force source image data to be loaded for `.im` to work
            image.load()
            image = image.im.convert("P", True, palette_image.im)
        self.buf = numpy.array(image, dtype=numpy.uint8).reshape((self.rows, self.cols))
