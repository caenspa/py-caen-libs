#!/usr/bin/env python3
"""
Python demo for CAEN Digitizer


The demo aims to show users how to work with the CAENDigitizer library in Python.
It performs a dummy acquisition using a CAEN Digitizer.
Once connected to the device, the acquisition starts, a software trigger is sent,
and the data are read after stopping the acquisition.
"""

__author__ = 'Giovanni Cerretani'
__copyright__ = 'Copyright (C) 2025 CAEN SpA'
__license__ = 'MIT-0'
# SPDX-License-Identifier: MIT-0
__contact__ = 'https://www.caen.it/'

from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from functools import partial

import matplotlib.pyplot as plt
import numpy as np

from caen_libs import caendigitizer as dgtz


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

plt.title('CAEN Digitizer Python demo')
plt.xlabel('Samples')
plt.ylabel('ADC counts')

with dgtz.Device.open(dgtz.ConnectionType[args.connectiontype], args.linknumber, args.conetnode, args.vmebaseaddress) as device:

    device.reset()

    info = device.get_info()
    print('Connected with Digitizer')
    print(f'  Model Name:        {info.model_name}')
    print(f'  Serial Number:     {info.serial_number}')
    print(f'  Firmware Code:     {info.firmware_code.name}')

    match info.firmware_code:
        case dgtz.FirmwareCode.STANDARD_FW:
            device.set_record_length(4096)
            device.set_channel_enable_mask(0xFF)
            device.set_channel_trigger_threshold(0, 32768)
            device.set_channel_self_trigger(0, dgtz.TriggerMode.ACQ_ONLY)
            device.set_sw_trigger_mode(dgtz.TriggerMode.ACQ_ONLY)
            device.set_max_num_events_blt(3)
            device.set_acquisition_mode(dgtz.AcqMode.SW_CONTROLLED)

            device.malloc_readout_buffer()
            device.allocate_event()

            device.sw_start_acquisition()
            device.send_sw_trigger()
            device.read_data(dgtz.ReadMode.SLAVE_TERMINATED_READOUT_MBLT)
            for i in range(device.get_num_events()):
                evt_info, buffer = device.get_event_info(i)
                evt = device.decode_event(buffer)  # Ignore result, same of evt
                for ch in range(info.channels):
                    plt.plot(evt.data_channel[ch].copy(), label=f'Ch{ch}')
            device.sw_stop_acquisition()

        case dgtz.FirmwareCode.V1730_DPP_PSD:
            device.set_dpp_acquisition_mode(dgtz.DPPAcqMode.MIXED, dgtz.DPPSaveParam.ENERGY_AND_TIME)
            device.set_acquisition_mode(dgtz.AcqMode.SW_CONTROLLED)
            device.set_io_level(dgtz.IOLevel.TTL)
            device.set_ext_trigger_input_mode(dgtz.TriggerMode.ACQ_ONLY)
            device.set_channel_enable_mask(0xFF)
            device.set_dpp_event_aggregation(0, 0)
            device.set_run_synchronization_mode(dgtz.RunSyncMode.DISABLED)
            for i in range(info.channels):
                if i % 2 == 0:
                    device.set_record_length(1024, i)
                device.set_channel_dc_offset(i, 0x8000)
                device.set_dpp_pre_trigger_size(i, 80)
                device.set_channel_pulse_polarity(i, dgtz.PulsePolarity.POSITIVE)

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

            device.malloc_readout_buffer()
            device.malloc_dpp_events()
            device.malloc_dpp_waveforms()

            device.sw_start_acquisition()
            device.send_sw_trigger()
            device.read_data(dgtz.ReadMode.SLAVE_TERMINATED_READOUT_MBLT)
            for ch_idx, ch in enumerate(device.get_dpp_events()):
                for evt_idx, evt in enumerate(ch):
                    w = device.decode_dpp_waveforms(ch_idx, evt_idx)
                    plt.plot(w.trace1, label=f'Ch{ch_idx}')
            device.sw_stop_acquisition()

        case dgtz.FirmwareCode.V1730_DPP_PHA:
            device.set_dpp_acquisition_mode(dgtz.DPPAcqMode.MIXED, dgtz.DPPSaveParam.ENERGY_AND_TIME)
            device.set_acquisition_mode(dgtz.AcqMode.SW_CONTROLLED)
            device.set_io_level(dgtz.IOLevel.TTL)
            device.set_ext_trigger_input_mode(dgtz.TriggerMode.ACQ_ONLY)
            device.set_channel_enable_mask(0xFF)
            device.set_dpp_event_aggregation(0, 0)
            device.set_run_synchronization_mode(dgtz.RunSyncMode.DISABLED)
            for i in range(info.channels):
                if i % 2 == 0:
                    device.set_record_length(1024, i)
                device.set_channel_dc_offset(i, 0x8000)
                device.set_dpp_pre_trigger_size(i, 80)
                device.set_channel_pulse_polarity(i, dgtz.PulsePolarity.POSITIVE)

            dpp_params = dgtz.DPPPHAParams()
            dpp_params.resize(info.channels)
            for ch in range(info.channels):
                dpp_params.thr[ch] = 100
                dpp_params.k[ch] = 3000
                dpp_params.m[ch] = 900
                dpp_params.m_[ch] = 50000
                dpp_params.ftd[ch] = 500
                dpp_params.a[ch] = 4
                dpp_params.b[ch] = 200
                dpp_params.trgho[ch] = 1200
                dpp_params.nsbl[ch] = 4
                dpp_params.nspk[ch] = 0
                dpp_params.pkho[ch] = 2000
                dpp_params.blho[ch] = 500
                dpp_params.enf[ch] = 1.0
                dpp_params.decimation[ch] = 0
                dpp_params.dgain[ch] = 0
                dpp_params.otrej[ch] = 0
                dpp_params.trgwin[ch] = 0
                dpp_params.twwdt[ch] = 100
            device.set_dpp_parameters(0xff, dpp_params)

            device.malloc_readout_buffer()
            device.malloc_dpp_events()
            device.malloc_dpp_waveforms()

            device.sw_start_acquisition()
            device.send_sw_trigger()
            device.read_data(dgtz.ReadMode.SLAVE_TERMINATED_READOUT_MBLT)
            for ch_idx, ch in enumerate(device.get_dpp_events()):
                for evt_idx, evt in enumerate(ch):
                    w = device.decode_dpp_waveforms(ch_idx, evt_idx)
                    plt.plot(w.trace1, label=f'Ch{ch_idx}')
            device.sw_stop_acquisition()

        case dgtz.FirmwareCode.V1730_DPP_ZLE:
            RECORD_LENGTH = 4096
            # ZLE firmware demo: basic configuration and acquisition
            device.set_acquisition_mode(dgtz.AcqMode.SW_CONTROLLED)
            device.set_io_level(dgtz.IOLevel.TTL)
            device.set_ext_trigger_input_mode(dgtz.TriggerMode.ACQ_ONLY)
            device.set_channel_enable_mask(0xFF)
            device.set_run_synchronization_mode(dgtz.RunSyncMode.DISABLED)
            device.set_record_length(RECORD_LENGTH // 4)
            device.set_max_num_events_blt(1)
            for i in range(info.channels):
                device.set_channel_dc_offset(i, 0x8000)
                device.set_channel_pulse_polarity(i, dgtz.PulsePolarity.POSITIVE)
                # Dummy configuration, just to see some waveforms
                device.registers[0x1054 | (i << 8)] = 4  # Pre-Samples
                device.registers[0x1058 | (i << 8)] = 4  # Post-Samples
                device.registers[0x105C | (i << 8)] = 5  # Data Threshold
                device.registers[0x1060 | (i << 8)] = 5  # Trigger Threshold

            device.malloc_readout_buffer()
            device.malloc_zle_events_and_waveforms()

            device.sw_start_acquisition()
            device.send_sw_trigger()
            device.read_data(dgtz.ReadMode.SLAVE_TERMINATED_READOUT_MBLT)
            full_indexes = np.arange(RECORD_LENGTH)
            for idx, evt in enumerate(device.get_zle_events()):
                device.decode_zle_waveforms(idx)
                for ch_idx, ch in enumerate(evt.channel):
                    if ch is not None:
                        w = ch.waveforms
                        full_values = np.full_like(full_indexes, ch.baseline, dtype=w.trace.dtype)
                        np.put(full_values, w.trace_index, w.trace)
                        plt.plot(full_indexes, full_values, label=f'Ch{ch_idx}')
            device.sw_stop_acquisition()

        case _:
            raise NotImplementedError(f'Firmware {info.firmware_code.name} not supported by this demo')

plt.legend()
plt.show()
