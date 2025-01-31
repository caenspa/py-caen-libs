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

import matplotlib.pyplot as plt
import matplotlib.animation as animation

from caen_libs import caendpplib as dpp


def hex_int(x: str):
    """Trick to make ArgumentParser support hex"""
    return int(x, 16)

# Parse arguments
parser = ArgumentParser(
    description=__doc__,
    formatter_class=ArgumentDefaultsHelpFormatter,
)

# Shared parser for subcommands
parser.add_argument('-c', '--connectiontype', type=str, help='connection type', required=True, choices=tuple(i.name for i in dpp.ConnectionType))
parser.add_argument('-l', '--linknumber', type=int, help='link number', default=0)
parser.add_argument('-n', '--conetnode', type=int, help='CONET node', default=0)
parser.add_argument('-b', '--vmebaseaddress', type=hex_int, help='VME base address (as hex)', default=0)
parser.add_argument('-a', '--ethaddress', type=str, help='ethernet address', default='')

args = parser.parse_args()

print('------------------------------------------------------------------------------------')
print('CAEN DPPLib binding loaded')
print('------------------------------------------------------------------------------------')

REF_CH = 0

with dpp.Device.open(dpp.LogMask.ALL) as lib:

    connection_params = dpp.ConnectionParams(
        dpp.ConnectionType[args.connectiontype],
        args.linknumber,
        args.conetnode,
        args.vmebaseaddress,
        args.ethaddress
    )

    idx = lib.add_board(connection_params)
    info = lib.get_dpp_info(idx)
    print(info.input_ranges)

    print(f'Connected with Digitizer {info.model_name} (sn={info.serial_number})')

    max_adc = (1 << info.adc_nbits) - 1

    # Define configuration
    params = dpp.DgtzParams()

    # List mode parameters
    params.list_params.enabled = False
    params.list_params.save_mode = dpp.ListSaveMode.FILE_BINARY
    params.list_params.file_name = 'data.bin'
    params.list_params.max_buff_num_events = 0
    params.list_params.save_mask = dpp.DumpMask.ALL_

    # Board configuration
    params.channel_mask = (0x1 << info.channels) - 1
    params.event_aggr = 0
    params.iolev = dpp.IOLevel.TTL

    # Waveform parameters
    params.wf_params.dual_trace_mode = 1
    params.wf_params.vp1 = dpp.VirtualProbe1.INPUT
    params.wf_params.vp2 = dpp.VirtualProbe2.TRAP_BL_CORR
    params.wf_params.dp1 = dpp.DigitalProbe1.PEAKING
    params.wf_params.dp2 = dpp.DigitalProbe2.TRIGGER
    params.wf_params.record_length = 1024
    params.wf_params.pre_trigger = 100
    params.wf_params.probe_self_trigger_val = 150
    params.wf_params.probe_trigger = dpp.ProbeTrigger.MAIN_TRIG

    params.resize(info.channels)

    # Channel parameters
    for i in range(info.channels):

        # Channel parameters
        params.dc_offset[i] = max_adc // 2
        params.pulse_polarity[i] = dpp.PulsePolarity.POSITIVE

        # Coicidence parameters between channels
        params.coinc_params[i].coinc_ch_mask = 0x0
        params.coinc_params[i].coinc_logic = dpp.CoincLogic.NONE
        params.coinc_params[i].coinc_op = dpp.CoincOp.OR
        params.coinc_params[i].maj_level = 0
        params.coinc_params[i].trg_win = 0

        # DPP parameters
        params.dpp_params.m_[i] = 50000
        params.dpp_params.m[i] = 1000
        params.dpp_params.k[i] = 3000
        params.dpp_params.ftd[i] = 800
        params.dpp_params.a[i] = 4
        params.dpp_params.b[i] = 200
        params.dpp_params.thr[i] = 5
        params.dpp_params.nsbl[i] = 3
        params.dpp_params.nspk[i] = 0
        params.dpp_params.pkho[i] = 0
        params.dpp_params.blho[i] = 1000
        params.dpp_params.dgain[i] = 0
        params.dpp_params.enf[i] = 1.0
        params.dpp_params.decimation[i] = 0
        params.dpp_params.trgho[i] = 1300

        # Reset Detector
        params.reset_detector[i].enabled = False
        params.reset_detector[i].reset_detection_mode = dpp.ResetDetectionMode.INTERNAL
        params.reset_detector[i].thrhold = 2
        params.reset_detector[i].reslenmin = 2
        params.reset_detector[i].reslength = 2000

        # Parameters for X770
        params.dpp_params.x770_extraparameters[i].cr_gain = 0
        params.dpp_params.x770_extraparameters[i].input_impedance = dpp.InputImpedance.O_1K
        params.dpp_params.x770_extraparameters[i].tr_gain = 0
        params.dpp_params.x770_extraparameters[i].saturation_holdoff = 300
        params.dpp_params.x770_extraparameters[i].energy_filter_mode = 0
        params.dpp_params.x770_extraparameters[i].trig_k = 30
        params.dpp_params.x770_extraparameters[i].trigm = 10
        params.dpp_params.x770_extraparameters[i].trig_mode = 0

        params.spectrum_control[i].spectrum_mode = dpp.SpectrumMode.ENERGY
        params.spectrum_control[i].time_scale = 1

    lib.set_board_configuration(idx, dpp.AcqMode.WAVEFORM, params)

    wf = lib.allocate_waveform(REF_CH)

    # Set up the figure and axis
    fig, ax = plt.subplots()
    line, = ax.plot(wf.at1)

    ax.set_ylim(0, max_adc)

    # Updater
    def _update_waveform(_):
        try:
            lib.get_waveform(REF_CH, False, wf)
        except dpp.Error as e:
            print(f'Error: {e}')
            return line,
        line.set_ydata(wf.at1)
        return line,

    lib.start_acquisition(idx)

    # Set up the animation
    ani = animation.FuncAnimation(fig, _update_waveform, blit=True, interval=100, cache_frame_data=False)

    plt.show()

    lib.stop_acquisition(idx)

print('Bye bye')
