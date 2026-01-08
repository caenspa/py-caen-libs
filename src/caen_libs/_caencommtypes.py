__author__ = 'Giovanni Cerretani'
__copyright__ = 'Copyright (C) 2024 CAEN SpA'
__license__ = 'LGPL-3.0-or-later'
# SPDX-License-Identifier: LGPL-3.0-or-later

from dataclasses import dataclass
from enum import IntEnum, IntFlag, unique


@dataclass(slots=True)
class ReadResult:
    """
    Result of a block transfer read operation.

    TERMINATED is not considered fatal during BLT/MBLT reads - it typically
    indicates the end of a transfer when the device has no more data available.
    The data field contains all successfully read bytes before the error.
    """
    data: bytes
    terminated: bool


@unique
class ConnectionType(IntEnum):
    """
    Binding of ::CAEN_Comm_ConnectionType
    """
    USB = 0
    OPTICAL_LINK = 1
    USB_A4818 = 5
    ETH_V4718 = 6
    USB_V4718 = 7


@unique
class Info(IntEnum):
    """
    Binding of ::CAENCOMM_INFO

    ::CAENComm_VMELIB_handle missing, since implemented on separated
    binding.
    """
    PCI_BOARD_SN = 0
    PCI_BOARD_FW_REL = 1
    VME_BRIDGE_SN = 2
    VME_BRIDGE_FW_REL_1 = 3
    VME_BRIDGE_FW_REL_2 = 4


class IRQLevels(IntFlag):
    """
    Binding of ::IRQLevels
    """
    L1 = 0x01
    L2 = 0x02
    L3 = 0x04
    L4 = 0x08
    L5 = 0x10
    L6 = 0x20
    L7 = 0x40
