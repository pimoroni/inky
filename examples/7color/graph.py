#!/usr/bin/env python3

import io

from PIL import Image
from inky.inky_uc8159 import Inky, DESATURATED_PALETTE
from matplotlib import pyplot
import seaborn
import argparse

print("""

Requires the seaborn library: suso python3 -m pip install seaborn
You may need to: sudo apt install libatlas-base-dev

""")

# Convert the built-in palette to a list of colours usable by seaborn,
# This nets us 6 colours: Green, Blue, Red, Yellow, Orange, Black
palette_colors = [(c[0] / 255.0, c[1] / 255.0, c[2] / 255.0) for c in DESATURATED_PALETTE[2:6] + [(0, 0, 0)]]

parser = argparse.ArgumentParser()
parser.add_argument("--dataset", "-d", choices=["penguins", "dots", "mpg"], default="mpg")
args = parser.parse_args()

inky = Inky()
saturation = 0
dpi = 80
buf = io.BytesIO()

seaborn.set_theme(style="white")

if args.dataset == "mpg":
    palette = seaborn.color_palette(palette_colors, n_colors=3)
    mpg = seaborn.load_dataset("mpg")

    plot = seaborn.relplot(
        x="horsepower", y="mpg", hue="origin", size="weight",
        sizes=(40, 400), alpha=1.0, palette=palette,
        data=mpg)

if args.dataset == "penguins":
    palette = seaborn.color_palette(palette_colors, n_colors=3)
    df = seaborn.load_dataset("penguins")
    plot = seaborn.pairplot(df, hue="species", palette=palette)

if args.dataset == "dots":
    palette = seaborn.color_palette(palette_colors, n_colors=6)
    dots = seaborn.load_dataset("dots")
    plot = seaborn.relplot(
        data=dots,
        x="time", y="firing_rate",
        hue="coherence", size="choice", col="align",
        kind="line", size_order=["T1", "T2"], palette=palette,
        facet_kws=dict(sharex=False),
    )

# Force the output plot to be approximately the right size for Inky
pyplot.gcf().set_size_inches(inky.width / dpi, inky.height / dpi)

plot.savefig(buf, format="png", dpi=dpi)
buf.seek(0)

plot_image = Image.open(buf).convert("RGB")
image = Image.new("RGB", (inky.width, inky.height), (255, 255, 255))
image.paste(plot_image, (0, 0))

inky.set_image(image, saturation=saturation)
inky.show()
