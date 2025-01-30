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
from caen_libs import _caendpplib as dpp


def hex_int(x: str):
    """Trick to make ArgumentParser support hex"""
    return int(x, 16)

# Parse arguments
parser = ArgumentParser(
    description=__doc__,
    formatter_class=ArgumentDefaultsHelpFormatter,
)

# Shared parser for subcommands

args = parser.parse_args()

print('------------------------------------------------------------------------------------')
print('CAEN DPPLib binding loaded')
print('------------------------------------------------------------------------------------')

with dpp.Device.open() as device:
    pass

print('Bye bye')
