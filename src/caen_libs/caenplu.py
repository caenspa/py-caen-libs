__author__ = 'Giovanni Cerretani'
__copyright__ = 'Copyright (C) 2024 CAEN SpA'
__license__ = 'LGPL-3.0-or-later'
# SPDX-License-Identifier: LGPL-3.0-or-later

from contextlib import contextmanager
import ctypes as ct
from dataclasses import dataclass, field
from enum import IntEnum, unique
import sys
from typing import Callable, List, Tuple, Type, TypeVar, Union

from caen_libs import _utils


@unique
class ErrorCode(IntEnum):
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


@dataclass(frozen=True)
class USBDevice(ct.Structure):
    """
    Binding of ::tUSBDevice
    """
    id: int
    sn: str
    desc: str


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
        ('reserved', ct.c_uint32 * 12),
        ('sernum1', ct.c_uint32),
        ('sernum0', ct.c_uint32),
    ]


@dataclass
class BoardInfo(ct.Structure):
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
    reserved: Tuple[int, ...]
    sernum1: int
    sernum0: int


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


class _Lib(_utils.Lib):

    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.__load_api()

    def __load_api(self) -> None:
        # Load API not related to devices
        self.__usb_enumerate = self.__get('USBEnumerate', ct.POINTER(_USBDeviceRaw), ct.POINTER(ct.c_uint32))
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
        self.get_info = self.__get('GetInfo', ct.c_int, ct.POINTER(_BoardInfoRaw))
        self.get_serial_number = self.__get('GetSerialNumber', ct.c_int, ct.c_char_p, ct.c_uint32)
        self.connection_status = self.__get('ConnectionStatus', ct.c_int, ct.POINTER(ct.c_int))

    def __api_errcheck(self, res: int, func: Callable, _: Tuple) -> int:
        if res < 0:
            raise Error(self.decode_error(res), res, func.__name__)
        return res

    def __get(self, name: str, *args: Type) -> Callable[..., int]:
        func = getattr(self.lib, f'CAEN_PLU_{name}')
        func.argtypes = args
        func.restype = ct.c_int
        func.errcheck = self.__api_errcheck
        return func

    # C API bindings

    def decode_error(self, error_code: int) -> str:
        """
        There is no function to decode error, we just use the enumeration name.
        """
        return ErrorCode(error_code).name

    def usb_enumerate(self) -> Tuple[USBDevice, ...]:
        """
        Binding of CAEN_PLU_USBEnumerate()
        """
        l_data_size = 128  # Undocumented but, hopefully, long enough
        l_data = (_USBDeviceRaw * l_data_size)()
        l_num_devs = ct.c_uint32()
        self.__usb_enumerate(l_data, l_num_devs)
        assert l_data_size >= l_num_devs.value
        return tuple(
            USBDevice(
                i.id,
                i.SN.value.decode(),
                i.DESC.value.decode(),
            ) for i in l_data[:l_num_devs.value]
        )

    def usb_enumerate_serial_number(self) -> List[str]:
        """
        Binding of CAEN_PLU_USBEnumerateSerialNumber()

        Note: the underlying library is bugged, as of version v1.3,
        if there is more than one board.
        """
        l_num_devs = ct.c_uint()
        l_device_sn_length = 512  # Undocumented but, hopefully, long enough
        l_device_sn = ct.create_string_buffer(l_device_sn_length)
        self.__usb_enumerate_serial_number(l_num_devs, l_device_sn, l_device_sn_length)
        return _utils.str_list_from_char(l_device_sn, l_num_devs.value)


# Library name is platform dependent
if sys.platform == 'win32':
    _lib_name = 'CAEN_PLULib'
else:
    _lib_name = 'CAEN_PLU'


