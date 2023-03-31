"""Install helper tests for Inky.

These validate that, in case of a missing package, an ImportError is raised.

They don't actually validate that our special message is produced!

"""
import pytest


def test_mock_invalid_size(tkinter, PIL):
    """Test a class with an invalid size raises a ValueError."""
    from inky.mock import InkyMock

    class InkyMockFAIL(InkyMock):
        """Inky wHAT e-Ink Display Simulator."""

        WIDTH = 999
        HEIGHT = 999

        WHITE = 0
        BLACK = 1
        RED = 2
        YELLOW = 2

        def _simulate(self, region):
            pass

    with pytest.raises(ValueError):
        InkyMockFAIL('black')


def test_mock_invalid_colour(tkinter, PIL):
    """Test that instantiating with an invalid colour raises a ValueError."""
    from inky.mock import InkyMockPHAT

    with pytest.raises(ValueError):
        InkyMockPHAT('octarine')


def test_mock_show_phat(tkinter, PIL):
    """Test that show doesn't explode."""
    from inky.mock import InkyMockPHAT

    inky = InkyMockPHAT('red')
    inky.show()


def test_mock_show_what(tkinter, PIL):
    """Test that show doesn't explode."""
    from inky.mock import InkyMockWHAT

    inky = InkyMockWHAT('red')
    inky.show()


def test_mock_show_180(tkinter, PIL):
    """Test that show doesn't explode."""
    from inky.mock import InkyMockPHAT

    inky = InkyMockPHAT('red', h_flip=True, v_flip=True)
    inky.show()
