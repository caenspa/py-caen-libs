#!/usr/bin/env python3
"""
Python demo for CAEN DPP Library


The demo aims to show users how to work with the CAEN DPP Library in Python.
It performs a dummy acquisition using either a Digitizer with DPP-PHA
firmware or a GammaStream.
Please check carefully the parameters in the script before running it,
expecially those related to the HV channels.
"""

__author__ = 'Giovanni Cerretani'
__copyright__ = 'Copyright (C) 2024 CAEN SpA'
__license__ = 'MIT-0'
# SPDX-License-Identifier: MIT-0
__contact__ = 'https://www.caen.it/'

from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from functools import partial
from time import sleep

import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np

from caen_libs import caendpplib as dpp


# Parse arguments
parser = ArgumentParser(
    description=__doc__,
    formatter_class=ArgumentDefaultsHelpFormatter,
)

# Shared parser for subcommands
parser.add_argument('-c', '--connectiontype', type=str, help='connection type', required=True, choices=tuple(i.name for i in dpp.ConnectionType))
parser.add_argument('-l', '--linknumber', type=int, help='link number', default=0)
parser.add_argument('-n', '--conetnode', type=int, help='CONET node', default=0)
parser.add_argument('-b', '--vmebaseaddress', type=partial(int, base=16), help='VME base address (as hex)', default=0)
parser.add_argument('-a', '--ethaddress', type=str, help='ethernet address', default='')
parser.add_argument('-w', '--waveform', action='store_true', help='waveform mode')
parser.add_argument('-C', '--channel', type=int, help='reference channel', default=0)
parser.add_argument('-H', '--hvchannel', type=int, help='reference HV channel', default=0)

args = parser.parse_args()

print('------------------------------------------------------------------------------------')
print('CAEN DPPLib binding loaded')
print('------------------------------------------------------------------------------------')

print(f'Log path: {dpp.lib.log_path}')


