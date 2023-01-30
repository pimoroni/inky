#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from time import sleep
import datetime
import struct, argparse
import smbus
import RPi.GPIO as gpio

EEP_ADRESS = 0x50
EEP_WP = 12

parser = argparse.ArgumentParser(description = ' welcome to V0.1 inky eeprom burner ' )
parser.add_argument('--type', '-t', type=str, required=True, choices=["what", "phat", "impression4", "impression57", "dev", "impressions74"], help="type of display")
parser.add_argument('--colour', '-c', type=str, required=True, choices=["red", "black", "yellow", "7colour", "impressions"], help="ePaper display colour")
parser.add_argument('--pcb' , '-p' , type=float, required=True, help = 'PCB version number', default = None )
parser.add_argument('--display' , '-d' , type=int, required=True, help = 'Display variant number', default = None )
arguments = parser.parse_args()

class EPDType:
    valid_colors = [None, "black", "red", "yellow", "7colour", "impressions"]

    def __init__(self, sizex, sizey, color, pcb_variant, display_variant, write_time=None):
        self.sizex = sizex
        self.sizey = sizey 
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
Time: {}""".format(self.sizex,
            self.sizey,
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
            self.sizex,
            self.sizey,
            self.color,
            self.pcb_variant,
            self.display_variant,
            str(datetime.datetime.now()))

    def to_list(self):
        return [ord(x) for x in self.encode()]
        
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

def eep_wp(state):    
    if (state == True):
        gpio.output(EEP_WP, 1)
    else:
        gpio.output(EEP_WP, 0)

def main(args):
    if (arguments.type =='what'):
        x = 400
        y = 300
    elif (arguments.type =='phat'):
        x = 250
        y = 122
    elif (arguments.type =='impression4'):
        x = 640
        y = 400 
    elif (arguments.type =='impression57'):
        x = 600
        y = 447
    elif (arguments.type =='dev'):
        x = 600
        y = 447
    elif (arguments.type =='impressions74'):
        x = 800
        y = 480

    epdtype = EPDType(x,y, color = arguments.colour, pcb_variant = arguments.pcb, display_variant = arguments.display)
    print("\nWriting data:")
    print (epdtype)
    i2c = smbus.SMBus(1)
    write_data = epdtype.to_list()
    write_data.insert(0, 0x00)
    gpio.setwarnings(False)
    gpio.setmode(gpio.BCM)
    gpio.setup(EEP_WP, gpio.OUT)
    gpio.output(EEP_WP, 0)

    i2c.write_i2c_block_data(EEP_ADRESS, 0x00,write_data)

    sleep(1)
    i2c.write_i2c_block_data(EEP_ADRESS, 0x00, [0x00]) 
    current_data = EPDType.from_bytes(i2c.read_i2c_block_data(EEP_ADRESS,0,29))
    
    print("\nReading back data:")
    print(current_data)

    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))