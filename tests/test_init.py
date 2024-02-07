"""Initialization tests for Inky."""

import pytest


def test_init_mock_phat_black(GPIO, tkinter, PIL):
    """Test initialisation of InkyMockPHAT with 'black' colour choice."""
    from inky import InkyMockPHAT

    InkyMockPHAT('black')


def test_init_mock_what_black(GPIO, tkinter, PIL):
    """Test initialisation of InkyMockWHAT with 'black' colour choice."""
    from inky import InkyMockWHAT

    InkyMockWHAT('black')


def test_init_phat_black(GPIO, spidev, smbus2, PIL):
    """Test initialisation of InkyPHAT with 'black' colour choice."""
    from inky import InkyPHAT

    InkyPHAT('black')


def test_init_phat_red(GPIO, spidev, smbus2, PIL):
    """Test initialisation of InkyPHAT with 'red' colour choice."""
    from inky import InkyPHAT

    InkyPHAT('red')


def test_init_phat_yellow(GPIO, spidev, smbus2, PIL):
    """Test initialisation of InkyPHAT with 'yellow' colour choice."""
    from inky import InkyPHAT

    InkyPHAT('red')


def test_init_what_black(GPIO, spidev, smbus2, PIL):
    """Test initialisation of InkyWHAT with 'black' colour choice."""
    from inky import InkyWHAT

    InkyWHAT('black')


def test_init_what_red(GPIO, spidev, smbus2, PIL):
    """Test initialisation of InkyWHAT with 'red' colour choice."""
    from inky import InkyWHAT

    InkyWHAT('red')


def test_init_what_yellow(GPIO, spidev, smbus2, PIL):
    """Test initialisation of InkyWHAT with 'yellow' colour choice."""
    from inky import InkyWHAT

    InkyWHAT('yellow')


def test_init_invalid_colour(GPIO, spidev, smbus2, PIL):
    """Test initialisation of InkyWHAT with an invalid colour choice."""
    from inky import InkyWHAT

    with pytest.raises(ValueError):
        InkyWHAT('octarine')


def test_init_what_setup(GPIO, spidev, smbus2, PIL):
    """Test initialisation and setup of InkyWHAT.

    Verify our expectations for GPIO setup in order to catch regressions.

    """
    from inky import InkyWHAT

    # _busy_wait will timeout after N seconds
    # GPIO.input.return_value = GPIO.LOW

    inky = InkyWHAT('red')
    inky.setup()

    # Check API will been opened
    spidev.SpiDev().open.assert_called_with(0, inky.cs_channel)


def test_init_7colour_setup(GPIO, spidev, smbus2, PIL):
    """Test initialisation and setup of 7-colour Inky.

    Verify our expectations for GPIO setup in order to catch regressions.

    """
    from inky.inky_uc8159 import Inky

    # _busy_wait will timeout after N seconds
    # GPIO.input.return_value = GPIO.LOW

    inky = Inky()
    inky.setup()

    # Check API will been opened
    spidev.SpiDev().open.assert_called_with(0, inky.cs_channel)
