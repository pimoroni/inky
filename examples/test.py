import sys

sys.path.insert(0, '../library/')

import inky

phat = inky.Inky(resolution=(104,212), colour='red')

phat.setup()

for x in range(104):
    for y in range(212):
        phat.set_pixel(x, y, 1)

phat.update()
