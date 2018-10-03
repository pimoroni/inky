import os
import glob

font_directory = os.path.abspath(os.path.dirname(__file__))

font_files = {}

for font in list(glob.glob(os.path.join(font_directory, "*.ttf"))):
    font_name = os.path.basename(font).replace(".ttf", "").replace("-Regular", "").replace("-", "")
    font_files[font_name] = font
    globals()[font_name] = font
