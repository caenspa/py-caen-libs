"""
Binding of CAEN HV Wrapper
"""

__author__ = 'Giovanni Cerretani'
__copyright__ = 'Copyright (C) 2024 CAEN SpA'
__license__ = 'LGPL-3.0-or-later'
# SPDX-License-Identifier: LGPL-3.0-or-later

import ctypes as ct
import ctypes.wintypes as ctw
import os
import socket
import sys
from collections.abc import Callable, Generator, Iterator, Sequence
from contextlib import contextmanager, suppress
from dataclasses import dataclass, field
from enum import IntEnum, unique
from typing import Any, ClassVar, Optional, TypeVar, Union

from caen_libs import _cache, _string, _utils, error


@unique
class SystemType(IntEnum):
    """
    Binding of ::CAENHV_SYSTEM_TYPE_t
    """
    SY1527      = 0
    SY2527      = 1
    SY4527      = 2
    SY5527      = 3
    N568        = 4
    V65XX       = 5
    N1470       = 6
    V8100       = 7
    N568E       = 8
    DT55XX      = 9
    FTK         = 10
    DT55XXE     = 11
    N1068       = 12
    SMARTHV     = 13
    NGPS        = 14
    N1168       = 15
    R6060       = 16


@unique
class LinkType(IntEnum):
    """
    Binding of Link Types for InitSystem
    """
    TCPIP   = 0
    RS232   = 1
    CAENET  = 2
    USB     = 3
    OPTLINK = 4
    USB_VCP = 5
    USB3    = 6
    A4818   = 7


@unique
class EventStatus(IntEnum):
    """
    Binding of ::CAENHV_EVT_STATUS_t
    """
    SYNC        = 0
    ASYNC       = 1
    UNSYNC      = 2
    NOTAVAIL    = 3


class _SystemStatusRaw(ct.Structure):
    _fields_ = [
        ('System', ct.c_int),
        ('Board', ct.c_int * 16),
    ]


@dataclass(frozen=True, **_utils.dataclass_slots)
class SystemStatus:
    """
    Binding of ::CAENHV_SYSTEMSTATUS_t
    """
    system: EventStatus
    board: tuple[EventStatus, ...]

    @classmethod
    def from_raw(cls, raw: _SystemStatusRaw):
        """Instantiate from raw data"""
        return cls(
            system=EventStatus(raw.System),
            board=tuple(map(EventStatus, raw.Board)),
        )


@unique
class EventType(IntEnum):
    """
    Binding of ::CAENHV_ID_TYPE_t
    """
    PARAMETER   = 0
    ALARM       = 1
    KEEPALIVE   = 2
    TRMODE      = 3


class _IdValueRaw(ct.Union):
    _fields_ = [
        ('StringValue', ct.c_char * 1024),
        ('FloatValue', ct.c_float),
        ('IntValue', ct.c_int),
    ]


class _EventDataRaw(ct.Structure):
    _fields_ = [
        ('Type', ct.c_int),
        ('SystemHandle', ct.c_int),
        ('BoardIndex', ct.c_int),
        ('ChannelIndex', ct.c_int),
        ('ItemID', ct.c_char * 20),
        ('Value', _IdValueRaw),
    ]


@dataclass(frozen=True, **_utils.dataclass_slots)
class EventData:
    """
    Binding of ::CAENHVEVENT_TYPE_t
    """
    type: EventType
    item_id: str
    board_index: int
    channel_index: int
    value: Union[str, float, int]


@dataclass(frozen=True, **_utils.dataclass_slots)
class FwVersion:
    """
    Firmware version
    """
    major: int
    minor: int

    def __str__(self) -> str:
        return f'{self.major}.{self.minor}'


@dataclass(frozen=True, **_utils.dataclass_slots)
class Board:
    """
    Type returned by ::CAENHV_GetCrateMap
    """
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
    STR     = 0
    REAL    = 1
    UINT2   = 2
    UINT4   = 3
    INT2    = 4
    INT4    = 5
    BOOLEAN = 6


@unique
class SysPropMode(IntEnum):
    """
    Binding of ::SYSPROP_MODE_*
    """
    RDONLY  = 0
    WRONLY  = 1
    RDWR    = 2


@dataclass(frozen=True, **_utils.dataclass_slots)
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
    _INVALID    = 0xBAAAAAAD  # Special value for Python binding
    NUMERIC     = 0
    ONOFF       = 1
    CHSTATUS    = 2
    BDSTATUS    = 3
    BINARY      = 4
    STRING      = 5
    ENUM        = 6
    CMD         = 7


@unique
class ParamMode(IntEnum):
    """
    Binding of ::PARAM_MODE_*
    """
    RDONLY  = 0
    WRONLY  = 1
    RDWR    = 2


@unique
class ParamUnit(IntEnum):
    """
    Binding of ::PARAM_UN_*
    """
    NONE    = 0
    AMPERE  = 1
    VOLT    = 2
    WATT    = 3
    CELSIUS = 4
    HERTZ   = 5
    BAR     = 6
    VPS     = 7
    SECOND  = 8
    RPM     = 9
    COUNT   = 10
    BIT     = 11
    APS     = 12


@dataclass(**_utils.dataclass_slots)
class ParamProp:
    """
    Type returned by ::CAENHV_GetBdParamProp
    """
    type: ParamType
    mode: ParamMode
    minval: Optional[float] = field(default=None)
    maxval: Optional[float] = field(default=None)
    unit: Optional[ParamUnit] = field(default=None)
    exp: Optional[int] = field(default=None)
    decimal: Optional[int] = field(default=None)
    resol: Optional[int] = field(default=None)
    onstate: Optional[str] = field(default=None)
    offstate: Optional[str] = field(default=None)
    enum: Optional[tuple[str, ...]] = field(default=None)


