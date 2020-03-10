"""Test configuration.

These allow the mocking of various Python modules
that might otherwise have runtime side-effects.

"""
import sys
import mock
import pytest

from tools import MockSMBus


@pytest.fixture(scope='function', autouse=False)
def GPIO():
    """Mock RPi.GPIO module."""
    GPIO = mock.MagicMock()
    # Fudge for Python < 37 (possibly earlier)
    sys.modules['RPi'] = mock.MagicMock()
    sys.modules['RPi'].GPIO = GPIO
    sys.modules['RPi.GPIO'] = GPIO
    yield GPIO
    del sys.modules['RPi']
    del sys.modules['RPi.GPIO']


@pytest.fixture(scope='function', autouse=False)
def smbus2():
    """Mock smbus2 module."""
    sys.modules['smbus2'] = mock.Mock()
    sys.modules['smbus2'].SMBus = MockSMBus
    yield MockSMBus
    del sys.modules['smbus2']


@pytest.fixture(scope='function', autouse=False)
def spidev():
    """Mock spidev module."""
    spidev = mock.MagicMock()
    sys.modules['spidev'] = spidev
    yield spidev
    del sys.modules['spidev']


@pytest.fixture(scope='function', autouse=False)
def tkinter():
    """Mock tkinter module."""
    tkinter = mock.MagicMock()
    sys.modules['tkinter'] = tkinter
    yield tkinter
    del sys.modules['tkinter']


@pytest.fixture(scope='function', autouse=False)
def PIL():
    """Mock PIL module."""
    PIL = mock.MagicMock()
    sys.modules['PIL'] = PIL
    yield PIL
    del sys.modules['PIL']
