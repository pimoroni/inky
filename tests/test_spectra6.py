"""Spectra 6 speed and partial refresh tests."""
import importlib
import time
import warnings
from unittest import mock

import pytest

MODULES = ["inky_e673", "inky_e640", "inky_el133uf1"]

DRIVERS = [
    ("inky_e673", "EL673"),
    ("inky_e640", "EL640"),
    ("inky_el133uf1", "EL133UF1"),
]


@pytest.fixture(autouse=True)
def fast_time(monkeypatch):
    clock = iter(range(0, 10**9, 10))
    monkeypatch.setattr(time, "sleep", lambda seconds: None)
    monkeypatch.setattr(time, "monotonic", lambda: next(clock))


def make_inky(module_name, **kwargs):
    module = importlib.import_module(f"inky.{module_name}")
    import gpiodevice
    from gpiod.line import Value

    lines = gpiodevice.find_chip_by_platform.return_value.request_lines.return_value
    lines.get_value.return_value = Value.ACTIVE
    display = module.Inky(spi_bus=mock.MagicMock(), **kwargs)
    display._send_command = mock.MagicMock(wraps=display._send_command)
    return module, display


def commands(display, command):
    return [call for call in display._send_command.call_args_list if call.args[0] == command]


@pytest.mark.filterwarnings("ignore")
@pytest.mark.parametrize("module_name,prefix", DRIVERS)
@pytest.mark.parametrize("speed", ["NORMAL", "MEDIUM", "FAST"])
def test_speed_sets_pll(GPIO, spidev, module_name, prefix, speed):
    module = importlib.import_module(f"inky.{module_name}")
    _, display = make_inky(module_name, speed=getattr(module.Inky, speed))
    display.show()

    pll = commands(display, getattr(module, f"{prefix}_PLL"))
    assert pll
    assert all(call.args[-1] == [getattr(module.Inky, speed)] for call in pll)


@pytest.mark.parametrize("module_name", MODULES)
def test_invalid_speed(GPIO, spidev, module_name):
    with pytest.raises(ValueError):
        make_inky(module_name, speed=0x99)


@pytest.mark.parametrize("module_name", MODULES)
@pytest.mark.parametrize("region", [
    (0, 0, 0, 10),
    (0, 0, 10, 0),
    (-1, 0, 10, 10),
    (0, -1, 10, 10),
    (0, 0, 10000, 10),
    (0, 0, 10, 10000),
])
def test_region_outside_display(GPIO, spidev, module_name, region):
    _, display = make_inky(module_name)
    with pytest.raises(ValueError):
        display.set_region(*region)


@pytest.mark.parametrize("module_name", MODULES)
def test_region_must_be_integers(GPIO, spidev, module_name):
    _, display = make_inky(module_name)
    with pytest.raises(TypeError):
        display.set_region(1.5, 0, 10, 10)


@pytest.mark.parametrize("module_name", MODULES)
def test_reset_region(GPIO, spidev, module_name):
    _, display = make_inky(module_name)
    display.set_region(0, 0, 10, 10)
    assert display.region == (0, 0, 10, 10)
    display.reset_region()
    assert display.region is None


@pytest.mark.filterwarnings("ignore")
@pytest.mark.parametrize("module_name,prefix", DRIVERS)
def test_full_refresh_has_no_window(GPIO, spidev, module_name, prefix):
    module, display = make_inky(module_name)
    display.show()
    assert commands(display, getattr(module, f"{prefix}_PTLW")) == []


def window(first_row, last_row, first_column, last_column):
    return [
        first_column >> 8, first_column & 0xFF, last_column >> 8, last_column & 0xFF,
        first_row >> 8, first_row & 0xFF, last_row >> 8, last_row & 0xFF, 0x01,
    ]


