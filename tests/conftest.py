"""Test configuration.

These allow the mocking of various Python modules
that might otherwise have runtime side-effects.

"""
import sys
from unittest import mock

import pytest

from tools import MockSMBus


@pytest.fixture(scope='function', autouse=True)
def cleanup():
    for module in list(sys.modules.keys()):
        if module.startswith('inky'):
            del sys.modules[module]


@pytest.fixture(scope='function', autouse=False)
def nopath():
    old_path = sys.path
    sys.path = [path for path in sys.path if not path.startswith("/usr/lib") and not path.startswith("/opt/hostedtoolcache")]
    yield
    sys.path = old_path


@pytest.fixture(scope='function', autouse=False)
def GPIO():
    """Mock gpiod and gpiodevice modules."""
    gpiod = mock.MagicMock()
    gpiodevice = mock.MagicMock()
    sys.modules['gpiod'] = gpiod
    sys.modules['gpiod.line'] = gpiod
    sys.modules['gpiodevice'] = gpiodevice
    sys.modules['gpiodevice.platform'] = mock.MagicMock()
    yield gpiod, gpiodevice
    del sys.modules['gpiod']
    del sys.modules['gpiod.line']
    del sys.modules['gpiodevice']
    del sys.modules['gpiodevice.platform']


@pytest.fixture(scope='function', autouse=False)
def smbus2():
    """Mock smbus2 module."""
    sys.modules['smbus2'] = mock.Mock()
    sys.modules['smbus2'].SMBus = MockSMBus
    yield MockSMBus
    del sys.modules['smbus2']


@pytest.fixture(scope='function', autouse=False)
def smbus2_eeprom():
    """Mock smbus2 module."""
    sys.modules['smbus2'] = mock.MagicMock()
    yield sys.modules['smbus2']
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
