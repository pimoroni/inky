#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Inky display-type EEPROM tools."""

import datetime
import struct


EEP_ADRESS = 0x50
EEP_WP = 12


class EPDType:
    """Class to represent EPD EEPROM structure."""

    valid_colors = [None, 'black', 'red', 'yellow']

    def __init__(self, width, height, color, pcb_variant, display_variant, write_time=None):
        """Initialise new EEPROM data structure."""
        self.width = width
        self.height = height
        self.color = color
        if type(color) == str:
            self.set_color(color)
        self.pcb_variant = pcb_variant
        self.display_variant = display_variant
        self.eeprom_write_time = str(datetime.datetime.now()) if write_time is None else write_time

    def __repr__(self):
        """Return string representation of EEPROM data structure."""
        return """Display: {}x{}
Color: {}
PCB Variant: {}
Display Variant: {}
Time: {}""".format(self.width,
                   self.height,
                   self.get_color(),
                   self.pcb_variant / 10.0,
                   self.display_variant,
                   self.eeprom_write_time)

    @classmethod
    def from_bytes(class_object, data):
        """Initialise new EEPROM data structure from a bytes-like object or list."""
        data = bytearray(data)
        data = struct.unpack('<HHBBB22p', data)
        return class_object(*data)

    def update_eeprom_write_time(self):
        """Update the stored write time."""
        self.eeprom_write_time = str(datetime.datetime.now())

    def encode(self):
        """Return a bytearray representing the EEPROM data structure."""
        return struct.pack('<HHBBB22p',
                           self.width,
                           self.height,
                           self.color,
                           self.pcb_variant,
                           self.display_variant,
                           str(datetime.datetime.now()))

    def to_list(self):
        """Return a list of bytes representing the EEPROM data structure."""
        return [ord(c) for c in self.encode()]

    def set_color(self, color):
        """Set the stored colour value."""
        try:
            self.color = self.valid_colors.index(color)
        except KeyError:
            raise ValueError('Invalid colour: {}'.format(color))

    def get_color(self):
        """Get the stored colour value."""
        try:
            return self.valid_colors[self.color]
        except KeyError:
            return None


# Normal Yellow wHAT
yellow_what_1_E = EPDType(400, 300, color='yellow', pcb_variant=12, display_variant=2)

# Normal Black wHAT
black_what_1_E = EPDType(400, 300, color='black', pcb_variant=12, display_variant=3)

# Normal Black pHAT
black_phat_1_E = EPDType(212, 104, color='black', pcb_variant=12, display_variant=4)

# Hightemp Red pHAT
red_small_1_E = EPDType(212, 104, color='red', pcb_variant=12, display_variant=1)


def read_eeprom(i2c_bus=None):
    """Return a class representing EEPROM contents, or none."""
    try:
        if i2c_bus is None:
            try:
                from smbus2 import SMBus
            except ImportError:
                raise ImportError('This library requires the smbus2 module\nInstall with: sudo pip install smbus2')
            i2c_bus = SMBus(1)
        i2c_bus.write_i2c_block_data(EEP_ADRESS, 0x00, [0x00])
        return EPDType.from_bytes(i2c_bus.read_i2c_block_data(0x50, 0, 29))
    except IOError:
        return None


def main(args):
    """EEPROM Test Function."""
    print(read_eeprom())
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