# 7.3" is drawn as-is, 4.0" is rotated onto the panel
@pytest.mark.filterwarnings("ignore")
@pytest.mark.parametrize("module_name,prefix,expected,length,index,shift", [
    ("inky_e673", "EL673", window(20, 22, 8, 15), 3 * 8 // 2, 1, 4),
    ("inky_e640", "EL640", window(10, 14, 376, 379), 5 * 4 // 2, 1, 0),
])
def test_partial_refresh_window(GPIO, spidev, module_name, prefix, expected, length, index, shift):
    module, display = make_inky(module_name)
    display.set_pixel(10, 20, display.RED)
    display.set_region(10, 20, 5, 3)
    display.show()

    ptlw = commands(display, getattr(module, f"{prefix}_PTLW"))
    assert ptlw[0].args[-1] == expected
    assert ptlw[-1].args[-1] == [0x00] * 9

    cdi = commands(display, getattr(module, f"{prefix}_CDI"))
    assert cdi[-1].args[-1] == [0xFF]

    drf = commands(display, getattr(module, f"{prefix}_DRF"))
    assert drf[0].args[-1] == [getattr(module, f"{prefix}_DRF_PARTIAL")]

    data = commands(display, getattr(module, f"{prefix}_DTM1"))[0].args[-1]
    assert len(data) == length
    assert data[index] == display.RED << shift


@pytest.mark.filterwarnings("ignore")
@pytest.mark.parametrize("module_name,prefix,h_flip,v_flip,rotation,expected", [
    ("inky_e673", "EL673", False, False, 0, window(0, 1, 0, 3)),
    ("inky_e673", "EL673", True, False, 0, window(478, 479, 0, 3)),
    ("inky_e673", "EL673", False, True, 0, window(0, 1, 796, 799)),
    ("inky_e673", "EL673", True, True, 0, window(478, 479, 796, 799)),
    ("inky_e673", "EL673", False, False, 180, window(478, 479, 796, 799)),
    ("inky_e640", "EL640", False, False, 0, window(0, 3, 396, 399)),
    ("inky_e640", "EL640", True, False, 0, window(0, 3, 0, 3)),
    ("inky_e640", "EL640", False, True, 0, window(596, 599, 396, 399)),
    ("inky_e640", "EL640", True, True, 0, window(596, 599, 0, 3)),
    ("inky_e640", "EL640", False, False, 180, window(596, 599, 0, 3)),
])
def test_partial_refresh_window_orientation(GPIO, spidev, module_name, prefix, h_flip, v_flip, rotation, expected):
    module, display = make_inky(module_name, h_flip=h_flip, v_flip=v_flip)
    display.rotation = rotation
    display.set_region(0, 0, 4, 2)
    display.show()

    assert commands(display, getattr(module, f"{prefix}_PTLW"))[0].args[-1] == expected


@pytest.mark.filterwarnings("ignore")
def test_el133uf1_partial_refresh_one_half(GPIO, spidev):
    module, display = make_inky("inky_el133uf1")
    display.set_region(10, 20, 5, 3)
    display.show()

    ptlw = commands(display, module.EL133UF1_PTLW)
    by_cs = {call.args[1]: call.args[-1] for call in ptlw}

    # region isn't in half A, so it gets a tiny window
    assert by_cs[module.CS0_SEL] == window(0, 0, 0, 31)
    # narrow region is widened to 16 columns
    assert by_cs[module.CS1_SEL] == window(5, 7, 1152, 1183)
    assert by_cs[module.CS_BOTH_SEL] == [0x00] * 9

    dtm = {call.args[1]: call.args[-1] for call in commands(display, module.EL133UF1_DTM)}
    assert len(dtm[module.CS0_SEL]) == 2 * 16 // 2
    assert len(dtm[module.CS1_SEL]) == 6 * 16 // 2

    drf = commands(display, module.EL133UF1_DRF)
    assert drf[0].args[-1] == [module.EL133UF1_DRF_PARTIAL]


@pytest.mark.filterwarnings("ignore")
@pytest.mark.parametrize("h_flip,v_flip,rotation", [(False, False, 0), (True, True, 0), (False, False, 180)])
def test_el133uf1_partial_refresh_both_halves(GPIO, spidev, h_flip, v_flip, rotation):
    module, display = make_inky("inky_el133uf1", h_flip=h_flip, v_flip=v_flip)
    display.rotation = rotation
    display.set_region(0, 0, 1600, 1200)
    display.show()

    ptlw = {call.args[1]: call.args[-1] for call in commands(display, module.EL133UF1_PTLW)}
    assert ptlw[module.CS0_SEL] == window(0, 799, 0, 1199)
    assert ptlw[module.CS1_SEL] == window(0, 799, 0, 1199)


@pytest.mark.filterwarnings("ignore")
def test_el133uf1_refresh_wait_waits_for_busy(GPIO, spidev):
    from gpiod.line import Value

    _, display = make_inky("inky_el133uf1")
    display.setup()
    display._gpio.get_value.side_effect = [Value.ACTIVE, Value.INACTIVE, Value.INACTIVE, Value.ACTIVE]
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        display._refresh_wait()


@pytest.mark.parametrize("module_name", MODULES)
def test_border_colour(GPIO, spidev, module_name):
    _, display = make_inky(module_name)
    display.set_border(display.RED)
    assert display.border_colour == display.RED
