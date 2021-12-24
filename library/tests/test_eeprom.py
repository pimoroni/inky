"""EEPROM tests for Inky."""

import mock
import pytest


def test_eeprom_7color_7inch(spidev, smbus2_eeprom, PIL):
    """Test EEPROM for 7color 7" Inky"""
    from inky.inky_uc8159 import Inky
    from inky.eeprom import EPDType

    eeprom_data = EPDType(600, 448, 0, 0, 14).encode()

    smbus2_eeprom.SMBus(1).read_i2c_block_data.return_value = eeprom_data

    inky = Inky()

    assert inky.resolution == (600, 448)


def test_eeprom_7color_5inch(spidev, smbus2_eeprom, PIL):
    """Test EEPROM for 7color 5" Inky"""
    from inky.inky_uc8159 import Inky
    from inky.eeprom import EPDType

    eeprom_data = EPDType(640, 400, 0, 0, 16).encode()

    smbus2_eeprom.SMBus(1).read_i2c_block_data.return_value = eeprom_data

    inky = Inky()

    assert inky.resolution == (640, 400)
