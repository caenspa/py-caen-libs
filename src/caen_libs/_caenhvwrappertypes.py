__author__ = 'Giovanni Cerretani'
__copyright__ = 'Copyright (C) 2024 CAEN SpA'
__license__ = 'LGPL-3.0-or-later'
# SPDX-License-Identifier: LGPL-3.0-or-later

import ctypes as ct
from dataclasses import dataclass
from enum import IntEnum, unique
import os
from typing import TypeVar
import warnings


# Constants from CAENHVWrapper.h
MAX_PARAM_NAME = 10
MAX_CH_NAME = 12
MAX_ENUM_NAME = 15  # From library documentation
MAX_ENUM_VALS = 10  # From library source code


@unique
class SystemType(IntEnum):
    """
    Binding of ::CAENHV_SYSTEM_TYPE_t
    """
    SY1527 = 0
    SY2527 = 1
    SY4527 = 2
    SY5527 = 3
    N568 = 4
    V65XX = 5
    N1470 = 6
    V8100 = 7
    N568E = 8
    DT55XX = 9
    FTK = 10
    DT55XXE = 11
    N1068 = 12
    SMARTHV = 13
    NGPS = 14
    N1168 = 15
    R6060 = 16


@unique
class LinkType(IntEnum):
    """
    Binding of Link Types for InitSystem
    """
    TCPIP = 0
    RS232 = 1
    CAENET = 2
    USB = 3
    OPTLINK = 4
    USB_VCP = 5
    USB3 = 6
    A4818 = 7


@unique
class EventStatus(IntEnum):
    """
    Binding of ::CAENHV_EVT_STATUS_t
    """
    SYNC = 0
    ASYNC = 1
    UNSYNC = 2
    NOTAVAIL = 3


class SystemStatusRaw(ct.Structure):
    """Raw view of ::CAENHV_SYSTEMSTATUS_t"""
    _fields_ = [
        ('System', ct.c_int),
        ('Board', ct.c_int * 16),
    ]


@dataclass(frozen=True, slots=True)
class SystemStatus:
    """
    Binding of ::CAENHV_SYSTEMSTATUS_t
    """
    system: EventStatus
    board: tuple[EventStatus, ...]

    @classmethod
    def from_raw(cls, raw: SystemStatusRaw):
        """Instantiate from raw data"""
        return cls(
            EventStatus(raw.System),
            tuple(map(EventStatus, raw.Board)),
        )


@unique
class EventType(IntEnum):
    """
    Binding of ::CAENHV_ID_TYPE_t
    """
    PARAMETER = 0
    ALARM = 1
    KEEPALIVE = 2
    TRMODE = 3


class IdValueRaw(ct.Union):
    """Raw view of ::CAENHV_IDValue_t"""
    _fields_ = [
        ('StringValue', ct.c_char * 1024),
        ('FloatValue', ct.c_float),
        ('IntValue', ct.c_int),
    ]


class EventDataRaw(ct.Structure):
    """Raw view of ::CAENHVEVENT_TYPE_t"""
    _fields_ = [
        ('Type', ct.c_int),
        ('SystemHandle', ct.c_int),
        ('BoardIndex', ct.c_int),
        ('ChannelIndex', ct.c_int),
        ('ItemID', ct.c_char * 20),
        ('Value', IdValueRaw),
    ]


@dataclass(frozen=True, slots=True)
class EventData:
    """
    Binding of ::CAENHVEVENT_TYPE_t
    """
    type: EventType
    item_id: str
    slot: int | None
    channel: int | None
    value: str | float | int

    @property
    def board_index(self) -> int:
        """Kept for backward compatibility"""
        return -1 if self.slot is None else self.slot

    @property
    def channel_index(self) -> int:
        """Kept for backward compatibility"""
        return -1 if self.channel is None else self.channel


@dataclass(frozen=True, slots=True)
class FwVersion:
    """
    Firmware version
    """
    major: int
    minor: int

    def __str__(self) -> str:
        return f'{self.major}.{self.minor}'


@dataclass(frozen=True, slots=True)
class Board:
    """
    Type returned by ::CAENHV_GetCrateMap and ::CAENHV_TestBdPresence
    """
    slot: int
    model: str
    description: str
    serial_number: int
    n_channel: int
    fw_version: FwVersion


@unique
class SysPropType(IntEnum):
    """
    Binding of ::SYSPROP_TYPE_*
    """
    STR = 0
    REAL = 1
    UINT2 = 2
    UINT4 = 3
    INT2 = 4
    INT4 = 5
    BOOLEAN = 6


@unique
class SysPropMode(IntEnum):
    """
    Binding of ::SYSPROP_MODE_*
    """
    RDONLY = 0
    WRONLY = 1
    RDWR = 2


@dataclass(frozen=True, slots=True)
class SysProp:
    """
    Type returned by ::CAENHV_GetSysPropInfo
    """
    name: str
    mode: SysPropMode
    type: SysPropType


@unique
class ParamType(IntEnum):
    """
    Binding of ::PARAM_TYPE_*
    """
    _INVALID = 0xBAAAAAAD  # Special value for Python binding
    NUMERIC = 0
    ONOFF = 1
    CHSTATUS = 2
    BDSTATUS = 3
    BINARY = 4
    STRING = 5
    ENUM = 6
    CMD = 7


@unique
class ParamMode(IntEnum):
    """
    Binding of ::PARAM_MODE_*
    """
    _INVALID = 0xBAAAAAAD  # Special value for Python binding
    RDONLY = 0
    WRONLY = 1
    RDWR = 2


@unique
class ParamUnit(IntEnum):
    """
    Binding of ::PARAM_UN_*
    """
    NONE = 0
    AMPERE = 1
    VOLT = 2
    WATT = 3
    CELSIUS = 4
    HERTZ = 5
    BAR = 6
    VPS = 7
    SECOND = 8
    RPM = 9
    COUNT = 10
    BIT = 11
    APS = 12


@dataclass(slots=True)
class ParamProp:
    """
    Type returned by ::CAENHV_GetBdParamProp
    """
    type: ParamType
    mode: ParamMode
    minval: float | None = None
    maxval: float | None = None
    unit: ParamUnit | None = None
    exp: int | None = None
    decimal: int | None = None
    resol: int | None = None
    onstate: str | None = None
    offstate: str | None = None
    enum: tuple[str, ...] | None = None


@dataclass(frozen=True, slots=True)
class TcpPorts:
    """
    TCP port range to bind to for event handling. Range is exclusive,
    so that the ports used are [first, last).
    """
    first: int = 0
    last: int = 1

    def __post_init__(self) -> None:
        if self.first < 0 or self.first > 65535:
            raise ValueError('First port must be between 0 and 65535.')
        if self.last < 1 or self.last > 65536:
            raise ValueError('Last port must be between 1 and 65536.')
        if self.first == 0 and self.last != 1:
            raise ValueError('Last port must be 1 if first port is 0.')
        if self.first >= self.last:
            raise ValueError('First port must be lower than last port.')

    _T = TypeVar('_T', bound='TcpPorts')

    @classmethod
    def load_defaults(cls: type[_T]) -> _T:
        """
        Utility function to handle deprecation of HV_FIRST_BIND_PORT.
        """
        env = 'HV_FIRST_BIND_PORT'
        first_env = os.environ.get(env)
        if first_env is not None:
            msg = f'Environment variable {env} is deprecated. Use Device.set_events_tcp_ports() instead.'
            warnings.warn(msg, DeprecationWarning)
        first = int(first_env) if first_env is not None else 0
        last = 1 if first == 0 else 65536
        return cls(first, last)
