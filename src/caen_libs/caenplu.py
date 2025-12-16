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
from typing import Sequence, TypeVar

from caen_libs import error, _string, _utils
import caen_libs._caenplutypes as _types

# Add some types to the module namespace
from caen_libs._caenplutypes import (  # pylint: disable=W0611
    ConnectionModes,
    FPGA,
    USBDevice,
    BoardInfo,
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


# Utility definitions
_c_int_p = ct.POINTER(ct.c_int)
_c_uint_p = ct.POINTER(ct.c_uint)
_c_uint32_p = ct.POINTER(ct.c_uint32)
_usb_device_p = ct.POINTER(_types.USBDeviceRaw)
_board_info_p = ct.POINTER(_types.BoardInfoRaw)


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

        Note: the underlying library is bugged, as of version v1.3, if
        there is one board that is already connected: in this case, it
        return a tuple with the correct size, but with the fields of
        the connected board set to empty strings.
        """
        l_data_size = 255  # Undocumented but, hopefully, long enough
        l_data = (_types.USBDeviceRaw * l_data_size)()
        l_num_devs = ct.c_uint32()
        self.__usb_enumerate(l_data, l_num_devs)
        assert l_data_size >= l_num_devs.value
        return tuple(map(USBDevice.from_raw, l_data[:l_num_devs.value]))

    def usb_enumerate_serial_number(self) -> tuple[str, ...]:
        """
        Binding of CAEN_PLU_USBEnumerateSerialNumber()

        Note: the underlying library is bugged, as of version v1.3, if
        there is one board that is already connected: in this case, it
        returns an empty tuple.
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


def _get_l_arg(connection_mode: ConnectionModes, arg: int | str):
    match connection_mode:
        case ConnectionModes.DIRECT_ETH | ConnectionModes.VME_V4718_ETH:
            if not isinstance(arg, str):
                raise TypeError(f'arg expected to be a string for {connection_mode.name} connection mode')
            return arg.encode('ascii')
        case ConnectionModes.DIRECT_USB | ConnectionModes.VME_V1718 | ConnectionModes.VME_V2718:
            l_link_number_i = int(arg)
            l_link_number_i_ct = ct.c_int(l_link_number_i)
            return ct.pointer(l_link_number_i_ct)
        case _:
            l_link_number_u32 = int(arg)
            l_link_number_u32_ct = ct.c_uint32(l_link_number_u32)
            return ct.pointer(l_link_number_u32_ct)


@dataclass(slots=True)
class Device:
    """
    Class representing a device.
    """

    # Public members
    handle: int
    connection_mode: ConnectionModes
    arg: int | str
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
    def open(cls: type[_T], connection_mode: ConnectionModes, arg: int | str, conet_node: int, vme_base_address: int | str) -> _T:
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

    def write_data32(self, start_address: int, data: Sequence[int]) -> None:
        """
        Binding of CAEN_PLU_WriteData32()
        """
        size = len(data)
        l_data = (ct.c_uint32 * size)(*data)
        lib.write_data32(self.handle, start_address, size, l_data)

    def write_fifo32(self, start_address: int, data: Sequence[int]) -> None:
        """
        Binding of CAEN_PLU_WriteFIFO32()
        """
        size = len(data)
        l_data = (ct.c_uint32 * size)(*data)
        lib.write_fifo32(self.handle, start_address, size, l_data)

    def read_data32(self, start_address: int, size: int) -> list[int]:
        """
        Binding of CAEN_PLU_ReadData32()
        """
        l_data = (ct.c_uint32 * size)()
        l_nw = ct.c_uint32()
        lib.read_data32(self.handle, start_address, size, l_data, l_nw)
        return l_data[:l_nw.value]

    def read_fifo32(self, start_address: int, size: int) -> list[int]:
        """
        Binding of CAEN_PLU_ReadFIFO32()
        """
        l_data = (ct.c_uint32 * size)()
        l_nw = ct.c_uint32()
        lib.read_fifo32(self.handle, start_address, size, l_data, l_nw)
        return l_data[:l_nw.value]

    def init_gate_and_delay_generators(self) -> None:
        """
        Binding of CAEN_PLU_InitGateAndDelayGenerators()
        """
        lib.init_gate_and_delay_generators(self.handle)

    def set_gate_and_delay_generator(self, channel: int, enable: int, gate: int, delay: int, scale_factor: int) -> None:
        """
        Binding of CAEN_PLU_SetGateAndDelayGenerator()
        """
        lib.set_gate_and_delay_generator(self.handle, channel, enable, gate, delay, scale_factor)

    def set_gate_and_delay_generators(self, gate: int, delay: int, scale_factor: int) -> None:
        """
        Binding of CAEN_PLU_SetGateAndDelayGenerators()
        """
        lib.set_gate_and_delay_generators(self.handle, gate, delay, scale_factor)

    def get_gate_and_delay_generator(self, channel: int) -> tuple[int, int, int]:
        """
        Binding of CAEN_PLU_GetGateAndDelayGenerator()
        """
        l_gate = ct.c_uint32()
        l_delay = ct.c_uint32()
        l_scale_factor = ct.c_uint32()
        lib.get_gate_and_delay_generator(self.handle, channel, l_gate, l_delay, l_scale_factor)
        return l_gate.value, l_delay.value, l_scale_factor.value

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
        return ct.string_at(l_data, length)

    def get_info(self) -> BoardInfo:
        """
        Binding of CAEN_PLU_GetInfo()
        """
        l_b = _types.BoardInfoRaw()
        lib.get_info(self.handle, l_b)
        return BoardInfo.from_raw(l_b)

    def get_serial_number(self) -> str:
        """
        Binding of CAEN_PLU_GetSerialNumber()
        """
        l_value = ct.create_string_buffer(32)  # Undocumented but, hopefully, long enough
        lib.get_serial_number(self.handle, l_value, len(l_value))
        return l_value.value.decode('ascii')

    def connection_status(self) -> int:
        """
        Binding of CAEN_PLU_ConnectionStatus()
        """
        l_status = ct.c_int()
        lib.connection_status(self.handle, l_status)
        return l_status.value

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
