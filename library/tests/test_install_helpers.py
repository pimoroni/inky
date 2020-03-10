"""Install helper tests for Inky.

These validate that, in case of a missing package, an ImportError is raised.

They don't actually validate that our special message is produced!

"""
import pytest


def test_mock_phat_no_tkinter():
    """Test initialisation of InkyMockPHAT without tkinter."""
    from inky import InkyMockPHAT

    with pytest.raises(ImportError):
        InkyMockPHAT('black')


def test_mock_what_no_tkinter():
    """Test initialisation of InkyMockWHAT without tkinter."""
    from inky import InkyMockWHAT

    with pytest.raises(ImportError):
        InkyMockWHAT('black')


def test_mock_phat_no_pil(tkinter):
    """Test initialisation of InkyMockPHAT without PIL."""
    from inky import InkyMockPHAT

    with pytest.raises(ImportError):
        InkyMockPHAT('black')


def test_mock_what_no_pil(tkinter):
    """Test initialisation of InkyMockWHAT without PIL."""
    from inky import InkyMockWHAT

    with pytest.raises(ImportError):
        InkyMockWHAT('black')