class Error(error.Error):
    """
    Raised when a wrapped C API function returns negative values.
    """

    @unique
    class Code(IntEnum):
        """
        Binding of ::CAENHVRESULT
        """
        UNKNOWN                 = 0xDEADFACE  # Special value for Python binding
        OK                      = 0
        SYSERR                  = 1
        WRITEERR                = 2
        READERR                 = 3
        TIMEERR                 = 4
        DOWN                    = 5
        NOTPRES                 = 6
        SLOTNOTPRES             = 7
        NOSERIAL                = 8
        MEMORYFAULT             = 9
        OUTOFRANGE              = 10
        EXECCOMNOTIMPL          = 11
        GETPROPNOTIMPL          = 12
        SETPROPNOTIMPL          = 13
        PROPNOTFOUND            = 14
        EXECNOTFOUND            = 15
        NOTSYSPROP              = 16
        NOTGETPROP              = 17
        NOTSETPROP              = 18
        NOTEXECOMM              = 19
        SYSCONFCHANGE           = 20
        PARAMPROPNOTFOUND       = 21
        PARAMNOTFOUND           = 22
        NODATA                  = 23
        DEVALREADYOPEN          = 24
        TOOMANYDEVICEOPEN       = 25
        INVALIDPARAMETER        = 26
        FUNCTIONNOTAVAILABLE    = 27
        SOCKETERROR             = 28
        COMMUNICATIONERROR      = 29
        NOTYETIMPLEMENTED       = 30
        CONNECTED               = 0x1000 + 1
        NOTCONNECTED            = 0x1000 + 2
        OS                      = 0x1000 + 3
        LOGINFAILED             = 0x1000 + 4
        LOGOUTFAILED            = 0x1000 + 5
        LINKNOTSUPPORTED        = 0x1000 + 6
        USERPASSFAILED          = 0x1000 + 7

        @classmethod
        def _missing_(cls, _):
            """
            Sometimes library returns values not contained in the
            enumerator, due to errors in the library itself. We
            catch them and return UNKNOWN.
            """
            return cls.UNKNOWN

    code: Code

    def __init__(self, message: str, res: int, func: str) -> None:
        self.code = Error.Code(res)
        super().__init__(message, self.code.name, func)


# For backward compatibility. Deprecated.
ErrorCode = Error.Code


# Utility definitions
_c_char_p = ct.POINTER(ct.c_char)  # ct.c_char_p is not fine due to its own memory management
_c_char_p_p = ct.POINTER(_c_char_p)
_c_ubyte_p = ct.POINTER(ct.c_ubyte)
_c_ubyte_p_p = ct.POINTER(_c_ubyte_p)
_c_ushort_p = ct.POINTER(ct.c_ushort)
_c_ushort_p_p = ct.POINTER(_c_ushort_p)
_c_int_p = ct.POINTER(ct.c_int)
_c_uint_p = ct.POINTER(ct.c_uint)
_c_uint_p_p = ct.POINTER(_c_uint_p)
_system_status_p = ct.POINTER(_SystemStatusRaw)
_event_data_p = ct.POINTER(_EventDataRaw)
_event_data_p_p = ct.POINTER(_event_data_p)
if sys.platform == 'win32':
    _socket = ctw.WPARAM  # Actually a SOCKET is UINT_PTR, same as WPARAM
else:
    _socket = ct.c_int


_SYS_PROP_TYPE_GET_ARG: dict[SysPropType, Callable] = {
    SysPropType.STR:        lambda v: v.value.decode('ascii'),
    SysPropType.REAL:       lambda v: ct.cast(v, ct.POINTER(ct.c_float)).contents.value,
    SysPropType.UINT2:      lambda v: ct.cast(v, ct.POINTER(ct.c_uint16)).contents.value,
    SysPropType.UINT4:      lambda v: ct.cast(v, ct.POINTER(ct.c_uint32)).contents.value,
    SysPropType.INT2:       lambda v: ct.cast(v, ct.POINTER(ct.c_int16)).contents.value,
    SysPropType.INT4:       lambda v: ct.cast(v, ct.POINTER(ct.c_int32)).contents.value,
    SysPropType.BOOLEAN:    lambda v: bool(ct.cast(v, _c_uint_p).contents.value),
}


_SYS_PROP_TYPE_SET_ARG: dict[SysPropType, Callable] = {
    SysPropType.STR:        lambda v: v.encode('ascii'),
    SysPropType.REAL:       lambda v: ct.pointer(ct.c_float(v)),
    SysPropType.UINT2:      lambda v: ct.pointer(ct.c_uint16(v)),
    SysPropType.UINT4:      lambda v: ct.pointer(ct.c_uint32(v)),
    SysPropType.INT2:       lambda v: ct.pointer(ct.c_int16(v)),
    SysPropType.INT4:       lambda v: ct.pointer(ct.c_int32(v)),
    SysPropType.BOOLEAN:    lambda v: ct.pointer(ct.c_uint(v)),
}


_STR_SIZE = 1024  # Undocumented but, hopefully, long enough


_PARAM_TYPE_GET_ARG: dict[ParamType, Callable[[int], ct.Array]] = {
    # c_int is replaced by c_uint on some systems, but should be the same.
    ParamType.NUMERIC:      lambda n: (ct.c_float * n)(),
    ParamType.ONOFF:        lambda n: (ct.c_int * n)(),
    ParamType.CHSTATUS:     lambda n: (ct.c_int * n)(),
    ParamType.BDSTATUS:     lambda n: (ct.c_int * n)(),
    ParamType.BINARY:       lambda n: (ct.c_int * n)(),
    ParamType.STRING:       lambda n: (ct.c_char * (_STR_SIZE * n))(),
    ParamType.ENUM:         lambda n: (ct.c_int * n)(),
    # ParamType.CMD is never found on readable parameters
}


_PARAM_TYPE_SET_ARG: dict[ParamType, Callable[[Any, int], Any]] = {
    # We generate an array with the same value for the reason described
    # in the caller docstring.
    # c_int is replaced by c_uint on some systems, but should be the same.
    ParamType.NUMERIC:      lambda v, n: (ct.c_float * n)(*[v]*n),
    ParamType.ONOFF:        lambda v, n: (ct.c_int * n)(*[v]*n),
    ParamType.CHSTATUS:     lambda v, n: (ct.c_int * n)(*[v]*n),
    ParamType.BDSTATUS:     lambda v, n: (ct.c_int * n)(*[v]*n),
    ParamType.BINARY:       lambda v, n: (ct.c_int * n)(*[v]*n),
    ParamType.STRING:       lambda v, n: v.encode('ascii'),  # no array here, only first value is used
    ParamType.ENUM:         lambda v, n: (ct.c_int * n)(*[v]*n),
    ParamType.CMD:          lambda v, n: ct.c_void_p(),  # value ignored, return a null pointer
}


_SYS_PROP_TYPE_EVENT_ARG: dict[SysPropType, Callable[[_IdValueRaw], Union[str, float, int]]] = {
    SysPropType.STR:        lambda v: v.StringValue.decode('ascii'),
    SysPropType.REAL:       lambda v: v.FloatValue,
    SysPropType.UINT2:      lambda v: v.IntValue,
    SysPropType.UINT4:      lambda v: v.IntValue,
    SysPropType.INT2:       lambda v: v.IntValue,
    SysPropType.INT4:       lambda v: v.IntValue,
    SysPropType.BOOLEAN:    lambda v: v.IntValue,
}


