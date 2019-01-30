"""Initialization tests for Inky."""
import sys
import mock
from tools import MockSMBus


def mockery():
    """Mock requires modules."""
    sys.modules['RPi'] = mock.Mock()
    sys.modules['RPi.GPIO'] = mock.Mock()
    sys.modules['spidev'] = mock.Mock()
    sys.modules['smbus'] = mock.Mock()
    sys.modules['smbus'].SMBus = MockSMBus


def test_init_phat_black():
    """Test initialisation of InkyPHAT with 'black' colour choice."""
    mockery()

    from inky import InkyPHAT

    InkyPHAT('black')


def test_init_phat_red():
    """Test initialisation of InkyPHAT with 'red' colour choice."""
    mockery()

    from inky import InkyPHAT

    InkyPHAT('red')


def test_init_phat_yellow():
    """Test initialisation of InkyPHAT with 'yellow' colour choice."""
    mockery()

    from inky import InkyPHAT

    InkyPHAT('red')


def test_init_what_black():
    """Test initialisation of InkyWHAT with 'black' colour choice."""
    mockery()

    from inky import InkyWHAT

    InkyWHAT('black')


def test_init_what_red():
    """Test initialisation of InkyWHAT with 'red' colour choice."""
    mockery()

    from inky import InkyWHAT

    InkyWHAT('red')


def test_init_what_yellow():
    """Test initialisation of InkyWHAT with 'yellow' colour choice."""
    mockery()

    from inky import InkyWHAT

    InkyWHAT('red')
