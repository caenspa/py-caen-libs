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
from contextlib import contextmanager
from dataclasses import dataclass, field
from functools import partial
from time import sleep

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


@dataclass
class Tests:
    """Tests for different firmwares"""

    device: dgtz.Device
    __info: dgtz.BoardInfo = field(init=False)

    def __post_init__(self):
        self.__info = self.device.get_info()
        print('Connected with Digitizer')
        print(f'  Model Name:        {self.__info.model_name}')
        print(f'  Family Code:       {self.__info.family_code.name}')
        print(f'  Serial Number:     {self.__info.serial_number}')
        print(f'  Firmware Code:     {self.__info.firmware_code.name}')

    def run(self):
        """
        Run the test for the detected firmware.

        Not all firmwares are supported by this demo.
        """
        match self.__info.firmware_code, self.__info.family_code:
            case dgtz.FirmwareCode.STANDARD_FW, _:
                self._test_standard_fw()
            case dgtz.FirmwareCode.STANDARD_FW_X742, dgtz.BoardFamilyCode.XX742:
                self._test_standard_fw_x742()
            case dgtz.FirmwareCode.V1720_DPP_CI, dgtz.BoardFamilyCode.XX720:
                self._test_dpp_ci_x720()
            case dgtz.FirmwareCode.V1720_DPP_PSD, dgtz.BoardFamilyCode.XX720:
                self._test_dpp_psd_x720()
            case dgtz.FirmwareCode.V1730_DPP_PSD, dgtz.BoardFamilyCode.XX725 | dgtz.BoardFamilyCode.XX730:
                self._test_dpp_psd_x730()
            case dgtz.FirmwareCode.V1751_DPP_PSD, dgtz.BoardFamilyCode.XX751:
                self._test_dpp_psd_x751()
            case dgtz.FirmwareCode.V1724_DPP_PHA, dgtz.BoardFamilyCode.XX724 | dgtz.BoardFamilyCode.XX781:
                self._test_dpp_pha_x724()
            case dgtz.FirmwareCode.V1730_DPP_PHA, dgtz.BoardFamilyCode.XX725 | dgtz.BoardFamilyCode.XX730:
                self._test_dpp_pha_x730()
            case dgtz.FirmwareCode.V1730_DPP_DAW, dgtz.BoardFamilyCode.XX725 | dgtz.BoardFamilyCode.XX730:
                self._test_dpp_daw_x730()
            case dgtz.FirmwareCode.V1730_DPP_ZLE, dgtz.BoardFamilyCode.XX725 | dgtz.BoardFamilyCode.XX730:
                self._test_dpp_zle_x730()
            case _:
                raise NotImplementedError(f'Firmware {self.__info.firmware_code.name} not supported by this demo')

    @contextmanager
    def _start_acquisition(self):
        self.device.sw_start_acquisition()
        try:
            yield
        finally:
            self.device.sw_stop_acquisition()

    def _run_standard_fw_readout(self):
        self.device.malloc_readout_buffer()
        self.device.allocate_event()
        with self._start_acquisition():
            self.device.send_sw_trigger()
            self.device.read_data(dgtz.ReadMode.SLAVE_TERMINATED_READOUT_MBLT)
            for i in range(self.device.get_num_events()):
                evt_info, buffer = self.device.get_event_info(i)
                evt = self.device.decode_event(buffer)
                for ch in range(self.__info.channels):
                    plt.plot(evt.data_channel[ch], label=f'Ch{ch}')

    def _run_standard_fw_x742_readout(self):
        self.device.malloc_readout_buffer()
        self.device.allocate_event()
        with self._start_acquisition():
            self.device.send_sw_trigger()
            sleep(0.1)
            self.device.read_data(dgtz.ReadMode.SLAVE_TERMINATED_READOUT_MBLT)
            for i in range(self.device.get_num_events()):
                evt_info, buffer = self.device.get_event_info(i)
                evt = self.device.decode_event(buffer)
                assert isinstance(evt, dgtz.X742Event)
                for gr_idx, group in enumerate(evt.data_group):
                    if group is not None:
                        # Each group has 8 data channels + 1 fast trigger channel
                        for ch_idx, ch_data in enumerate(group.data_channel):  # 0-7: data channels, 8: fast trigger
                            if ch_data is not None and len(ch_data) > 0:
                                label = f'Gr{gr_idx}_TR' if ch_idx == 8 else f'Ch{gr_idx * 8 + ch_idx}'
                                plt.plot(ch_data, label=label)

    def _run_dpp_ci_readout(self):
        self.device.malloc_readout_buffer()
        self.device.malloc_dpp_events()
        self.device.malloc_dpp_waveforms()
        with self._start_acquisition():
            self.device.send_sw_trigger()
            self.device.read_data(dgtz.ReadMode.SLAVE_TERMINATED_READOUT_MBLT)
            for ch_idx, ch in enumerate(self.device.get_dpp_events()):
                for evt_idx, evt in enumerate(ch):
                    assert isinstance(evt, dgtz.DPPCIEvent)
                    w = self.device.decode_dpp_waveforms(ch_idx, evt_idx)
                    assert isinstance(w, dgtz.DPPCIWaveforms)
                    plt.plot(w.trace1, label=f'Ch{ch_idx}')

    def _run_dpp_psd_readout(self):
        self.device.malloc_readout_buffer()
        self.device.malloc_dpp_events()
        self.device.malloc_dpp_waveforms()
        with self._start_acquisition():
            self.device.send_sw_trigger()
            self.device.read_data(dgtz.ReadMode.SLAVE_TERMINATED_READOUT_MBLT)
            for ch_idx, ch in enumerate(self.device.get_dpp_events()):
                for evt_idx, evt in enumerate(ch):
                    assert isinstance(evt, dgtz.DPPPSDEvent)
                    w = self.device.decode_dpp_waveforms(ch_idx, evt_idx)
                    assert isinstance(w, dgtz.DPPPSDWaveforms)
                    plt.plot(w.trace1, label=f'Ch{ch_idx}')

    def _run_dpp_pha_readout(self):
        self.device.malloc_readout_buffer()
        self.device.malloc_dpp_events()
        self.device.malloc_dpp_waveforms()
        with self._start_acquisition():
            self.device.send_sw_trigger()
            self.device.read_data(dgtz.ReadMode.SLAVE_TERMINATED_READOUT_MBLT)
            for ch_idx, ch in enumerate(self.device.get_dpp_events()):
                for evt_idx, evt in enumerate(ch):
                    assert isinstance(evt, dgtz.DPPPHAEvent)
                    w = self.device.decode_dpp_waveforms(ch_idx, evt_idx)
                    assert isinstance(w, dgtz.DPPPHAWaveforms)
                    plt.plot(w.trace1, label=f'Ch{ch_idx}')

    def _run_dpp_daw_readout(self):
        self.device.malloc_readout_buffer()
        self.device.malloc_daw_events_and_waveforms()
        with self._start_acquisition():
            self.device.send_sw_trigger()
            self.device.read_data(dgtz.ReadMode.SLAVE_TERMINATED_READOUT_MBLT)
            for idx, evt in enumerate(self.device.get_daw_events()):
                assert isinstance(evt, dgtz.DPPDAWEvent)
                self.device.decode_daw_waveforms(idx)
                for ch_idx, ch in enumerate(evt.channel):
                    if ch is not None:
                        plt.plot(ch.waveforms.trace, label=f'Ch{ch_idx} (timetag={ch.time_stamp})')

    def _run_dpp_zle_readout(self, record_length: int):
        self.device.malloc_readout_buffer()
        self.device.malloc_zle_events_and_waveforms()
        with self._start_acquisition():
            self.device.send_sw_trigger()
            self.device.read_data(dgtz.ReadMode.SLAVE_TERMINATED_READOUT_MBLT)
            full_indexes = np.arange(record_length)
            for idx, evt in enumerate(self.device.get_zle_events()):
                assert isinstance(evt, dgtz.ZLEEvent730)
                self.device.decode_zle_waveforms(idx)
                for ch_idx, ch in enumerate(evt.channel):
                    if ch is not None:
                        w = ch.waveforms
                        full_values = np.full_like(full_indexes, ch.baseline, dtype=w.trace.dtype)
                        np.put(full_values, w.trace_index, w.trace)
                        plt.plot(full_indexes, full_values, label=f'Ch{ch_idx}')

    def _test_standard_fw(self):
        ch_mask = (1 << self.__info.channels) - 1
        self.device.set_record_length(4096)
        self.device.set_channel_enable_mask(ch_mask)
        self.device.set_channel_trigger_threshold(0, 32768)
        self.device.set_channel_self_trigger(dgtz.TriggerMode.ACQ_ONLY, ch_mask)
        self.device.set_sw_trigger_mode(dgtz.TriggerMode.ACQ_ONLY)
        self.device.set_max_num_events_blt(1)
        self.device.set_acquisition_mode(dgtz.AcqMode.SW_CONTROLLED)

        self._run_standard_fw_readout()

    def _test_standard_fw_x742(self):
        groups = self.__info.channels
        channels = groups * 8
        group_mask = (1 << groups) - 1
        self.device.set_group_enable_mask(group_mask)
        self.device.set_record_length(1024)
        self.device.set_post_trigger_size(50)
        self.device.set_fast_trigger_digitizing(dgtz.EnaDis.ENABLE)
        self.device.set_fast_trigger_mode(dgtz.TriggerMode.ACQ_ONLY)
        self.device.set_max_num_events_blt(1024)
        self.device.set_ext_trigger_input_mode(dgtz.TriggerMode.ACQ_ONLY)
        self.device.set_acquisition_mode(dgtz.AcqMode.SW_CONTROLLED)
        for ch in range(channels):
            self.device.set_channel_dc_offset(ch, 0x8000)
        self.device.set_drs4_sampling_frequency(dgtz.DRS4Frequency.F_5GHz)
        for gr in range(groups):
            self.device.set_group_fast_trigger_dc_offset(gr, 32768)
            self.device.set_group_fast_trigger_threshold(gr, 20934)
        self.device.load_drs4_correction_data(dgtz.DRS4Frequency.F_5GHz)
        self.device.enable_drs4_correction()

        self._run_standard_fw_x742_readout()

    def _test_dpp_ci_x720(self):
        ch_mask = (1 << self.__info.channels) - 1
        self.device.set_dpp_acquisition_mode(dgtz.DPPAcqMode.MIXED, dgtz.DPPSaveParam.ENERGY_AND_TIME)
        self.device.set_acquisition_mode(dgtz.AcqMode.SW_CONTROLLED)
        self.device.set_record_length(300)
        self.device.set_io_level(dgtz.IOLevel.TTL)
        self.device.set_ext_trigger_input_mode(dgtz.TriggerMode.ACQ_ONLY)
        self.device.set_channel_enable_mask(ch_mask)
        self.device.set_dpp_event_aggregation(0, 0)
        self.device.set_run_synchronization_mode(dgtz.RunSyncMode.DISABLED)
        # Set pre-trigger size for CI (common to all channels, use -1)
        self.device.set_dpp_pre_trigger_size(-1, 80)
        for i in range(self.__info.channels):
            self.device.set_channel_dc_offset(i, 0x8000)
            self.device.set_channel_pulse_polarity(i, dgtz.PulsePolarity.NEGATIVE)

        dpp_params = dgtz.DPPCIParams()
        dpp_params.resize(self.__info.channels)
        for par_ch in dpp_params.ch:
            par_ch.thr = 100
            par_ch.nsbl = 2
            par_ch.gate = 200
            par_ch.pgate = 25
            par_ch.selft = True
            par_ch.trgc = dgtz.DPPTriggerConfig.PEAK
            par_ch.tvaw = 50
        dpp_params.blthr = 3
        dpp_params.bltmo = 100
        dpp_params.trgho = 0
        self.device.set_dpp_parameters(ch_mask, dpp_params)

        self._run_dpp_ci_readout()

    def _test_dpp_psd_x720(self):
        ch_mask = (1 << self.__info.channels) - 1
        self.device.set_dpp_acquisition_mode(dgtz.DPPAcqMode.MIXED, dgtz.DPPSaveParam.ENERGY_AND_TIME)
        self.device.set_acquisition_mode(dgtz.AcqMode.SW_CONTROLLED)
        self.device.set_io_level(dgtz.IOLevel.TTL)
        self.device.set_ext_trigger_input_mode(dgtz.TriggerMode.ACQ_ONLY)
        self.device.set_channel_enable_mask(ch_mask)
        self.device.set_dpp_event_aggregation(0, 0)
        self.device.set_run_synchronization_mode(dgtz.RunSyncMode.DISABLED)
        for i in range(self.__info.channels):
            self.device.set_record_length(12, i)
            self.device.set_channel_dc_offset(i, 0x8000)
            self.device.set_dpp_pre_trigger_size(i, 80)
            self.device.set_channel_pulse_polarity(i, dgtz.PulsePolarity.NEGATIVE)

        dpp_params = dgtz.DPPPSDParams()
        dpp_params.resize(self.__info.channels)
        for par_ch in dpp_params.ch:
            par_ch.thr = 50
            par_ch.nsbl = 2
            par_ch.lgate = 32
            par_ch.sgate = 24
            par_ch.pgate = 8
            par_ch.selft = True
            par_ch.trgc = dgtz.DPPTriggerConfig.THRESHOLD
            par_ch.tvaw = 50
            par_ch.csens = 0
        dpp_params.purh = dgtz.DPPPUR.DETECT_ONLY
        dpp_params.purgap = 100
        dpp_params.blthr = 3
        dpp_params.trgho = 8
        self.device.set_dpp_parameters(ch_mask, dpp_params)

        self._run_dpp_psd_readout()

    def _test_dpp_psd_x730(self):
        ch_mask = (1 << self.__info.channels) - 1
        self.device.set_dpp_acquisition_mode(dgtz.DPPAcqMode.MIXED, dgtz.DPPSaveParam.ENERGY_AND_TIME)
        self.device.set_acquisition_mode(dgtz.AcqMode.SW_CONTROLLED)
        self.device.set_io_level(dgtz.IOLevel.TTL)
        self.device.set_ext_trigger_input_mode(dgtz.TriggerMode.ACQ_ONLY)
        self.device.set_channel_enable_mask(ch_mask)
        self.device.set_dpp_event_aggregation(0, 0)
        self.device.set_run_synchronization_mode(dgtz.RunSyncMode.DISABLED)
        for i in range(self.__info.channels):
            if i % 2 == 0:
                self.device.set_record_length(1024, i)
            self.device.set_channel_dc_offset(i, 0x8000)
            self.device.set_dpp_pre_trigger_size(i, 80)
            self.device.set_channel_pulse_polarity(i, dgtz.PulsePolarity.POSITIVE)

        dpp_params = dgtz.DPPPSDParams()
        dpp_params.resize(self.__info.channels)
        for par_ch in dpp_params.ch:
            par_ch.thr = 50
            par_ch.nsbl = 2
            par_ch.lgate = 32
            par_ch.sgate = 24
            par_ch.pgate = 8
            par_ch.selft = True
            par_ch.trgc = dgtz.DPPTriggerConfig.THRESHOLD
            par_ch.tvaw = 50
            par_ch.csens = 0
        self.device.set_dpp_parameters(ch_mask, dpp_params)

        self._run_dpp_psd_readout()

    def _test_dpp_psd_x751(self):
        ch_mask = (1 << self.__info.channels) - 1
        self.device.set_dpp_acquisition_mode(dgtz.DPPAcqMode.MIXED, dgtz.DPPSaveParam.ENERGY_AND_TIME)
        self.device.set_acquisition_mode(dgtz.AcqMode.SW_CONTROLLED)
        self.device.set_io_level(dgtz.IOLevel.TTL)
        self.device.set_ext_trigger_input_mode(dgtz.TriggerMode.ACQ_ONLY)
        self.device.set_channel_enable_mask(ch_mask)
        self.device.set_dpp_event_aggregation(0, 0)
        self.device.set_run_synchronization_mode(dgtz.RunSyncMode.DISABLED)
        for i in range(self.__info.channels):
            self.device.set_record_length(360, i)
            self.device.set_channel_dc_offset(i, 0x8000)
            self.device.set_dpp_pre_trigger_size(i, 80)
            self.device.set_channel_pulse_polarity(i, dgtz.PulsePolarity.NEGATIVE)

        dpp_params = dgtz.DPPPSDParams()
        dpp_params.resize(self.__info.channels)
        for par_ch in dpp_params.ch:
            par_ch.thr = 50
            par_ch.nsbl = 1
            par_ch.lgate = 200
            par_ch.sgate = 24
            par_ch.pgate = 8
            par_ch.selft = True
            par_ch.trgc = dgtz.DPPTriggerConfig.THRESHOLD
            par_ch.tvaw = 50
            par_ch.csens = 0
        dpp_params.purh = dgtz.DPPPUR.DETECT_ONLY
        dpp_params.blthr = 3
        dpp_params.trgho = 8
        self.device.set_dpp_parameters(ch_mask, dpp_params)

        self._run_dpp_psd_readout()

    def _test_dpp_pha_x724(self):
        ch_mask = (1 << self.__info.channels) - 1
        self.device.registers[0x8000] |= 0x01000100  # Force bit 8 and 24 to 1 (see manual)
        self.device.set_dpp_acquisition_mode(dgtz.DPPAcqMode.MIXED, dgtz.DPPSaveParam.ENERGY_AND_TIME)
        self.device.set_acquisition_mode(dgtz.AcqMode.SW_CONTROLLED)
        self.device.set_record_length(4096)
        self.device.set_io_level(dgtz.IOLevel.TTL)
        self.device.set_ext_trigger_input_mode(dgtz.TriggerMode.ACQ_ONLY)
        self.device.set_channel_enable_mask(ch_mask)
        self.device.set_dpp_event_aggregation(0, 0)
        self.device.set_run_synchronization_mode(dgtz.RunSyncMode.DISABLED)
        for i in range(self.__info.channels):
            self.device.set_channel_dc_offset(i, 0x8000)
            self.device.set_dpp_pre_trigger_size(i, 512)
            self.device.set_channel_pulse_polarity(i, dgtz.PulsePolarity.POSITIVE)

        dpp_params = dgtz.DPPPHAParams()
        dpp_params.resize(self.__info.channels)
        for ch in dpp_params.ch:
            ch.thr = 100
            ch.k = 2000
            ch.m = 1000
            ch.m_ = 50000
            ch.ftd = 800
            ch.a = 4
            ch.b = 200
            ch.trgho = 1200
            ch.nsbl = 4
            ch.nspk = 0
            ch.pkho = 2000
            ch.blho = 500
            ch.enf = 1.0
            ch.decimation = 0
            ch.dgain = 0
            ch.otrej = 0
            ch.trgwin = 0
            ch.twwdt = 0
        self.device.set_dpp_parameters(ch_mask, dpp_params)

        self._run_dpp_pha_readout()

    def _test_dpp_pha_x730(self):
        ch_mask = (1 << self.__info.channels) - 1
        self.device.set_dpp_acquisition_mode(dgtz.DPPAcqMode.MIXED, dgtz.DPPSaveParam.ENERGY_AND_TIME)
        self.device.set_acquisition_mode(dgtz.AcqMode.SW_CONTROLLED)
        self.device.set_io_level(dgtz.IOLevel.TTL)
        self.device.set_ext_trigger_input_mode(dgtz.TriggerMode.ACQ_ONLY)
        self.device.set_channel_enable_mask(ch_mask)
        self.device.set_dpp_event_aggregation(0, 0)
        self.device.set_run_synchronization_mode(dgtz.RunSyncMode.DISABLED)
        for i in range(self.__info.channels):
            if i % 2 == 0:
                self.device.set_record_length(1024, i)
            self.device.set_channel_dc_offset(i, 0x8000)
            self.device.set_dpp_pre_trigger_size(i, 80)
            self.device.set_channel_pulse_polarity(i, dgtz.PulsePolarity.POSITIVE)

        dpp_params = dgtz.DPPPHAParams()
        dpp_params.resize(self.__info.channels)
        for par_ch in dpp_params.ch:
            par_ch.thr = 100
            par_ch.k = 3000
            par_ch.m = 900
            par_ch.m_ = 50000
            par_ch.ftd = 500
            par_ch.a = 4
            par_ch.b = 200
            par_ch.trgho = 1200
            par_ch.nsbl = 4
            par_ch.nspk = 0
            par_ch.pkho = 2000
            par_ch.blho = 500
            par_ch.enf = 1.0
            par_ch.decimation = 0
            par_ch.dgain = 0
            par_ch.otrej = 0
            par_ch.trgwin = 0
            par_ch.twwdt = 100
        self.device.set_dpp_parameters(ch_mask, dpp_params)

        self._run_dpp_pha_readout()

    def _test_dpp_daw_x730(self):
        self.device.set_acquisition_mode(dgtz.AcqMode.SW_CONTROLLED)
        self.device.set_io_level(dgtz.IOLevel.TTL)
        self.device.set_ext_trigger_input_mode(dgtz.TriggerMode.ACQ_ONLY)
        self.device.set_channel_enable_mask((1 << self.__info.channels) - 1)
        self.device.set_run_synchronization_mode(dgtz.RunSyncMode.DISABLED)
        self.device.set_record_length(1024)  # 1 LSB == 5 samples (minimum record length)
        self.device.set_max_num_events_blt(1)
        for i in range(self.__info.channels):
            self.device.set_channel_dc_offset(i, 0x8000)
            self.device.set_channel_pulse_polarity(i, dgtz.PulsePolarity.POSITIVE)
            # Dummy configuration, just to see some waveforms
            self.device.registers[0x1060 | (i << 8)] = 50  # Trigger Threshold
            self.device.registers[0x1080 | (i << 8)] |= 0x00100000  # Automatic baseline
            self.device.registers[0x1080 | (i << 8)] |= 0x01000000  # Disable self trigger (only SW trigger)
            self.device.registers[0x107C | (i << 8)] = 4096  # Max-Tail
            self.device.registers[0x1078 | (i << 8)] = 1024  # Look-Ahead window

        self._run_dpp_daw_readout()

    def _test_dpp_zle_x730(self):
        record_length = 4096
        # ZLE firmware demo: basic configuration and acquisition
        self.device.set_acquisition_mode(dgtz.AcqMode.SW_CONTROLLED)
        self.device.set_io_level(dgtz.IOLevel.TTL)
        self.device.set_ext_trigger_input_mode(dgtz.TriggerMode.ACQ_ONLY)
        self.device.set_channel_enable_mask((1 << self.__info.channels) - 1)
        self.device.set_run_synchronization_mode(dgtz.RunSyncMode.DISABLED)
        self.device.set_record_length(record_length // 4)  # 1 LSB == 4 samples
        self.device.set_max_num_events_blt(1)
        for i in range(self.__info.channels):
            self.device.set_channel_dc_offset(i, 0x8000)
            self.device.set_channel_pulse_polarity(i, dgtz.PulsePolarity.POSITIVE)
            # Dummy configuration, just to see some waveforms
            self.device.registers[0x1054 | (i << 8)] = 4  # Pre-Samples
            self.device.registers[0x1058 | (i << 8)] = 4  # Post-Samples
            self.device.registers[0x105C | (i << 8)] = 5  # Data Threshold
            self.device.registers[0x1060 | (i << 8)] = 5  # Trigger Threshold

        self._run_dpp_zle_readout(record_length)


plt.title('CAEN Digitizer Python demo')
plt.xlabel('Samples')
plt.ylabel('ADC counts')


connection_type = dgtz.ConnectionType[args.connectiontype]
link_number = args.linknumber
conet_node = args.conetnode
vme_base_address = args.vmebaseaddress

with dgtz.Device.open(connection_type, link_number, conet_node, vme_base_address) as device:

    device.reset()

    test = Tests(device)
    test.run()

plt.legend()
plt.show()
