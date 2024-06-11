__author__ = 'Giovanni Cerretani'
__copyright__ = 'Copyright (C) 2024 CAEN SpA'
__license__ = 'LGPL-3.0-or-later'  # SPDX-License-Identifier

from contextlib import contextmanager
import ctypes as ct
from dataclasses import dataclass, field
from enum import Flag, IntEnum, unique
from typing import Callable, Sequence, Tuple, Type, TypeVar, Union

from caen_libs import _utils


@unique
class ErrorCode(IntEnum):
    """
    Wrapper to ::CAENComm_ErrorCode
    """
    SUCCESS = 0
    VME_BUS_ERROR = -1
    COMM_ERROR = -2
    GENERIC_ERROR = -3
    INVALID_PARAM = -4
    INVALID_LINK_TYPE = -5
    INVALID_HANDLER = -6
    COMM_TIMEOUT = -7
    DEVICE_NOT_FOUND = -8
    MAX_DEVICES_ERROR = -9
    DEVICE_ALREADY_OPEN = -10
    NOT_SUPPORTED = -11
    UNUSED_BRIDGE = -12
    TERMINATED = -13
    UNSUPPORTED_BASE_ADDRESS = -14


@unique
class ConnectionType(IntEnum):
    """
    Wrapper to ::CAEN_Comm_ConnectionType
    """
    USB = 0
    OPTICAL_LINK = 1
    USB_A4818 = 5
    ETH_V4718 = 6
    USB_V4718 = 7


@unique
class Info(IntEnum):
    """
    Wrapper to ::CAENCOMM_INFO
    """
    PCI_BOARD_SN = 0
    PCI_BOARD_FW_REL = 1
    VME_BRIDGE_SN = 2
    VME_BRIDGE_FW_REL_1 = 3
    VME_BRIDGE_FW_REL_2 = 4
    VMELIB_HANDLE = 5


