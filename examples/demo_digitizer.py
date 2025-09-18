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

import matplotlib.pyplot as plt

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
print(f'CAEN Digitizer binding loaded (lib version {dgtz.lib.sw_release()})')
print('------------------------------------------------------------------------------------')

with dgtz.Device.open(dgtz.ConnectionType[args.connectiontype], args.linknumber, args.conetnode, args.vmebaseaddress) as device:

    print('Connected with Digitizer')
    info = device.get_info()

    device.reset()

    match info.firmware_code:
        case dgtz.FirmwareCode.STANDARD_FW:
            device.set_record_length(4096)
            device.set_channel_enable_mask(0x1)
            device.set_channel_trigger_threshold(0, 32768)
            device.set_channel_self_trigger(0, dgtz.TriggerMode.ACQ_ONLY)
            device.set_sw_trigger_mode(dgtz.TriggerMode.ACQ_ONLY)
            device.set_max_num_events_blt(3)
            device.set_acquisition_mode(dgtz.AcqMode.SW_CONTROLLED)

            device.malloc_readout_buffer()
            device.sw_start_acquisition()
            device.send_sw_trigger()
            device.read_data(dgtz.ReadMode.SLAVE_TERMINATED_READOUT_MBLT)
            for i in range(device.get_num_events()):
                evt_info, buffer = device.get_event_info(i)
                evt = device.decode_event(buffer)
                plt.plot(evt.data_channel[0])
            device.sw_stop_acquisition()
            device.free_readout_buffer()

        case dgtz.FirmwareCode.V1730_DPP_PSD:
            device.set_dpp_acquisition_mode(dgtz.DPPAcqMode.MIXED, dgtz.DPPSaveParam.ENERGY_AND_TIME)
            device.set_acquisition_mode(dgtz.AcqMode.SW_CONTROLLED)
            device.set_io_level(dgtz.IOLevel.TTL)
            device.set_ext_trigger_input_mode(dgtz.TriggerMode.ACQ_ONLY)
            device.set_channel_enable_mask(0xFF)
            device.set_dpp_event_aggregation(0, 0)
            device.set_run_synchronization_mode(dgtz.RunSyncMode.DISABLED)

            dpp_params = dgtz.DPPPSDParams()
            dpp_params.resize(info.channels)
            for ch in range(info.channels):
                dpp_params.thr[ch] = 50
                dpp_params.nsbl[ch] = 2
                dpp_params.lgate[ch] = 32
                dpp_params.sgate[ch] = 24
                dpp_params.pgate[ch] = 8
                dpp_params.selft[ch] = 1
                dpp_params.trgc[ch] = dgtz.DPPTriggerConfig.THRESHOLD
                dpp_params.tvaw[ch] = 50
                dpp_params.csens[ch] = 0

            device.set_dpp_parameters(0xff, dpp_params)

            for i in range(info.channels):
                if i % 2 == 0:
                    device.set_record_length(1024, i)
                device.set_channel_dc_offset(i, 0x8000)
                device.set_dpp_pre_trigger_size(i, 80)
                device.set_channel_pulse_polarity(i, dgtz.PulsePolarity.POSITIVE)

            device.malloc_readout_buffer()
            device.malloc_dpp_events()
            device.malloc_dpp_waveforms()

            device.sw_start_acquisition()
            device.send_sw_trigger()
            device.read_data(dgtz.ReadMode.SLAVE_TERMINATED_READOUT_MBLT)
            for ch_idx, ch in enumerate(device.get_dpp_events()):
                for evt_idx, evt in enumerate(ch):
                    w = device.decode_dpp_waveforms(ch_idx, evt_idx)
                    plt.plot(w.trace1)
            device.sw_stop_acquisition()

            device.free_dpp_waveforms()
            device.free_dpp_events()
            device.free_readout_buffer()

plt.show()
