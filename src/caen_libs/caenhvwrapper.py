__author__ = 'Giovanni Cerretani'
__copyright__ = 'Copyright (C) 2024 CAEN SpA'
__license__ = 'LGPL-3.0-or-later'  # SPDX-License-Identifier

from contextlib import contextmanager
import ctypes as ct
import ctypes.wintypes as ctw
from dataclasses import dataclass, field
from enum import IntEnum, unique
import socket
import sys
from typing import Callable, ClassVar, Dict, List, Optional, Sequence, Tuple, Type, TypeVar, Union

from caen_libs import _utils


@unique
class ErrorCode(IntEnum):
    """
    Wrapper to ::CAENHVRESULT
    """
    UNKNOWN                 = 0xFFFF  # Special value for Python wrapper
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
    def _missing_(cls, value):
        """Sometimes library return values not contained in the enumerator"""
        return cls.UNKNOWN


@unique
class SystemType(IntEnum):
    """
    Wrapper to ::CAENHV_SYSTEM_TYPE_t
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
    Wrapper to Link Types for InitSystem
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
    Wrapper to ::CAENHV_EVT_STATUS_t
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


@dataclass
class SystemStatus:
    """
    Wrapper to ::CAENHV_SYSTEMSTATUS_t
    """
    system: EventStatus
    board: List[EventStatus]


@unique
class EventType(IntEnum):
    """
    Wrapper to ::CAENHV_ID_TYPE_t
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


EventValue = Union[str, float, int]
"""
Wrapper to ::IDValue_t
"""


class _EventDataRaw(ct.Structure):
    _fields_ = [
        ('Type', ct.c_int),
        ('SystemHandle', ct.c_int),
        ('BoardIndex', ct.c_int),
        ('ChannelIndex', ct.c_int),
        ('ItemID', ct.c_char * 20),
        ('Value', _IdValueRaw),
    ]


@dataclass
class EventData:
    """
    Wrapper to ::CAENHVEVENT_TYPE_t
    """
    type: EventType
    item_id: str
    system_handle: int = field(default=-1)
    board_index: int = field(default=-1)
    channel_index: int = field(default=-1)
    value: EventValue = field(default=-1)


@dataclass
class Board:
    """
    Type returned by ::CAENHV_GetCrateMap
    """
    model: str
    description: str
    serial_number: int
    n_channel: int
    fw_version: Tuple[int, ...]


@unique
class SysPropType(IntEnum):
    """
    Wrapper to ::SYSPROP_TYPE_*
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
    Wrapper to ::SYSPROP_MODE_*
    """
    RDONLY  = 0
    WRONLY  = 1
    RDWR    = 2


@dataclass
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
    Wrapper to ::PARAM_TYPE_*
    """
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
    Wrapper to ::PARAM_MODE_*
    """
    RDONLY  = 0
    WRONLY  = 1
    RDWR    = 2


