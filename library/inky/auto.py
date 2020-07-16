from .phat import InkyPHAT, InkyPHAT_SSD1608  # noqa: F401
from .what import InkyWHAT                    # noqa: F401
from . import eeprom


def auto(i2c_bus=None):
    _eeprom = eeprom.read_eeprom(i2c_bus=i2c_bus)

    if _eeprom is None:
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

    if _eeprom.display_variant in (1, 4, 5):
        return InkyPHAT(_eeprom.get_color())
    if _eeprom.display_variant in (10, 11, 12):
        return InkyPHAT_SSD1608(_eeprom.get_color())

    return InkyWHAT(_eeprom.get_color())
