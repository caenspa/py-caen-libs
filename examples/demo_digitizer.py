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
from time import sleep
from caen_libs import _caendigitizer as dgtz


# Parse arguments
parser = ArgumentParser(
    description=__doc__,
    formatter_class=ArgumentDefaultsHelpFormatter,
)

# Shared parser for subcommands
parser.add_argument('-c', '--connectiontype', type=str, help='connection type', required=True, choices=tuple(i.name for i in dgtz.ConnectionType))
parser.add_argument('-l', '--linknumber', type=str, help='link number, PID or hostname (depending on connectiontype)', required=True)
parser.add_argument('-n', '--conetnode', type=int, help='CONET node', default=0)
parser.add_argument('-b', '--vmebaseaddress', type=partial(int, base=16), help='VME base address (as hex)', default=0)

args = parser.parse_args()

print('------------------------------------------------------------------------------------')
print(f'CAEN Comm binding loaded (lib version {dgtz.lib.sw_release()})')
print('------------------------------------------------------------------------------------')

with dgtz.Device.open(dgtz.ConnectionType[args.connectiontype], args.linknumber, args.conetnode, args.vmebaseaddress) as device:

    print('Connected with Digitizer')
    info = device.get_info()

    device.reset()

    device.set_dpp_acquisition_mode(dgtz.DPPAcqMode.MIXED, dgtz.DPPSaveParam.ENERGY_AND_TIME)
    device.set_acquisition_mode(dgtz.AcqMode.SW_CONTROLLED)
    device.set_io_level(dgtz.IOLevel.TTL)
    device.set_ext_trigger_input_mode(dgtz.TriggerMode.ACQ_ONLY)
    device.set_channel_enable_mask(0xFF)
    device.set_dpp_event_aggregation(0, 0)
    device.set_run_synchronization_mode(dgtz.RunSyncMode.DISABLED)

    device.malloc_readout_buffer()
    device.malloc_dpp_events()
    device.malloc_dpp_waveforms()

    device.sw_start_acquisition()
    device.send_sw_trigger()
    device.read_data(dgtz.ReadMode.SLAVE_TERMINATED_READOUT_MBLT)
    for ch, ch_evt in enumerate(device.get_dpp_events()):
        for evt in ch_evt:
            print(f'Ch: {ch}\tEvent: {evt.time_tag}')
    device.sw_stop_acquisition()

    device.free_dpp_waveforms()
    device.free_dpp_events()
    device.free_readout_buffer()
