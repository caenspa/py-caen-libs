"""
Binding of CAEN PLU
"""

__author__ = 'Giovanni Cerretani'
__copyright__ = 'Copyright (C) 2024 CAEN SpA'
__license__ = 'LGPL-3.0-or-later'
# SPDX-License-Identifier: LGPL-3.0-or-later

import ctypes as ct
import sys
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import IntEnum, unique
from typing import TypeVar, Union

from caen_libs import error, _string, _utils


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


class _USBDeviceRaw(ct.Structure):
    _fields_ = [
        ('id', ct.c_uint32),
        ('SN', ct.c_char * 64),
        ('DESC', ct.c_char * 64),
    ]


@dataclass(frozen=True, **_utils.dataclass_slots)
class USBDevice:
    """
    Binding of ::tUSBDevice
    """
    id: int
    sn: str
    desc: str

    @classmethod
    def from_raw(cls, raw: _USBDeviceRaw):
        """Instantiate from raw data"""
        return cls(raw.id, raw.SN.decode('ascii'), raw.DESC.decode('ascii'))


class _BoardInfoRaw(ct.Structure):
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


@dataclass(frozen=True, **_utils.dataclass_slots)
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
    def from_raw(cls, raw: _BoardInfoRaw):
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


class Error(error.Error):
    """
    Raised when a wrapped C API function returns negative values.
    """

    @unique
    class Code(IntEnum):
        """
        Binding of ::CAEN_PLU_ERROR_CODE
        """
        OK = 0
        GENERIC = -1
        INTERFACE = -2
        FPGA = -3
        TRANSFER_MAX_LENGTH = -4
        NOTCONNECTED = -5
        NO_DATA_AVAILABLE = -6
        TOO_MANY_DEVICES_CONNECTED = -7
        INVALID_HANDLE = -8
        INVALID_HARDWARE = -9
        INVALID_PARAMETERS = -10
        TERMINATED = -13

    code: Code

    def __init__(self, message: str, res: int, func: str) -> None:
        self.code = Error.Code(res)
        super().__init__(message, self.code.name, func)


# For backward compatibility. Deprecated.
ErrorCode = Error.Code


# Utility definitions
_c_int_p = ct.POINTER(ct.c_int)
_c_uint_p = ct.POINTER(ct.c_uint)
_c_uint32_p = ct.POINTER(ct.c_uint32)
_usb_device_p = ct.POINTER(_USBDeviceRaw)
_board_info_p = ct.POINTER(_BoardInfoRaw)


