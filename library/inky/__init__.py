"""Inky e-Ink Display Drivers."""

from . import inky  # noqa: F401
from .phat import InkyPHAT  # noqa: F401
from .what import InkyWHAT  # noqa: F401
from .mock import InkyMockPHAT, InkyMockWHAT  # noqa: F401


__version__ = '0.0.5.1'

try:
    from pkg_resources import declare_namespace
    declare_namespace(__name__)
except ImportError:
    from pkgutil import extend_path
    __path__ = extend_path(__path__, __name__)
