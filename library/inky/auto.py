from .phat import InkyPHAT, InkyPHAT_SSD1608  # noqa: F401
from .what import InkyWHAT                    # noqa: F401
from . import eeprom
import argparse


def auto(i2c_bus=None, ask_user=False, verbose=False):
    _eeprom = eeprom.read_eeprom(i2c_bus=i2c_bus)

    if _eeprom is None:
        if ask_user:
            if verbose:
                print("""Failed to detect an Inky board, you must specify the type and colour manually.
""")
            parser = argparse.ArgumentParser()
            parser.add_argument('--type', '-t', type=str, required=True, choices=["what", "phat", "phatssd1608"], help="Type of display")
            parser.add_argument('--colour', '-c', type=str, required=False, choices=["red", "black", "yellow"], help="Display colour")
            args = parser.parse_known_args()
            if args.type == "phat":
                return InkyPHAT(args.colour)
            if args.type == "phatssd1608":
                return InkyPHAT_SSD1608(args.colour)
            if args.type == "what":
                return InkyWHAT(args.colour)
        else:
            raise RuntimeError("No EEPROM detected! You must manually initialise your Inky board.")

    """
    The EEPROM is used to disambiguate the variants of wHAT and pHAT
    1   Red pHAT (High-Temp)
    2   Yellow wHAT (1_E)
    3   Black wHAT (1_E)
    4   Black pHAT (Normal)
    5   Yellow pHAT (DEP0213YNS75AFICP)
    6   Red wHAT (Regular)
    7   Red wHAT (High-Temp)
    8   Red wHAT (DEPG0420RWS19AF0HP)
    10  BW pHAT (ssd1608) (DEPG0213BNS800F13CP)
    11  Red pHAT (ssd1608)
    12  Yellow pHAT (ssd1608)
    """

    if verbose:
        print("Detected {}".format(_eeprom.get_variant()))

    if _eeprom.display_variant in (1, 4, 5):
        return InkyPHAT(_eeprom.get_color())
    if _eeprom.display_variant in (10, 11, 12):
        return InkyPHAT_SSD1608(_eeprom.get_color())

    return InkyWHAT(_eeprom.get_color())
