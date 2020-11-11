#!/usr/bin/env python3

from inky.inky_uc8159 import Inky
import argparse
import pathlib
import struct
import sys

parser = argparse.ArgumentParser()

parser.add_argument('--type', '-t', choices=['css', 'act', 'raw', 'pal', 'gpl'], help='Type of palette to output')
parser.add_argument('--saturation', '-s', type=float, default=0.5, help='Colour palette saturation')
parser.add_argument('--file', '-f', type=pathlib.Path, help='Output file')

args = parser.parse_args()

inky = Inky()

names = ['black', 'white', 'green', 'blue', 'red', 'yellow', 'orange']

if args.file is None:
    print("You must specify an output palette file.")
    sys.exit(1)


def raw_palette():
    palette = bytearray(768)
    palette[0:8 * 3] = inky._palette_blend(args.saturation, dtype='uint8')
    return palette


if args.type == 'css':
    palette = inky._palette_blend(args.saturation, dtype='uint24')
    with open(args.file, 'w+') as f:
        for i in range(7):
            name = names[i]
            colour = palette[i]
            f.write(""".{name}_fg {{font-color:#{colour:06x}}}
.{name}_bg {{background-color:#{colour:06x}}}
""".format(name=name, colour=colour))

if args.type == 'gpl':
    palette = inky._palette_blend(args.saturation, dtype='uint24')
    with open(args.file, 'w+') as f:
        f.write("GIMP Palette\n")
        f.write("Name: InkyImpressions\n")
        f.write("Columns: 7\n")
        for i in range(7):
            name = names[i]
            colour = palette[i]
            r = (colour & 0xff0000) >> 16
            g = (colour & 0x00ff00) >> 8
            b = (colour & 0x0000ff)
            f.write("{r} {g} {b} Index {i} # {name}\n".format(r=r, g=g, b=b, i=i, name=name))

if args.type in ('pal', 'raw'):
    palette = raw_palette()
    with open(args.file, 'wb+') as f:
        f.write(palette)

if args.type == 'act':
    palette = raw_palette()
    palette += struct.pack(">HH", 7, 0xFFFF)
    with open(args.file, 'wb+') as f:
        f.write(palette)
