"""Install helper tests for Inky.

These validate that, in case of a missing package, an ImportError is raised.

They don't actually validate that our special message is produced!

"""
import pytest


def test_mock_phat_no_tkinter(PIL, nopath):
    """Test initialisation of InkyMockPHAT without tkinter."""
    from inky import InkyMockPHAT

    with pytest.raises(ImportError):
        InkyMockPHAT('black')


def test_mock_what_no_tkinter(PIL, nopath):
    """Test initialisation of InkyMockWHAT without tkinter."""
    from inky import InkyMockWHAT

    with pytest.raises(ImportError):
        InkyMockWHAT('black')

