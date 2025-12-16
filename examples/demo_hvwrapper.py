#!/usr/bin/env python3
"""
Python demo for CAEN HV Wrapper


The demo aims to show the user how to work with the CAEN HW Wrapper library in Python.
"""

__author__ = 'Giovanni Cerretani'
__copyright__ = 'Copyright (C) 2024 CAEN SpA'
__license__ = 'MIT-0'
# SPDX-License-Identifier: MIT-0
__contact__ = 'https://www.caen.it/'

from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser

from caen_libs import caenhvwrapper as hv

# Parse arguments
parser = ArgumentParser(
    description=__doc__,
    formatter_class=ArgumentDefaultsHelpFormatter,
)

# Shared parser for subcommands
parser.add_argument('-s', '--systemtype', type=str, help='system type', required=True, choices=tuple(i.name for i in hv.SystemType))
parser.add_argument('-l', '--linktype', type=str, help='system type', required=True, choices=tuple(i.name for i in hv.LinkType))
parser.add_argument('-a', '--arg', type=str, help='connection argument (depending on systemtype and linktype)', required=True)
parser.add_argument('-u', '--username', type=str, help='username', default='')
parser.add_argument('-p', '--password', type=str, help='password', default='')

args = parser.parse_args()

print('------------------------------------------------------------------------------------')
print(f'CAEN HV Wrapper binding loaded (lib version {hv.lib.sw_release()})')
print('------------------------------------------------------------------------------------')

system_type = hv.SystemType[args.systemtype]
link_type = hv.LinkType[args.linktype]
arg = args.arg
username = args.username
password = args.password

with hv.Device.open(system_type, link_type, arg, username, password) as device:

    slots = device.get_crate_map()  # initialize internal stuff

    comm_list = device.get_exec_comm_list()
    print('EXEC_COMM_LIST', comm_list)

    sys_props = device.get_sys_prop_list()
    for prop_name in sys_props:
        prop_info = device.get_sys_prop_info(prop_name)
        print('SYSPROP', prop_name, prop_info.type.name)
        if prop_info.mode is not hv.SysPropMode.WRONLY:
            prop_value = device.get_sys_prop(prop_name)
            print('VALUE', prop_value)
            device.subscribe_system_params([prop_name])

    for board in slots:
        if board is None:
            continue
        bd_params = device.get_bd_param_info(board.slot)
        for param_name in bd_params:
            param_prop = device.get_bd_param_prop(board.slot, param_name)
            print('BD_PARAM', board.slot, param_name, param_prop.type.name)
            if param_prop.mode is not hv.ParamMode.WRONLY:
                param_value = device.get_bd_param([board.slot], param_name)
                print('VALUE', param_value)
                device.subscribe_board_params(board.slot, [param_name])
        for ch in range(board.n_channel):
            ch_params = device.get_ch_param_info(board.slot, ch)
            for param_name in ch_params:
                param_prop = device.get_ch_param_prop(board.slot, ch, param_name)
                print('CH_PARAM', board.slot, ch, param_name, param_prop.type.name)
                if param_prop.mode is not hv.ParamMode.WRONLY:
                    param_value = device.get_ch_param(board.slot, [ch], param_name)
                    print('VALUE', param_value)
                    device.subscribe_channel_params(board.slot, ch, [param_name])

    # Listen for events
    for _ in range(10):
        evt_list, _ = device.get_event_data()
        for evt in evt_list:
            print(evt)