def my_configuration(n_channels: int, adc_nbits: int) -> dpp.DgtzParams:
    """
    Generate a configuration for the digitizer.
    """

    max_adc = 2 ** adc_nbits - 1

    # Define configuration
    res = dpp.DgtzParams()

    # List mode parameters (ignored by GammaStream, see run_specifications below)
    res.list_params.enabled = False
    res.list_params.save_mode = dpp.ListSaveMode.FILE_BINARY
    res.list_params.file_name = 'py_dpplib_demo.bin'
    res.list_params.max_buff_num_events = 10
    res.list_params.save_mask = dpp.DumpMask.ALL_

    # Board configuration
    res.channel_mask = (0x1 << n_channels) - 1
    res.event_aggr = 0
    res.iolev = dpp.IOLevel.TTL

    # Waveform parameters
    res.wf_params.dual_trace_mode = 1
    res.wf_params.vp1 = dpp.VirtualProbe1.INPUT
    res.wf_params.vp2 = dpp.VirtualProbe2.TRAP_BL_CORR
    res.wf_params.dp1 = dpp.DigitalProbe1.PEAKING
    res.wf_params.dp2 = dpp.DigitalProbe2.TRIGGER
    res.wf_params.record_length = 1024
    res.wf_params.pre_trigger = 100
    res.wf_params.probe_self_trigger_val = 150
    res.wf_params.probe_trigger = dpp.ProbeTrigger.MAIN_TRIG

    # Parameters for Gamma Stream
    res.run_specifications.run_name = 'py_dpplib_demo'
    res.run_specifications.run_duration_sec = 0  # 0 means infinite
    res.run_specifications.cycles_count = 1
    res.run_specifications.save_lists = False

    res.resize(n_channels)

    # Channel parameters
    for i in range(n_channels):

        # Channel parameters
        res.dc_offset[i] = max_adc // 2
        res.pulse_polarity[i] = dpp.PulsePolarity.POSITIVE

        # Coicidence parameters between channels
        res.coinc_params[i].coinc_ch_mask = 0x0
        res.coinc_params[i].coinc_logic = dpp.CoincLogic.NONE
        res.coinc_params[i].coinc_op = dpp.CoincOp.OR
        res.coinc_params[i].maj_level = 0
        res.coinc_params[i].trg_win = 0

        # DPP parameters
        res.dpp_params.m_[i] = 50000
        res.dpp_params.m[i] = 1000
        res.dpp_params.k[i] = 3000
        res.dpp_params.ftd[i] = 800
        res.dpp_params.a[i] = 4
        res.dpp_params.b[i] = 200
        res.dpp_params.thr[i] = 50
        res.dpp_params.nsbl[i] = 3
        res.dpp_params.nspk[i] = 0
        res.dpp_params.pkho[i] = 0
        res.dpp_params.blho[i] = 1000
        res.dpp_params.dgain[i] = 0
        res.dpp_params.enf[i] = 1.0
        res.dpp_params.decimation[i] = 0
        res.dpp_params.trgho[i] = 1000

        # Reset Detector
        res.reset_detector[i].enabled = False
        res.reset_detector[i].reset_detection_mode = dpp.ResetDetectionMode.INTERNAL
        res.reset_detector[i].thrhold = 2
        res.reset_detector[i].reslenmin = 2
        res.reset_detector[i].reslength = 2000

        # Parameters for X770
        res.dpp_params.x770_extraparameters[i].cr_gain = 0
        res.dpp_params.x770_extraparameters[i].input_impedance = dpp.InputImpedance.O_1K
        res.dpp_params.x770_extraparameters[i].tr_gain = 0
        res.dpp_params.x770_extraparameters[i].saturation_holdoff = 300
        res.dpp_params.x770_extraparameters[i].energy_filter_mode = 0
        res.dpp_params.x770_extraparameters[i].trig_k = 30
        res.dpp_params.x770_extraparameters[i].trigm = 10
        res.dpp_params.x770_extraparameters[i].trig_mode = 0

        res.spectrum_control[i].spectrum_mode = dpp.SpectrumMode.ENERGY
        res.spectrum_control[i].time_scale = 1

    return res


def configure_hv(lib: dpp.Device, board_id: int, hv_ch: int) -> None:
    """
    Configure HV

    Note: GammaStream does not support ramp and power down mode.
    """
    print('Configuring HV...')
    hv_config = lib.get_hv_channel_configuration(board_id, hv_ch)
    hv_config.v_set = 650.
    hv_config.ramp_up = 10
    hv_config.ramp_down = 10
    hv_config.pw_down_mode = dpp.PWDownMode.KILL
    lib.set_hv_channel_configuration(board_id, hv_ch, hv_config)
    lib.set_hv_channel_vmax(board_id, hv_ch, hv_config.v_set * 1.1)
    print('Done.')


def enable_hv(lib: dpp.Device, board_id: int, hv_ch: int) -> None:
    """
    Power on HV

    Note: GammaStream does not support ramp and power down mode,
    and we cannot rely on lib.get_hv_channel_status to check if HV is
    ramped.
    """
    print('Powering on HV...')
    lib.set_hv_channel_power_on(board_id, hv_ch, True)
    print('Waiting for HV ramping...')
    hv_config = lib.get_hv_channel_configuration(board_id, hv_ch)
    thr = hv_config.v_set * 0.9
    while lib.read_hv_channel_monitoring(board_id, hv_ch).v_mon < thr:
        sleep(.5)
    sleep(1.)
    print('Done.')


def shutdown_hv(lib: dpp.Device, board_id: int, hv_ch: int) -> None:
    """
    Shutdown HV

    Note: see comment on enable_hv
    """
    print('Shutting down HV...')
    lib.set_hv_channel_power_on(board_id, hv_ch, False)
    print('Waiting for HV ramping...')
    while lib.read_hv_channel_monitoring(board_id, hv_ch).v_mon > 20:
        sleep(.5)
    sleep(1.)
    print('Done.')


