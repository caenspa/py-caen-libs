#!/usr/bin/env python3
"""
Python demo for CAEN PLULib


The demo aims to show the user how to work with the CAEN PLULib in Python.
"""

__author__ = 'Matteo Bianchini'
__copyright__ = 'Copyright (C) 2024 CAEN SpA'
__license__ = 'MIT-0'
# SPDX-License-Identifier: MIT-0
__contact__ = 'https://www.caen.it/'

from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from functools import partial

from caen_libs import caenplu as plu


# Parse arguments
parser = ArgumentParser(
    description=__doc__,
    formatter_class=ArgumentDefaultsHelpFormatter,
)

# Shared parser for subcommands
parser.add_argument('-c', '--connectiontype', type=str, help='connection type', required=True, choices=tuple(i.name for i in plu.ConnectionModes))
parser.add_argument('-l', '--linknumber', type=str, help='link number, PID or hostname (depending on connectiontype)', required=True)
parser.add_argument('-n', '--conetnode', type=int, help='CONET node', default=0)
parser.add_argument('-b', '--vmebaseaddress', type=partial(int, base=16), help='VME base address (as hex)', default=0)

args = parser.parse_args()

print('------------------------------------------------------------------------------------')
print('CAEN PLULib binding loaded')
print('------------------------------------------------------------------------------------')

with plu.Device.open(plu.ConnectionModes[args.connectiontype], args.linknumber, args.conetnode, args.vmebaseaddress) as device:
    pcb_revision = device.registers[0x814C]
    print(f'PCB Revision = {pcb_revision}')
    fw_version = device.registers[0x8200].to_bytes(2, 'little')
    print(f'FW Revision = {fw_version[1]}.{fw_version[0]}')
    serial_num = device.get_serial_number()
    print(f'Serial number = {serial_num}')
