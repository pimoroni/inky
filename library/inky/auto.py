from .phat import InkyPHAT, InkyPHAT_SSD1608  # noqa: F401
from .what import InkyWHAT                    # noqa: F401
from . import eeprom


class Auto:
    def __init__(self, spi_bus=None, i2c_bus=None):
        self._spi_bus = spi_bus
        self._i2c_bus = i2c_bus
        self.eeprom = eeprom.read_eeprom(i2c_bus=i2c_bus)

        if self.eeprom is None:
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

        if self.eeprom.display_variant in (1, 4, 5):
            return InkyPHAT((self.eeprom.width, self.eeprom.height), self.eeprom.get_color())
        if self.eeprom.display_variant in (10, 11, 12):
            return InkyPHAT_SSD1608((self.eeprom.width, self.eeprom.height), self.eeprom.get_color())

        return InkyWHAT((self.eeprom.width, self.eeprom.height), self.eeprom.get_color())
