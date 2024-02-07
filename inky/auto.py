"""Automatic Inky setup from i2c EEPROM."""
import argparse

from . import eeprom
from .inky_ac073tc1a import Inky as InkyAC073TC1A  # noqa: F401
from .inky_ssd1683 import Inky as InkyWHAT_SSD1683  # noqa: F401
from .inky_uc8159 import Inky as InkyUC8159  # noqa: F401
from .phat import InkyPHAT, InkyPHAT_SSD1608  # noqa: F401
from .what import InkyWHAT  # noqa: F401

DISPLAY_TYPES = ["what", "phat", "phatssd1608", "impressions", "7colour", "whatssd1683", "impressions73"]
DISPLAY_COLORS = ["red", "black", "yellow"]


def auto(i2c_bus=None, ask_user=False, verbose=False):
    """Auto-detect Inky board from EEPROM and return an Inky class instance."""
    _eeprom = eeprom.read_eeprom(i2c_bus=i2c_bus)

    if _eeprom is not None:
        if verbose:
            print("Detected {}".format(_eeprom.get_variant()))

        if _eeprom.display_variant in (1, 4, 5):
            return InkyPHAT(_eeprom.get_color())
        if _eeprom.display_variant in (10, 11, 12):
            return InkyPHAT_SSD1608(_eeprom.get_color())
        if _eeprom.display_variant in (2, 3, 6, 7, 8):
            return InkyWHAT(_eeprom.get_color())
        if _eeprom.display_variant == 14:
            return InkyUC8159(resolution=(600, 448))
        if _eeprom.display_variant in (15, 16):
            return InkyUC8159(resolution=(640, 400))
        if _eeprom.display_variant in (17, 18, 19):
            return InkyWHAT_SSD1683((400, 300), _eeprom.get_color())
        if _eeprom.display_variant == 20:
            return InkyAC073TC1A(resolution=(800, 480))

    if ask_user:
        if verbose:
            print("Failed to detect an Inky board. Trying --type/--colour arguments instead...\n")
        parser = argparse.ArgumentParser()
        parser.add_argument("--simulate", "-s", action="store_true", default=False, help="Simulate Inky display")
        parser.add_argument("--type", "-t", type=str, required=True, choices=DISPLAY_TYPES, help="Type of display")
        parser.add_argument("--colour", "-c", type=str, required=False, choices=DISPLAY_COLORS, help="Display colour")
        args, _ = parser.parse_known_args()
        if args.simulate:
            cls = None
            if args.type == "phat":
                from .mock import InkyMockPHAT
                cls = InkyMockPHAT(args.colour)
            if args.type == "phatssd1608":
                from .mock import InkyMockPHATSSD1608
                cls = InkyMockPHATSSD1608(args.colour)
            if args.type == "what":
                from .mock import InkyMockWHAT
                cls = InkyMockWHAT(args.colour)
            if args.type in ("impressions", "7colour"):
                from .mock import InkyMockImpression
                cls = InkyMockImpression()
            if args.type == "whatssd1683":
                from .mock import InkyMockWHAT
                cls = InkyMockWHAT(args.colour)
            if cls is not None:
                import atexit
                atexit.register(cls.wait_for_window_close)
                return cls
            raise RuntimeError("Unable to simulate {}".format(args.type))
        else:
            if args.type == "phat":
                return InkyPHAT(args.colour)
            if args.type == "phatssd1608":
                return InkyPHAT_SSD1608(args.colour)
            if args.type == "what":
                return InkyWHAT(args.colour)
            if args.type == "whatssd1683":
                return InkyWHAT_SSD1683(colour=args.colour)
            if args.type in ("impressions", "7colour"):
                return InkyUC8159()
            if args.type == "impressions73":
                return InkyAC073TC1A()

    if _eeprom is None:
        raise RuntimeError("No EEPROM detected! You must manually initialise your Inky board.")
    else:
        raise RuntimeError("Can't find a driver this display.")
