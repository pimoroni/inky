import inky

phat = inky.InkyPHAT('red')

phat.setup()

for x in range(phat.WIDTH):
    for y in range(phat.HEIGHT):
        phat.set_pixel(x, y, 1)

phat.show()
