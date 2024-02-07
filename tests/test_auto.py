"""Auto-detect tests for Inky."""
import sys

import pytest

DISPLAY_VARIANT = [
    None,
    'Red pHAT (High-Temp)',
    'Yellow wHAT',
    'Black wHAT',
    'Black pHAT',
    'Yellow pHAT',
    'Red wHAT',
    'Red wHAT (High-Temp)',
    'Red wHAT',
    None,
    'Black pHAT (SSD1608)',
    'Red pHAT (SSD1608)',
    'Yellow pHAT (SSD1608)',
    None,
    '7-Colour (UC8159)',
    '7-Colour 640x400 (UC8159)',
    '7-Colour 640x400 (UC8159)',
    'Black wHAT (SSD1683)',
    'Red wHAT (SSD1683)',
    'Yellow wHAT (SSD1683)'
]


@pytest.mark.parametrize('verbose', [True, False])
@pytest.mark.parametrize('inky_colour', ['black', 'red', 'yellow', None])
@pytest.mark.parametrize('inky_type', ['phat', 'what', 'phatssd1608', 'impressions', '7colour', 'whatssd1683'])
def test_auto_fallback(GPIO, spidev, smbus2, PIL, inky_type, inky_colour, verbose):
    """Test auto init of 'phat', 'black'."""
    from inky import Inky7Colour, InkyPHAT, InkyPHAT_SSD1608, InkyWHAT, InkyWHAT_SSD1683, auto

    if inky_type in ['impressions', '7colour']:
        if inky_colour is not None:
            pytest.skip('Impressions does not take a colour argument')
    else:
        if inky_colour is None:
            pytest.skip('PHAT/WHAT must specify colour')

    sys.argv[1:3] = ['--type', inky_type]

    if inky_colour is not None:
        sys.argv[3:5] = ['--colour', inky_colour]

    inky_class = {
        'phat': InkyPHAT,
        'what': InkyWHAT,
        'phatssd1608': InkyPHAT_SSD1608,
        'impressions': Inky7Colour,
        '7colour': Inky7Colour,
        'whatssd1683': InkyWHAT_SSD1683}[inky_type]

    inky = auto(ask_user=True, verbose=verbose)
    assert isinstance(inky, inky_class) is True
    if inky_colour is not None:
        assert inky.colour == inky_colour


@pytest.mark.parametrize('inky_display', enumerate(DISPLAY_VARIANT))
def test_auto(GPIO, spidev, smbus2_eeprom, PIL, inky_display):
    """Test auto init of 'phat', 'black'."""
    from inky import Inky7Colour, InkyPHAT, InkyPHAT_SSD1608, InkyWHAT, InkyWHAT_SSD1683, auto, eeprom

    display_id, display_name = inky_display

    if display_name is None:
        pytest.skip('Skipping unsupported display ID')

    inky_class, inky_colour, inky_size = [
        (None, None, None),
        (InkyPHAT, 'red', (212, 104)),
        (InkyWHAT, 'yellow', (400, 300)),
        (InkyWHAT, 'black', (400, 300)),
        (InkyPHAT, 'black', (212, 104)),
        (InkyPHAT, 'yellow', (212, 104)),
        (InkyWHAT, 'red', (400, 300)),
        (InkyWHAT, 'red', (400, 300)),
        (InkyWHAT, 'red', (400, 300)),
        (None, None, None),
        (InkyPHAT_SSD1608, 'black', (250, 122)),
        (InkyPHAT_SSD1608, 'red', (250, 122)),
        (InkyPHAT_SSD1608, 'yellow', (250, 122)),
        (None, None, None),
        (Inky7Colour, '7colour', (600, 448)),
        (Inky7Colour, '7colour', (600, 448)),
        (Inky7Colour, '7colour', (600, 448)),
        (InkyWHAT_SSD1683, 'black', (400, 300)),
        (InkyWHAT_SSD1683, 'red', (400, 300)),
        (InkyWHAT_SSD1683, 'yellow', (400, 300))
    ][display_id]

    width, height = inky_size

    eeprom_data = eeprom.EPDType(width, height, inky_colour, 0, display_id).encode()

    smbus2_eeprom.SMBus(1).read_i2c_block_data.return_value = eeprom_data

    inky = auto()
    assert isinstance(inky, inky_class)
