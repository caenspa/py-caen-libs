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
from typing import Callable, Dict, List, Optional, Sequence, Tuple, Type, TypeVar, Union

from caen_libs import _utils


@unique
class ErrorCode(IntEnum):
    """
    Wrapper to ::CAENHVRESULT
    """
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


class IdValueRaw(ct.Union):
    """
    Wrapper to ::IDValue_t
    """
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
        ('Value', IdValueRaw),
    ]


@unique
class EventType(IntEnum):
    """
    Wrapper to ::CAENHV_ID_TYPE_t
    """
    PARAMETER   = 0
    ALARM       = 1
    KEEPALIVE   = 2
    TRMODE      = 3


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
    value: Union[str, int, float] = field(default=-1)


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
    name: str
    type: ParamType
    mode: ParamMode
    minval: Optional[float] = field(default=None)
    maxval: Optional[float] = field(default=None)
    unit: Optional[ParamUnit] = field(default=None)
    exp: Optional[int] = field(default=None)
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


_PARAM_TYPE_ARG: Dict[ParamType, Callable[[int], ct.Array]] = {
    ParamType.NUMERIC:  lambda n: (ct.c_float * n)(),
    ParamType.ONOFF:    lambda n: (ct.c_int * n)(),
    ParamType.CHSTATUS: lambda n: (ct.c_int * n)(),
    ParamType.BDSTATUS: lambda n: (ct.c_int * n)(),
    ParamType.BINARY:   lambda n: (ct.c_int * n)(),
    ParamType.STRING:   lambda n: (ct.c_char * 1024 * n)(),
    ParamType.ENUM:     lambda n: (ct.c_int * n)(),
    ParamType.CMD:      lambda n: (ct.c_int * n)(),
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
    ParamType.ONOFF: lambda v: v.IntValue,
    ParamType.CHSTATUS: lambda v: v.IntValue,
    ParamType.BDSTATUS: lambda v: v.IntValue,
    ParamType.BINARY: lambda v: v.IntValue,
    ParamType.STRING: lambda v: v.StringValue.decode(),
    ParamType.ENUM: lambda v: v.IntValue,
    ParamType.CMD: lambda v: v.IntValue,
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
        self.get_ch_name = self.__get('GetChName', ct.c_int, ct.c_ushort, ct.c_ushort, _c_ushort_p, _c_char_p_p)
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
    def auto_free(self, pointer_type: Type):
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


def _decode_char(data: ct.c_char, n_string: int) -> List[str]:
    res: List[str] = []
    offset = 0
    for _ in range(n_string):
        value = ct.string_at(ct.addressof(data) + offset).decode()
        offset += len(value) + 1
        res.append(value)
    return res


def _decode_char_p(data: ct._Pointer, n_string: int) -> List[str]:
    # Trick to avoid dereferences in case of n_string == 0
    return _decode_char(data.contents, n_string) if n_string != 0 else []


def _decode_char_fixed_size(data: ct.c_char, string_size: int) -> List[str]:
    res: List[str] = []
    offset = 0
    while True:
        value = ct.string_at(ct.addressof(data) + offset).decode()
        if len(value) == 0:
            return res
        offset += string_size
        res.append(value)


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
    arg: Union[str] = field(repr=False)
    username: str = field(repr=False)
    password: str = field(repr=False)
    port: int = field(repr=False, default=0)
    skt_server: Optional[socket.socket] = field(repr=False, default=None)
    skt_client: Optional[socket.socket] = field(repr=False, default=None)

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

    def close(self) -> None:
        """
        Wrapper to CAENHV_DeinitSystem()
        """
        lib.deinit_system(self.handle)
        self.opened = False


    def get_crate_map(self) -> List[Board]:
        """
        Wrapper to CAENHV_GetCrateMap()
        """
        l_nr_of_slot = ct.c_ushort()
        g_nr_of_ch_list = lib.auto_free(_c_ushort_p)
        g_model_list = lib.auto_free(_c_char_p)
        g_description_list = lib.auto_free(_c_char_p)
        g_ser_num_list = lib.auto_free(_c_ushort_p)
        g_fmw_rel_min_list = lib.auto_free(_c_ubyte_p)
        g_fmw_rel_max_list = lib.auto_free(_c_ubyte_p)
        res: List[Board] = []
        with g_nr_of_ch_list as l_nocl, g_model_list as l_ml, g_description_list as l_dl, g_ser_num_list as l_snl, g_fmw_rel_min_list as l_frminl, g_fmw_rel_max_list as l_frmaxl:
            lib.get_crate_map(self.handle, l_nr_of_slot, l_nocl, l_ml, l_dl, l_snl, l_frminl, l_frmaxl)
            ml = _decode_char_p(l_ml, l_nr_of_slot.value)
            dl = _decode_char_p(l_dl, l_nr_of_slot.value)
            for i in range(l_nr_of_slot.value):
                res.append(Board(ml[i], dl[i], l_snl[i], l_nocl[i], (l_frmaxl[i], l_frminl[i])))
        return res

    def get_sys_prop_list(self) -> List[str]:
        """
        Wrapper to CAENHV_GetSysPropList()
        """
        l_num_prop = ct.c_ushort()
        g_prop_name_list = lib.auto_free(_c_char_p)
        with g_prop_name_list as l_pnl:
            lib.get_sys_prop_list(self.handle, l_num_prop, l_pnl)
            return _decode_char_p(l_pnl, l_num_prop.value)

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

    def __get_param(self, index_list: Sequence[int], name: str, slot: Optional[int] = None) -> Union[List[float], List[int], List[str]]:
        n_indexes = len(index_list)
        first_index = index_list[0]  # Assuming all are equal
        if slot is None:
            param_type = self.get_bd_param_prop(first_index, name).type
        else:
            param_type = self.get_ch_param_prop(slot, first_index, name).type
        l_data = _PARAM_TYPE_ARG[param_type](n_indexes)
        l_index_list = (ct.c_ushort * n_indexes)(*index_list)
        if slot is None:
            lib.get_bd_param(self.handle, n_indexes, l_index_list, name.encode(), l_data)
        else:
            lib.get_ch_param(self.handle, slot, name.encode(), n_indexes, l_index_list, l_data)
        if param_type == ParamType.STRING:
            return _decode_char(l_data, n_indexes)
        else:
            return list(l_data)

    def __set_param(self, index_list: Sequence[int], name: str, value: Union[float, int, str], slot: Optional[int] = None) -> None:
        n_indexes = len(index_list)
        first_index = index_list[0]  # Assuming all are equal
        if slot is None:
            param_type = self.get_bd_param_prop(first_index, name).type
        else:
            param_type = self.get_ch_param_prop(slot, first_index, name).type
        l_data: Union[bytes, ct._SimpleCData]
        if param_type == ParamType.NUMERIC:
            assert isinstance(value, (int, float)), 'value expected to be an instance of str'
            l_data = ct.c_float(value)
        elif param_type == ParamType.STRING:
            assert isinstance(value, str), 'value expected to be an instance of str'
            l_data = value.encode()
        else:
            assert isinstance(value, int), 'value expected to be an instance of int'
            l_data = ct.c_int(value)
        l_index_list = (ct.c_ushort * n_indexes)(*index_list)
        if slot is None:
            lib.set_bd_param(self.handle, n_indexes, l_index_list, name.encode(), l_data)
        else:
            lib.set_ch_param(self.handle, slot, name.encode(), n_indexes, l_index_list, l_data)

    def __get_param_prop(self, slot: int, name: str, channel: Optional[int] = None) -> ParamProp:
        def _get(prop_name: str, l_value, gen):
            try:
                if channel is None:
                    lib.get_bd_param_prop(self.handle, slot, name.encode(), prop_name.encode(), ct.byref(l_value))
                else:
                    lib.get_ch_param_prop(self.handle, slot, channel, name.encode(), prop_name.encode(), ct.byref(l_value))
            except Error:
                # Ignore errors
                return None
            return gen(l_value)
        l_str = ct.create_string_buffer(1024)  # should be enough for all types
        l_uint = ct.c_uint()
        l_short = ct.c_short()
        l_ushort = ct.c_ushort()
        l_float = ct.c_float()
        param_type = _get('Type', l_uint, lambda v: ParamType(v.value))
        param_mode = _get('Mode', l_uint, lambda v: ParamMode(v.value))
        res = ParamProp(name, param_type, param_mode)
        if param_type == ParamType.NUMERIC:
            res.minval = _get('Minval', l_float, lambda v: v.value)
            res.maxval = _get('Maxval', l_float, lambda v: v.value)
            res.unit = _get('Unit', l_ushort, lambda v: ParamUnit(v.value))
            res.minval = _get('Exp', l_short, lambda v: v.value)
        elif param_type == ParamType.ONOFF:
            res.onstate = _get('Onstate', l_str, lambda v: v.value.decode())
            res.offstate = _get('Offstate', l_str, lambda v: v.value.decode())
        elif param_type == ParamType.ENUM:
            res.minval = _get('Minval', l_float, lambda v: v.value)
            res.maxval = _get('Maxval', l_float, lambda v: v.value)
            if res.minval is not None and res.maxval is not None:
                n_enum_value = int(res.maxval - res.minval)
                g_value_str_array = lib.auto_free(_c_char_p)
                with g_value_str_array as l_value_str_array:
                    l_value = _get('Enum', l_value_str_array, lambda v: v.contents)
                    if l_value is not None:
                        enum = _decode_char(l_value, n_enum_value)
                        res.enum = enum
        return res

    def __get_param_info(self, slot: int, channel: Optional[int] = None) -> List[str]:
        g_value = lib.auto_free(_c_char_p)
        max_param_name = 10  # see MAX_PARAM_NAME
        with g_value as l_value:
            if channel is None:
                lib.get_bd_param_info(self.handle, slot, l_value)
                return _decode_char_fixed_size(l_value.contents, max_param_name)
            else:
                l_size = ct.c_int()
                lib.get_ch_param_info(self.handle, slot, channel, l_value, l_size)
                res = _decode_char_fixed_size(l_value.contents, max_param_name)
                assert l_size.value == len(res)  # only channel version return result size...
                return res

    def get_bd_param(self, slot_list: Sequence[int], name: str) -> Union[List[float], List[int], List[str]]:
        """
        Wrapper to CAENHV_GetBdParam()
        """
        return self.__get_param(slot_list, name)

    def set_bd_param(self, slot_list: Sequence[int], name: str, value: Union[float, int, str]) -> None:
        """
        Wrapper to CAENHV_SetBdParam()
        """
        self.__set_param(slot_list, name, value)

    def get_bd_param_prop(self, slot: int, name: str) -> ParamProp:
        """
        Wrapper to CAENHV_GetBdParamProp()
        """
        return self.__get_param_prop(slot, name)

    def get_bd_param_info(self, slot: int) -> List[str]:
        """
        Wrapper to CAENHV_GetBdParamInfo()
        """
        return self.__get_param_info(slot)

    def test_bd_presence(self, slot: int) -> Board:
        """
        Wrapper to CAENHV_TestBdPresence()
        """
        l_nr_of_ch = ct.c_ushort()
        g_model = lib.auto_free(_c_char_p)
        g_description = lib.auto_free(_c_char_p)
        l_ser_num = ct.c_ushort()
        l_fmw_rel_min = ct.c_ubyte()
        l_fmw_rel_max = ct.c_ubyte()
        with g_model as l_m, g_description as l_d:
            lib.test_bd_presence(self.handle, slot, l_nr_of_ch, l_m, l_d, l_ser_num, l_fmw_rel_min, l_fmw_rel_max)
            model = l_m.contents.value.decode()
            description = l_d.contents.value.decode()
            return Board(model, description, l_ser_num.value, l_nr_of_ch.value, (l_fmw_rel_max.value, l_fmw_rel_min.value))

    def get_ch_param_prop(self, slot: int, channel: int, name: str) -> ParamProp:
        """
        Wrapper to CAENHV_GetChParamProp()
        """
        return self.__get_param_prop(slot, name, channel)

    def get_ch_param_info(self, slot: int, channel: int) -> List[str]:
        """
        Wrapper to CAENHV_GetChParamInfo()
        """
        return self.__get_param_info(slot, channel)

    def get_ch_param(self, slot: int, channel_list: Sequence[int], name: str) -> Union[List[float], List[int], List[str]]:
        """
        Wrapper to CAENHV_GetBdParam()
        """
        return self.__get_param(channel_list, name, slot)

    def set_ch_param(self, slot: int, channel_list: Sequence[int], name: str, value: Union[float, int, str]) -> None:
        """
        Wrapper to CAENHV_SetBdParam()
        """
        self.__set_param(channel_list, name, value, slot)

    def get_exec_comm_list(self) -> List[str]:
        """
        Wrapper to CAENHV_GetExecCommList()
        """
        l_num_comm = ct.c_ushort()
        g_comm_name_list = lib.auto_free(_c_char_p)
        with g_comm_name_list as l_cnl:
            lib.get_exec_comm_list(self.handle, l_num_comm, l_cnl)
            return _decode_char(l_cnl.contents, l_num_comm.value)

    def exec_comm(self, name: str) -> None:
        """
        Wrapper to CAENHV_ExecComm()
        """
        lib.get_exec_comm_list(self.handle, name.encode())

    def __init_events_server(self):
        if self.skt_server is not None:
            return
        if self.system_type == SystemType.R6060:
            # Nothing to do, client socket intialized within the library
            return
        skt = socket.socket()
        port = 10001 + self.handle  # Should be unique
        skt.bind(('', port))
        skt.listen(socket.SOMAXCONN)
        self.port = port
        self.skt_server = skt

    def __init_events_client(self):
        if self.skt_client is not None:
            return
        if self.system_type == SystemType.R6060:
            # A socket has already been opened by the library: we must use the value
            # returned by the special system property EventDataSocket to get the fd.
            # Since self.get_sys_prop calls get_sys_prop_info to get the output type,
            # and since that function is not implemented for EventDataSocket being a
            # library only property, that returns a socket object, we call directly
            # the ctypes object.
            l_value = _socket()
            lib.get_sys_prop(self.handle, b'EventDataSocket', ct.byref(l_value))
            lib_socket = l_value.value if l_value.value is not None else 0
            self.skt_client = socket.socket(fileno=lib_socket)
        else:
            if self.skt_server is None:
                # Initialization is done on first call to a subscribe function
                raise RuntimeError('No subscription done.')
            self.skt_client = self.skt_server.accept()[0]

    def subscribe_system_params(self, param_list: Sequence[str]) -> None:
        """
        Wrapper to CAENHV_SubscribeSystemParams()
        """
        self.__init_events_server()
        param_list_len = len(param_list)
        l_param_name_list = ':'.join(param_list).encode()
        l_result_codes = (ct.c_char * param_list_len)()
        lib.subscribe_system_params(self.handle, self.port, l_param_name_list, param_list_len, l_result_codes)
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
        lib.subscribe_board_params(self.handle, self.port, slot, l_param_name_list, param_list_len, l_result_codes)
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
        lib.subscribe_channel_params(self.handle, self.port, slot, channel, l_param_name_list, param_list_len, l_result_codes)
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
        lib.unsubscribe_system_params(self.handle, self.port, l_param_name_list, param_list_len, l_result_codes)
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
        lib.unsubscribe_board_params(self.handle, self.port, slot, l_param_name_list, param_list_len, l_result_codes)
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
        lib.unsubscribe_channel_params(self.handle, self.port, slot, channel, l_param_name_list, param_list_len, l_result_codes)
        result_codes = [int.from_bytes(ec) for ec in l_result_codes]
        if any(result_codes):
            failed_params = [i for i, ec in enumerate(result_codes) if ec]
            raise RuntimeError(f'unsubscribe_channel_params failed at params {failed_params}')

    def __decode_event_data(self, ed: _EventDataRaw) -> EventData:
        event_type = EventType(ed.Type)
        idem_id = ed.ItemID.decode()
        system_handle = ed.SystemHandle
        board_index = ed.BoardIndex
        channel_index = ed.ChannelIndex
        if event_type in (EventType.KEEPALIVE, EventType.ALARM):
            return EventData(event_type, idem_id, system_handle, board_index, channel_index)
        value: Union[str, int, float]
        if board_index == -1:
            # System prop
            prop_type = self.get_sys_prop_info(idem_id).type
            value = _SYS_PROP_TYPE_EVENT_ARG[prop_type](ed.Value)
        else:
            if channel_index == -1:
                # Board param
                param_type = self.get_bd_param_prop(board_index, idem_id).type
            else:
                # Channel param
                param_type = self.get_ch_param_prop(board_index, channel_index, idem_id).type
            value = _PARAM_TYPE_EVENT_ARG[param_type](ed.Value)
        return EventData(event_type, idem_id, system_handle, board_index, channel_index, value)

    def get_event_data(self) -> Tuple[List[EventData], SystemStatus]:
        """
        Wrapper to CAENHV_GetEventData()
        """
        self.__init_events_client()
        assert self.skt_client is not None
        l_system_status = _SystemStatusRaw()
        g_event_data = lib.auto_free(_event_data_p)
        l_data_number = ct.c_uint()
        with g_event_data as l_ed:
            lib.get_event_data(self.skt_client.fileno(), l_system_status, l_ed, l_data_number)
            events = [self.__decode_event_data(l_ed[i]) for i in range(l_data_number.value)]
        system_status = EventStatus(l_system_status.System)
        board_status = [EventStatus(i) for i in l_system_status.Board]
        status = SystemStatus(system_status, board_status)
        return events, status

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
