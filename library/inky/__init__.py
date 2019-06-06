"""Inky e-Ink Display Drivers."""
from . import inky
from .phat import InkyPHAT
from .what import InkyWHAT

__version__ = '0.0.5'

try:
    from pkg_resources import declare_namespace
    declare_namespace(__name__)
except ImportError:
    from pkgutil import extend_path
    __path__ = extend_path(__path__, __name__)