class _Lib(_utils.Lib):

    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.__load_api()

    def __load_api(self) -> None:
        # Load API not related to devices
        self.__usb_enumerate = self.__get('USBEnumerate', _usb_device_p, _c_uint32_p)
        self.__usb_enumerate_serial_number = self.__get('USBEnumerateSerialNumber', _c_uint_p, ct.c_char_p, ct.c_uint32)

        # Load API
        self.open_device = self.__get('OpenDevice', ct.c_int, ct.c_char_p, ct.c_int, ct.c_int, _c_int_p)
        self.open_device2 = self.__get('OpenDevice2', ct.c_int, ct.c_void_p, ct.c_int, ct.c_char_p, _c_int_p)
        self.close_device = self.__get('CloseDevice', ct.c_int)
        self.write_reg = self.__get('WriteReg', ct.c_int, ct.c_uint32, ct.c_uint32)
        self.read_reg = self.__get('ReadReg', ct.c_int, ct.c_uint32, _c_uint32_p)
        self.write_data32 = self.__get('WriteData32', ct.c_int, ct.c_uint32, ct.c_uint32, _c_uint32_p)
        self.write_fifo32 = self.__get('WriteFIFO32', ct.c_int, ct.c_uint32, ct.c_uint32, _c_uint32_p)
        self.read_data32 = self.__get('ReadData32', ct.c_int, ct.c_uint32, ct.c_uint32, _c_uint32_p, _c_uint32_p)
        self.read_fifo32 = self.__get('ReadFIFO32', ct.c_int, ct.c_uint32, ct.c_uint32, _c_uint32_p, _c_uint32_p)
        self.init_gate_and_delay_generators = self.__get('InitGateAndDelayGenerators', ct.c_int)
        self.set_gate_and_delay_generator = self.__get('SetGateAndDelayGenerator', ct.c_int, ct.c_uint32, ct.c_uint32, ct.c_uint32, ct.c_uint32, ct.c_uint32)
        self.set_gate_and_delay_generators = self.__get('SetGateAndDelayGenerators', ct.c_int, ct.c_uint32, ct.c_uint32, ct.c_uint32)
        self.get_gate_and_delay_generator = self.__get('GetGateAndDelayGenerator', ct.c_int, ct.c_uint32, _c_uint32_p, _c_uint32_p, _c_uint32_p)
        self.enable_flash_access = self.__get('EnableFlashAccess', ct.c_int, ct.c_int)
        self.disable_flash_access = self.__get('DisableFlashAccess', ct.c_int, ct.c_int)
        self.delete_flash_sector = self.__get('DeleteFlashSector', ct.c_int, ct.c_int, ct.c_uint32)
        self.write_flash_data = self.__get('WriteFlashData', ct.c_int, ct.c_int, ct.c_uint32, _c_uint32_p, ct.c_uint32)
        self.read_flash_data = self.__get('ReadFlashData', ct.c_int, ct.c_int, ct.c_uint32, _c_uint32_p, ct.c_uint32)
        self.get_info = self.__get('GetInfo', ct.c_int, _board_info_p)
        self.get_serial_number = self.__get('GetSerialNumber', ct.c_int, ct.c_char_p, ct.c_uint32)
        self.connection_status = self.__get('ConnectionStatus', ct.c_int, _c_int_p)

    def __api_errcheck(self, res: int, func, _: tuple) -> int:
        if res < 0:
            raise Error(self.decode_error(res), res, func.__name__)
        return res

    def __get(self, name: str, *args: type) -> Callable[..., int]:
        func = self.get(f'CAEN_PLU_{name}')
        func.argtypes = args
        func.restype = ct.c_int
        func.errcheck = self.__api_errcheck  # type: ignore
        return func

    # C API bindings

    def sw_release(self) -> str:
        """
        No equivalent function on CAEN_PLU
        """
        raise NotImplementedError('Not available on CAEN_PLU')

    def decode_error(self, error_code: int) -> str:
        """
        There is no function to decode error, we just use the
        enumeration name.
        """
        return Error.Code(error_code).name

    def usb_enumerate(self) -> tuple[USBDevice, ...]:
        """
        Binding of CAEN_PLU_USBEnumerate()
        """
        l_data_size = 128  # Undocumented but, hopefully, long enough
        l_data = (_USBDeviceRaw * l_data_size)()
        l_num_devs = ct.c_uint32()
        self.__usb_enumerate(l_data, l_num_devs)
        assert l_data_size >= l_num_devs.value
        return tuple(map(USBDevice.from_raw, l_data[:l_num_devs.value]))

    def usb_enumerate_serial_number(self) -> tuple[str, ...]:
        """
        Binding of CAEN_PLU_USBEnumerateSerialNumber()

        Note: the underlying library is bugged, as of version v1.3, if
        there is more than one board.
        """
        l_num_devs = ct.c_uint()
        l_device_sn_length = 512  # Undocumented but, hopefully, long enough
        l_device_sn = ct.create_string_buffer(l_device_sn_length)
        self.__usb_enumerate_serial_number(l_num_devs, l_device_sn, l_device_sn_length)
        return tuple(_string.from_char(l_device_sn, l_num_devs.value))


# Library name is platform dependent
if sys.platform == 'win32':
    _LIB_NAME = 'CAEN_PLULib'
else:
    _LIB_NAME = 'CAEN_PLU'


lib = _Lib(_LIB_NAME)


def _get_l_arg(connection_mode: ConnectionModes, arg: Union[int, str]):
    if connection_mode in (ConnectionModes.DIRECT_ETH, ConnectionModes.VME_V4718_ETH):
        assert isinstance(arg, str), 'arg expected to be a string'
        return arg.encode('ascii')
    elif connection_mode in (ConnectionModes.DIRECT_USB, ConnectionModes.VME_V1718, ConnectionModes.VME_V2718):
        l_link_number_i = int(arg)
        l_link_number_i_ct = ct.c_int(l_link_number_i)
        return ct.pointer(l_link_number_i_ct)
    else:
        l_link_number_u32 = int(arg)
        l_link_number_u32_ct = ct.c_uint32(l_link_number_u32)
        return ct.pointer(l_link_number_u32_ct)