@unique
class ParamUnit(IntEnum):
    """
    Wrapper to ::PARAM_UN_*
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


@dataclass
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
    onstate: Optional[str] = field(default=None)
    offstate: Optional[str] = field(default=None)
    enum: Optional[List[str]] = field(default=None)


class Error(RuntimeError):
    """
    Raised when a wrapped C API function returns
    negative values.
    """

    code: ErrorCode  ## Error code as instance of ErrorCode
    message: str  ## Message description
    func: str  ## Name of failed function

    def __init__(self, res: int, func: str) -> None:
        self.code = ErrorCode(res)
        self.func = func
        super().__init__(f'{self.func} failed: {self.code.name}')


# Utility definitions
_P = ct.POINTER
_c_char_p = _P(ct.c_char)  # ct.c_char_p is not fine due to its own memory management
_c_char_p_p = _P(_c_char_p)
_c_ubyte_p = _P(ct.c_ubyte)
_c_ubyte_p_p = _P(_c_ubyte_p)
_c_ushort_p = _P(ct.c_ushort)
_c_ushort_p_p = _P(_c_ushort_p)
_c_int_p = _P(ct.c_int)
_c_uint_p = _P(ct.c_uint)
_system_status_p = _P(_SystemStatusRaw)
_event_data_p = _P(_EventDataRaw)
_event_data_p_p = _P(_event_data_p)
if sys.platform == 'win32':
    _socket = ctw.WPARAM  # Actually a SOCKET is UINT_PTR, same as WPARAM
else:
    _socket = ct.c_int


_SYS_PROP_TYPE_GET_ARG = {
    SysPropType.STR:        lambda v: v.value.decode(),
    SysPropType.REAL:       lambda v: ct.cast(v, _P(ct.c_float)).contents.value,
    SysPropType.UINT2:      lambda v: ct.cast(v, _P(ct.c_uint16)).contents.value,
    SysPropType.UINT4:      lambda v: ct.cast(v, _P(ct.c_uint32)).contents.value,
    SysPropType.INT2:       lambda v: ct.cast(v, _P(ct.c_int16)).contents.value,
    SysPropType.INT4:       lambda v: ct.cast(v, _P(ct.c_int32)).contents.value,
    SysPropType.BOOLEAN:    lambda v: bool(ct.cast(v, _P(ct.c_uint)).contents.value),
}


_SYS_PROP_TYPE_SET_ARG = {
    SysPropType.STR:        lambda v: v.encode(),
    SysPropType.REAL:       lambda v: ct.pointer(ct.c_float(v)),
    SysPropType.UINT2:      lambda v: ct.pointer(ct.c_uint16(v)),
    SysPropType.UINT4:      lambda v: ct.pointer(ct.c_uint32(v)),
    SysPropType.INT2:       lambda v: ct.pointer(ct.c_int16(v)),
    SysPropType.INT4:       lambda v: ct.pointer(ct.c_int32(v)),
    SysPropType.BOOLEAN:    lambda v: ct.pointer(ct.c_uint(v)),
}


_PARAM_TYPE_GET_ARG: Dict[ParamType, Callable[[int], ct.Array]] = {
    ParamType.NUMERIC:  lambda n: (ct.c_float * n)(),
    ParamType.ONOFF:    lambda n: (ct.c_int * n)(),
    ParamType.CHSTATUS: lambda n: (ct.c_int * n)(),
    ParamType.BDSTATUS: lambda n: (ct.c_int * n)(),
    ParamType.BINARY:   lambda n: (ct.c_int * n)(),
    ParamType.STRING:   lambda n: (ct.c_char * (1024 * n))(),
    ParamType.ENUM:     lambda n: (ct.c_int * n)(),
    ParamType.CMD:      lambda n: (ct.c_int * n)(),
}


_PARAM_TYPE_SET_ARG: Dict[ParamType, Callable] = {
    ParamType.NUMERIC:  ct.c_float,
    ParamType.ONOFF:    ct.c_int,
    ParamType.CHSTATUS: ct.c_int,
    ParamType.BDSTATUS: ct.c_int,
    ParamType.BINARY:   ct.c_int,
    ParamType.STRING:   lambda v: v.encode(),
    ParamType.ENUM:     ct.c_int,
    ParamType.CMD:      ct.c_int,
}


_SYS_PROP_TYPE_EVENT_ARG = {
    SysPropType.STR:        lambda v: v.StringValue.decode(),
    SysPropType.REAL:       lambda v: v.FloatValue,
    SysPropType.UINT2:      lambda v: v.IntValue,
    SysPropType.UINT4:      lambda v: v.IntValue,
    SysPropType.INT2:       lambda v: v.IntValue,
    SysPropType.INT4:       lambda v: v.IntValue,
    SysPropType.BOOLEAN:    lambda v: v.IntValue,
}


_PARAM_TYPE_EVENT_ARG = {
    ParamType.NUMERIC:  lambda v: v.FloatValue,
    ParamType.ONOFF:    lambda v: v.IntValue,
    ParamType.CHSTATUS: lambda v: v.IntValue,
    ParamType.BDSTATUS: lambda v: v.IntValue,
    ParamType.BINARY:   lambda v: v.IntValue,
    ParamType.STRING:   lambda v: v.StringValue.decode(),
    ParamType.ENUM:     lambda v: v.IntValue,
    ParamType.CMD:      lambda v: v.IntValue,
}

class _Lib(_utils.Lib):

    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.__load_api()

    def __load_api(self) -> None:
        # Load API not related to devices
        self.get_event_data = self.__get('GetEventData', _socket, _system_status_p, _event_data_p_p, _c_uint_p)
        self.free_event_data = self.__get('FreeEventData', _event_data_p_p)
        self.__free = self.__get('Free', ct.c_void_p)

        # CAENHVLibSwRel has non conventional API
        self.___sw_rel = self.__lib.CAENHVLibSwRel
        self.___sw_rel.argtypes = []
        self.___sw_rel.restype = ct.c_char_p

        # Load API
        self.init_system = self.__get('InitSystem', ct.c_int, ct.c_int, ct.c_void_p, _c_char_p, _c_char_p, _c_int_p)
        self.deinit_system = self.__get('DeinitSystem', ct.c_int)
        self.get_crate_map = self.__get('GetCrateMap', ct.c_int, _c_ushort_p, _c_ushort_p_p, _c_char_p_p, _c_char_p_p, _c_ushort_p_p, _c_ubyte_p_p, _c_ubyte_p_p)
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

        # CAENHV_GetError has non conventional API
        self.get_error = self.__lib.CAENHV_GetError
        self.get_error.argtypes = [ct.c_int]
        self.get_error.restype = ct.c_char_p

    def __api_errcheck(self, res: int, func: Callable, _: Tuple) -> int:
        if res != ErrorCode.OK:
            raise Error(res, func.__name__)
        return res

    def __get(self, name: str, *args: Type) -> Callable[..., int]:
        # Use lib_variadic as API is __cdecl
        func = getattr(self.lib_variadic, f'CAENHV_{name}')
        func.argtypes = args
        func.restype = ct.c_int
        func.errcheck = self.__api_errcheck
        return func

    # C API wrappers

    def sw_release(self) -> str:
        """
        Wrapper to CAENHVLibSwRel()
        """
        return self.___sw_rel().decode()

    @contextmanager
    def auto_ptr(self, pointer_type: Type):
        """Context manager to auto free on scope exit"""
        value = pointer_type()
        try:
            yield value
        finally:
            self.__free(value)

    # Python utilities

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.path})'

    def __str__(self) -> str:
        return self.path


lib: _Lib


lib = _Lib('CAENHVWrapper')


def _str_list_from_char(data: Union[ct.c_char, ct.Array[ct.c_char]], n_strings: int) -> List[str]:
    """
    Split a buffer into a list of N string.
    Strings are separated by the null terminator.
    For ct.c_char and arrays of it.
    """
    res: List[str] = []
    offset = 0
    for _ in range(n_strings):
        value = ct.string_at(ct.addressof(data) + offset).decode()
        offset += len(value) + 1
        res.append(value)
    return res


def _str_list_from_char_p(data: ct._Pointer, n_strings: int) -> List[str]:
    """
    Same of _str_list_from_char.
    For pointers to ct.c_char, to avoid dereferences in case of zero size.
    """
    return _str_list_from_char(data.contents, n_strings) if n_strings != 0 else []


def _str_list_from_char_array(data: Union[ct.c_char, ct.Array[ct.c_char]], string_size: int) -> List[str]:
    """
    Split a buffer of fixed size string.
    Size is deduced by the first zero size string found.
    For ct.c_char and arrays of it.
    """
    res: List[str] = []
    offset = 0
    while True:
        value = ct.string_at(ct.addressof(data) + offset).decode()
        if len(value) == 0:
            return res
        offset += string_size
        res.append(value)


def _str_list_from_n_char_array(data: Union[ct.c_char, ct.Array[ct.c_char]], string_size: int, n_strings: int) -> List[str]:
    """
    Split a buffer of fixed size string.
    Size is passed as parameter.
    For ct.c_char and arrays of it.
    """
    res: List[str] = []
    offset = 0
    for _ in range(n_strings):
        value = ct.string_at(ct.addressof(data) + offset).decode()
        offset += string_size
        res.append(value)
    return res


def _str_list_from_n_char_array_p(data: ct._Pointer, string_size: int, n_strings: int) -> List[str]:
    """
    Same of _str_list_from_n_char_array.
    For pointers to ct.c_char, to avoid dereferences in case of zero size.
    """
    return _str_list_from_n_char_array(data.contents, string_size, n_strings) if n_strings != 0 else []


@dataclass
class Device:
    """
    Class representing a device.
    """

    # Public members
    handle: int
    opened: bool = field(repr=False)
    system_type: SystemType = field(repr=False)
    link_type: LinkType = field(repr=False)
    arg: str = field(repr=False)
    username: str = field(repr=False)
    password: str = field(repr=False)

    # Static private members
    __node_cache_manager: ClassVar[_utils.CacheManager] = _utils.CacheManager()

    # Constants
    MAX_PARAM_NAME = 10
    MAX_CH_NAME = 12
    FIRST_BIND_PORT = 10001  # This wrapper will bind TCP ports starting from this value

    def __post_init__(self):
        # Internal events related stuff
        self.__port = 0
        self.__skt_server = None
        self.__skt_client = None

    def __del__(self) -> None:
        if self.opened:
            self.close()

    # C API wrappers

    _T = TypeVar('_T', bound='Device')

    @classmethod
    def open(cls: Type[_T], system_type: SystemType, link_type: LinkType, arg: str, username: str = '', password: str = '') -> _T:
        """
        Wrapper to CAENHV_InitSystem()
        """
        l_handle = ct.c_int()
        lib.init_system(system_type.value, link_type.value, arg.encode(), username.encode(), password.encode(), l_handle)
        return cls(l_handle.value, True, system_type, link_type, arg, username, password)

    def connect(self) -> None:
        """
        Wrapper to CAENHV_InitSystem()
        New instances should be created with open().
        This is meant to reconnect a device closed with close().
        """
        if self.opened:
            raise RuntimeError('Already connected.')
        l_handle = ct.c_int()
        lib.init_system(self.system_type, self.link_type, self.arg.encode(), self.username.encode(), self.password.encode(), l_handle)
        self.handle = l_handle.value
        self.opened = True

    @_utils.lru_cache_clear(cache_manager=__node_cache_manager)
    def close(self) -> None:
        """
        Wrapper to CAENHV_DeinitSystem()

        This will also clear class cache.
        """
        lib.deinit_system(self.handle)
        self.opened = False

    @_utils.lru_cache_clear(cache_manager=__node_cache_manager)
    def get_crate_map(self) -> List[Board]:
        """
        Wrapper to CAENHV_GetCrateMap()

        This will also clear class cache, since the functio
        invalidates some internal stuctures of the C library.
        """
        l_nos = ct.c_ushort()
        g_nocl = lib.auto_ptr(_c_ushort_p)
        g_ml = lib.auto_ptr(_c_char_p)
        g_dl = lib.auto_ptr(_c_char_p)
        g_snl = lib.auto_ptr(_c_ushort_p)
        g_frminl = lib.auto_ptr(_c_ubyte_p)
        g_frmaxl = lib.auto_ptr(_c_ubyte_p)
        with g_nocl as l_nocl, g_ml as l_ml, g_dl as l_dl, g_snl as l_snl, g_frminl as l_frminl, g_frmaxl as l_frmaxl:
            lib.get_crate_map(self.handle, l_nos, l_nocl, l_ml, l_dl, l_snl, l_frminl, l_frmaxl)
            ml = _str_list_from_char_p(l_ml, l_nos.value)
            dl = _str_list_from_char_p(l_dl, l_nos.value)
            return [Board(ml[i], dl[i], l_snl[i], l_nocl[i], (l_frmaxl[i], l_frminl[i])) for i in range(l_nos.value)]

    @_utils.lru_cache_method(cache_manager=__node_cache_manager)
    def get_sys_prop_list(self) -> List[str]:
        """
        Wrapper to CAENHV_GetSysPropList()
        """
        l_num_prop = ct.c_ushort()
        g_prop_name_list = lib.auto_ptr(_c_char_p)
        with g_prop_name_list as l_pnl:
            lib.get_sys_prop_list(self.handle, l_num_prop, l_pnl)
            return _str_list_from_char_p(l_pnl, l_num_prop.value)

    @_utils.lru_cache_method(cache_manager=__node_cache_manager)
    def get_sys_prop_info(self, name: str) -> SysProp:
        """
        Wrapper to CAENHV_GetSysPropInfo()
        """
        l_prop_mode = ct.c_uint()
        l_prop_type = ct.c_uint()
        lib.get_sys_prop_info(self.handle, name.encode(), l_prop_mode, l_prop_type)
        return SysProp(name, SysPropMode(l_prop_mode.value), SysPropType(l_prop_type.value))

    def get_sys_prop(self, name: str) -> Union[str, float, int, bool]:
        """
        Wrapper to CAENHV_GetSysProp()
        """
        l_value = ct.create_string_buffer(1024)  # should be enough for all types
        lib.get_sys_prop(self.handle, name.encode(), l_value)
        prop_type = self.get_sys_prop_info(name).type
        return _SYS_PROP_TYPE_GET_ARG[prop_type](l_value)

    def set_sys_prop(self, name: str, value: Union[str, float, int, bool]) -> None:
        """
        Wrapper to CAENHV_SetSysProp()
        """
        prop_type = self.get_sys_prop_info(name).type
        l_value = _SYS_PROP_TYPE_SET_ARG[prop_type](value)
        lib.set_sys_prop(self.handle, name.encode(), l_value)

    def get_bd_param(self, slot_list: Sequence[int], name: str) -> Union[List[float], List[int], List[str]]:
        """
        Wrapper to CAENHV_GetBdParam()
        """
        n_indexes = len(slot_list)
        first_index = slot_list[0]  # Assuming all types are equal
        param_type = self.__get_param_type(first_index, name)
        l_data = _PARAM_TYPE_GET_ARG[param_type](n_indexes)
        l_index_list = (ct.c_ushort * n_indexes)(*slot_list)
        lib.get_bd_param(self.handle, n_indexes, l_index_list, name.encode(), l_data)
        if param_type == ParamType.STRING:
            return _str_list_from_char(l_data, n_indexes)
        else:
            return list(l_data)

    def set_bd_param(self, slot_list: Sequence[int], name: str, value: Union[float, int, str]) -> None:
        """
        Wrapper to CAENHV_SetBdParam()
        """
        n_indexes = len(slot_list)
        first_index = slot_list[0]  # Assuming all types are equal
        param_type = self.__get_param_type(first_index, name)
        l_data = _PARAM_TYPE_SET_ARG[param_type](value)
        l_index_list = (ct.c_ushort * n_indexes)(*slot_list)
        lib.set_bd_param(self.handle, n_indexes, l_index_list, name.encode(), l_data)

    @_utils.lru_cache_method(cache_manager=__node_cache_manager)
    def get_bd_param_prop(self, slot: int, name: str) -> ParamProp:
        """
        Wrapper to CAENHV_GetBdParamProp()
        """
        return self.__get_param_prop(slot, name)

    @_utils.lru_cache_method(cache_manager=__node_cache_manager)
    def get_bd_param_info(self, slot: int) -> List[str]:
        """
        Wrapper to CAENHV_GetBdParamInfo()
        """
        g_value = lib.auto_ptr(_c_char_p)
        with g_value as l_value:
            lib.get_bd_param_info(self.handle, slot, l_value)
            return _str_list_from_char_array(l_value.contents, self.MAX_PARAM_NAME)

    def test_bd_presence(self, slot: int) -> Board:
        """
        Wrapper to CAENHV_TestBdPresence()
        """
        l_nr_of_ch = ct.c_ushort()
        g_model = lib.auto_ptr(_c_char_p)
        g_description = lib.auto_ptr(_c_char_p)
        l_ser_num = ct.c_ushort()
        l_fmw_rel_min = ct.c_ubyte()
        l_fmw_rel_max = ct.c_ubyte()
        with g_model as l_m, g_description as l_d:
            lib.test_bd_presence(self.handle, slot, l_nr_of_ch, l_m, l_d, l_ser_num, l_fmw_rel_min, l_fmw_rel_max)
            model = l_m.contents.value.decode()
            description = l_d.contents.value.decode()
            return Board(model, description, l_ser_num.value, l_nr_of_ch.value, (l_fmw_rel_max.value, l_fmw_rel_min.value))

    @_utils.lru_cache_method(cache_manager=__node_cache_manager, maxsize=4096)
    def get_ch_param_prop(self, slot: int, channel: int, name: str) -> ParamProp:
        """
        Wrapper to CAENHV_GetChParamProp()
        """
        return self.__get_param_prop(slot, name, channel)

    @_utils.lru_cache_method(cache_manager=__node_cache_manager, maxsize=4096)
    def get_ch_param_info(self, slot: int, channel: int) -> List[str]:
        """
        Wrapper to CAENHV_GetChParamInfo()
        """
        g_value = lib.auto_ptr(_c_char_p)
        with g_value as l_value:
            l_size = ct.c_int()
            lib.get_ch_param_info(self.handle, slot, channel, l_value, l_size)
            res = _str_list_from_n_char_array_p(l_value, self.MAX_PARAM_NAME, l_size.value)
            return res

    def get_ch_name(self, slot: int, channel_list: Sequence[int]) -> List[str]:
        """
        Wrapper to CAENHV_GetChName()
        """
        n_indexes = len(channel_list)
        l_index_list = (ct.c_ushort * n_indexes)(*channel_list)
        n_allocated_values = n_indexes + 1  # In case library tries to set an empty string after the last
        l_value = (ct.c_char * (self.MAX_CH_NAME * n_allocated_values))()
        lib.get_ch_name(self.handle, slot, n_indexes, l_index_list, l_value)
        return _str_list_from_n_char_array(l_value, self.MAX_CH_NAME, n_indexes)

    def set_ch_name(self, slot: int, channel_list: Sequence[int], name: str) -> None:
        """
        Wrapper to CAENHV_SetChName()
        """
        n_indexes = len(channel_list)
        l_index_list = (ct.c_ushort * n_indexes)(*channel_list)
        lib.set_ch_name(self.handle, slot, n_indexes, l_index_list, name.encode())

    def get_ch_param(self, slot: int, channel_list: Sequence[int], name: str) -> Union[List[float], List[int], List[str]]:
        """
        Wrapper to CAENHV_GetBdParam()
        """
        n_indexes = len(channel_list)
        first_index = channel_list[0]  # Assuming all types are equal
        param_type = self.__get_param_type(slot, name, first_index)
        l_data = _PARAM_TYPE_GET_ARG[param_type](n_indexes)
        l_index_list = (ct.c_ushort * n_indexes)(*channel_list)
        lib.get_ch_param(self.handle, slot, name.encode(), n_indexes, l_index_list, l_data)
        if param_type == ParamType.STRING:
            return _str_list_from_char(l_data, n_indexes)
        else:
            return list(l_data)

    def set_ch_param(self, slot: int, channel_list: Sequence[int], name: str, value: Union[float, int, str]) -> None:
        """
        Wrapper to CAENHV_SetBdParam()
        """
        n_indexes = len(channel_list)
        first_index = channel_list[0]  # Assuming all types are equal
        param_type = self.__get_param_type(slot, name, first_index)
        l_data = _PARAM_TYPE_SET_ARG[param_type](value)
        l_index_list = (ct.c_ushort * n_indexes)(*channel_list)
        lib.set_ch_param(self.handle, slot, name.encode(), n_indexes, l_index_list, ct.byref(l_data))

    @_utils.lru_cache_method(cache_manager=__node_cache_manager)
    def get_exec_comm_list(self) -> List[str]:
        """
        Wrapper to CAENHV_GetExecCommList()
        """
        l_num_comm = ct.c_ushort()
        g_comm_name_list = lib.auto_ptr(_c_char_p)
        with g_comm_name_list as l_cnl:
            lib.get_exec_comm_list(self.handle, l_num_comm, l_cnl)
            return _str_list_from_char_p(l_cnl, l_num_comm.value)

    def exec_comm(self, name: str) -> None:
        """
        Wrapper to CAENHV_ExecComm()
        """
        lib.get_exec_comm_list(self.handle, name.encode())

    def subscribe_system_params(self, param_list: Sequence[str]) -> None:
        """
        Wrapper to CAENHV_SubscribeSystemParams()
        """
        self.__init_events_server()
        param_list_len = len(param_list)
        l_param_name_list = ':'.join(param_list).encode()
        l_result_codes = (ct.c_char * param_list_len)()
        lib.subscribe_system_params(self.handle, self.__port, l_param_name_list, param_list_len, l_result_codes)
        result_codes = [int.from_bytes(ec) for ec in l_result_codes]
        if any(result_codes):
            failed_params = [i for i, ec in enumerate(result_codes) if ec]
            raise RuntimeError(f'subscribe_system_params failed at params {failed_params}')

    def subscribe_board_params(self, slot: int, param_list: Sequence[str]) -> None:
        """
        Wrapper to CAENHV_SubscribeBoardParams()
        """
        self.__init_events_server()
        param_list_len = len(param_list)
        l_param_name_list = ':'.join(param_list).encode()
        l_result_codes = (ct.c_char * param_list_len)()
        lib.subscribe_board_params(self.handle, self.__port, slot, l_param_name_list, param_list_len, l_result_codes)
        result_codes = [int.from_bytes(ec) for ec in l_result_codes]
        if any(result_codes):
            failed_params = [i for i, ec in enumerate(result_codes) if ec]
            raise RuntimeError(f'subscribe_board_params failed at params {failed_params}')

    def subscribe_channel_params(self, slot: int, channel: int, param_list: Sequence[str]) -> None:
        """
        Wrapper to CAENHV_SubscribeChannelParams()
        """
        self.__init_events_server()
        param_list_len = len(param_list)
        l_param_name_list = ':'.join(param_list).encode()
        l_result_codes = (ct.c_char * param_list_len)()
        lib.subscribe_channel_params(self.handle, self.__port, slot, channel, l_param_name_list, param_list_len, l_result_codes)
        result_codes = [int.from_bytes(ec) for ec in l_result_codes]
        if any(result_codes):
            failed_params = [i for i, ec in enumerate(result_codes) if ec]
            raise RuntimeError(f'subscribe_channel_params failed at params {failed_params}')

    def unsubscribe_system_params(self, param_list: Sequence[str]) -> None:
        """
        Wrapper to CAENHV_UnSubscribeSystemParams()
        """
        param_list_len = len(param_list)
        l_param_name_list = ':'.join(param_list).encode()
        l_result_codes = (ct.c_char * param_list_len)()
        lib.unsubscribe_system_params(self.handle, self.__port, l_param_name_list, param_list_len, l_result_codes)
        result_codes = [int.from_bytes(ec) for ec in l_result_codes]
        if any(l_result_codes):
            failed_params = [i for i, ec in enumerate(result_codes) if ec]
            raise RuntimeError(f'unsubscribe_system_params failed at params {failed_params}')

    def unsubscribe_board_params(self, slot: int, param_list: Sequence[str]) -> None:
        """
        Wrapper to CAENHV_UnSubscribeBoardParams()
        """
        param_list_len = len(param_list)
        l_param_name_list = ':'.join(param_list).encode()
        l_result_codes = (ct.c_char * param_list_len)()
        lib.unsubscribe_board_params(self.handle, self.__port, slot, l_param_name_list, param_list_len, l_result_codes)
        result_codes = [int.from_bytes(ec) for ec in l_result_codes]
        if any(l_result_codes):
            failed_params = [i for i, ec in enumerate(result_codes) if ec]
            raise RuntimeError(f'unsubscribe_board_params failed at params {failed_params}')

    def unsubscribe_channel_params(self, slot: int, channel: int, param_list: Sequence[str]) -> None:
        """
        Wrapper to CAENHV_SubscribeChannelParams()
        """
        param_list_len = len(param_list)
        l_param_name_list = ':'.join(param_list).encode()
        l_result_codes = (ct.c_char * param_list_len)()
        lib.unsubscribe_channel_params(self.handle, self.__port, slot, channel, l_param_name_list, param_list_len, l_result_codes)
        result_codes = [int.from_bytes(ec) for ec in l_result_codes]
        if any(result_codes):
            failed_params = [i for i, ec in enumerate(result_codes) if ec]
            raise RuntimeError(f'unsubscribe_channel_params failed at params {failed_params}')

    def get_event_data(self) -> Tuple[List[EventData], SystemStatus]:
        """
        Wrapper to CAENHV_GetEventData()
        """
        self.__init_events_client()
        assert self.__skt_client is not None
        l_system_status = _SystemStatusRaw()
        g_event_data = lib.auto_ptr(_event_data_p)
        l_data_number = ct.c_uint()
        with g_event_data as l_ed:
            lib.get_event_data(self.__skt_client.fileno(), l_system_status, l_ed, l_data_number)
            events = [self.__decode_event_data(l_ed[i]) for i in range(l_data_number.value)]
        system_status = EventStatus(l_system_status.System)
        board_status = [EventStatus(i) for i in l_system_status.Board]
        status = SystemStatus(system_status, board_status)
        return events, status

    def get_error(self) -> str:
        """
        Wrapper to CAENHV_GetError()
        """
        return lib.get_error(self.handle).decode()

    # Private utilities

    @_utils.lru_cache_method(cache_manager=__node_cache_manager, maxsize=4096)
    def __get_param_prop(self, slot: int, name: str, channel: Optional[int] = None) -> ParamProp:
        def _get(prop_name: str, prop_type: Type):
            l_value = prop_type()
            try:
                if channel is None:
                    lib.get_bd_param_prop(self.handle, slot, name.encode(), prop_name.encode(), ct.byref(l_value))
                else:
                    lib.get_ch_param_prop(self.handle, slot, channel, name.encode(), prop_name.encode(), ct.byref(l_value))
            except Error:
                # Ignore errors, return empty value
                return prop_type()
            return l_value
        param_type = ParamType(_get('Type', ct.c_uint).value)
        param_mode = ParamMode(_get('Mode', ct.c_uint).value)
        if param_type is None or param_mode is None:
            raise RuntimeError('Missing parameter property Type or Mode')
        res = ParamProp(param_type, param_mode)
        if param_type == ParamType.NUMERIC:
            res.minval = _get('Minval', ct.c_float).value
            res.maxval = _get('Maxval', ct.c_float).value
            res.unit = ParamUnit(_get('Unit', ct.c_ushort).value)
            res.exp = _get('Exp', ct.c_short).value
            res.decimal = _get('Decimal', ct.c_short).value
        elif param_type == ParamType.ONOFF:
            res.onstate = _get('Onstate', ct.c_char * 1024).value.decode()
            res.offstate = _get('Offstate', ct.c_char * 1024).value.decode()
        elif param_type == ParamType.ENUM:
            res.minval = _get('Minval', ct.c_float).value
            res.maxval = _get('Maxval', ct.c_float).value
            if res.minval is not None and res.maxval is not None:
                n_enums = int(res.maxval - res.minval)
                max_string_size = 15  # From library documentation
                n_allocated_values = n_enums + 1  # In case library tries to set an empty string after the last
                l_value = _get('Enum', ct.c_char * (max_string_size * n_allocated_values))
                enum = _str_list_from_n_char_array(l_value, max_string_size, n_enums)
                res.enum = enum
        return res

    @_utils.lru_cache_method(cache_manager=__node_cache_manager, maxsize=4096)
    def __get_param_type(self, slot: int, name: str, channel: Optional[int] = None) -> ParamType:
        """Simplified version used internally to retrieve just param type"""
        l_uint = ct.c_uint()
        if channel is None:
            lib.get_bd_param_prop(self.handle, slot, name.encode(), b'Type', ct.byref(l_uint))
        else:
            lib.get_ch_param_prop(self.handle, slot, channel, name.encode(), b'Type', ct.byref(l_uint))
        return ParamType(l_uint.value)

    def __new_events_format(self) -> bool:
        return self.system_type in (SystemType.R6060.value,)

    def __init_events_server(self):
        if self.__skt_server is not None:
            return
        if self.__new_events_format():
            # Nothing to do, client socket initialized within the library. We store
            # an uninitialized value just as a reminder that a subscription has been
            # made, to be checked later in __init_events_client to be sure
            # EventDataSocket is meaningful
            self.__skt_server = socket.socket()
        else:
            skt = socket.socket()
            port = self.FIRST_BIND_PORT + self.handle  # Should be unique
            skt.bind(('', port))
            skt.listen(1)
            self.__port = port
            self.__skt_server = skt

    def __init_events_client(self):
        if self.__skt_client is not None:
            return
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
            lib_socket = l_value.value if l_value.value is not None else 0
            self.__skt_client = socket.socket(fileno=lib_socket)
        else:
            self.__skt_client, addr = self.__skt_server.accept()
            if addr[0] == '127.0.0.1':
                # If connecting to library polling thread, ignore the first string
                # that should contain the string used as InitSystem argument.
                arg = bytearray()
                while True:
                    char = self.__skt_client.recv(1)
                    if char == b'\x00':
                        break
                    arg.extend(char)
                assert self.arg == arg.decode()

    def __decode_event_data(self, ed: _EventDataRaw) -> EventData:
        event_type = EventType(ed.Type)
        idem_id = ed.ItemID.decode()
        system_handle = ed.SystemHandle
        board_index = ed.BoardIndex
        channel_index = ed.ChannelIndex
        if event_type in (EventType.KEEPALIVE, EventType.ALARM):
            return EventData(event_type, idem_id, system_handle, board_index, channel_index)
        if board_index == -1:
            # System prop
            prop_type = self.get_sys_prop_info(idem_id).type
            value = _SYS_PROP_TYPE_EVENT_ARG[prop_type](ed.Value)
        else:
            if channel_index == -1:
                # Board param
                param_type = self.__get_param_type(board_index, idem_id)
            else:
                # Channel param
                if idem_id == 'Name':
                    # Workaround for Name: even if not being a real channel parameter, i.e.
                    # get_ch_param_prop does not work, changes are sent as events of type PARAMETER.
                    param_type = ParamType.STRING
                else:
                    param_type = self.__get_param_type(board_index, idem_id, channel_index)
            value = _PARAM_TYPE_EVENT_ARG[param_type](ed.Value)
        return EventData(event_type, idem_id, system_handle, board_index, channel_index, value)

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
        if self.opened:
            self.close()

    def __hash__(self) -> int:
        return hash(self.handle)
