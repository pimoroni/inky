"""Set image tests for Inky."""
import pytest


@pytest.mark.parametrize('resolution', [(800, 480), (600, 448), (400, 300), (212, 104), (250, 122)])
def test_inky_set_image(GPIO, spidev, smbus2, resolution):
    from PIL import Image

    from inky.inky import Inky

    phat = Inky(resolution)

    width, height = phat.resolution

    image = Image.new("P", (width, height))

    for x in range(width):
        image.putpixel((x, 0), x % 3)

    assert image.size == (width, height)

    phat.set_image(image)
    phat.set_pixel(0, 0, 2)

    data = [x % 3 for x in range(width)]
    data[0] = 2

    assert phat.buf.flatten().tolist()[0:width] == data
