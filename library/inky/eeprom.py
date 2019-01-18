#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import struct
import smbus

EEP_ADRESS = 0x50
EEP_WP = 12

class EPDType:
    valid_colors = [None, "black", "red", "yellow"]

    def __init__(self, width, height, color, pcb_variant, display_variant, write_time=None):
        self.width = width
        self.height = height 
        self.color = color
        if type(color) == str:
            self.set_color(color)
        self.pcb_variant = pcb_variant 
        self.display_variant = display_variant
        self.eeprom_write_time = str(datetime.datetime.now()) if write_time is None else write_time

    def __repr__(self):
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
        data = bytearray(data)
        data = struct.unpack("<HHBBB22p", data)
        return class_object(*data)
    
    def update_eeprom_write_time(self):
        self.eeprom_write_time = str(datetime.datetime.now())
        
    def encode(self):
        return struct.pack("<HHBBB22p",
            self.width,
            self.height,
            self.color,
            self.pcb_variant,
            self.display_variant,
            str(datetime.datetime.now()))

    def to_list(self):
        return [ord(c) for x in self.encode()]
        
    def set_color(self, color):
        try:
            self.color = self.valid_colors.index(color)
        except KeyError:
            raise ValueError("Invalid colour: {}".format(color))
            
    def get_color(self):
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


def read_eeprom():
    try:
        i2c = smbus.SMBus(1)
        i2c.write_i2c_block_data(EEP_ADRESS, 0x00, [0x00]) 
        return EPDType.from_bytes(i2c.read_i2c_block_data(0x50,0,29))
    except IOError:
        return None

def main(args):
    print(read_eeprom()) 
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
    
