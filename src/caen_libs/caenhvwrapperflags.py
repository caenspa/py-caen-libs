"""
Tools to decode encoded values of CAEN HV Wrapper
"""

__author__ = 'Giovanni Cerretani'
__copyright__ = 'Copyright (C) 2024 CAEN SpA'
__license__ = 'LGPL-3.0-or-later'
# SPDX-License-Identifier: LGPL-3.0-or-later

from enum import IntFlag

from caen_libs import caenhvwrapper as hv


class _BdStatusDefault(IntFlag):
    """
    Values of ParamType.BDSTATUS, from library documentation
    """
    PW_FAIL     = 0x00000001
    FW_CHKERR   = 0x00000002
    HVCAL_ERR   = 0x00000004
    TEMP_ERR    = 0x00000008
    UN_TEMP     = 0x00000010
    OV_TEMP     = 0x00000020
#    UNKNOWN     = 0x00000200


class _BdStatusN1470(IntFlag):
    """
    Values of ParamType.BDSTATUS for N1470
    """
    CH0_ALARM   = 0x00000001
    CH1_ALARM   = 0x00000002
    CH2_ALARM   = 0x00000004
    CH3_ALARM   = 0x00000008
    PW_FAIL     = 0x00000010
    OV_POWER    = 0x00000020
    HV_CLK_FAIL = 0x00000040


class _BdStatusDT55XXE(IntFlag):
    """
    Values of ParamType.BDSTATUS for DT55XXE
    """
    ALARMED     = 0x00000001


class _BdStatusSMARTHV(IntFlag):
    """
    Values of ParamType.BDSTATUS for SMARTHV
    """
    PW_FAIL     = 0x00000001
    CAL_ERR     = 0x00000002
    INTERLOCK   = 0x00000004
    TEMP_ERR    = 0x00000008


class _ChStatusDefault(IntFlag):
    """
    Values of ParamType.CHSTATUS, from library documentation
    """
    ON          = 0x00000001
    UP          = 0x00000002
    DOWN        = 0x00000004
    OVC         = 0x00000008
    OVV         = 0x00000010
    UNV         = 0x00000020
    E_TRIPPED   = 0x00000040
    HV_MAX      = 0x00000080
    EXT_DIS     = 0x00000100
    I_TRIPPED   = 0x00000200
    CAL_ERR     = 0x00000400
    UNPLUGG     = 0x00000800


class _ChStatusSY4527(IntFlag):
    """
    Values of ParamType.CHSTATUS for SY4527, SY5527 and R6060
    """
    ON          = 0x00000001
    UP          = 0x00000002
    DOWN        = 0x00000004
    OVC         = 0x00000008
    OVV         = 0x00000010
    UNV         = 0x00000020
    E_TRIPPED   = 0x00000040
    HV_MAX      = 0x00000080
    EXT_DIS     = 0x00000100
    I_TRIPPED   = 0x00000200
    CAL_ERR     = 0x00000400
    UNPLUGG     = 0x00000800
    UNC         = 0x00001000
    OVV_PROT    = 0x00002000
    PWR_FAIL    = 0x00004000
    TEMP_FAIL   = 0x00008000


class _ChStatusN1470(IntFlag):
    """
    Values of ParamType.CHSTATUS for N1470
    """
    ON          = 0x00000001
    UP          = 0x00000002
    DOWN        = 0x00000004
    OVC         = 0x00000008
    OVV         = 0x00000010
    UNV         = 0x00000020
    MAX_V       = 0x00000040
    TRIPPED     = 0x00000080
    OVP         = 0x00000100
    OVT         = 0x00000200
    DISABLED    = 0x00000400
    KILL        = 0x00000800
    INTERLOCK   = 0x00001000
    CAL_ERR     = 0x00002000


class _ChStatusV65XX(IntFlag):
    """
    Values of ParamType.CHSTATUS for V65XX
    """
    ON          = 0x00000001
    UP          = 0x00000002
    DOWN        = 0x00000004
    OVC         = 0x00000008
    OVV         = 0x00000010
    UNV         = 0x00000020
    I_MAX       = 0x00000040
    HV_MAX      = 0x00000080
    TRIP        = 0x00000100
    OVP         = 0x00000200
    OVT         = 0x00000400
    DISABLED    = 0x00000800
    INTERLOCK   = 0x00001000
    UNCAL       = 0x00002000


class _ChStatusDT55XXE(IntFlag):
    """
    Values of ParamType.CHSTATUS for DT55XXE
    """
    ON          = 0x00000001
    UP          = 0x00000002
    DOWN        = 0x00000004
    OVC         = 0x00000008
    OVV         = 0x00000010
    UNV         = 0x00000020
    MAX_V       = 0x00000040
    TRIPPED     = 0x00000080
    MAX_POWER   = 0x00000100
    TEMP_WARN   = 0x00000200
    DISABLED    = 0x00000400
    KILL        = 0x00000800
    INTERLOCK   = 0x00001000
    CAL_ERR     = 0x00002000


class _ChStatusSMARTHV(IntFlag):
    """
    Values of ParamType.CHSTATUS for SMARTHV
    """
    ON          = 0x00000001
    UP          = 0x00000002
    DOWN        = 0x00000004
    OVC         = 0x00000008
    OVV         = 0x00000010
    UNV         = 0x00000020
    TRIPPED     = 0x00000040
    OVP         = 0x00000080
    TEMP_WARN   = 0x00000100
    OVT         = 0x00000200
    KILL        = 0x00000400
    INTERLOCK   = 0x00000800
    DISABLED    = 0x00001000
    COMM_FAIL   = 0x00002000
    LOCK        = 0x00004000
    MAX_V       = 0x00008000
    CAL_ERR     = 0x00010000


_BD_STATUS_TYPE: dict[hv.SystemType, type[IntFlag]] = {
    hv.SystemType.N1470:    _BdStatusN1470,
    hv.SystemType.DT55XXE:  _BdStatusDT55XXE,
    hv.SystemType.SMARTHV:  _BdStatusSMARTHV,
}


_CH_STATUS_TYPE: dict[hv.SystemType, type[IntFlag]] = {
    hv.SystemType.SY4527:   _ChStatusSY4527,
    hv.SystemType.SY5527:   _ChStatusSY4527,
    hv.SystemType.V65XX:    _ChStatusV65XX,
    hv.SystemType.N1470:    _ChStatusN1470,
    hv.SystemType.DT55XXE:  _ChStatusDT55XXE,
    hv.SystemType.SMARTHV:  _ChStatusSMARTHV,
    hv.SystemType.R6060:    _ChStatusSY4527,
}


def decode_bd_status(system_type: hv.SystemType, value: int) -> str:
    """
    Convert board status to a string
    """
    status_type = _BD_STATUS_TYPE.get(system_type, _BdStatusDefault)
    status = status_type(value).name
    return '' if status is None else status


def decode_ch_status(system_type: hv.SystemType, value: int) -> str:
    """
    Convert channel status to a string
    """
    status_type = _CH_STATUS_TYPE.get(system_type, _ChStatusDefault)
    status = status_type(value).name
    return '' if status is None else status
