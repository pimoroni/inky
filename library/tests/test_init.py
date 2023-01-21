"""Initialization tests for Inky."""

from unittest import mock
import pytest


def test_init_mock_phat_black(tkinter, PIL):
    """Test initialisation of InkyMockPHAT with 'black' colour choice."""
    from inky import InkyMockPHAT

    InkyMockPHAT('black')


def test_init_mock_what_black(tkinter, PIL):
    """Test initialisation of InkyMockWHAT with 'black' colour choice."""
    from inky import InkyMockWHAT

    InkyMockWHAT('black')


def test_init_phat_black(spidev, smbus2):
    """Test initialisation of InkyPHAT with 'black' colour choice."""
    from inky import InkyPHAT

    InkyPHAT('black')


def test_init_phat_red(spidev, smbus2):
    """Test initialisation of InkyPHAT with 'red' colour choice."""
    from inky import InkyPHAT

    InkyPHAT('red')


def test_init_phat_yellow(spidev, smbus2):
    """Test initialisation of InkyPHAT with 'yellow' colour choice."""
    from inky import InkyPHAT

    InkyPHAT('red')


def test_init_what_black(spidev, smbus2):
    """Test initialisation of InkyWHAT with 'black' colour choice."""
    from inky import InkyWHAT

    InkyWHAT('black')


def test_init_what_red(spidev, smbus2):
    """Test initialisation of InkyWHAT with 'red' colour choice."""
    from inky import InkyWHAT

    InkyWHAT('red')


def test_init_what_yellow(spidev, smbus2):
    """Test initialisation of InkyWHAT with 'yellow' colour choice."""
    from inky import InkyWHAT

    InkyWHAT('yellow')


def test_init_invalid_colour(spidev, smbus2):
    """Test initialisation of InkyWHAT with an invalid colour choice."""
    from inky import InkyWHAT

    with pytest.raises(ValueError):
        InkyWHAT('octarine')


def test_init_what_setup_no_gpio(spidev, smbus2):
    """Test Inky init with a missing RPi.GPIO library."""
    from inky import InkyWHAT

    inky = InkyWHAT('red')

    with pytest.raises(ImportError):
        inky.setup()


def test_init_what_setup(spidev, smbus2, GPIO):
    """Test initialisation and setup of InkyWHAT.

    Verify our expectations for GPIO setup in order to catch regressions.

    """
    from inky import InkyWHAT

    # TODO: _busy_wait should timeout after N seconds
    GPIO.input.return_value = GPIO.LOW

    inky = InkyWHAT('red')
    inky.setup()

    # Check GPIO setup
    GPIO.setwarnings.assert_called_with(False)
    GPIO.setmode.assert_called_with(GPIO.BCM)
    GPIO.setup.assert_has_calls([
        mock.call(inky.dc_pin, GPIO.OUT, initial=GPIO.LOW, pull_up_down=GPIO.PUD_OFF),
        mock.call(inky.reset_pin, GPIO.OUT, initial=GPIO.HIGH, pull_up_down=GPIO.PUD_OFF),
        mock.call(inky.busy_pin, GPIO.IN, pull_up_down=GPIO.PUD_OFF)
    ])

    # Check device will been reset
    GPIO.output.assert_has_calls([
        mock.call(inky.reset_pin, GPIO.LOW),
        mock.call(inky.reset_pin, GPIO.HIGH)
    ])

    # Check API will been opened
    spidev.SpiDev().open.assert_called_with(0, inky.cs_channel)


def test_init_7colour_setup_no_gpio(spidev, smbus2):
    """Test initialisation and setup of 7-colour Inky.

    Verify an error is raised when RPi.GPIO is not present.

    """
    from inky.inky_uc8159 import Inky

    inky = Inky()

    with pytest.raises(ImportError):
        inky.setup()


def test_init_7colour_setup(spidev, smbus2, GPIO):
    """Test initialisation and setup of 7-colour Inky.

    Verify our expectations for GPIO setup in order to catch regressions.

    """
    from inky.inky_uc8159 import Inky

    # TODO: _busy_wait should timeout after N seconds
    GPIO.input.return_value = GPIO.LOW

    inky = Inky()
    inky.setup()

    # Check GPIO setup
    GPIO.setwarnings.assert_called_with(False)
    GPIO.setmode.assert_called_with(GPIO.BCM)
    GPIO.setup.assert_has_calls([
        mock.call(inky.dc_pin, GPIO.OUT, initial=GPIO.LOW, pull_up_down=GPIO.PUD_OFF),
        mock.call(inky.reset_pin, GPIO.OUT, initial=GPIO.HIGH, pull_up_down=GPIO.PUD_OFF),
        mock.call(inky.busy_pin, GPIO.IN, pull_up_down=GPIO.PUD_OFF)
    ])

    # Check device will been reset
    GPIO.output.assert_has_calls([
        mock.call(inky.reset_pin, GPIO.LOW),
        mock.call(inky.reset_pin, GPIO.HIGH)
    ])

    # Check API will been opened
    spidev.SpiDev().open.assert_called_with(0, inky.cs_channel)
