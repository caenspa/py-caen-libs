__author__ = 'Giovanni Cerretani'
__copyright__ = 'Copyright (C) 2024 CAEN SpA'
__license__ = 'LGPL-3.0-or-later'  # SPDX-License-Identifier

from contextlib import contextmanager
import ctypes as ct
from dataclasses import dataclass, field
from enum import IntEnum, unique
import sys
from typing import Callable, Tuple, Type, TypeVar, Union


@unique
class ErrorCode(IntEnum):
    """
    Wrapper to ::CAEN_PLU_ERROR_CODE
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


@unique
class ConnectionModes(IntEnum):
    """
    Wrapper to ::t_ConnectionModes
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
    Wrapper to ::t_FPGA_V2495
    """
    MAIN = 0
    USER = 1
    DELAY = 2


class Error(RuntimeError):
    """
    Raised when a wrapped C API function returns
    negative values.
    """

    code: ErrorCode  ## Error code as instance of ErrorCode
    message: str  ## Message description
    func: str  ## Name of failed function

    def __init__(self, message: str, res: int, func: str) -> None:
        self.code = ErrorCode(res)
        self.message = message
        self.func = func
        super().__init__(f'{self.func} failed: {self.message} ({self.code.name})')


class USBDevice(ct.Structure):
    """
    Wrapper to ::tUSBDevice
    """
    _fields_ = [
        ('id', ct.c_uint32),
        ('SN', ct.c_char * 64),
        ('DESC', ct.c_char * 64),
    ]


class BoardInfo(ct.Structure):
    """
    Wrapper to ::tBOARDInfo
    """
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
        ('reserved', ct.c_uint32 * 12),
        ('sernum1', ct.c_uint32),
        ('sernum0', ct.c_uint32),
    ]


class _Lib:
    """
    This class loads the shared library and
    exposes its functions on its public attributes
    using ctypes.
    """

    def __init__(self, name: str) -> None:
        self.name = name
        self.__load_lib()
        self.__load_api()

    def __load_lib(self) -> None:
        loader: ct.LibraryLoader

        # Platform dependent stuff
        if sys.platform == 'win32':
            loader = ct.windll
            path = f'{self.name}.dll'
        else:
            loader = ct.cdll
            path = f'lib{self.name}.so'

        ## Library path on the filesystem
        self.path = path

        # Load library
        try:
            self.__lib = loader.LoadLibrary(self.path)
        except FileNotFoundError as ex:
            raise RuntimeError(
                f'Library {self.name} not found. '
                'This module requires the latest version of '
                'the library to be installed on your system. '
                'You may find the official installers at '
                'https://www.caen.it/. '
                'Please install it and retry.'
            ) from ex

    def __load_api(self) -> None:
        # Load API not related to devices
        self.__usb_enumerate = self.__get('USBEnumerate', ct.POINTER(USBDevice), ct.POINTER(ct.c_uint32))
        self.__usb_enumerate_serial_number = self.__get('USBEnumerateSerialNumber', ct.POINTER(ct.c_uint), ct.c_char_p, ct.c_uint32)

        # Load API
        self.open_device = self.__get('OpenDevice', ct.c_int, ct.c_char_p, ct.c_int, ct.c_int, ct.POINTER(ct.c_int))
        self.open_device2 = self.__get('OpenDevice2', ct.c_int, ct.c_void_p, ct.c_int, ct.c_char_p, ct.POINTER(ct.c_int))
        self.close_device = self.__get('CloseDevice', ct.c_int)
        self.write_reg = self.__get('WriteReg', ct.c_int, ct.c_uint32, ct.c_uint32)
        self.read_reg = self.__get('ReadReg', ct.c_int, ct.c_uint32, ct.POINTER(ct.c_uint32))
        self.write_data32 = self.__get('WriteData32', ct.c_int, ct.c_uint32, ct.c_uint32, ct.POINTER(ct.c_uint32))
        self.write_fifo32 = self.__get('WriteFIFO32', ct.c_int, ct.c_uint32, ct.c_uint32, ct.POINTER(ct.c_uint32))
        self.read_data32 = self.__get('ReadData32', ct.c_int, ct.c_uint32, ct.c_uint32, ct.POINTER(ct.c_uint32), ct.POINTER(ct.c_uint32))
        self.read_fifo32 = self.__get('ReadFIFO32', ct.c_int, ct.c_uint32, ct.c_uint32, ct.POINTER(ct.c_uint32), ct.POINTER(ct.c_uint32))
        self.init_gate_and_delay_generators = self.__get('InitGateAndDelayGenerators', ct.c_int)
        self.set_gate_and_delay_generator = self.__get('SetGateAndDelayGenerator', ct.c_int, ct.c_uint32, ct.c_uint32, ct.c_uint32, ct.c_uint32, ct.c_uint32)
        self.set_gate_and_delay_generators = self.__get('SetGateAndDelayGenerators', ct.c_int, ct.c_uint32, ct.c_uint32, ct.c_uint32)
        self.get_gate_and_delay_generator = self.__get('GetGateAndDelayGenerator', ct.c_int, ct.c_uint32, ct.POINTER(ct.c_uint32), ct.POINTER(ct.c_uint32), ct.POINTER(ct.c_uint32))
        self.enable_flash_access = self.__get('EnableFlashAccess', ct.c_int, ct.c_int)
        self.disable_flash_access = self.__get('DisableFlashAccess', ct.c_int, ct.c_int)
        self.delete_flash_sector = self.__get('DeleteFlashSector', ct.c_int, ct.c_int, ct.c_uint32)
        self.write_flash_data = self.__get('WriteFlashData', ct.c_int, ct.c_int, ct.c_uint32, ct.POINTER(ct.c_uint32), ct.c_uint32)
        self.read_flash_data = self.__get('ReadFlashData', ct.c_int, ct.c_int, ct.c_uint32, ct.POINTER(ct.c_uint32), ct.c_uint32)
        self.get_info = self.__get('GetInfo', ct.c_int, ct.POINTER(BoardInfo))
        self.get_serial_number = self.__get('GetSerialNumber', ct.c_int, ct.c_char_p, ct.c_uint32)
        self.connection_status = self.__get('ConnectionStatus', ct.c_int, ct.POINTER(ct.c_int))

    def __api_errcheck(self, res: int, func: Callable, _: Tuple) -> int:
        if res < 0:
            raise Error(self.decode_error(res), res, func.__name__)
        return res

    def __get(self, name: str, *args: Type) -> Callable[..., int]:
        func = getattr(self.__lib, f'CAEN_PLU_{name}')
        func.argtypes = args
        func.restype = ct.c_int
        func.errcheck = self.__api_errcheck
        return func

    # C API wrappers

    def decode_error(self, error_code: int) -> str:
        """
        There is no function to decode error, we just use the enumeration name.
        """
        return ErrorCode(error_code).name

    def usb_enumerate(self) -> Tuple[USBDevice, ...]:
        """
        Wrapper to CAEN_PLU_USBEnumerate()
        """
        l_data = (USBDevice * 128)()
        l_num_devs = ct.c_uint32()
        self.__usb_enumerate(l_data, l_num_devs)
        return tuple(i for i in l_data[:l_num_devs.value])

    def usb_enumerate_serial_number(self) -> str:
        """
        Wrapper to CAEN_PLU_USBEnumerateSerialNumber()
        """
        l_num_devs = ct.c_uint()
        l_device_sn_length = 256
        l_device_sn = ct.create_string_buffer(l_device_sn_length)
        self.__usb_enumerate_serial_number(l_num_devs, l_device_sn, l_device_sn_length)
        return l_device_sn.value.decode()

    # Python utilities

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.path})'

    def __str__(self) -> str:
        return self.path


lib: _Lib

# Library name is platform dependent
if sys.platform == 'win32':
    lib = _Lib('CAEN_PLULib')
else:
    lib = _Lib('CAEN_PLU')


def _get_l_arg(connection_mode: ConnectionModes, arg: Union[int, str]):
    if connection_mode in (ConnectionModes.DIRECT_ETH, ConnectionModes.VME_V4718_ETH):
        assert isinstance(arg, str), 'arg expected to be an instance of str'
        return arg.encode()
    elif connection_mode in (ConnectionModes.DIRECT_USB, ConnectionModes.VME_V1718, ConnectionModes.VME_V2718):
        l_link_number_i = int(arg)
        l_link_number_i_ct = ct.c_int(l_link_number_i)
        return ct.pointer(l_link_number_i_ct)
    else:
        l_link_number_u32 = int(arg)
        l_link_number_u32_ct = ct.c_uint32(l_link_number_u32)
        return ct.pointer(l_link_number_u32_ct)


@dataclass
class Device:
    """
    Class representing a device.
    """

    # Public members
    handle: int
    opened: bool = field(repr=False)
    connection_mode: ConnectionModes = field(repr=False)
    arg: Union[int, str] = field(repr=False)
    conet_node: int = field(repr=False)
    vme_base_address: str = field(repr=False)

    def __del__(self) -> None:
        if self.opened:
            self.close()

    # C API wrappers

    _T = TypeVar('_T', bound='Device')

    @classmethod
    def open(cls: Type[_T], connection_mode: ConnectionModes, arg: Union[int, str], conet_node: int, vme_base_address: Union[int, str]) -> _T:
        """
        Wrapper to CAEN_PLU_OpenDevice2()
        """
        l_arg = _get_l_arg(connection_mode, arg)
        l_handle = ct.c_int()
        vme_base_address_str = f'{vme_base_address:X}' if isinstance(vme_base_address, int) else vme_base_address
        l_vme_base_address = vme_base_address_str.encode()
        lib.open_device2(connection_mode, l_arg, conet_node, l_vme_base_address, l_handle)
        return cls(l_handle.value, True, connection_mode, arg, conet_node, vme_base_address_str)

    def connect(self) -> None:
        """
        Wrapper to CAEN_PLU_OpenDevice2()
        New instances should be created with open().
        This is meant to reconnect a device closed with close().
        """
        if self.opened:
            raise RuntimeError('Already connected.')
        l_arg = _get_l_arg(self.connection_mode, self.arg)
        l_handle = ct.c_int32()
        l_vme_base_address = self.vme_base_address.encode()
        lib.open_device2(self.connection_mode, l_arg, self.conet_node, l_vme_base_address, l_handle)
        self.handle = l_handle.value
        self.opened = True

    def close(self) -> None:
        """
        Wrapper to CAEN_PLU_CloseDevice()
        """
        lib.close_device(self.handle)
        self.opened = False

    def write_reg(self, address: int, value: int) -> None:
        """
        Wrapper to CAEN_PLU_WriteReg()
        """
        lib.write_reg(self.handle, address, value)

    def read_reg(self, address: int) -> int:
        """
        Wrapper to CAEN_PLU_ReadReg()
        """
        l_value = ct.c_uint32()
        lib.read_reg(self.handle, address, l_value)
        return l_value.value

    def enable_flash_access(self, fpga: FPGA) -> None:
        """
        Wrapper to CAEN_PLU_EnableFlashAccess()
        """
        lib.enable_flash_access(self.handle, fpga.value)

    def disable_flash_access(self, fpga: FPGA) -> None:
        """
        Wrapper to CAEN_PLU_DisableFlashAccess()
        """
        lib.disable_flash_access(self.handle, fpga.value)

    def delete_flash_sector(self, fpga: FPGA, sector: int) -> None:
        """
        Wrapper to CAEN_PLU_DeleteFlashSector()
        """
        lib.delete_flash_sector(self.handle, fpga.value, sector)

    def write_flash_data(self, fpga: FPGA, address: int, data: bytes) -> None:
        """
        Wrapper to CAEN_PLU_WriteFlashData()
        """
        length = len(data)
        l_data_length = length // ct.sizeof(ct.c_uint32)
        l_data = (ct.c_uint32 * l_data_length).from_buffer_copy(data)
        lib.write_flash_data(self.handle, fpga.value, address, l_data, l_data_length)

    def read_flash_data(self, fpga: FPGA, address: int, length: int) -> bytes:
        """
        Wrapper to CAEN_PLU_ReadFlashData()
        """
        l_data_length = length // ct.sizeof(ct.c_uint32)
        l_data = (ct.c_uint32 * l_data_length)()
        lib.read_flash_data(self.handle, fpga.value, address, l_data, l_data_length)
        return bytes(l_data)

    def get_serial_number(self) -> str:
        """
        Wrapper to CAEN_PLU_GetSerialNumber()
        """
        l_value = ct.create_string_buffer(32)
        lib.get_serial_number(self.handle, l_value, len(l_value))
        return l_value.value.decode()

    def get_info(self) -> BoardInfo:
        """
        Wrapper to CAEN_PLU_GetInfo()
        """
        l_data = BoardInfo()
        lib.get_info(self.handle, l_data)
        return l_data

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