class IRQLevels(Flag):
    """
    Wrapper to ::IRQLevels
    """
    _1 = 0x01
    _2 = 0x02
    _3 = 0x04
    _4 = 0x08
    _5 = 0x10
    _6 = 0x20
    _7 = 0x40


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
        self.__decode_error = self.__get('DecodeError', ct.c_int, ct.c_char_p)
        self.__sw_release = self.__get('SWRelease', ct.c_char_p)

        # Load API
        self.open_device = self.__get('OpenDevice', ct.c_int, ct.c_int, ct.c_int, ct.c_uint32, ct.POINTER(ct.c_int))
        self.open_device2 = self.__get('OpenDevice2', ct.c_int, ct.c_void_p, ct.c_int, ct.c_uint32, ct.POINTER(ct.c_int))
        self.close_device = self.__get('CloseDevice', ct.c_int)
        self.write32 = self.__get('Write32', ct.c_int, ct.c_uint32, ct.c_uint32)
        self.write16 = self.__get('Write16', ct.c_int, ct.c_uint32, ct.c_uint16)
        self.read32 = self.__get('Read32', ct.c_int, ct.c_uint32, ct.POINTER(ct.c_uint32))
        self.read16 = self.__get('Read16', ct.c_int, ct.c_uint32, ct.POINTER(ct.c_uint16))
        self.multi_write32 = self.__get('MultiWrite32', ct.c_int, ct.POINTER(ct.c_uint32), ct.c_int, ct.POINTER(ct.c_uint32), ct.POINTER(ct.c_int))
        self.multi_write16 = self.__get('MultiWrite16', ct.c_int, ct.POINTER(ct.c_uint32), ct.c_int, ct.POINTER(ct.c_uint16), ct.POINTER(ct.c_int))
        self.multi_read32 = self.__get('MultiRead32', ct.c_int, ct.POINTER(ct.c_uint32), ct.c_int, ct.POINTER(ct.c_uint32), ct.POINTER(ct.c_int))
        self.multi_read16 = self.__get('MultiRead16', ct.c_int, ct.POINTER(ct.c_uint32), ct.c_int, ct.POINTER(ct.c_uint16), ct.POINTER(ct.c_int))
        self.blt_read = self.__get('BLTRead', ct.c_int, ct.c_uint32, ct.POINTER(ct.c_uint32), ct.c_int, ct.POINTER(ct.c_int))
        self.mblt_read = self.__get('MBLTRead', ct.c_int, ct.c_uint32, ct.POINTER(ct.c_uint32), ct.c_int, ct.POINTER(ct.c_int))
        self.irq_disable = self.__get('IRQDisable', ct.c_int)
        self.irq_enable = self.__get('IRQEnable', ct.c_int)
        self.iack_cycle = self.__get('IACKCycle', ct.c_int, ct.c_int, ct.POINTER(ct.c_int))
        self.irq_wait = self.__get('IRQWait', ct.c_int, ct.c_uint32)
        self.info = self.__get('Info', ct.c_int, ct.c_int, ct.c_void_p)

        # Load API related to CAENVME wrappers
        self.__vme_irq_check = self.__get('VMEIRQCheck', ct.c_int32, ct.POINTER(ct.c_uint8))
        self.__vme_iack_cycle16 = self.__get('VMEIACKCycle16', ct.c_int32, ct.c_int, ct.POINTER(ct.c_int))
        self.__vme_iack_cycle32 = self.__get('VMEIACKCycle32', ct.c_int32, ct.c_int, ct.POINTER(ct.c_int))
        self.__vme_irq_wait = self.__get('VMEIRQWait', ct.c_int, ct.c_int, ct.c_int, ct.c_uint8, ct.c_uint32, ct.POINTER(ct.c_int32))

        # Load API available only on recent library versions
        self.__reboot_device = self.__get('RebootDevice', ct.c_int, ct.c_int, min_version=(1, 7, 0))

    def __api_errcheck(self, res: int, func: Callable, _: Tuple) -> int:
        if res < 0:
            raise Error(self.decode_error(res), res, func.__name__)
        return res

    def __get(self, name: str, *args: Type, **kwargs) -> Callable[..., int]:
        min_version = kwargs.get('min_version')
        if min_version is not None:
            # This feature requires __sw_release to be already defined
            assert self.__sw_release is not None
            if not self.__ver_at_least(min_version):
                def fallback(*args, **kwargs):
                    raise RuntimeError(f'{name} requires {self.name} >= {min_version}. Please update it.')
                return fallback
        func = getattr(self.lib, f'CAENComm_{name}')
        func.argtypes = args
        func.restype = ct.c_int
        func.errcheck = self.__api_errcheck
        return func

    # C API wrappers

    def decode_error(self, error_code: int) -> str:
        """
        Wrapper to CAENComm_DecodeError()
        """
        l_value = ct.create_string_buffer(256)
        self.__decode_error(error_code, l_value)
        return l_value.value.decode()

    def sw_release(self) -> str:
        """
        Wrapper to CAENComm_SWRelease()
        """
        l_value = ct.create_string_buffer(16)
        self.__sw_release(l_value)
        return l_value.value.decode()

    def vme_irq_check(self, vme_handle: int) -> IRQLevels:
        """
        Wrapper to CAENComm_VMEIRQCheck()
        """
        l_value = ct.c_ubyte()
        self.__vme_irq_check(vme_handle, l_value)
        return IRQLevels(l_value.value)

    def vme_iack_cycle16(self, vme_handle: int, levels: IRQLevels) -> int:
        """
        Wrapper to CAENComm_VMEIACKCycle16()
        """
        l_value = ct.c_int()
        self.__vme_iack_cycle16(vme_handle, levels)
        return l_value.value

    def vme_iack_cycle32(self, vme_handle: int, levels: IRQLevels) -> int:
        """
        Wrapper to CAENComm_VMEIACKCycle32()
        """
        l_value = ct.c_int()
        self.__vme_iack_cycle32(vme_handle, levels)
        return l_value.value

    def vme_irq_wait(self, connection_type: ConnectionType, link_num: int, conet_node: int, irq_mask: IRQLevels, timeout: int) -> int:
        """
        Wrapper to CAENComm_VMEIRQWait()
        """
        l_value = ct.c_int32()
        self.__vme_irq_wait(connection_type.value, link_num, conet_node, irq_mask.value, timeout, l_value)
        return l_value.value

    def reboot_device(self, link_number: int, use_backup: bool) -> None:
        """
        Wrapper to CAENComm_RebootDevice()
        """
        self.__reboot_device(link_number, use_backup)

    @staticmethod
    def __ver_tuple(version: str) -> Tuple[int, ...]:
        return tuple(map(int, version.split('.')))

    def __ver_at_least(self, target: Tuple[int, ...]) -> bool:
        ver = self.sw_release()
        return self.__ver_tuple(ver) >= target

    # Python utilities

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.path})'

    def __str__(self) -> str:
        return self.path