@dataclass(**_utils.dataclass_slots)
class Device:
    """
    Class representing a device.
    """

    # Public members
    handle: int
    connection_mode: ConnectionModes
    arg: Union[int, str]
    conet_node: int
    vme_base_address: str

    # Private members
    __opened: bool = field(default=True, repr=False)
    __registers: _utils.Registers = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.__registers = _utils.Registers(self.read_reg, self.write_reg)

    def __del__(self) -> None:
        if self.__opened:
            self.close()

    # C API bindings

    _T = TypeVar('_T', bound='Device')

    @classmethod
    def open(cls: type[_T], connection_mode: ConnectionModes, arg: Union[int, str], conet_node: int, vme_base_address: Union[int, str]) -> _T:
        """
        Binding of CAEN_PLU_OpenDevice2()
        """
        l_arg = _get_l_arg(connection_mode, arg)
        l_handle = ct.c_int()
        vme_base_address_str = f'{vme_base_address:X}' if isinstance(vme_base_address, int) else vme_base_address
        l_vme_base_address = vme_base_address_str.encode('ascii')
        lib.open_device2(connection_mode, l_arg, conet_node, l_vme_base_address, l_handle)
        return cls(l_handle.value, connection_mode, arg, conet_node, vme_base_address_str)

    def connect(self) -> None:
        """
        Binding of CAEN_PLU_OpenDevice2()

        New instances should be created with open(). This is meant to
        reconnect a device closed with close().
        """
        if self.__opened:
            raise RuntimeError('Already connected.')
        l_arg = _get_l_arg(self.connection_mode, self.arg)
        l_handle = ct.c_int()
        l_vme_base_address = self.vme_base_address.encode('ascii')
        lib.open_device2(self.connection_mode, l_arg, self.conet_node, l_vme_base_address, l_handle)
        self.handle = l_handle.value
        self.__opened = True

    def close(self) -> None:
        """
        Binding of CAEN_PLU_CloseDevice()
        """
        lib.close_device(self.handle)
        self.__opened = False

    def write_reg(self, address: int, value: int) -> None:
        """
        Binding of CAEN_PLU_WriteReg()
        """
        lib.write_reg(self.handle, address, value)

    def read_reg(self, address: int) -> int:
        """
        Binding of CAEN_PLU_ReadReg()
        """
        l_value = ct.c_uint32()
        lib.read_reg(self.handle, address, l_value)
        return l_value.value

    @property
    def registers(self) -> _utils.Registers:
        """Utility to simplify register access"""
        return self.__registers

    def enable_flash_access(self, fpga: FPGA) -> None:
        """
        Binding of CAEN_PLU_EnableFlashAccess()
        """
        lib.enable_flash_access(self.handle, fpga)

    def disable_flash_access(self, fpga: FPGA) -> None:
        """
        Binding of CAEN_PLU_DisableFlashAccess()
        """
        lib.disable_flash_access(self.handle, fpga)

    def delete_flash_sector(self, fpga: FPGA, sector: int) -> None:
        """
        Binding of CAEN_PLU_DeleteFlashSector()
        """
        lib.delete_flash_sector(self.handle, fpga, sector)

    def write_flash_data(self, fpga: FPGA, address: int, data: bytes) -> None:
        """
        Binding of CAEN_PLU_WriteFlashData()
        """
        length = len(data)
        l_data_length = length // ct.sizeof(ct.c_uint32)
        l_data = (ct.c_uint32 * l_data_length).from_buffer_copy(data)
        lib.write_flash_data(self.handle, fpga, address, l_data, l_data_length)

    def read_flash_data(self, fpga: FPGA, address: int, length: int) -> bytes:
        """
        Binding of CAEN_PLU_ReadFlashData()
        """
        l_data_length = length // ct.sizeof(ct.c_uint32)
        l_data = (ct.c_uint32 * l_data_length)()
        lib.read_flash_data(self.handle, fpga, address, l_data, l_data_length)
        return bytes(l_data)

    def get_serial_number(self) -> str:
        """
        Binding of CAEN_PLU_GetSerialNumber()
        """
        l_value = ct.create_string_buffer(32)  # Undocumented but, hopefully, long enough
        lib.get_serial_number(self.handle, l_value, len(l_value))
        return l_value.value.decode('ascii')

    def get_info(self) -> BoardInfo:
        """
        Binding of CAEN_PLU_GetInfo()
        """
        l_b = _BoardInfoRaw()
        lib.get_info(self.handle, l_b)
        return BoardInfo.from_raw(l_b)

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