_PARAM_TYPE_EVENT_ARG: dict[ParamType, Callable[[_IdValueRaw], Union[str, float, int]]] = {
    ParamType.NUMERIC:      lambda v: v.FloatValue,
    ParamType.ONOFF:        lambda v: v.IntValue,
    ParamType.CHSTATUS:     lambda v: v.IntValue,
    ParamType.BDSTATUS:     lambda v: v.IntValue,
    ParamType.BINARY:       lambda v: v.IntValue,
    ParamType.STRING:       lambda v: v.StringValue.decode('ascii'),
    ParamType.ENUM:         lambda v: v.IntValue,
    ParamType.CMD:          lambda v: v.IntValue,
}


_R = TypeVar('_R', bound='ct._CData')


class _Lib(_utils.Lib):

    def __init__(self, name: str) -> None:
        super().__init__(name, False)
        self.__load_api()

    def __load_api(self) -> None:
        # Load API not related to devices
        self.get_event_data = self.__get('GetEventData', _socket, _system_status_p, _event_data_p_p, _c_uint_p, handle_errcheck=False)
        self.__free_event_data = self.__get('FreeEventData', _event_data_p_p, handle_errcheck=False)
        self.__free = self.__get('Free', ct.c_void_p, handle_errcheck=False)
        self.__sw_rel = self.__get_str('LibSwRel', legacy=True)

        ser_num_type = _c_uint_p_p if self.support_32bit_pid() else _c_ushort_p_p

        # Load API
        self.init_system = self.__get('InitSystem', ct.c_int, ct.c_int, ct.c_void_p, _c_char_p, _c_char_p, _c_int_p)
        self.deinit_system = self.__get('DeinitSystem', ct.c_int)
        self.get_crate_map = self.__get('GetCrateMap', ct.c_int, _c_ushort_p, _c_ushort_p_p, _c_char_p_p, _c_char_p_p, ser_num_type, _c_ubyte_p_p, _c_ubyte_p_p)
        self.get_sys_prop_list = self.__get('GetSysPropList', ct.c_int, _c_ushort_p, _c_char_p_p)
        self.get_sys_prop_info = self.__get('GetSysPropInfo', ct.c_int, _c_char_p, _c_uint_p, _c_uint_p)
        self.get_sys_prop = self.__get('GetSysProp', ct.c_int, _c_char_p, ct.c_void_p)
        self.set_sys_prop = self.__get('SetSysProp', ct.c_int, _c_char_p, ct.c_void_p)
        self.get_bd_param = self.__get('GetBdParam', ct.c_int, ct.c_ushort, _c_ushort_p, _c_char_p, ct.c_void_p)
        self.set_bd_param = self.__get('SetBdParam', ct.c_int, ct.c_ushort, _c_ushort_p, _c_char_p, ct.c_void_p)
        self.get_bd_param_prop = self.__get('GetBdParamProp', ct.c_int, ct.c_ushort, _c_char_p, _c_char_p, ct.c_void_p)
        self.get_bd_param_info = self.__get('GetBdParamInfo', ct.c_int, ct.c_ushort, _c_char_p_p)
        self.test_bd_presence = self.__get('TestBdPresence', ct.c_int, ct.c_ushort, _c_ushort_p, _c_char_p_p, _c_char_p_p, _c_ushort_p, _c_ubyte_p, _c_ubyte_p)
        self.get_ch_param_prop = self.__get('GetChParamProp', ct.c_int, ct.c_ushort, ct.c_ushort, _c_char_p, _c_char_p, ct.c_void_p)
        self.get_ch_param_info = self.__get('GetChParamInfo', ct.c_int, ct.c_ushort, ct.c_ushort, _c_char_p_p, _c_int_p)
        self.get_ch_name = self.__get('GetChName', ct.c_int, ct.c_ushort, ct.c_ushort, _c_ushort_p, _c_char_p)
        self.set_ch_name = self.__get('SetChName', ct.c_int, ct.c_ushort, ct.c_ushort, _c_ushort_p, _c_char_p)
        self.get_ch_param = self.__get('GetChParam', ct.c_int, ct.c_ushort, _c_char_p, ct.c_ushort, _c_ushort_p, ct.c_void_p)
        self.set_ch_param = self.__get('SetChParam', ct.c_int, ct.c_ushort, _c_char_p, ct.c_ushort, _c_ushort_p, ct.c_void_p)
        self.get_exec_comm_list = self.__get('GetExecCommList', ct.c_int, _c_ushort_p, _c_char_p_p)
        self.exec_comm = self.__get('ExecComm', ct.c_int, _c_char_p)
        self.subscribe_system_params = self.__get('SubscribeSystemParams', ct.c_int, ct.c_short, _c_char_p, ct.c_uint, _c_char_p)
        self.subscribe_board_params = self.__get('SubscribeBoardParams', ct.c_int, ct.c_short, ct.c_ushort, _c_char_p, ct.c_uint, _c_char_p)
        self.subscribe_channel_params = self.__get('SubscribeChannelParams', ct.c_int, ct.c_short, ct.c_ushort, ct.c_ushort, _c_char_p, ct.c_uint, _c_char_p)
        self.unsubscribe_system_params = self.__get('UnSubscribeSystemParams', ct.c_int, ct.c_short, _c_char_p, ct.c_uint, _c_char_p)
        self.unsubscribe_board_params = self.__get('UnSubscribeBoardParams', ct.c_int, ct.c_short, ct.c_ushort, _c_char_p, ct.c_uint, _c_char_p)
        self.unsubscribe_channel_params = self.__get('UnSubscribeChannelParams', ct.c_int, ct.c_short, ct.c_ushort, ct.c_ushort, _c_char_p, ct.c_uint, _c_char_p)
        self.__get_error = self.__get_str('GetError', ct.c_int)

    def __api_errcheck(self, res: int, func, _: tuple) -> int:
        if res != Error.Code.OK:
            raise Error('details not available', res, func.__name__)
        return res

    def __api_handle_errcheck(self, res: int, func, func_args: tuple) -> int:
        """
        Binding of CAENHV_GetError()

        Even if the first argument is an handle, this binding
        is defined as errcheck rather then a method of Device class
        because actually it has to be called after a failed call.
        The handle is obtained assuming it is the first argument
        of the failed function.
        """
        if res != Error.Code.OK:
            handle = func_args[0]  # first argument is always handle
            raise Error(self.__get_error(handle), res, func.__name__)
        return res

    def __get(self, name: str, *args: type, **kwargs) -> Callable[..., int]:
        func = self.get(f'CAENHV_{name}')
        func.argtypes = args
        func.restype = ct.c_int
        if kwargs.get('handle_errcheck', True):
            func.errcheck = self.__api_handle_errcheck  # type: ignore
        else:
            func.errcheck = self.__api_errcheck  # type: ignore
        return func

    def __get_str(self, name: str, *args: type, **kwargs) -> Callable[..., str]:
        if kwargs.get('legacy', False):
            func_name = f'CAENHV{name}'
        else:
            func_name = f'CAENHV_{name}'
        func = self.get(func_name)
        func.argtypes = args
        func.restype = ct.c_char_p
        # cannot fail, errcheck improperly used to cast bytes to str
        func.errcheck = lambda res, *_: res.decode('ascii')  # type: ignore
        return func

    # C API bindings

    def sw_release(self) -> str:
        """
        Binding of CAENHVLibSwRel()
        """
        return self.__sw_rel()

    def support_32bit_pid(self) -> bool:
        """
        Check if library support 32-bit PID
        """
        return self.ver_at_least((7, 0, 0))

    @contextmanager
    def auto_ptr(self, pointer_type: type[_R]) -> Generator['ct._Pointer[_R]', None, None]:
        """
        Context manager to auto free on scope exit.

        The returned pointer is initialized to NULL to avoid error
        when freeing, in case callee function does not set the pointer.
        """
        value = ct.POINTER(pointer_type)()
        assert bool(value) is False  # Must be NULL
        try:
            yield value
        finally:
            self.__free(value)

    @contextmanager
    def evt_data_auto_ptr(self) -> Generator['ct._Pointer[_EventDataRaw]', None, None]:
        """
        Context manager to auto free event data on scope exit

        The returned pointer is initialized to NULL to avoid error
        when freeing, in case callee function does not set the pointer.
        """
        value = _event_data_p()
        assert bool(value) is False  # Must be NULL
        try:
            yield value
        finally:
            self.__free_event_data(value)