def main() -> None:
    """
    Main function
    """

    ref_ch: int = args.channel
    ref_hv_ch: int = args.hvchannel

    with dpp.Device.open(dpp.LogMask.ALL) as lib:

        connection_params = dpp.ConnectionParams(
            dpp.ConnectionType[args.connectiontype],
            args.linknumber,
            args.conetnode,
            args.vmebaseaddress,
            args.ethaddress
        )

        acq_mode = dpp.AcqMode.WAVEFORM if args.waveform else dpp.AcqMode.HISTOGRAM

        board_id = lib.add_board(connection_params)
        info = lib.get_dpp_info(board_id)

        print(f'Connected with {info.model_name} (PID={info.serial_number})')

        max_adc = 2 ** info.adc_nbits - 1

        params = my_configuration(info.channels, info.adc_nbits)

        print('Configuring board...')
        lib.set_board_configuration(board_id, acq_mode, params)
        print('Done.')

        if ref_hv_ch < info.hv_channels:
            configure_hv(lib, board_id, ref_hv_ch)
            enable_hv(lib, board_id, ref_hv_ch)

        if acq_mode is dpp.AcqMode.WAVEFORM:

            wf = lib.allocate_waveform(ref_ch)

            # Set up the figure and axis
            fig, ax = plt.subplots()
            lines: list[plt.Line2D] = []
            for _ in range(4):
                line, = ax.plot([], [], drawstyle='steps-post')
                lines.append(line)

            fig.legend([
                params.wf_params.vp1.name,
                params.wf_params.vp2.name,
                params.wf_params.dp1.name,
                params.wf_params.dp2.name,
            ], loc='upper right')

            ax.set_xlim(0, wf.samples - 1)
            ax.set_ylim(0, max_adc)

            # Updater
            def _update_waveform(_):
                samples, _ = lib.get_waveform(ref_ch, False, wf)
                valid_sample_range = np.arange(0, samples)
                ax.set_title(f'Waveform (ch={ref_ch})')
                lines[0].set_data(valid_sample_range, wf.at1)
                lines[1].set_data(valid_sample_range, wf.at2)
                lines[2].set_data(valid_sample_range, wf.dt1.astype(np.float64) * 1000 + 2000)
                lines[3].set_data(valid_sample_range, wf.dt2.astype(np.float64) * 1000 + 3000)

            lib.start_acquisition()

            # Set up the animation
            ani = animation.FuncAnimation(fig, _update_waveform, interval=200, cache_frame_data=False)

            plt.show()

            lib.stop_acquisition()

        else:

            current_idx = lib.get_current_histogram_index(ref_ch)
            nbins = lib.get_histogram_size(ref_ch, current_idx)
            lib.clear_histogram(ref_ch, current_idx)

            # Set up the figure and axis for histogram
            fig, ax = plt.subplots()
            bins_range = np.arange(0, nbins)
            empty = np.zeros(nbins)
            line, = ax.plot(bins_range, empty, drawstyle='steps-post')
            min_ylim = 10
            ax.set_ylim(0, min_ylim)
            ax.set_xlabel('Energy (ch)')
            ax.set_ylabel('Counts')

            # Histogram update function
            def _update_histogram(_):
                spectrum = lib.get_histogram(ref_ch, current_idx)
                max_bin = max(spectrum.histo)
                line.set_ydata(spectrum.histo)
                ax.set_title(f'Histogram (ch={ref_ch}, realtime={spectrum.realtime})')
                ax.set_ylim(0, max(min_ylim, max_bin * 1.1))
                return line,

            lib.start_acquisition()

            # Set up the animation
            ani = animation.FuncAnimation(fig, _update_histogram, interval=200, cache_frame_data=False)

            plt.show()

            lib.stop_acquisition()

        if ref_hv_ch < info.hv_channels:
            shutdown_hv(lib, board_id, ref_hv_ch)

if __name__ == '__main__':
    main()