lib: _Lib


lib = _Lib('CAENComm')


def _get_l_arg(connection_type: ConnectionType, arg: Union[int, str]):
    if connection_type == ConnectionType.ETH_V4718:
        assert isinstance(arg, str), 'arg expected to be an instance of str'
        return arg.encode()
    else:
        l_link_number = int(arg)
        l_link_number_ct = ct.c_uint32(l_link_number)
        return ct.pointer(l_link_number_ct)


@dataclass
class Device:
    """
    Class representing a device.
    """

    # Public members
    handle: int
    opened: bool = field(repr=False)
    connection_type: ConnectionType = field(repr=False)
    arg: Union[int, str] = field(repr=False)
    conet_node: int = field(repr=False)
    vme_base_address: int = field(repr=False)

    def __del__(self) -> None:
        if self.opened:
            self.close()

    # C API wrappers

    _T = TypeVar('_T', bound='Device')

    @classmethod
    def open(cls: Type[_T], connection_type: ConnectionType, arg: Union[int, str], conet_node: int, vme_base_address: int) -> _T:
        """
        Wrapper to CAENComm_OpenDevice2()
        """
        l_arg = _get_l_arg(connection_type, arg)
        l_handle = ct.c_int()
        lib.open_device2(connection_type, l_arg, conet_node, vme_base_address, l_handle)
        return cls(l_handle.value, True, connection_type, arg, conet_node, vme_base_address)

    def connect(self) -> None:
        """
        Wrapper to CAENComm_OpenDevice2()
        New instances should be created with open().
        This is meant to reconnect a device closed with close().
        """
        if self.opened:
            raise RuntimeError('Already connected.')
        l_arg = _get_l_arg(self.connection_type, self.arg)
        l_handle = ct.c_int()
        lib.open_device2(self.connection_type, l_arg, self.conet_node, self.vme_base_address, l_handle)
        self.handle = l_handle.value
        self.opened = True

    def close(self) -> None:
        """
        Wrapper to CAENComm_CloseDevice()
        """
        lib.close_device(self.handle)
        self.opened = False

    def write32(self, address: int, value: int) -> None:
        """
        Wrapper to CAENComm_Write32()
        """
        lib.write32(self.handle, address, value)

    def write16(self, address: int, value: int) -> None:
        """
        Wrapper to CAENComm_Write16()
        """
        lib.write16(self.handle, address, value)

    def read32(self, address: int) -> int:
        """
        Wrapper to CAENComm_Read32()
        """
        l_value = ct.c_uint32()
        lib.read32(self.handle, address, l_value)
        return l_value.value

    def read16(self, address: int) -> int:
        """
        Wrapper to CAENComm_Read16()
        """
        l_value = ct.c_uint16()
        lib.read16(self.handle, address, l_value)
        return l_value.value

    def multi_write32(self, address: Sequence[int], data: Sequence[int]) -> None:
        """
        Wrapper to CAENComm_MultiWrite32()
        """
        n_cycles = len(address)
        l_address = (ct.c_uint32 * n_cycles)(*address)
        l_data = (ct.c_uint32 * n_cycles)(*data)
        l_error_code = (ct.c_int * n_cycles)()
        lib.multi_write32(self.handle, l_address, n_cycles, l_data, l_error_code)
        if any(l_error_code):
            failed_cycles = [i for i, ec in enumerate(l_error_code) if ec]
            raise RuntimeError(f'multi_write32 failed at cycles {failed_cycles}')

    def multi_write16(self, address: Sequence[int], data: Sequence[int]) -> None:
        """
        Wrapper to CAENComm_MultiWrite16()
        """
        n_cycles = len(address)
        l_address = (ct.c_uint32 * n_cycles)(*address)
        l_data = (ct.c_uint16 * n_cycles)(*data)
        l_error_code = (ct.c_int * n_cycles)()
        lib.multi_write16(self.handle, l_address, n_cycles, l_data, l_error_code)
        if any(l_error_code):
            failed_cycles = [i for i, ec in enumerate(l_error_code) if ec]
            raise RuntimeError(f'multi_write16 failed at cycles {failed_cycles}')

    def multi_read32(self, address: Sequence[int]) -> Tuple[int, ...]:
        """
        Wrapper to CAENComm_MultiRead32()
        """
        n_cycles = len(address)
        l_address = (ct.c_uint32 * n_cycles)(*address)
        l_data = (ct.c_uint32 * n_cycles)()
        l_error_code = (ct.c_int * n_cycles)()
        lib.multi_read32(self.handle, l_address, n_cycles, l_data, l_error_code)
        if any(l_error_code):
            failed_cycles = [i for i, ec in enumerate(l_error_code) if ec]
            raise RuntimeError(f'multi_read32 failed at cycles {failed_cycles}')
        return tuple(int(d) for d in l_data)

    def multi_read16(self, address: Sequence[int]) -> Tuple[int, ...]:
        """
        Wrapper to CAENComm_MultiRead16()
        """
        n_cycles = len(address)
        l_address = (ct.c_uint32 * n_cycles)(*address)
        l_data = (ct.c_uint16 * n_cycles)()
        l_error_code = (ct.c_int * n_cycles)()
        lib.multi_read16(self.handle, l_address, n_cycles, l_data, l_error_code)
        if any(l_error_code):
            failed_cycles = [i for i, ec in enumerate(l_error_code) if ec]
            raise RuntimeError(f'multi_read16 failed at cycles {failed_cycles}')
        return tuple(int(d) for d in l_data)

    def blt_read(self, address: int, blt_size: int) -> Tuple[int, ...]:
        """
        Wrapper to CAENComm_BLTRead()
        """
        l_data = (ct.c_uint32 * blt_size)()
        l_nw = ct.c_int()
        lib.blt_read(self.handle, address, l_data, blt_size, l_nw)
        return tuple(int(d) for d in l_data[:l_nw.value])

    def mblt_read(self, address: int, blt_size: int) -> Tuple[int, ...]:
        """
        Wrapper to CAENComm_MBLTRead()
        """
        l_data = (ct.c_uint32 * blt_size)()
        l_nw = ct.c_int()
        lib.mblt_read(self.handle, address, l_data, blt_size, l_nw)
        return tuple(int(d) for d in l_data[:l_nw.value])

    def irq_disable(self, mask: int) -> None:
        """
        Wrapper to CAENComm_IRQDisable()
        """
        lib.irq_disable(self.handle, mask)

    def irq_enable(self, mask: int) -> None:
        """
        Wrapper to CAENComm_IRQEnable()
        """
        lib.irq_enable(self.handle, mask)

    def iack_cycle(self, levels: IRQLevels) -> int:
        """
        Wrapper to CAENComm_IACKCycle()
        """
        l_data = ct.c_int()
        lib.iack_cycle(self.handle, levels.value, l_data)
        return l_data.value

    def irq_wait(self, timeout: int) -> None:
        """
        Wrapper to CAENComm_IRQWait()
        """
        lib.irq_wait(self.handle, timeout)

    def vme_handle(self) -> int:
        """
        Wrapper to CAENComm_Info() with CAENComm_VMELIB_handle
        """
        l_value = ct.c_int32()
        lib.info(self.handle, Info.VMELIB_HANDLE, ct.pointer(l_value))
        return l_value.value

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
