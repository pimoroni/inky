"""Inky e-Ink Display Drivers."""

import os

uname = os.uname()

arch = uname[4]
on_rpi = arch.startswith('arm')

if not on_rpi:
    from .mockp import InkyMockP
    from .mockw import InkyMockW

from . import inky
from .phat import InkyPHAT
from .what import InkyWHAT


__version__ = '0.0.5.1'

try:
    from pkg_resources import declare_namespace
    declare_namespace(__name__)
except ImportError:
    from pkgutil import extend_path
    __path__ = extend_path(__path__, __name__)
