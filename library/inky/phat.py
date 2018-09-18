import inky

__version__ = '0.0.1'

_colour = None
_flip_h = False
_flip_v = True

WIDTH = 212
HEIGHT = 104

WHITE = 0
BLACK = 1
RED = YELLOW = 2

phat = None


def setup():
    global phat
    if phat is not None:
        return
    phat = inky.Inky(
        resolution=(HEIGHT, WIDTH),
        colour=_colour,
        h_flip=_flip_h,
        v_flip=_flip_v)


def set_colour(colour):
    global _colour
    _colour = colour


def set_border(color):
    pass


def set_image(image):
    """Copy an image to the Inky pHAT."""
    setup()
    # Two dimensional list
    if isinstance(image, list):
        w, h = len(image), len(image[0])
        w = min(w, WIDTH)
        h = min(h, HEIGHT)
        for x in range(w):
            for y in range(h):
                pixel = image[x][y]
                phat.set_pixel(y, x, pixel)
        return

    # PIL image
    if getattr(image, 'size') and getattr(image, 'getpixel'):
        w, h = image.size
        w = min(w, WIDTH)
        h = min(h, HEIGHT)
        for x in range(w):
            for y in range(h):
                pixel = image.getpixel((x, y))
                phat.set_pixel(y, x, pixel)
        return


def show():
    """Show the image on the Inky pHAT."""
    setup()
    phat.setup()
    phat.update()
    
