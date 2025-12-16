__author__ = 'Giovanni Cerretani'
__copyright__ = 'Copyright (C) 2024 CAEN SpA'
__license__ = 'LGPL-3.0-or-later'
# SPDX-License-Identifier: LGPL-3.0-or-later

import ctypes as ct
from dataclasses import dataclass
from enum import IntEnum, unique


@unique
class ConnectionModes(IntEnum):
    """
    Binding of ::t_ConnectionModes
    """
    DIRECT_USB = 0
    DIRECT_ETH = 1
    VME_V1718 = 2
    VME_V2718 = 3
    VME_V4718_ETH = 4
    VME_V4718_USB = 5
    VME_A4818 = 6


@unique
class FPGA(IntEnum):
    """
    Binding of ::t_FPGA_V2495
    """
    MAIN = 0
    USER = 1
    DELAY = 2


class USBDeviceRaw(ct.Structure):
    """Raw view of ::tUSBDevice"""
    _fields_ = [
        ('id', ct.c_uint32),
        ('SN', ct.c_char * 64),
        ('DESC', ct.c_char * 64),
    ]


@dataclass(frozen=True, slots=True)
class USBDevice:
    """
    Binding of ::tUSBDevice
    """
    id: int
    sn: str
    desc: str

    @classmethod
    def from_raw(cls, raw: USBDeviceRaw):
        """Instantiate from raw data"""
        return cls(
            raw.id,
            raw.SN.decode('ascii'),
            raw.DESC.decode('ascii'),
        )


class BoardInfoRaw(ct.Structure):
    """Raw view of ::tBOARDInfo"""
    _fields_ = [
        ('checksum', ct.c_uint32),
        ('checksum_length2', ct.c_uint32),
        ('checksum_length1', ct.c_uint32),
        ('checksum_length0', ct.c_uint32),
        ('checksum_constant2', ct.c_uint32),
        ('checksum_constant1', ct.c_uint32),
        ('checksum_constant0', ct.c_uint32),
        ('c_code', ct.c_uint32),
        ('r_code', ct.c_uint32),
        ('oui2', ct.c_uint32),
        ('oui1', ct.c_uint32),
        ('oui0', ct.c_uint32),
        ('version', ct.c_uint32),
        ('board2', ct.c_uint32),
        ('board1', ct.c_uint32),
        ('board0', ct.c_uint32),
        ('revis3', ct.c_uint32),
        ('revis2', ct.c_uint32),
        ('revis1', ct.c_uint32),
        ('revis0', ct.c_uint32),
        ('reserved', ct.c_uint32 * 8),
        ('sernum0_v2', ct.c_uint32),
        ('sernum1_v2', ct.c_uint32),
        ('sernum2_v2', ct.c_uint32),
        ('sernum3_v2', ct.c_uint32),
        ('sernum1', ct.c_uint32),
        ('sernum0', ct.c_uint32),
    ]


@dataclass(frozen=True, slots=True)
class BoardInfo:
    """
    Binding of ::tBOARDInfo
    """
    checksum: int
    checksum_length2: int
    checksum_length1: int
    checksum_length0: int
    checksum_constant2: int
    checksum_constant1: int
    checksum_constant0: int
    c_code: int
    r_code: int
    oui2: int
    oui1: int
    oui0: int
    version: int
    board2: int
    board1: int
    board0: int
    revis3: int
    revis2: int
    revis1: int
    revis0: int
    reserved: tuple[int, ...]
    sernum0_v2: int
    sernum1_v2: int
    sernum2_v2: int
    sernum3_v2: int
    sernum1: int
    sernum0: int

    @classmethod
    def from_raw(cls, raw: BoardInfoRaw):
        """Instantiate from raw data"""
        return cls(
            raw.checksum,
            raw.checksum_length2,
            raw.checksum_length1,
            raw.checksum_length0,
            raw.checksum_constant2,
            raw.checksum_constant1,
            raw.checksum_constant0,
            raw.c_code,
            raw.r_code,
            raw.oui2,
            raw.oui1,
            raw.oui0,
            raw.version,
            raw.board2,
            raw.board1,
            raw.board0,
            raw.revis3,
            raw.revis2,
            raw.revis1,
            raw.revis0,
            tuple(raw.reserved),
            raw.sernum0_v2,
            raw.sernum1_v2,
            raw.sernum2_v2,
            raw.sernum3_v2,
            raw.sernum1,
            raw.sernum0,
        )
