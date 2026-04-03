def test_set_image_p256(GPIO, spidev):
    from PIL import Image

    from inky import inky_e673

    img = Image.new("P", (800, 480))

    for x in range(256):
        img.putpixel((x, x), (x, 0, 0))

    inky = inky_e673.Inky()

    inky.set_image(img)
