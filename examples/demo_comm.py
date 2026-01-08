#!/usr/bin/env python3
"""
Python demo for CAEN Comm


The demo aims to show users how to work with the CAENComm library in Python.
It performs a dummy acquisition using a CAEN Digitizer.
Once connected to the device, the acquisition starts, a software trigger is sent,
and the data are read after stopping the acquisition.
"""

__author__ = 'Matteo Bianchini'
__copyright__ = 'Copyright (C) 2024 CAEN SpA'
__license__ = 'MIT-0'
# SPDX-License-Identifier: MIT-0
__contact__ = 'https://www.caen.it/'

from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from functools import partial
from caen_libs import caencomm as comm


# Parse arguments
parser = ArgumentParser(
    description=__doc__,
    formatter_class=ArgumentDefaultsHelpFormatter,
)

# Shared parser for subcommands
parser.add_argument('-c', '--connectiontype', type=str, help='connection type', required=True, choices=tuple(i.name for i in comm.ConnectionType))
parser.add_argument('-l', '--linknumber', type=str, help='link number, PID or hostname (depending on connectiontype)', required=True)
parser.add_argument('-n', '--conetnode', type=int, help='CONET node', default=0)
parser.add_argument('-b', '--vmebaseaddress', type=partial(int, base=16), help='VME base address (as hex)', default=0)

args = parser.parse_args()

print('------------------------------------------------------------------------------------')
print(f'CAEN Comm binding loaded (lib version {comm.lib.sw_release()})')
print('------------------------------------------------------------------------------------')

connection_type = comm.ConnectionType[args.connectiontype]
link_number = args.linknumber
conet_node = args.conetnode
vme_base_address = args.vmebaseaddress

with comm.Device.open(connection_type, link_number, conet_node, vme_base_address) as device:

    print('Connected with Digitizer')

    # Assuming to be connected to a CAEN Digitizer 1.0
    serial = device.reg32[0xF080:0xF088:4]
    serial_number = int.from_bytes(serial[:2], 'big')
    if serial_number == 0xFFFF:
        # Support for 32-bit serial number
        serial = device.reg32[0xF070:0xF080:4]
        serial_number = int.from_bytes(serial[:4], 'little')
    print(f'Serial number: {serial_number})')
    # Read ROC revision register 0x8124
    fw_version = device.reg32[0x8124].to_bytes(4, 'little')
    print(f'ROC firmware version: {fw_version[1]}.{fw_version[0]}')
    # Read AMC revision register 0x108C
    fw_version = device.reg32[0x108C].to_bytes(4, 'little')
    print(f'AMC firmware version: {fw_version[1]}.{fw_version[0]}')

    # Check if we are using waveform recording firmware
    if fw_version[1] != 0x00:
        raise RuntimeError('This demo requires a waveform recording firmware.')

    # Dummy acquisition with a digitizer
    device.reg32[0xEF24] = 1        # Reset
    device.reg32[0x8100] |= 0x4     # Start Command
    device.reg32[0x8108] = 1        # Send SW trigger
    device.reg32[0x8100] &= ~0x4    # Stop Command

    # Read data from the digitizer
    res = device.blt_read(0x0000, 256)
    print(f'Size of data read: {len(res.data)} bytes')
    print(f'Terminated: {res.terminated}')
    print(res.data)

    device.reg32[0xEF24] = 1        # Reset
