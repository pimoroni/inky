#!/bin/bash

CWD=`pwd`
filename=$1

firefox --headless --screenshot --window-size=600,448 file://$CWD/$filename
../image.py screenshot.png
