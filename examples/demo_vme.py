#!/usr/bin/env python3
"""
Python demo for CAEN VMELib


The demo as the aim to show the user how to work with the CAEN VMELib library in Python.
The user can cofigure the parameter for the VME operation, and then launch it.
The demo is able to perform a VME Read Cycle, a VME Write Cycle and a VME BLT Read Cycle.
"""

__author__ = 'Matteo Bianchini'
__copyright__ = 'Copyright (C) 2024 CAEN SpA'
__license__ = 'MIT-0'
# SPDX-License-Identifier: MIT-0
__contact__ = 'https://www.caen.it/'

from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
import sys
from caen_libs import caenvme as vme

# Parse arguments
parser = ArgumentParser(
    description=__doc__,
    formatter_class=ArgumentDefaultsHelpFormatter,
)

# Shared parser for subcommands
parser.add_argument('-b', '--boardtype', type=str, help='board type', required=True, choices=tuple(i.name for i in vme.BoardType))
parser.add_argument('-l', '--linknumber', type=str, help='link number, PID or hostname (depending on connectiontype)', required=True)
parser.add_argument('-n', '--conetnode', type=int, help='CONET node', default=0)

args = parser.parse_args()

print('------------------------------------------------------------------------------------')
print(f'CAEN VMELib binding loaded (lib version {vme.lib.sw_release()})')
print('------------------------------------------------------------------------------------')

with vme.Device.open(vme.BoardType[args.boardtype], args.linknumber, args.conetnode) as device:

    # Default values
    vme_base_address = 0
    address_modifier = vme.AddressModifiers.A32_U_DATA
    data_width = vme.DataWidth.D32

    def set_vme_baseaddress():
        """Set VME base address"""
        global vme_base_address
        print(f'Current value: {vme_base_address:08x}')
        try:
            vme_base_address = int(input('Set VME base address: 0x'), 16)
        except ValueError as ex:
            print(f'Invalid value: {ex}')

    def set_address_modifier():
        """Set address modifier"""
        global address_modifier
        print(f'Current value: {address_modifier.name}')
        try:
            address_modifier = vme.AddressModifiers[input('Set address modifier: ')]
        except KeyError as ex:
            print(f'Invalid value: {ex}')

    def set_data_width():
        """Set data width"""
        global data_width
        print(f'Current value: {data_width.name}')
        try:
            data_width = vme.DataWidth[input('Set data width: ')]
        except KeyError as ex:
            print(f'Invalid value: {ex}')

    def read_cycle():
        """Read cycle"""
        global device, vme_base_address, address_modifier, data_width
        print(f'VME base address: {vme_base_address:08x}')
        print(f'Address modifier: {address_modifier.name}')
        print(f'Data width: {data_width.name}')
        try:
            address = int(input('Set address: 0x'), 16)
        except ValueError as ex:
            print(f'Invalid input: {ex}')
            return
        try:
            value = device.read_cycle(vme_base_address | address, address_modifier, data_width)
        except vme.Error as ex:
            print(f'Failed: {ex}')
            return
        print(f'Value: {value:08x}')

    def write_cycle():
        """Write cycle"""
        global device, vme_base_address, address_modifier, data_width
        print(f'VME base address: {vme_base_address:08x}')
        print(f'Address modifier: {address_modifier.name}')
        print(f'Data width: {data_width.name}')
        try:
            address = int(input('Set address: 0x'), 16)
            value = int(input('Set value: 0x'), 16)
        except ValueError as ex:
            print(f'Invalid input: {ex}')
            return
        try:
            device.write_cycle(vme_base_address | address, value, address_modifier, data_width)
        except vme.Error as ex:
            print(f'Failed: {ex}')

    def blt_read_cycle():
        """BLT read cycle"""
        global device, vme_base_address, address_modifier, data_width, size
        print(f'VME base address: {vme_base_address:08x}')
        print(f'Address modifier: {address_modifier.name}')
        print(f'Data width: {data_width.name}')
        try:
            address = int(input('Set address: 0x'), 16)
            size = int(input('Set size: '))
        except ValueError as ex:
            print(f'Invalid input: {ex}')
            return
        try:
            buffer = device.blt_read_cycle(vme_base_address | address, size, address_modifier, data_width)
        except vme.Error as ex:
            print(f'Failed: {ex}')
            return
        print('Buffer:')
        for value in buffer:
            print(value)

    def quit():
        """Quit"""
        print('Quitting...')
        sys.exit()

    def display_menu(menu):
        """Display menu"""
        print('------------------------------------------------------------------------------------')
        print('Menu')
        print('------------------------------------------------------------------------------------')
        for k, function in menu.items():
            print(k, function.__doc__)

    menu_items = {
        'b': set_vme_baseaddress,
        'a': set_address_modifier,
        'd': set_data_width,
        'r': read_cycle,
        'w': write_cycle,
        't': blt_read_cycle,
        'q': quit,
    }

    while True:
        display_menu(menu_items)
        selection = input('Please enter your selection: ')
        selected_value = menu_items[selection]
        selected_value()
