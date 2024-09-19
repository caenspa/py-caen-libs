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
from caen_libs import caencomm as comm


def hex_int(x: str):
    """Trick to make ArgumentParser support hex"""
    return int(x, 16)

# Parse arguments
parser = ArgumentParser(
    description=__doc__,
    formatter_class=ArgumentDefaultsHelpFormatter,
)

# Shared parser for subcommands
parser.add_argument('-c', '--connectiontype', type=str, help='connection type', required=True, choices=tuple(i.name for i in comm.ConnectionType))
parser.add_argument('-l', '--linknumber', type=str, help='link number, PID or hostname (depending on connectiontype)', required=True)
parser.add_argument('-n', '--conetnode', type=int, help='CONET node', default=0)
parser.add_argument('-b', '--vmebaseaddress', type=hex_int, help='VME base address (as hex)', default=0)

args = parser.parse_args()

print('------------------------------------------------------------------------------------')
print(f'CAEN Comm binding loaded (lib version {comm.lib.sw_release()})')
print('------------------------------------------------------------------------------------')

with comm.Device.open(comm.ConnectionType[args.connectiontype], args.linknumber, args.conetnode, args.vmebaseaddress) as device:

    # Assuming to be connected to a CAEN Digitizer 1.0
    serial = device.reg32[0xF080:0xF088:4]
    serial_number = (serial[0] << 8) | serial[1]
    if serial_number == 0xFFFF:
        # Support for 32-bit serial number
        serial = device.reg32[0xF070:0xF080:4]
        serial_number = (serial[3] << 24) | (serial[2] << 16) | (serial[1] << 8) | serial[0]
    print(f'Connected with Digitizer {serial_number}')
    # Read ROC revision register 0x8124
    fw_version = device.reg32[0x8124].to_bytes(4, 'little')
    print(f'ROC firmware version {fw_version[1]}.{fw_version[0]}')
    # Read AMC revision register 0x108C
    fw_version = device.reg32[0x108C].to_bytes(4, 'little')
    print(f'AMC firmware version {fw_version[1]}.{fw_version[0]}')

    # Check if we are using waveform recording firmware
    assert fw_version[1] == 0x00, 'This demo requires a waveform recording firmware.'

    # Dummy acquisition with a digitizer
    device.reg32[0xEF24] = 1        # Reset
    device.reg32[0x8100] |= 0x4     # Start Command
    device.reg32[0x8108] = 1        # Send SW trigger
    device.reg32[0x8100] &= ~0x4    # Stop Command

    # Read data from the digitizer
    buffer = device.blt_read(0x0000, 256)
    print(f'Size of data read: {len(buffer)} bytes')
    print(buffer)

    device.reg32[0xEF24] = 1            # Reset

print('Bye bye')
