"""Initialization tests for Inky."""


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

    InkyWHAT('red')
