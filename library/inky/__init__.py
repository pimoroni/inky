"""Inky e-Ink Display Drivers."""

from . import inky                            # noqa: F401
from .inky import BLACK, WHITE, RED, YELLOW   # noqa: F401
from .phat import InkyPHAT, InkyPHAT_SSD1608  # noqa: F401
from .what import InkyWHAT                    # noqa: F401
from .mock import InkyMockPHAT, InkyMockWHAT  # noqa: F401
from .inky_uc8159 import Inky as Inky7Colour  # noqa: F401
from .auto import auto                        # noqa: F401

__version__ = '1.3.0'

try:
    from pkg_resources import declare_namespace
    declare_namespace(__name__)
except ImportError:
    from pkgutil import extend_path
    __path__ = extend_path(__path__, __name__)
