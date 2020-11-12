import pytest
import sys


@pytest.mark.parametrize('inky_colour', ['black', 'red', 'yellow', None])
@pytest.mark.parametrize('inky_type', ['phat', 'what', 'phatssd1608', 'impressions', '7colour'])
def test_auto_fallback(spidev, smbus2, PIL, inky_type, inky_colour):
    """Test auto init of 'phat', 'black'."""
    from inky import auto
    from inky import InkyPHAT, InkyPHAT_SSD1608, InkyWHAT, Inky7Colour

    if inky_type in ['impressions', '7colour']:
        if inky_colour is not None:
            pytest.skip('Impressions does not take a colour argument')
    else:
        if inky_colour is None:
            pytest.skip('PHAT/WHAT must specify colour')

    sys.argv[1:3] = ['--type', inky_type]
    if inky_colour is not None:
        sys.argv[3:5] = ['--colour', inky_colour]
    inky_class = {'phat': InkyPHAT, 'what': InkyWHAT, 'phatssd1608': InkyPHAT_SSD1608, 'impressions': Inky7Colour, '7colour': Inky7Colour}[inky_type]

    inky = auto(ask_user=True)
    assert isinstance(inky, inky_class) is True
    if inky_colour is not None:
        assert inky.colour == inky_colour
