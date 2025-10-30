#!/usr/bin/env python3
"""
Python demo for CAEN VMELib


The demo aims to show the user how to work with the CAEN VMELib library in Python.
The user can cofigure the parameter for the VME operation, and then launch it.
The demo is able to perform a VME Read Cycle, a VME Write Cycle and a VME BLT Read Cycle.
"""

__author__ = 'Matteo Bianchini'
__copyright__ = 'Copyright (C) 2024 CAEN SpA'
__license__ = 'MIT-0'
# SPDX-License-Identifier: MIT-0
__contact__ = 'https://www.caen.it/'

from collections.abc import Callable
from dataclasses import dataclass
import sys
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser

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


@dataclass
class InteractiveDemo:
    """Interactive demo for CAEN VMELib"""

    device: vme.Device

    # Private fields
    __vme_base_address: int = 0
    __address_modifier: vme.AddressModifiers = vme.AddressModifiers.A32_U_DATA
    __data_width: vme.DataWidth = vme.DataWidth.D32

    def set_vme_baseaddress(self):
        """Set VME base address"""
        print(f'Current value: {self.__vme_base_address:08x}')
        try:
            self.__vme_base_address = int(input('Set VME base address: 0x'), 16)
        except ValueError as ex:
            print(f'Invalid value: {ex}')

    def set_address_modifier(self):
        """Set address modifier"""
        print(f'Current value: {self.__address_modifier.name}')
        try:
            self.__address_modifier = vme.AddressModifiers[input('Set address modifier: ')]
        except KeyError as ex:
            print(f'Invalid value: {ex}')

    def set_data_width(self):
        """Set data width"""
        print(f'Current value: {self.__data_width.name}')
        try:
            self.__data_width = vme.DataWidth[input('Set data width: ')]
        except KeyError as ex:
            print(f'Invalid value: {ex}')

    def read_cycle(self):
        """Read cycle"""
        print(f'VME base address: {self.__vme_base_address:08x}')
        print(f'Address modifier: {self.__address_modifier.name}')
        print(f'Data width: {self.__data_width.name}')
        try:
            address = int(input('Set address: 0x'), 16)
        except ValueError as ex:
            print(f'Invalid input: {ex}')
            return
        try:
            value = self.device.read_cycle(self.__vme_base_address | address, self.__address_modifier, self.__data_width)
        except vme.Error as ex:
            print(f'Failed: {ex}')
            return
        print(f'Value: {value:08x}')

    def write_cycle(self):
        """Write cycle"""
        print(f'VME base address: {self.__vme_base_address:08x}')
        print(f'Address modifier: {self.__address_modifier.name}')
        print(f'Data width: {self.__data_width.name}')
        try:
            address = int(input('Set address: 0x'), 16)
            value = int(input('Set value: 0x'), 16)
        except ValueError as ex:
            print(f'Invalid input: {ex}')
            return
        try:
            self.device.write_cycle(self.__vme_base_address | address, value, self.__address_modifier, self.__data_width)
        except vme.Error as ex:
            print(f'Failed: {ex}')

    def read_register(self):
        """Read register"""
        try:
            address = int(input('Set address: 0x'), 16)
        except ValueError as ex:
            print(f'Invalid input: {ex}')
            return
        try:
            value = self.device.registers[address]
        except vme.Error as ex:
            print(f'Failed: {ex}')
            return
        print(f'Value: {value:08x}')

    def write_register(self):
        """Write register"""
        try:
            address = int(input('Set address: 0x'), 16)
            value = int(input('Set value: 0x'), 16)
        except ValueError as ex:
            print(f'Invalid input: {ex}')
            return
        try:
            self.device.registers[address] = value
        except vme.Error as ex:
            print(f'Failed: {ex}')

    def blt_read_cycle(self):
        """BLT read cycle"""
        print(f'VME base address: {self.__vme_base_address:08x}')
        print(f'Address modifier: {self.__address_modifier.name}')
        print(f'Data width: {self.__data_width.name}')
        try:
            address = int(input('Set address: 0x'), 16)
            size = int(input('Set size: '))
        except ValueError as ex:
            print(f'Invalid input: {ex}')
            return
        try:
            buffer = self.device.blt_read_cycle(self.__vme_base_address | address, size, self.__address_modifier, self.__data_width)
        except vme.Error as ex:
            print(f'Failed: {ex}')
            return
        print('Buffer:')
        print(buffer)


def _quit():
    """Quit"""
    print('Quitting...')
    sys.exit()


board_type = vme.BoardType[args.boardtype]
link_number = args.linknumber
conet_node = args.conetnode

with vme.Device.open(board_type, link_number, conet_node) as device:

    demo = InteractiveDemo(device)

    menu_items: dict[str, Callable[[], None]] = {
        'b': demo.set_vme_baseaddress,
        'a': demo.set_address_modifier,
        'd': demo.set_data_width,
        'r': demo.read_cycle,
        'w': demo.write_cycle,
        'R': demo.read_register,
        'W': demo.write_register,
        't': demo.blt_read_cycle,
        'q': _quit,
    }

    while True:
        print('----------------------------------------------------------------------------------')
        print('Menu')
        print('----------------------------------------------------------------------------------')
        for k, function in menu_items.items():
            print(k, function.__doc__)
        selection = input('Please enter your selection: ')
        selected_value = menu_items.get(selection)
        if selected_value is None:
            print('Invalid selection')
            continue
        selected_value()