lib = _Lib(_lib_name)


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
    connection_mode: ConnectionModes
    arg: Union[int, str]
    conet_node: int
    vme_base_address: str

    def __del__(self) -> None:
        if self.opened:
            self.close()

    # C API bindings

    _T = TypeVar('_T', bound='Device')

    @classmethod
    def open(cls: Type[_T], connection_mode: ConnectionModes, arg: Union[int, str], conet_node: int, vme_base_address: Union[int, str]) -> _T:
        """
        Binding of CAEN_PLU_OpenDevice2()
        """
        l_arg = _get_l_arg(connection_mode, arg)
        l_handle = ct.c_int()
        vme_base_address_str = f'{vme_base_address:X}' if isinstance(vme_base_address, int) else vme_base_address
        l_vme_base_address = vme_base_address_str.encode()
        lib.open_device2(connection_mode, l_arg, conet_node, l_vme_base_address, l_handle)
        return cls(l_handle.value, True, connection_mode, arg, conet_node, vme_base_address_str)

    def connect(self) -> None:
        """
        Binding of CAEN_PLU_OpenDevice2()
        New instances should be created with open().
        This is meant to reconnect a device closed with close().
        """
        if self.opened:
            raise RuntimeError('Already connected.')
        l_arg = _get_l_arg(self.connection_mode, self.arg)
        l_handle = ct.c_int()
        l_vme_base_address = self.vme_base_address.encode()
        lib.open_device2(self.connection_mode, l_arg, self.conet_node, l_vme_base_address, l_handle)
        self.handle = l_handle.value
        self.opened = True

    def close(self) -> None:
        """
        Binding of CAEN_PLU_CloseDevice()
        """
        lib.close_device(self.handle)
        self.opened = False

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

    def enable_flash_access(self, fpga: FPGA) -> None:
        """
        Binding of CAEN_PLU_EnableFlashAccess()
        """
        lib.enable_flash_access(self.handle, fpga.value)

    def disable_flash_access(self, fpga: FPGA) -> None:
        """
        Binding of CAEN_PLU_DisableFlashAccess()
        """
        lib.disable_flash_access(self.handle, fpga.value)

    def delete_flash_sector(self, fpga: FPGA, sector: int) -> None:
        """
        Binding of CAEN_PLU_DeleteFlashSector()
        """
        lib.delete_flash_sector(self.handle, fpga.value, sector)

    def write_flash_data(self, fpga: FPGA, address: int, data: bytes) -> None:
        """
        Binding of CAEN_PLU_WriteFlashData()
        """
        length = len(data)
        l_data_length = length // ct.sizeof(ct.c_uint32)
        l_data = (ct.c_uint32 * l_data_length).from_buffer_copy(data)
        lib.write_flash_data(self.handle, fpga.value, address, l_data, l_data_length)

    def read_flash_data(self, fpga: FPGA, address: int, length: int) -> bytes:
        """
        Binding of CAEN_PLU_ReadFlashData()
        """
        l_data_length = length // ct.sizeof(ct.c_uint32)
        l_data = (ct.c_uint32 * l_data_length)()
        lib.read_flash_data(self.handle, fpga.value, address, l_data, l_data_length)
        return bytes(l_data)

    def get_serial_number(self) -> str:
        """
        Binding of CAEN_PLU_GetSerialNumber()
        """
        l_value = ct.create_string_buffer(32)  # Undocumented but, hopefully, long enough
        lib.get_serial_number(self.handle, l_value, len(l_value))
        return l_value.value.decode()

    def get_info(self) -> BoardInfo:
        """
        Binding of CAEN_PLU_GetInfo()
        """
        l_b = _BoardInfoRaw()
        lib.get_info(self.handle, l_b)
        return BoardInfo(
            l_b.checksum,
            l_b.checksum_length2,
            l_b.checksum_length1,
            l_b.checksum_length0,
            l_b.checksum_constant2,
            l_b.checksum_constant1,
            l_b.checksum_constant0,
            l_b.c_code,
            l_b.r_code,
            l_b.oui2,
            l_b.oui1,
            l_b.oui0,
            l_b.version,
            l_b.board2,
            l_b.board1,
            l_b.board0,
            l_b.revis3,
            l_b.revis2,
            l_b.revis1,
            l_b.revis0,
            tuple(l_b.reserved),
            l_b.sernum1,
            l_b.sernum0,
        )

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