# Library name is platform dependent
if sys.platform == 'win32':
    _LIB_NAME = 'CAENHVWrapper'
else:
    _LIB_NAME = 'caenhvwrapper'


lib = _Lib(_LIB_NAME)


@dataclass(**_utils.dataclass_slots_weakref)
class Device:
    """
    Class representing a device.
    """

    # Public members
    handle: int
    system_type: SystemType
    link_type: LinkType
    arg: str
    username: str = field(repr=False)
    password: str = field(repr=False)

    # Constants
    MAX_PARAM_NAME: ClassVar[int] = 10  # From CAENHVWrapper.h
    MAX_CH_NAME: ClassVar[int] = 12  # From CAENHVWrapper.h
    MAX_ENUM_NAME: ClassVar[int] = 15  # From library documentation
    MAX_ENUM_VALS: ClassVar[int] = 10  # From library source code

    # Private members
    __opened: bool = field(default=True, repr=False)
    __skt_server: Optional[socket.socket] = field(default=None, repr=False)
    __skt_client: Optional[socket.socket] = field(default=None, repr=False)

    # Static private members
    __cache_manager: ClassVar[_cache.Manager] = _cache.Manager()
    __first_bind_port: ClassVar[int] = int(os.environ.get('HV_FIRST_BIND_PORT', '10001'))  # This binding will bind TCP ports starting from this value

    def __del__(self) -> None:
        if self.__opened:
            self.close()

    # C API bindings

    _T = TypeVar('_T', bound='Device')

    @classmethod
    def open(cls: type[_T], system_type: SystemType, link_type: LinkType, arg: str, username: str = '', password: str = '') -> _T:
        """
        Binding of CAENHV_InitSystem()
        """
        l_handle = ct.c_int()
        lib.init_system(system_type, link_type, arg.encode('ascii'), username.encode('ascii'), password.encode('ascii'), l_handle)
        return cls(l_handle.value, system_type, link_type, arg, username, password)

    def connect(self) -> None:
        """
        Binding of CAENHV_InitSystem()

        New instances should be created with open(). This is meant to
        reconnect a device closed with close().
        """
        if self.__opened:
            raise RuntimeError('Already connected.')
        l_handle = ct.c_int()
        lib.init_system(self.system_type, self.link_type, self.arg.encode('ascii'), self.username.encode('ascii'), self.password.encode('ascii'), l_handle)
        self.handle = l_handle.value
        self.__opened = True

    @_cache.clear(cache_manager=__cache_manager)
    def close(self) -> None:
        """
        Binding of CAENHV_DeinitSystem()

        This will also clear class cache.
        """
        lib.deinit_system(self.handle)
        # Close connections, if any
        if self.__skt_client is not None:
            if self.__new_events_format():
                # Nothing to do, socket managed internally by the library
                pass
            else:
                # Gracefully close the connection.
                self.__skt_client.shutdown(socket.SHUT_RDWR)
                self.__skt_client.close()
            self.__skt_client = None
        if self.__skt_server is not None:
            self.__skt_server.close()
            self.__skt_server = None
        self.__opened = False

    @_cache.clear(cache_manager=__cache_manager)
    def get_crate_map(self) -> tuple[Optional[Board], ...]:
        """
        Binding of CAENHV_GetCrateMap()

        This will also clear class cache, since the function
        invalidates some internal stuctures of the C library.
        """
        l_nos = ct.c_ushort()
        g_nocl = lib.auto_ptr(ct.c_ushort)
        g_ml = lib.auto_ptr(ct.c_char)
        g_dl = lib.auto_ptr(ct.c_char)
        g_snl = lib.auto_ptr(ct.c_uint if lib.support_32bit_pid() else ct.c_ushort)
        g_frminl = lib.auto_ptr(ct.c_ubyte)
        g_frmaxl = lib.auto_ptr(ct.c_ubyte)
        with g_nocl as l_nocl, g_ml as l_ml, g_dl as l_dl, g_snl as l_snl, g_frminl as l_frminl, g_frmaxl as l_frmaxl:
            lib.get_crate_map(self.handle, l_nos, l_nocl, l_ml, l_dl, l_snl, l_frminl, l_frmaxl)
            ml = tuple(_string.from_char_p(l_ml, l_nos.value))
            dl = tuple(_string.from_char_p(l_dl, l_nos.value))
            return tuple(
                Board(
                    ml[i],
                    dl[i],
                    l_snl[i],
                    l_nocl[i],
                    FwVersion(l_frmaxl[i], l_frminl[i]),
                ) if l_nocl[i] != 0 else None for i in range(l_nos.value)
            )

    @_cache.cached(cache_manager=__cache_manager)
    def get_sys_prop_list(self) -> tuple[str, ...]:
        """
        Binding of CAENHV_GetSysPropList()
        """
        l_num_prop = ct.c_ushort()
        g_prop_name_list = lib.auto_ptr(ct.c_char)
        with g_prop_name_list as l_pnl:
            lib.get_sys_prop_list(self.handle, l_num_prop, l_pnl)
            return tuple(_string.from_char_p(l_pnl, l_num_prop.value))

    @_cache.cached(cache_manager=__cache_manager)
    def get_sys_prop_info(self, name: str) -> SysProp:
        """
        Binding of CAENHV_GetSysPropInfo()
        """
        l_prop_mode = ct.c_uint()
        l_prop_type = ct.c_uint()
        lib.get_sys_prop_info(self.handle, name.encode('ascii'), l_prop_mode, l_prop_type)
        return SysProp(name, SysPropMode(l_prop_mode.value), SysPropType(l_prop_type.value))

    def get_sys_prop(self, name: str) -> Union[str, float, int, bool]:
        """
        Binding of CAENHV_GetSysProp()
        """
        l_value = ct.create_string_buffer(1024)  # Should be enough for all types
        lib.get_sys_prop(self.handle, name.encode('ascii'), l_value)
        prop_type = self.get_sys_prop_info(name).type
        return _SYS_PROP_TYPE_GET_ARG[prop_type](l_value)

    def set_sys_prop(self, name: str, value: Union[str, float, int, bool]) -> None:
        """
        Binding of CAENHV_SetSysProp()
        """
        prop_type = self.get_sys_prop_info(name).type
        l_value = _SYS_PROP_TYPE_SET_ARG[prop_type](value)
        lib.set_sys_prop(self.handle, name.encode('ascii'), l_value)

    def get_bd_param(self, slot_list: Sequence[int], name: str) -> Union[list[str], list[float], list[int]]:
        """
        Binding of CAENHV_GetBdParam()
        """
        n_indexes = len(slot_list)
        if n_indexes == 0:
            return []  # type: ignore
        l_index_list = (ct.c_ushort * n_indexes)(*slot_list)
        first_index = slot_list[0]  # Assuming all types are equal
        param_type = self.__get_param_type(first_index, name, None)
        l_data = _PARAM_TYPE_GET_ARG[param_type](n_indexes)
        if param_type is ParamType.STRING and self.__char_p_p_str_bd_param_arg():
            # Some systems require a char** instead of a char*: we build it using the same buffer, with different decode.
            p_begin = ct.addressof(l_data)
            p_size = ct.sizeof(l_data)
            assert p_size % _STR_SIZE == 0
            l_data_proxy = (ct.c_void_p * n_indexes)(*range(p_begin, p_begin + p_size, _STR_SIZE))
        else:
            l_data_proxy = l_data
        lib.get_bd_param(self.handle, n_indexes, l_index_list, name.encode('ascii'), l_data_proxy)
        if param_type is ParamType.STRING:
            if self.__char_p_p_str_bd_param_arg():
                return list(_string.from_n_char_array(l_data, _STR_SIZE, n_indexes))
            else:
                return list(_string.from_char(l_data, n_indexes))
        else:
            return l_data[:]

    def set_bd_param(self, slot_list: Sequence[int], name: str, value: Optional[Union[str, float, int]]) -> None:
        """
        Binding of CAENHV_SetBdParam()

        The CAEN HV Wrapper is not consistent, since it allows to pass
        an array of values as input, to be set respectively to the slots
        in the slot_list, but this is done only on some system types
        (notably, on SY4527 and R6060 it uses only the first value of
        the array for all channels in the slot_list). To make their
        behavior homogeneous, we do the same also on systems supporting
        different values, setting the same value on all slots. The trick
        is not done on parameters of STRING type because the systems
        that accept an array as input do not have any writable parameter
        of that type. The trick is not done on CMD type because the
        input value is ignored.
        """
        n_indexes = len(slot_list)
        if n_indexes == 0:
            return
        l_index_list = (ct.c_ushort * n_indexes)(*slot_list)
        first_index = slot_list[0]  # Assuming all types are equal
        param_type = self.__get_param_type(first_index, name, None)
        l_data = _PARAM_TYPE_SET_ARG[param_type](value, n_indexes)
        lib.set_bd_param(self.handle, n_indexes, l_index_list, name.encode('ascii'), l_data)

    def get_bd_param_prop(self, slot: int, name: str) -> ParamProp:
        """
        Binding of CAENHV_GetBdParamProp()
        """
        return self.__get_param_prop(slot, name, None)

    @_cache.cached(cache_manager=__cache_manager)
    def get_bd_param_info(self, slot: int) -> tuple[str, ...]:
        """
        Binding of CAENHV_GetBdParamInfo()
        """
        g_value = lib.auto_ptr(ct.c_char)
        with g_value as l_value:
            lib.get_bd_param_info(self.handle, slot, l_value)
            return tuple(_string.from_char_array(l_value.contents, self.MAX_PARAM_NAME))

    def test_bd_presence(self, slot: int) -> Board:
        """
        Binding of CAENHV_TestBdPresence()
        """
        l_nr_of_ch = ct.c_ushort()
        g_model = lib.auto_ptr(ct.c_char)
        g_description = lib.auto_ptr(ct.c_char)
        l_ser_num = ct.c_ushort()
        l_fmw_rel_min = ct.c_ubyte()
        l_fmw_rel_max = ct.c_ubyte()
        with g_model as l_m, g_description as l_d:
            lib.test_bd_presence(self.handle, slot, l_nr_of_ch, l_m, l_d, l_ser_num, l_fmw_rel_min, l_fmw_rel_max)
            model = l_m.contents.value.decode('ascii')
            description = l_d.contents.value.decode('ascii')
            return Board(
                model,
                description,
                l_ser_num.value,
                l_nr_of_ch.value,
                FwVersion(l_fmw_rel_max.value, l_fmw_rel_min.value),
            )

    def get_ch_param_prop(self, slot: int, channel: int, name: str) -> ParamProp:
        """
        Binding of CAENHV_GetChParamProp()
        """
        return self.__get_param_prop(slot, name, channel)

    @_cache.cached(cache_manager=__cache_manager, maxsize=4096)
    def get_ch_param_info(self, slot: int, channel: int) -> tuple[str, ...]:
        """
        Binding of CAENHV_GetChParamInfo()
        """
        g_value = lib.auto_ptr(ct.c_char)
        with g_value as l_value:
            l_size = ct.c_int()
            lib.get_ch_param_info(self.handle, slot, channel, l_value, l_size)
            return tuple(_string.from_n_char_array_p(l_value, self.MAX_PARAM_NAME, l_size.value))

    def get_ch_name(self, slot: int, channel_list: Sequence[int]) -> tuple[str, ...]:
        """
        Binding of CAENHV_GetChName()
        """
        n_indexes = len(channel_list)
        if n_indexes == 0:
            return []  # type: ignore
        l_index_list = (ct.c_ushort * n_indexes)(*channel_list)
        n_allocated_values = n_indexes + 1  # In case library tries to set an empty string after the last
        l_value = (ct.c_char * (self.MAX_CH_NAME * n_allocated_values))()
        lib.get_ch_name(self.handle, slot, n_indexes, l_index_list, l_value)
        return tuple(_string.from_n_char_array(l_value, self.MAX_CH_NAME, n_indexes))

    def set_ch_name(self, slot: int, channel_list: Sequence[int], name: str) -> None:
        """
        Binding of CAENHV_SetChName()
        """
        n_indexes = len(channel_list)
        if n_indexes == 0:
            return
        l_index_list = (ct.c_ushort * n_indexes)(*channel_list)
        lib.set_ch_name(self.handle, slot, n_indexes, l_index_list, name.encode('ascii'))

    def get_ch_param(self, slot: int, channel_list: Sequence[int], name: str) -> Union[list[str], list[float], list[int]]:
        """
        Binding of CAENHV_GetChParam()
        """
        n_indexes = len(channel_list)
        if n_indexes == 0:
            return []  # type: ignore
        l_index_list = (ct.c_ushort * n_indexes)(*channel_list)
        first_index = channel_list[0]  # Assuming all types are equal
        param_type = self.__get_param_type(slot, name, first_index)
        l_data = _PARAM_TYPE_GET_ARG[param_type](n_indexes)
        if param_type is ParamType.STRING and self.__char_p_p_str_ch_param_arg():
            # Some systems require a char** instead of a char*: we build it using the same buffer, with different decode.
            p_begin = ct.addressof(l_data)
            p_size = ct.sizeof(l_data)
            assert p_size % _STR_SIZE == 0
            l_data_proxy = (ct.c_void_p * n_indexes)(*range(p_begin, p_begin + p_size, _STR_SIZE))
        else:
            l_data_proxy = l_data
        lib.get_ch_param(self.handle, slot, name.encode('ascii'), n_indexes, l_index_list, l_data_proxy)
        if param_type is ParamType.STRING:
            if self.__char_p_p_str_ch_param_arg():
                return list(_string.from_n_char_array(l_data, _STR_SIZE, n_indexes))
            else:
                return list(_string.from_char(l_data, n_indexes))
        else:
            return l_data[:]

    def set_ch_param(self, slot: int, channel_list: Sequence[int], name: str, value: Optional[Union[str, float, int]]) -> None:
        """
        Binding of CAENHV_SetChParam()

        See comment on set_bd_param() for additional information.
        """
        n_indexes = len(channel_list)
        if n_indexes == 0:
            return
        l_index_list = (ct.c_ushort * n_indexes)(*channel_list)
        first_index = channel_list[0]  # Assuming all types are equal
        param_type = self.__get_param_type(slot, name, first_index)
        l_data = _PARAM_TYPE_SET_ARG[param_type](value, n_indexes)
        lib.set_ch_param(self.handle, slot, name.encode('ascii'), n_indexes, l_index_list, ct.byref(l_data))

    @_cache.cached(cache_manager=__cache_manager)
    def get_exec_comm_list(self) -> tuple[str, ...]:
        """
        Binding of CAENHV_GetExecCommList()
        """
        l_num_comm = ct.c_ushort()
        g_comm_name_list = lib.auto_ptr(ct.c_char)
        with g_comm_name_list as l_cnl:
            lib.get_exec_comm_list(self.handle, l_num_comm, l_cnl)
            return tuple(_string.from_char_p(l_cnl, l_num_comm.value))

    def exec_comm(self, name: str) -> None:
        """
        Binding of CAENHV_ExecComm()
        """
        lib.exec_comm(self.handle, name.encode('ascii'))

    def subscribe_system_params(self, param_list: Sequence[str]) -> None:
        """
        Binding of CAENHV_SubscribeSystemParams()
        """
        self.__subscribe_params(param_list, None, None)

    def subscribe_board_params(self, slot: int, param_list: Sequence[str]) -> None:
        """
        Binding of CAENHV_SubscribeBoardParams()
        """
        self.__subscribe_params(param_list, slot, None)

    def subscribe_channel_params(self, slot: int, channel: int, param_list: Sequence[str]) -> None:
        """
        Binding of CAENHV_SubscribeChannelParams()
        """
        return self.__subscribe_params(param_list, slot, channel)

    def unsubscribe_system_params(self, param_list: Sequence[str]) -> None:
        """
        Binding of CAENHV_UnSubscribeSystemParams()
        """
        return self.__unsubscribe_params(param_list, None, None)

    def unsubscribe_board_params(self, slot: int, param_list: Sequence[str]) -> None:
        """
        Binding of CAENHV_UnSubscribeBoardParams()
        """
        return self.__unsubscribe_params(param_list, slot, None)

    def unsubscribe_channel_params(self, slot: int, channel: int, param_list: Sequence[str]) -> None:
        """
        Binding of CAENHV_UnSubscribeChannelParams()
        """
        return self.__unsubscribe_params(param_list, slot, channel)

    def get_event_data(self) -> tuple[tuple[EventData, ...], SystemStatus]:
        """
        Binding of CAENHV_GetEventData()

        Even if the first call of the C API is a socket rather
        than an handle, we do here a trick to make this anomaly
        transparent to the user.
        """
        self.__init_events_client()
        assert self.__skt_client is not None
        l_system_status = _SystemStatusRaw()
        g_event_data = lib.evt_data_auto_ptr()
        l_data_number = ct.c_uint()
        with g_event_data as l_ed:
            lib.get_event_data(self.__skt_client.fileno(), l_system_status, l_ed, l_data_number)
            events = tuple(self.__decode_event_data(l_ed, l_data_number.value))
        return events, SystemStatus.from_raw(l_system_status)

    # Private utilities

    def __get_prop(self, slot: int, name: str, prop_name: bytes, channel: Optional[int], var_type: Callable[..., _R], *args, **kwargs) -> _R:
        """
        Get single parameter property.

        If args are defined, they are used to construct the value passed
        to the C library, and could be used to catch errors (see comment
        in __get_param_type). If default is set in kwargs, it returns
        var_type(default) in case of PARAMPROPNOTFOUND error.
        """
        l_value = var_type(*args)
        try:
            if channel is None:
                lib.get_bd_param_prop(self.handle, slot, name.encode('ascii'), prop_name, ct.byref(l_value))
            else:
                lib.get_ch_param_prop(self.handle, slot, channel, name.encode('ascii'), prop_name, ct.byref(l_value))
        except Error as ex:
            if ex.code is Error.Code.PARAMPROPNOTFOUND:
                default = kwargs.get('default')
                if default is not None:
                    return var_type(default)
            raise ex
        return l_value

    def __get_param_prop(self, slot: int, name: str, channel: Optional[int]) -> ParamProp:
        """
        Get all parameter properties.
        Cannot be cached since minval/maxval may depend on the value of
        other parameters.
        """
        # Mandatory values (raise if name is not valid)
        param_type = self.__get_param_type(slot, name, channel)
        param_mode = self.__get_param_mode(slot, name, channel)
        res = ParamProp(param_type, param_mode)
        # Optional values
        if param_type is ParamType.NUMERIC:
            # Always defined
            res.unit = ParamUnit(self.__get_prop(slot, name, b'Unit', channel, ct.c_ushort).value)
            res.exp = self.__get_prop(slot, name, b'Exp', channel, ct.c_short).value
            # Not defined on some old systems
            res.minval = self.__get_prop(slot, name, b'Minval', channel, ct.c_float, default=0.).value
            res.maxval = self.__get_prop(slot, name, b'Maxval', channel, ct.c_float, default=0.).value
            res.decimal = self.__get_prop(slot, name, b'Decimal', channel, ct.c_short, default=0).value
            if self.__resol_param_prop():
                res.resol = self.__get_prop(slot, name, b'Resol', channel, ct.c_short, default=1).value
        elif param_type is ParamType.ONOFF:
            res.onstate = self.__get_prop(slot, name, b'Onstate', channel, ct.c_char * _STR_SIZE).value.decode('ascii')
            res.offstate = self.__get_prop(slot, name, b'Offstate', channel, ct.c_char * _STR_SIZE).value.decode('ascii')
        elif param_type is ParamType.ENUM:
            res.minval = self.__get_prop(slot, name, b'Minval', channel, ct.c_float).value
            res.maxval = self.__get_prop(slot, name, b'Maxval', channel, ct.c_float).value
            n_enums = int(res.maxval - res.minval + 1)
            assert n_enums <= self.MAX_ENUM_VALS
            l_value = self.__get_prop(slot, name, b'Enum', channel, ct.c_char * (self.MAX_ENUM_NAME * self.MAX_ENUM_VALS))
            res.enum = tuple(_string.from_n_char_array(l_value, self.MAX_ENUM_NAME, n_enums))
        return res

    @_cache.cached(cache_manager=__cache_manager, maxsize=4096)
    def __get_param_type(self, slot: int, name: str, channel: Optional[int]) -> ParamType:
        """
        Simplified version of __get_param_prop used internally to
        retrieve just param type.
        """
        # Initialize arg to -1 to detect errors because library functions, at least
        # on some modules like N1470, return success even if the parameter does not
        # exist. We detect this error as the value is not modified by the library,
        # and we map it to a library Error value. The check is not done on all the
        # properties because, in case of invalid parameter, it will fail in the very
        # first call.
        # pylint: disable=W0212
        value = self.__get_prop(slot, name, b'Type', channel, ct.c_uint, ParamType._INVALID).value
        if value == ParamType._INVALID:
            raise Error('Parameter not found', Error.Code.PARAMNOTFOUND.value, '__get_param_type')
        return ParamType(value)

    @_cache.cached(cache_manager=__cache_manager, maxsize=4096)
    def __get_param_mode(self, slot: int, name: str, channel: Optional[int]) -> ParamMode:
        """
        Simplified version of __get_param_prop used internally to
        retrieve just param mode.
        """
        # See comment on __get_param_type
        # pylint: disable=W0212
        value = self.__get_prop(slot, name, b'Mode', channel, ct.c_uint, ParamType._INVALID).value
        if value == ParamType._INVALID:
            raise Error('Parameter not found', Error.Code.PARAMNOTFOUND.value, '__get_param_mode')
        return ParamMode(value)

    def __check_events_support(self) -> None:
        """
        SY1527/SY2527 have a legacy version of events not supported by
        this binding
        """
        if self.system_type in (SystemType.SY1527, SystemType.SY2527):
            raise NotImplementedError('Legacy events not supported by this binding.')

    def __library_event_thread(self) -> bool:
        """
        Devices with polling thread within library
        """
        return self.system_type not in (SystemType.SY4527, SystemType.SY5527, SystemType.R6060)

    def __resol_param_prop(self) -> bool:
        """
        Devices with weird Resol parameter property on numeric data
        """
        return self.system_type in (SystemType.V8100,)

    def __new_events_format(self) -> bool:
        """
        Devices with new events format, with socket opened within the
        library
        """
        return self.system_type in (SystemType.R6060,)

    def __char_p_p_str_bd_param_arg(self) -> bool:
        """
        Devices that requires a char** as argument of get_bd_param of
        type STRING
        """
        return self.system_type in (SystemType.N1068, SystemType.N1168, SystemType.N568E)

    def __char_p_p_str_ch_param_arg(self) -> bool:
        """
        Devices that requires a char** as argument of get_ch_param of
        type STRING
        """
        return self.system_type in (SystemType.N1068, SystemType.N1168, SystemType.N568E, SystemType.V8100)

    def __subscribe_params(self, param_list: Sequence[str], slot: Optional[int], channel: Optional[int]) -> None:
        """
        Binding of CAENHV_Subscribe*Params()
        """
        param_list_len = len(param_list)
        if param_list_len == 0:
            return
        self.__init_events_server()
        l_param_name_list = ':'.join(param_list).encode('ascii')
        l_result_codes = (ct.c_char * param_list_len)()
        if slot is None:
            lib.subscribe_system_params(self.handle, self.__skt_port, l_param_name_list, param_list_len, l_result_codes)
        elif channel is None:
            lib.subscribe_board_params(self.handle, self.__skt_port, slot, l_param_name_list, param_list_len, l_result_codes)
        else:
            lib.subscribe_channel_params(self.handle, self.__skt_port, slot, channel, l_param_name_list, param_list_len, l_result_codes)
        # l_result_codes values are not instances of ::CAENHVRESULT
        failed_params = {par: ec for par, ec in zip(param_list, l_result_codes.raw) if ec}
        if failed_params:
            raise RuntimeError(f'subscribe failed at params {failed_params}')

    def __unsubscribe_params(self, param_list: Sequence[str], slot: Optional[int], channel: Optional[int]) -> None:
        """
        Binding of CAENHV_UnSubscribe*Params()
        """
        param_list_len = len(param_list)
        if param_list_len == 0:
            return
        l_param_name_list = ':'.join(param_list).encode('ascii')
        l_result_codes = (ct.c_char * param_list_len)()
        if slot is None:
            lib.unsubscribe_system_params(self.handle, self.__skt_port, l_param_name_list, param_list_len, l_result_codes)
        elif channel is None:
            lib.unsubscribe_board_params(self.handle, self.__skt_port, slot, l_param_name_list, param_list_len, l_result_codes)
        else:
            lib.unsubscribe_channel_params(self.handle, self.__skt_port, slot, channel, l_param_name_list, param_list_len, l_result_codes)
        # l_result_codes values are not instances of ::CAENHVRESULT
        failed_params = {par: ec for par, ec in zip(param_list, l_result_codes.raw) if ec}
        if failed_params:
            raise RuntimeError(f'unsubscribe failed at params {failed_params}')

    def __create_server(self):
        """
        Initialize a server socket for events.

        Socket will be compatible with both IPv6 and IPv4, if supported.
        """
        # If possible, bind to loopback to prevent ask for administator rights on Windows
        bind_addr = '127.0.0.1' if self.__library_event_thread() else ''
        for port in range(self.__first_bind_port, 65536):
            # Suppress OSError raised if bind fails
            with suppress(OSError):
                return socket.create_server((bind_addr, port), family=socket.AF_INET, backlog=1)
        raise RuntimeError('No available port found.')

    def __init_events_server(self):
        if self.__skt_server is not None:
            return
        self.__check_events_support()
        if self.__new_events_format():
            # Nothing to do, client socket initialized within the library. We store
            # an uninitialized value just as a reminder that a subscription has been
            # made, to be checked later in __init_events_client to be sure
            # EventDataSocket is meaningful. No need to set port value, it's ignored.
            self.__skt_server = socket.socket()
        else:
            self.__skt_server = self.__create_server()

    def __init_events_client(self):
        if self.__skt_client is not None:
            return
        self.__check_events_support()
        if self.__skt_server is None:
            # Initialization is done on first call to a subscribe function
            raise RuntimeError('No subscription done.')
        if self.__new_events_format():
            # A socket has already been opened by the library: we must use the value
            # returned by the special system property EventDataSocket to get the fd.
            # Since self.get_sys_prop calls get_sys_prop_info to get the output type,
            # and since that function is not implemented for EventDataSocket being a
            # library only property, that returns a socket object, we call directly
            # the ctypes object.
            l_value = _socket()
            lib.get_sys_prop(self.handle, b'EventDataSocket', ct.byref(l_value))
            self.__skt_client = socket.socket(fileno=l_value.value)
        else:
            self.__skt_client, addr_info = self.__skt_server.accept()
            if self.__library_event_thread():
                # If connecting to library event thread, ignore the first string
                # that should contain the string used as InitSystem argument,
                # except when connecting using TCPIP.
                assert addr_info[0] == '127.0.0.1'
                # Read char by char until null terminator
                arg = b''.join(iter(lambda: self.__skt_client.recv(1), b'\x00'))
                assert self.arg == arg.decode('ascii')

    @property
    def __skt_port(self) -> int:
        assert self.__skt_server is not None
        return self.__skt_server.getsockname()[1]  # Return (host, port) on IPv4 and (host, port, flowinfo, scopeid) on IPv6

    def __extended_get_param_type(self, slot: int, name: str, channel: Optional[int]) -> ParamType:
        """
        Same of __get_param_type, with a workaround for Name: even if
        not being a real channel parameter, i.e. get_ch_param_prop does
        not work, changes are sent as events of type PARAMETER.
        """
        if channel is not None and name == 'Name':
            return ParamType.STRING
        return self.__get_param_type(slot, name, channel)

    def __decode_event_value(self, event_type: EventType, board_index: int, channel_index: int, item_id: str, value: _IdValueRaw) -> Union[str, float, int]:
        if event_type is not EventType.PARAMETER:
            return -1
        if board_index == -1:
            prop_type = self.get_sys_prop_info(item_id).type
            return _SYS_PROP_TYPE_EVENT_ARG[prop_type](value)
        param_type = self.__extended_get_param_type(board_index, item_id, channel_index if channel_index != -1 else None)
        return _PARAM_TYPE_EVENT_ARG[param_type](value)

    def __decode_event_data(self, event_data: ct._Pointer, n_events: int) -> Iterator[EventData]:
        for i in range(n_events):
            event: _EventDataRaw = event_data[i]
            item_id = event.ItemID.decode('ascii')
            if not item_id:
                # There could be empty events, expecially from library event thread, to be ignored.
                assert self.__library_event_thread()
                continue
            event_type = EventType(event.Type)
            system_handle = event.SystemHandle
            assert system_handle == self.handle  # should always be the same
            board_index = event.BoardIndex
            channel_index = event.ChannelIndex
            value = self.__decode_event_value(event_type, board_index, channel_index, item_id, event.Value)
            yield EventData(event_type, item_id, board_index, channel_index, value)

    # Python utilities

    @contextmanager
    def device_closed(self):
        """Close and reopen the device. Useful for reboots."""
        self.close()
        try:
            yield
        finally:
            self.connect()

    def __enter__(self):
        """Used by `with`"""
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """Called when exiting from `with` block"""
        if self.__opened:
            self.close()

    def __hash__(self) -> int:
        return hash(self.handle)
