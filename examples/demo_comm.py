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
    serial_byte_1 = device.read32(0xF080) & 0xFF
    serial_byte_0 = device.read32(0xF080) & 0xFF
    serial_number = (serial_byte_1 << 8) | serial_byte_0
    print(f'Connected with Digitizer {serial_number}')
    # Read ROC revision register 0x8124
    fw_version = device.read32(0x8124)
    ROC_fw_revision_major = (fw_version & 0xFF00) >> 8
    ROC_fw_revision_minor = fw_version & 0xFF
    print(f'ROC firmware version {ROC_fw_revision_major}.{ROC_fw_revision_minor}')
    # Read AMC revision register 0x108C
    fw_version = device.read32(0x108C)
    AMC_fw_revision_major = (fw_version & 0xFF00) >> 8
    AMC_fw_revision_minor = fw_version & 0xFF
    print(f'AMC firmware version {AMC_fw_revision_major}.{AMC_fw_revision_minor}')

    # Dummy acquisition with a digitizer
    # Reset
    data = 1
    device.write32(0xEF24, data)

    # Start Command
    data = device.read32(0x8100)
    data |= 0x4
    device.write32(0x8100, data)

    # Send SW trigger
    data = 1
    device.write32(0x8108, data)

    # Stop Command
    data = device.read32(0x8100)
    data &= 0xFFFFFFF8
    device.write32(0x8100, data)

    # Read data from the digitizer
    buffer = device.blt_read(0x0, 256)
    print(f'Size of data read: {len(buffer)} bytes')
    print(buffer)

    # Reset
    data = 1
    device.write32((0xEF24), data)

print('Bye bye')
