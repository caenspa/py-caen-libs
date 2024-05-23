__author__ = 'Giovanni Cerretani'
__copyright__ = 'Copyright (C) 2024 CAEN SpA'
__license__ = 'LGPL-3.0-or-later'  # SPDX-License-Identifier

from contextlib import contextmanager
import ctypes as ct
from dataclasses import dataclass, field
from enum import IntEnum, unique
import sys
from typing import Callable, Sequence, Tuple, Type, TypeVar, Union

from caen_libs import _utils


@unique
class ErrorCode(IntEnum):
    """
    Wrapper to ::CVErrorCodes
    """
    SUCCESS = 0
    BUS_ERROR = -1
    COMM_ERROR = -2
    GENERIC_ERROR = -3
    INVALID_PARAM = -4
    TIMEOUT_ERROR = -5
    ALREADY_OPEN_ERROR = -6
    MAX_BOARD_COUNT_ERROR = -7
    NOT_SUPPORTED = -8


@unique
class BoardType(IntEnum):
    """
    Wrapper to ::CVBoardTypes
    """
    # V1718
    V1718 = 0

    # V2718
    V2718 = 1
    USB_A4818_V2718_LOCAL = 5
    USB_A4818_V2718 = 6

    #V3718
    USB_V3718_LOCAL = 14
    USB_V3718 = 17
    PCI_A2818_V3718_LOCAL = 15
    PCI_A2818_V3718 = 18
    PCIE_A3818_V3718_LOCAL = 16
    PCIE_A3818_V3718 = 19
    USB_A4818_V3718_LOCAL = 8
    USB_A4818_V3718 = 9
    PCIE_A5818_V3718_LOCAL = 29
    PCIE_A5818_V3718 = 30

    # V4718
    USB_V4718_LOCAL = 20
    USB_V4718 = 24
    ETH_V4718_LOCAL = 23
    ETH_V4718 = 27
    PCI_A2818_V4718_LOCAL = 21
    PCI_A2818_V4718 = 25
    PCIE_A3818_V4718_LOCAL = 22
    PCIE_A3818_V4718 = 26
    USB_A4818_V4718_LOCAL = 10
    USB_A4818_V4718 = 11
    PCIE_A5818_V4718_LOCAL = 31
    PCIE_A5818_V4718 = 32

    # Generic access to CONET device
    USB_A4818 = 12

    # CONET master (internal registers)
    A2818 = 2
    A3818 = 4
    USB_A4818_LOCAL = 7
    A5818 = 28

    # A2719, CONET piggy-back of V2718
    A2719 = 3
    USB_A4818_A2719_LOCAL = 13

    # Error
    INVALID = -1


@unique
class DataWidth(IntEnum):
    """
    Wrapper to ::CVDataWidth
    """
    D8       = 0x01          # 8 bit
    D16      = 0x02          # 16 bit
    D32      = 0x04          # 32 bit
    D64      = 0x08          # 64 bit
    DSWAP_   = 0x10          # Swapped mask
    D16_SWAP = D16 | DSWAP_  # 16 bit, swapped
    D32_SWAP = D32 | DSWAP_  # 32 bit, swapped
    D64_SWAP = D64 | DSWAP_  # 64 bit, swapped

    @property
    def ctypes(self) -> Type:
        """Get underlying ctypes type"""
        types = {
            DataWidth.D8: ct.c_uint8,
            DataWidth.D16: ct.c_uint16,
            DataWidth.D16_SWAP: ct.c_uint16,
            DataWidth.D32: ct.c_uint32,
            DataWidth.D32_SWAP: ct.c_uint32,
            DataWidth.D64: ct.c_uint64,
            DataWidth.D64_SWAP: ct.c_uint64,
        }
        return types[self]


@unique
class AddressModifiers(IntEnum):
    """
    Wrapper to ::CVAddressModifier
    """
    A16_S        = 0x2D  # A16 supervisory access
    A16_U        = 0x29  # A16 non-privileged
    A16_LCK      = 0x2C  # A16 lock command
    A24_S_BLT    = 0x3F  # A24 supervisory block transfer
    A24_S_PGM    = 0x3E  # A24 supervisory program access
    A24_S_DATA   = 0x3D  # A24 supervisory data access
    A24_S_MBLT   = 0x3C  # A24 supervisory 64-bit block transfer
    A24_U_BLT    = 0x3B  # A24 non-privileged block transfer
    A24_U_PGM    = 0x3A  # A24 non-privileged program access
    A24_U_DATA   = 0x39  # A24 non-privileged data access
    A24_U_MBLT   = 0x38  # A24 non-privileged 64-bit block transfer
    A24_LCK      = 0x32  # A24 lock command
    A32_S_BLT    = 0x0F  # A32 supervisory block transfer
    A32_S_PGM    = 0x0E  # A32 supervisory program access
    A32_S_DATA   = 0x0D  # A32 supervisory data access
    A32_S_MBLT   = 0x0C  # A32 supervisory 64-bit block transfer
    A32_U_BLT    = 0x0B  # A32 non-privileged block transfer
    A32_U_PGM    = 0x0A  # A32 non-privileged program access
    A32_U_DATA   = 0x09  # A32 non-privileged data access
    A32_U_MBLT   = 0x08  # A32 non-privileged 64-bit block transfer
    A32_LCK      = 0x05  # A32 lock command
    CR_CSR       = 0x2F  # CR/CSR space

    # The following address modifiers are not yet implemented.
    A40_BLT      = 0x37  # A40 block transfer (MD32) @warning Not yet implem
    A40_LCK      = 0x35  # A40 lock command @warning Not yet implemented
    A40          = 0x34  # A40 access @warning Not yet implemented
    A64          = 0x01  # A64 single trnsfer access @warning Not yet implem
    A64_BLT      = 0x03  # A64 block transfer @warning Not yet implemented
    A64_MBLT     = 0x00  # A64 64-bit block transfer @warning Not yet implem
    A64_LCK      = 0x04  # A64 lock command @warning Not yet implemented
    A3U_2eVME    = 0x21  # 2eVME for 3U modules @warning Not yet implemented
    A6U_2eVME    = 0x20  # 2eVME for 6U modules @warning Not yet implemented


@unique
class PulserSelect(IntEnum):
    """
    Wrapper to ::CVPulserSelect
    """
    A = 0
    B = 1


@unique
class OutputSelect(IntEnum):
    """
    Wrapper to ::CVOutputSelect
    """
    _0 = 0  # Identifies the output line 0
    _1 = 1  # Identifies the output line 1
    _2 = 2  # Identifies the output line 2
    _3 = 3  # Identifies the output line 3
    _4 = 4  # Identifies the output line 4


@unique
class InputSelect(IntEnum):
    """
    Wrapper to ::CVInputSelect
    """
    _0 = 0  # Identifies the input line 0
    _1 = 1  # Identifies the input line 1


@unique
class IOSources(IntEnum):
    """
    Wrapper to ::CVIOSources
    """
    MANUAL_SW     = 0  # Manual (button) or software controlled
    INPUT_SRC_0   = 1  # Input line 0
    INPUT_SRC_1   = 2  # Input line 1
    COINCIDENCE   = 3  # Inputs coincidence
    VME_SIGNALS   = 4  # Signals from VME bus
    MISC_SIGNALS  = 6  # Various internal signals
    PULSER_V3718A = 7  # Pulser A output
    PULSER_V3718B = 8  # Pulser B output
    SCALER_END    = 9  # Scaler End output


@unique
class TimeUnits(IntEnum):
    """
    Wrapper to ::CVTimeUnits
    """
    _25_NS   = 0  # Time unit is 25 nanoseconds
    _1600_NS = 1  # Time unit is 1.6 microseconds
    _410_US  = 2  # Time unit is 410 microseconds
    _104_MS  = 3  # Time unit is 104 milliseconds
    _25_US   = 4  # Time unit is 25 microseconds


@unique
class LEDPolarity(IntEnum):
    """
    Wrapper to ::CVLEDPolarity
    """
    ACTIVE_HIGH = 0  # LED emits on signal high level
    ACTIVE_LOW  = 1  # LED emits on signal low level


@unique
class IOPolarity(IntEnum):
    """
    Wrapper to ::CVIOPolarity
    """
    DIRECT   = 0  # Normal polarity
    INVERTED = 1  # Inverted polarity


if sys.platform == 'win32':
    _CAEN_BOOL = ct.c_short
else:
    _CAEN_BOOL = ct.c_int


class Display(ct.Structure):
    """
    Wrapper to ::CVDisplay
    """
    _fields_ = [
        ('Address', ct.c_long),     # VME Address
        ('Data', ct.c_long),        # VME Data
        ('AM', ct.c_long),          # Address modifier
        ('IRQ', ct.c_long),         # IRQ levels
        ('DS0', _CAEN_BOOL),        # Data Strobe 0 signal
        ('DS1', _CAEN_BOOL),        # Data Strobe 1 signal
        ('AS', _CAEN_BOOL),         # Address Strobe signal
        ('IACK', _CAEN_BOOL),       # Interrupt Acknowledge signa
        ('WRITE', _CAEN_BOOL),      # Write signal
        ('LWORD', _CAEN_BOOL),      # Long Word signal
        ('DTACK', _CAEN_BOOL),      # Data Acknowledge signal
        ('BERR', _CAEN_BOOL),       # Bus Error signal
        ('SYSRES', _CAEN_BOOL),     # System Reset signal
        ('BR', _CAEN_BOOL),         # Bus Request signal
        ('BG', _CAEN_BOOL),         # Bus Grant signal
    ]


@unique
class ArbiterTypes(IntEnum):
    """
    Wrapper to ::CVArbiterTypes
    """
    PRIORIZED  = 0  # Priority Arbiter
    ROUNDROBIN = 1  # Round-Robin Arbiter


@unique
class RequesterTypes(IntEnum):
    """
    Wrapper to ::CVRequesterTypes
    """
    FAIR   = 0  # Fair bus requester
    DEMAND = 1  # On demand bus requester


@unique
class ReleaseTypes(IntEnum):
    """
    Wrapper to ::CVReleaseTypes
    """
    RWD = 0  # Release When Done
    ROR = 1  # Release On Request


@unique
class BusReqLevels(IntEnum):
    """
    Wrapper to ::CVBusReqLevels
    """
    BR0 = 0  # Bus request level 0
    BR1 = 1  # Bus request level 1
    BR2 = 2  # Bus request level 2
    BR3 = 3  # Bus request level 3


@unique
class VMETimeouts(IntEnum):
    """
    Wrapper to ::CVVMETimeouts
    """
    _50_US  = 0  # Timeout is 50 microseconds
    _400_US = 1  # Timeout is 400 microseconds


@unique
class ScalerSource(IntEnum):
    """
    Wrapper to ::CVScalerSource
    """
    IN0       = 0x0002
    IN1       = 0x0003
    DTACK     = 0x0006
    BERR      = 0x0007
    DS        = 0x0004
    AS        = 0x0005
    SW        = 0x0008
    FP_BUTTON = 0x0009
    COINC     = 0x000A
    INOR      = 0x000B


@unique
class ScalerMode(IntEnum):
    """
    Wrapper to ::CVScalerMode
    """
    GATE_MODE       = 0
    DWELL_TIME_MODE = 1
    MAX_HITS_MODE   = 2


@unique
class ContinuosRun(IntEnum):
    """
    Wrapper to ::CVContinuosRun
    """
    OFF = 1
    ON  = 0


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
        # CAENVME_DecodeError has non conventional API
        self.__decode_error = self.__lib.CAENVME_DecodeError
        self.__decode_error.argtypes = [ct.c_int]
        self.__decode_error.restype = ct.c_char_p
        self.__sw_release = self.__get('SWRelease', ct.c_char_p)

        # Load API
        self.init = self.__get('Init', ct.c_int, ct.c_short, ct.c_short, ct.POINTER(ct.c_int32))
        self.init2 = self.__get('Init2', ct.c_int, ct.c_void_p, ct.c_short, ct.POINTER(ct.c_int32))
        self.end = self.__get('End', ct.c_int32)
        self.board_fw_release = self.__get('BoardFWRelease', ct.c_int32, ct.c_char_p)
        self.driver_release = self.__get('DriverRelease', ct.c_int32, ct.c_char_p)
        self.device_reset = self.__get('DeviceReset', ct.c_int32)
        self.read_cycle = self.__get('ReadCycle', ct.c_int32, ct.c_uint32, ct.c_void_p, ct.c_int, ct.c_int)
        self.rmw_cycle = self.__get('RMWCycle', ct.c_int32, ct.c_uint32, ct.c_void_p, ct.c_int, ct.c_int)
        self.write_cycle = self.__get('WriteCycle', ct.c_int32, ct.c_uint32, ct.c_void_p, ct.c_int, ct.c_int)
        self.multi_read = self.__get('MultiRead', ct.c_int32, ct.POINTER(ct.c_uint32), ct.POINTER(ct.c_uint32), ct.c_int, ct.POINTER(ct.c_int), ct.POINTER(ct.c_int), ct.POINTER(ct.c_int))
        self.multi_write = self.__get('MultiWrite', ct.c_int32, ct.POINTER(ct.c_uint32), ct.POINTER(ct.c_uint32), ct.c_int, ct.POINTER(ct.c_int), ct.POINTER(ct.c_int), ct.POINTER(ct.c_int))
        self.blt_read_cycle = self.__get('BLTReadCycle', ct.c_int32, ct.c_uint32, ct.c_void_p, ct.c_int, ct.c_int, ct.c_int, ct.POINTER(ct.c_int))
        self.fifo_blt_read_cycle = self.__get('FIFOBLTReadCycle', ct.c_int32, ct.c_uint32, ct.c_void_p, ct.c_int, ct.c_int, ct.c_int, ct.POINTER(ct.c_int))
        self.mblt_read_cycle = self.__get('MBLTReadCycle', ct.c_int32, ct.c_uint32, ct.c_void_p, ct.c_int, ct.c_int, ct.POINTER(ct.c_int))
        self.fifo_mblt_read_cycle = self.__get('FIFOMBLTReadCycle', ct.c_int32, ct.c_uint32, ct.c_void_p, ct.c_int, ct.c_int, ct.POINTER(ct.c_int))
        self.blt_write_cycle = self.__get('BLTWriteCycle', ct.c_int32, ct.c_uint32, ct.c_void_p, ct.c_int, ct.c_int, ct.c_int, ct.POINTER(ct.c_int))
        self.fifo_blt_write_cycle = self.__get('FIFOBLTWriteCycle', ct.c_int32, ct.c_uint32, ct.c_void_p, ct.c_int, ct.c_int, ct.c_int, ct.POINTER(ct.c_int))
        self.mblt_write_cycle = self.__get('MBLTWriteCycle', ct.c_int32, ct.c_uint32, ct.c_void_p, ct.c_int, ct.c_int, ct.POINTER(ct.c_int))
        self.fifo_mblt_write_cycle = self.__get('FIFOMBLTWriteCycle', ct.c_int32, ct.c_uint32, ct.c_void_p, ct.c_int, ct.c_int, ct.POINTER(ct.c_int))
        self.ado_cycle = self.__get('ADOCycle', ct.c_int32, ct.c_uint32, ct.c_int)
        self.adoh_cycle = self.__get('ADOHCycle', ct.c_int32, ct.c_uint32, ct.c_int)
        self.iack_cycle = self.__get('IACKCycle', ct.c_int32, ct.c_int, ct.c_void_p, ct.c_int)
        self.irq_check = self.__get('IRQCheck', ct.c_int32, ct.POINTER(ct.c_ubyte))
        self.irq_enable = self.__get('IRQEnable', ct.c_int32, ct.c_uint32)
        self.irq_disable = self.__get('IRQDisable', ct.c_int32, ct.c_uint32)
        self.irq_wait = self.__get('IRQWait', ct.c_int32, ct.c_uint32, ct.c_uint32)
        self.set_pulser_conf = self.__get('SetPulserConf', ct.c_int32, ct.c_int, ct.c_ubyte, ct.c_ubyte, ct.c_int, ct.c_ubyte, ct.c_int, ct.c_int)
        self.set_scaler_conf = self.__get('SetScalerConf', ct.c_int32, ct.c_short, ct.c_short, ct.c_int, ct.c_int, ct.c_int)
        self.set_output_conf = self.__get('SetOutputConf', ct.c_int32, ct.c_int, ct.c_int, ct.c_int, ct.c_int)
        self.set_input_conf = self.__get('SetInputConf', ct.c_int32, ct.c_int, ct.c_int, ct.c_int)
        self.get_pulser_conf = self.__get('GetPulserConf', ct.c_int32, ct.c_int, ct.POINTER(ct.c_ubyte), ct.POINTER(ct.c_ubyte), ct.POINTER(ct.c_int), ct.POINTER(ct.c_ubyte), ct.POINTER(ct.c_int), ct.POINTER(ct.c_int))
        self.get_scaler_conf = self.__get('GetScalerConf', ct.c_int32, ct.POINTER(ct.c_short), ct.POINTER(ct.c_short), ct.POINTER(ct.c_int), ct.POINTER(ct.c_int), ct.POINTER(ct.c_int))
        self.get_output_conf = self.__get('GetOutputConf', ct.c_int32, ct.c_int, ct.POINTER(ct.c_int), ct.POINTER(ct.c_int), ct.POINTER(ct.c_int))
        self.get_input_conf = self.__get('GetInputConf', ct.c_int32, ct.c_int, ct.POINTER(ct.c_int), ct.POINTER(ct.c_int))
        self.read_register = self.__get('ReadRegister', ct.c_int32, ct.c_int, ct.POINTER(ct.c_uint))
        self.write_register = self.__get('WriteRegister', ct.c_int32, ct.c_int, ct.c_uint)
        self.set_output_register = self.__get('SetOutputRegister', ct.c_int32, ct.c_ushort)
        self.clear_output_register = self.__get('ClearOutputRegister', ct.c_int32, ct.c_ushort)
        self.pulse_output_register = self.__get('PulseOutputRegister', ct.c_int32, ct.c_ushort)
        self.read_display = self.__get('ReadDisplay', ct.c_int32, ct.POINTER(ct.c_int))
        self.set_arbiter_type = self.__get('SetArbiterType', ct.c_int32, ct.c_int)
        self.set_requester_type = self.__get('SetRequesterType', ct.c_int32, ct.c_int)
        self.set_release_type = self.__get('SetReleaseType', ct.c_int32, ct.c_int)
        self.set_bus_req_level = self.__get('SetBusReqLevel', ct.c_int32, ct.c_int)
        self.set_timeout = self.__get('SetTimeout', ct.c_int32, ct.c_int)
        self.set_location_monitor = self.__get('SetLocationMonitor', ct.c_int32, ct.c_uint32, ct.c_int, ct.c_short, ct.c_short, ct.c_short)
        self.set_fifo_mode = self.__get('SetFIFOMode', ct.c_int32, ct.c_short)
        self.get_arbiter_type = self.__get('GetArbiterType', ct.c_int32, ct.POINTER(ct.c_int))
        self.get_requester_type = self.__get('GetRequesterType', ct.c_int32, ct.POINTER(ct.c_int))
        self.get_release_type = self.__get('GetReleaseType', ct.c_int32, ct.POINTER(ct.c_int))
        self.get_bus_req_level = self.__get('GetBusReqLevel', ct.c_int32, ct.POINTER(ct.c_int))
        self.get_timeout = self.__get('GetTimeout', ct.c_int32, ct.POINTER(ct.c_int))
        self.get_fifo_mode = self.__get('GetFIFOMode', ct.c_int32, ct.POINTER(ct.c_short))
        self.system_reset = self.__get('SystemReset', ct.c_int32)
        self.reset_scaler_count = self.__get('ResetScalerCount', ct.c_int32)
        self.enable_scaler_gate = self.__get('EnableScalerGate', ct.c_int32)
        self.disable_scaler_gate = self.__get('DisableScalerGate', ct.c_int32)
        self.start_pulser = self.__get('StartPulser', ct.c_int32, ct.c_int)
        self.stop_pulser = self.__get('StopPulser', ct.c_int32, ct.c_int)
        self.write_flash_page = self.__get('WriteFlashPage', ct.c_int32, ct.POINTER(ct.c_ubyte), ct.c_int)
        self.read_flash_page = self.__get('ReadFlashPage', ct.c_int32, ct.POINTER(ct.c_ubyte), ct.c_int)
        self.erase_flash_page = self.__get('EraseFlashPage', ct.c_int32, ct.c_int)
        self.set_scaler_input_source = self.__get('SetScaler_InputSource', ct.c_int32, ct.c_int)
        self.get_scaler_input_source = self.__get('GetScaler_InputSource', ct.c_int32, ct.POINTER(ct.c_int))
        self.set_scaler_gate_source = self.__get('SetScaler_GateSource', ct.c_int32, ct.c_int)
        self.get_scaler_gate_source = self.__get('GetScaler_GateSource', ct.c_int32, ct.POINTER(ct.c_int))
        self.set_scaler_mode = self.__get('SetScaler_Mode', ct.c_int32, ct.c_int)
        self.get_scaler_mode = self.__get('GetScaler_Mode', ct.c_int32, ct.POINTER(ct.c_int))
        self.set_scaler_clear_source = self.__get('SetScaler_ClearSource', ct.c_int32, ct.c_int)
        self.set_scaler_start_source = self.__get('SetScaler_StartSource', ct.c_int32, ct.c_int)
        self.get_scaler_start_source = self.__get('GetScaler_StartSource', ct.c_int32, ct.POINTER(ct.c_int))
        self.set_scaler_continuous_run = self.__get('SetScaler_ContinuousRun', ct.c_int32, ct.c_int)
        self.get_scaler_continuous_run = self.__get('GetScaler_ContinuousRun', ct.c_int32, ct.POINTER(ct.c_int))
        self.set_scaler_max_hits = self.__get('SetScaler_MaxHits', ct.c_int32, ct.c_uint16)
        self.get_scaler_max_hits = self.__get('GetScaler_MaxHits', ct.c_int32, ct.POINTER(ct.c_uint16))
        self.set_scaler_dwell_time = self.__get('SetScaler_DWellTime', ct.c_int32, ct.c_uint16)
        self.get_scaler_dwell_time = self.__get('GetScaler_DWellTime', ct.c_int32, ct.POINTER(ct.c_uint16))
        self.set_scaler_sw_start = self.__get('SetScaler_SWStart', ct.c_int32)
        self.set_scaler_sw_stop = self.__get('SetScaler_SWStop', ct.c_int32)
        self.set_scaler_sw_reset = self.__get('SetScaler_SWReset', ct.c_int32)
        self.set_scaler_sw_open_gate = self.__get('SetScaler_SWOpenGate', ct.c_int32)
        self.set_scaler_sw_close_gate = self.__get('SetScaler_SWCloseGate', ct.c_int32)
        self.blt_read_async = self.__get('BLTReadAsync', ct.c_int32, ct.c_uint32, ct.c_void_p, ct.c_int, ct.c_int, ct.c_int, linux_only=True)
        self.blt_read_wait = self.__get('BLTReadWait', ct.c_int32, ct.POINTER(ct.c_int), linux_only=True)

    def __api_errcheck(self, res: int, func: Callable, _: Tuple) -> int:
        if res < 0:
            raise Error(self.__decode_error(res).decode(), res, func.__name__)
        return res

    def __get(self, name: str, *args: Type, **kwargs) -> Callable[..., int]:
        linux_only = kwargs.get('linux_only')
        if linux_only is not None:
            if linux_only and sys.platform == 'win32':
                def fallback_win(*args, **kwargs):
                    raise RuntimeError(f'{name} function is Linux only.')
                return fallback_win
        min_version = kwargs.get('min_version')
        if min_version is not None:
            # This feature requires __sw_release to be already defined
            assert self.__sw_release is not None
            if not self.__ver_at_least(min_version):
                def fallback_ver(*args, **kwargs):
                    raise RuntimeError(f'{name} requires {self.name} >= {min_version}. Please update it.')
                return fallback_ver
        func = getattr(self.lib, f'CAENVME_{name}')
        func.argtypes = args
        func.restype = ct.c_int
        func.errcheck = self.__api_errcheck
        return func

    # C API wrappers

    def sw_release(self) -> str:
        """
        Wrapper to CAENVME_SWRelease()
        """
        l_value = ct.create_string_buffer(16)
        self.__sw_release(l_value)
        return l_value.value.decode()

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


# Library name is platform dependent
if sys.platform == 'win32':
    lib = _Lib('CAENVMElib')
else:
    lib = _Lib('CAENVME')


def _get_l_arg(board_type: BoardType, arg: Union[int, str]):
    if board_type in (BoardType.ETH_V4718, BoardType.ETH_V4718_LOCAL):
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
    board_type: BoardType = field(repr=False)
    arg: Union[int, str] = field(repr=False)
    conet_node: int = field(repr=False)

    def __del__(self) -> None:
        if self.opened:
            self.close()

    # C API wrappers

    _T = TypeVar('_T', bound='Device')

    @classmethod
    def open(cls: Type[_T], board_type: BoardType, arg: Union[int, str], conet_node: int = 0) -> _T:
        """
        Wrapper to CAENVME_Init2()
        """
        l_arg = _get_l_arg(board_type, arg)
        l_handle = ct.c_int32()
        lib.init2(board_type, l_arg, conet_node, l_handle)
        return cls(l_handle.value, True, board_type, arg, conet_node)

    def connect(self) -> None:
        """
        Wrapper to CAENVME_Init2()
        New instances should be created with open().
        This is meant to reconnect a device closed with close().
        """
        if self.opened:
            raise RuntimeError('Already connected.')
        l_arg = _get_l_arg(self.board_type, self.arg)
        l_handle = ct.c_int32()
        lib.init2(self.board_type, l_arg, self.conet_node, l_handle)
        self.handle = l_handle.value
        self.opened = True

    def close(self) -> None:
        """
        Wrapper to CAENVME_End()
        """
        lib.end(self.handle)
        self.opened = False

    def board_fw_release(self) -> str:
        """
        Wrapper to CAENVME_BoardFWRelease()
        """
        l_value = ct.create_string_buffer(16)
        lib.board_fw_release(self.handle, l_value)
        return l_value.value.decode()

    def driver_release(self) -> str:
        """
        Wrapper to CAENVME_DriverRelease()
        """
        l_value = ct.create_string_buffer(16)
        lib.driver_release(self.handle, l_value)
        return l_value.value.decode()

    def device_reset(self) -> None:
        """
        Wrapper to CAENVME_DeviceReset()
        """
        lib.device_reset(self.handle)

    def read_cycle(self, address: int, am: AddressModifiers, dw: DataWidth) -> int:
        """
        Wrapper to CAENVME_ReadCycle()
        """
        l_value = dw.ctypes()
        lib.read_cycle(self.handle, address, ct.pointer(l_value), am, dw)
        return l_value.value

    def rmw_cycle(self, address: int, value: int, am: AddressModifiers, dw: DataWidth) -> int:
        """
        Wrapper to CAENVME_RMWCycle()
        """
        l_value = dw.ctypes(value)
        lib.rmw_cycle(self.handle, address, ct.pointer(l_value), am, dw)
        return l_value.value

    def write_cycle(self, address: int, value: int, am: AddressModifiers, dw: DataWidth) -> None:
        """
        Wrapper to CAENVME_WriteCycle()
        """
        l_value = dw.ctypes(value)
        lib.write_cycle(self.handle, address, ct.pointer(l_value), am, dw)

    def multi_read(self, addrs: Sequence[int], n_cycles: int, ams: Sequence[AddressModifiers], dws: Sequence[DataWidth]) -> Tuple[int, ...]:
        """
        Wrapper to CAENVME_MultiRead()
        """
        l_addrs = (ct.c_uint32 * n_cycles)(*addrs[:n_cycles])
        l_data = (ct.c_uint32 * n_cycles)()
        l_ams = (ct.c_int * n_cycles)(*ams[:n_cycles])
        l_dws = (ct.c_int * n_cycles)(*dws[:n_cycles])
        l_ecs = (ct.c_int * n_cycles)()
        lib.multi_read(self.handle, l_addrs, l_data, n_cycles, l_ams, l_dws, l_ecs)
        if any(l_ecs):
            failed_cycles = [i for i, ec in enumerate(l_ecs) if ec]
            raise RuntimeError(f'multi_read failed at cycles {failed_cycles}')
        return tuple(int(d) for d in l_data)

    def multi_write(self, addrs: Sequence[int], data: Sequence[int], n_cycles: int, ams: Sequence[AddressModifiers], dws: Sequence[DataWidth]) -> None:
        """
        Wrapper to CAENVME_MultiWrite()
        """
        l_addrs = (ct.c_uint32 * n_cycles)(*addrs[:n_cycles])
        l_data = (ct.c_uint32 * n_cycles)(*data[:n_cycles])
        l_ams = (ct.c_int * n_cycles)(*ams[:n_cycles])
        l_dws = (ct.c_int * n_cycles)(*dws[:n_cycles])
        l_ecs = (ct.c_int * n_cycles)()
        lib.multi_read(self.handle, l_addrs, l_data, n_cycles, l_ams, l_dws, l_ecs)
        if any(l_ecs):
            failed_cycles = [i for i, ec in enumerate(l_ecs) if ec]
            raise RuntimeError(f'multi_write failed at cycles {failed_cycles}')

    def blt_read_cycle(self, address: int, size: int, am: AddressModifiers, dw: DataWidth) -> Tuple[int, ...]:
        """
        Wrapper to CAENVME_BLTReadCycle()
        """
        l_data = (dw.ctypes * size)()
        l_count = ct.c_int()
        lib.blt_read_cycle(self.handle, address, l_data, size, am, dw, l_count)
        return tuple(int(d) for d in l_data[:l_count.value])

    def fifo_blt_read_cycle(self, address: int, size: int, am: AddressModifiers, dw: DataWidth) -> Tuple[int, ...]:
        """
        Wrapper to CAENVME_FIFOBLTReadCycle()
        """
        l_data = (dw.ctypes * size)()
        l_count = ct.c_int()
        lib.fifo_blt_read_cycle(self.handle, address, l_data, size, am, dw, l_count)
        return tuple(int(d) for d in l_data[:l_count.value])

    def mblt_read_cycle(self, address: int, size: int, am: AddressModifiers) -> bytes:
        """
        Wrapper to CAENVME_MBLTReadCycle()
        """
        l_data = (ct.c_ubyte * size)()
        l_count = ct.c_int()
        lib.mblt_read_cycle(self.handle, address, l_data, size, am, l_count)
        return bytes(l_data[:l_count.value])

    def fifo_mblt_read_cycle(self, address: int, size: int, am: AddressModifiers) -> bytes:
        """
        Wrapper to CAENVME_FIFOMBLTReadCycle()
        """
        l_data = (ct.c_ubyte * size)()
        l_count = ct.c_int()
        lib.fifo_mblt_read_cycle(self.handle, address, l_data, size, am, l_count)
        return bytes(l_data[:l_count.value])

    def blt_write_cycle(self, address: int, data: Sequence[int], size: int, am: AddressModifiers, dw: DataWidth) -> int:
        """
        Wrapper to CAENVME_BLTWriteCycle()
        """
        n_data = size // ct.sizeof(dw.ctypes)  # size in bytes
        l_data = (dw.ctypes * size)(*data[:n_data])
        l_count = ct.c_int()
        lib.blt_write_cycle(self.handle, address, l_data, size, am, dw, l_count)
        return l_count.value

    def fifo_blt_write_cycle(self, address: int, data: Sequence[int], size: int, am: AddressModifiers, dw: DataWidth) -> int:
        """
        Wrapper to CAENVME_FIFOBLTWriteCycle()
        """
        n_data = size // ct.sizeof(dw.ctypes)  # data in bytes
        l_data = (dw.ctypes * size)(*data[:n_data])
        l_count = ct.c_int()
        lib.fifo_blt_write_cycle(self.handle, address, l_data, size, am, dw, l_count)
        return l_count.value

    def mblt_write_cycle(self, address: int, data: bytes, size: int, am: AddressModifiers) -> int:
        """
        Wrapper to CAENVME_MBLTWriteCycle()
        """
        if len(data) < size:
            raise RuntimeError('Invalid data size')
        l_count = ct.c_int()
        lib.mblt_write_cycle(self.handle, address, data, size, am, l_count)
        return l_count.value

    def fifo_mblt_write_cycle(self, address: int, data: bytes, size: int, am: AddressModifiers) -> int:
        """
        Wrapper to CAENVME_FIFOMBLTWriteCycle()
        """
        if len(data) < size:
            raise RuntimeError('Invalid data size')
        l_count = ct.c_int()
        lib.fifo_mblt_write_cycle(self.handle, address, data, size, am, l_count)
        return l_count.value

    def ado_cycle(self, address: int, am: AddressModifiers) -> None:
        """
        Wrapper to CAENVME_ADOCycle()
        """
        lib.ado_cycle(self.handle, address, am)

    def adoh_cycle(self, address: int, am: AddressModifiers) -> None:
        """
        Wrapper to CAENVME_ADOHCycle()
        """
        lib.adoh_cycle(self.handle, address, am)

    def iack_cycle(self, levels: int, dw: DataWidth) -> int:
        """
        Wrapper to CAENVME_IACKCycle()
        """
        l_data = dw.ctypes()
        lib.iack_cycle(self.handle, levels, l_data, dw)
        return l_data.value

    def irq_check(self) -> int:
        """
        Wrapper to CAENVME_IRQCheck()
        """
        l_data = ct.c_ubyte()
        lib.irq_check(self.handle, l_data)
        return l_data.value

    def irq_enable(self, mask: int) -> None:
        """
        Wrapper to CAENVME_IRQEnable()
        """
        lib.irq_enable(self.handle, mask)

    def irq_disable(self, mask: int) -> None:
        """
        Wrapper to CAENVME_IRQDisable()
        """
        lib.irq_disable(self.handle, mask)

    def irq_wait(self, mask: int, timeout: int) -> None:
        """
        Wrapper to CAENVME_IRQWait()
        """
        lib.irq_wait(self.handle, mask, timeout)

    def set_pulser_conf(self, pul_sel: PulserSelect, period: int, width: int, unit: TimeUnits, pulse_no: int, start: IOSources, reset: IOSources) -> None:
        """
        Wrapper to CAENVME_SetPulserConf()
        """
        lib.set_pulser_conf(self.handle, pul_sel, period, width, unit, pulse_no, start, reset)

    def set_scaler_conf(self, limit: int, auto_reset: int, hit: IOSources, gate: IOSources, reset: IOSources) -> None:
        """
        Wrapper to CAENVME_SetScalerConf()
        """
        lib.set_scaler_conf(self.handle, limit, auto_reset, hit, gate, reset)

    def set_output_conf(self, out_sel: OutputSelect, out_pol: IOPolarity, led_pol: LEDPolarity, source: IOSources) -> None:
        """
        Wrapper to CAENVME_SetOutputConf()
        """
        lib.set_output_conf(self.handle, out_sel, out_pol, led_pol, source)

    def set_input_conf(self, in_sel: InputSelect, in_pol: IOPolarity, led_pol: LEDPolarity) -> None:
        """
        Wrapper to CAENVME_SetInputConf()
        """
        lib.set_input_conf(self.handle, in_sel, in_pol, led_pol)

    def get_pulser_conf(self, pul_sel: PulserSelect) -> Tuple[int, int, TimeUnits, int, IOSources, IOSources]:
        """
        Wrapper to CAENVME_GetPulserConf()
        """
        l_period = ct.c_ubyte()
        l_width = ct.c_ubyte()
        l_unit = ct.c_int()
        l_pulse_no = ct.c_ubyte()
        l_start = ct.c_int()
        l_reset = ct.c_int()
        lib.get_pulser_conf(self.handle, pul_sel, l_period, l_width, l_unit, l_pulse_no, l_start, l_reset)
        return l_period.value, l_width.value, TimeUnits(l_unit.value), l_pulse_no.value, IOSources(l_start.value), IOSources(l_reset.value)

    def get_scaler_conf(self) -> Tuple[int, int, IOSources, IOSources, IOSources]:
        """
        Wrapper to CAENVME_GetScalerConf()
        """
        l_limit = ct.c_short()
        l_auto_reset = ct.c_short()
        l_hit = ct.c_int()
        l_gate = ct.c_int()
        l_reset = ct.c_int()
        lib.get_scaler_conf(self.handle, l_limit, l_auto_reset, l_hit, l_gate, l_reset)
        return l_limit.value, l_auto_reset.value, IOSources(l_hit.value), IOSources(l_gate.value), IOSources(l_reset.value)

    def get_output_conf(self, out_sel: OutputSelect) -> Tuple[IOPolarity, LEDPolarity, IOSources]:
        """
        Wrapper to CAENVME_GetOutputConf()
        """
        l_out_pol = ct.c_int()
        l_led_pol = ct.c_int()
        l_source = ct.c_int()
        lib.get_output_conf(out_sel, l_out_pol, l_led_pol, l_source)
        return IOPolarity(l_out_pol.value), LEDPolarity(l_led_pol.value), IOSources(l_source.value)

    def get_input_conf(self, in_sel: InputSelect) -> Tuple[IOPolarity, LEDPolarity]:
        """
        Wrapper to CAENVME_GetInputConf()
        """
        l_in_pol = ct.c_int()
        l_led_pol = ct.c_int()
        lib.get_input_conf(in_sel, l_in_pol, l_led_pol)
        return IOPolarity(l_in_pol.value), LEDPolarity(l_led_pol.value)

    def read_register(self, address: int) -> int:
        """
        Wrapper to CAENVME_ReadRegister()
        """
        l_value = ct.c_uint()
        lib.read_register(self.handle, address, l_value)
        return l_value.value

    def write_register(self, address: int, value: int) -> None:
        """
        Wrapper to CAENVME_WriteRegister()
        """
        lib.write_register(self.handle, address, value)

    def write_flash_page(self, page_num: int, data: bytes) -> None:
        """
        Wrapper to CAENVME_WriteFlashPage()
        """
        # Size could be either 264 or 256
        size = len(data)
        l_data = (ct.c_ubyte * size).from_buffer_copy(data)
        lib.write_flash_page(self.handle, l_data, page_num)

    def set_output_register(self, mask: int) -> None:
        """
        Wrapper to CAENVME_SetOutputRegister()
        """
        lib.set_output_register(self.handle, mask)

    def clear_output_register(self, mask: int) -> None:
        """
        Wrapper to CAENVME_ClearOutputRegister()
        """
        lib.clear_output_register(self.handle, mask)

    def pulse_output_register(self, mask: int) -> None:
        """
        Wrapper to CAENVME_PulseOutputRegister()
        """
        lib.pulse_output_register(self.handle, mask)

    def read_display(self) -> Display:
        """
        Wrapper to CAENVME_ReadDisplay()
        """
        l_value = Display()
        lib.read_display(self.handle, l_value)
        return l_value

    def set_arbiter_type(self, value: ArbiterTypes) -> None:
        """
        Wrapper to CAENVME_SetArbiterType()
        """
        lib.set_arbiter_type(self.handle, value)

    def set_requester_type(self, value: RequesterTypes) -> None:
        """
        Wrapper to CAENVME_SetRequesterType()
        """
        lib.set_requester_type(self.handle, value)

    def set_release_type(self, value: ReleaseTypes) -> None:
        """
        Wrapper to CAENVME_SetReleaseType()
        """
        lib.set_release_type(self.handle, value)

    def set_bus_req_level(self, value: BusReqLevels) -> None:
        """
        Wrapper to CAENVME_SetBusReqLevel()
        """
        lib.set_bus_req_level(self.handle, value)

    def set_timeout(self, value: VMETimeouts) -> None:
        """
        Wrapper to CAENVME_SetTimeout()
        """
        lib.set_timeout(self.handle, value)

    def set_location_monitor(self, addr: int, am: AddressModifiers, write: int, lword: int, iack: int) -> None:
        """
        Wrapper to CAENVME_SetLocationMonitor()
        """
        lib.set_location_monitor(self.handle, addr, am, write, lword, iack)

    def set_fifo_mode(self, value: int) -> None:
        """
        Wrapper to CAENVME_SetFIFOMode()
        """
        lib.set_fifo_mode(self.handle, value)

    def get_arbiter_type(self) -> ArbiterTypes:
        """
        Wrapper to CAENVME_GetArbiterType()
        """
        l_value = ct.c_int()
        lib.get_arbiter_type(self.handle, l_value)
        return ArbiterTypes(l_value.value)

    def get_requester_type(self) -> RequesterTypes:
        """
        Wrapper to CAENVME_GetRequesterType()
        """
        l_value = ct.c_int()
        lib.get_requester_type(self.handle, l_value)
        return RequesterTypes(l_value.value)

    def get_release_type(self, value: ReleaseTypes) -> ReleaseTypes:
        """
        Wrapper to CAENVME_GetReleaseType()
        """
        l_value = ct.c_int()
        lib.get_release_type(self.handle, value)
        return ReleaseTypes(l_value.value)

    def get_bus_req_level(self) -> BusReqLevels:
        """
        Wrapper to CAENVME_GetBusReqLevel()
        """
        l_value = ct.c_int()
        lib.get_bus_req_level(self.handle, l_value)
        return BusReqLevels(l_value.value)

    def get_timeout(self) -> VMETimeouts:
        """
        Wrapper to CAENVME_GetTimeout()
        """
        l_value = ct.c_int()
        lib.get_timeout(self.handle, l_value)
        return VMETimeouts(l_value.value)

    def system_reset(self) -> None:
        """
        Wrapper to CAENVME_SystemReset()
        """
        lib.system_reset(self.handle)

    def reset_scaler_count(self) -> None:
        """
        Wrapper to CAENVME_ResetScalerCount()
        """
        lib.reset_scaler_count(self.handle)

    def enable_scaler_gate(self) -> None:
        """
        Wrapper to CAENVME_EnableScalerGate()
        """
        lib.enable_scaler_gate(self.handle)

    def disable_scaler_gate(self) -> None:
        """
        Wrapper to CAENVME_DisableScalerGate()
        """
        lib.disable_scaler_gate(self.handle)

    def start_pulser(self, pulsel: PulserSelect) -> None:
        """
        Wrapper to CAENVME_StartPulser()
        """
        lib.start_pulser(self.handle, pulsel)

    def stop_pulser(self, pulsel: PulserSelect) -> None:
        """
        Wrapper to CAENVME_StopPulser()
        """
        lib.stop_pulser(self.handle, pulsel)

    def read_flash_page(self, page_num: int) -> bytes:
        """
        Wrapper to CAENVME_ReadFlashPage()
        """
        # Allocate maximum size, there is no way to get the read size from API
        l_data = (ct.c_ubyte * 264)()
        lib.read_flash_page(self.handle, l_data, page_num)
        return bytes(l_data)

    def erase_flash_page(self, page_num: int) -> None:
        """
        Wrapper to CAENVME_EraseFlashPage()
        """
        lib.erase_flash_page(self.handle, page_num)

    def set_scaler_input_source(self, source: ScalerSource) -> None:
        """
        Wrapper to CAENVME_SetScaler_InputSource()
        """
        lib.set_scaler_input_source(self.handle, source)

    def get_scaler_input_source(self) -> ScalerSource:
        """
        Wrapper to CAENVME_GetScaler_InputSource()
        """
        l_value = ct.c_int()
        lib.get_scaler_input_source(self.handle, l_value)
        return ScalerSource(l_value.value)

    def set_scaler_gate_source(self, source: ScalerSource) -> None:
        """
        Wrapper to CAENVME_SetScaler_GateSource()
        """
        lib.set_scaler_gate_source(self.handle, source)

    def get_scaler_gate_source(self) -> ScalerSource:
        """
        Wrapper to CAENVME_GetScaler_GateSource()
        """
        l_value = ct.c_int()
        lib.get_scaler_gate_source(self.handle, l_value)
        return ScalerSource(l_value.value)

    def set_scaler_mode(self, mode: ScalerMode) -> None:
        """
        Wrapper to CAENVME_SetScaler_Mode()
        """
        lib.set_scaler_mode(self.handle, mode)

    def get_scaler_mode(self) -> ScalerMode:
        """
        Wrapper to CAENVME_GetScaler_Mode()
        """
        l_value = ct.c_int()
        lib.get_scaler_mode(self.handle, l_value)
        return ScalerMode(l_value.value)

    def set_scaler_clear_source(self, source: ScalerSource) -> None:
        """
        Wrapper to CAENVME_SetScaler_ClearSource()
        """
        lib.set_scaler_clear_source(self.handle, source)

    def set_scaler_start_source(self, source: ScalerSource) -> None:
        """
        Wrapper to CAENVME_SetScaler_StartSource()
        """
        lib.set_scaler_start_source(self.handle, source)

    def get_scaler_start_source(self) -> ScalerSource:
        """
        Wrapper to CAENVME_GetScaler_StartSource()
        """
        l_value = ct.c_int()
        lib.get_scaler_start_source(self.handle, l_value)
        return ScalerSource(l_value.value)

    def set_scaler_continuous_run(self, value: ContinuosRun) -> None:
        """
        Wrapper to CAENVME_SetScaler_ContinuousRun()
        """
        lib.set_scaler_continuous_run(self.handle, value)

    def get_scaler_continuous_run(self) -> ContinuosRun:
        """
        Wrapper to CAENVME_GetScaler_ContinuousRun()
        """
        l_value = ct.c_int()
        lib.get_scaler_continuous_run(self.handle, l_value)
        return ContinuosRun(l_value.value)

    def set_scaler_max_hits(self, value: int) -> None:
        """
        Wrapper to CAENVME_SetScaler_MaxHits()
        """
        lib.set_scaler_max_hits(self.handle, value)

    def get_scaler_max_hits(self) -> int:
        """
        Wrapper to CAENVME_GetScaler_MaxHits()
        """
        l_value = ct.c_uint16()
        lib.get_scaler_max_hits(self.handle, l_value)
        return l_value.value

    def set_scaler_dwell_time(self, value: int) -> None:
        """
        Wrapper to CAENVME_SetScaler_DWellTime()
        """
        lib.set_scaler_dwell_time(self.handle, value)

    def get_scaler_dwell_time(self) -> int:
        """
        Wrapper to CAENVME_GetScaler_DWellTime()
        """
        l_value = ct.c_uint16()
        lib.get_scaler_dwell_time(self.handle, l_value)
        return l_value.value

    def set_scaler_sw_start(self) -> None:
        """
        Wrapper to CAENVME_SetScaler_SWStart()
        """
        lib.set_scaler_sw_start(self.handle)

    def set_scaler_sw_stop(self) -> None:
        """
        Wrapper to CAENVME_SetScaler_SWStop()
        """
        lib.set_scaler_sw_stop(self.handle)

    def set_scaler_sw_reset(self) -> None:
        """
        Wrapper to CAENVME_SetScaler_SWReset()
        """
        lib.set_scaler_sw_reset(self.handle)

    def set_scaler_sw_open_gate(self) -> None:
        """
        Wrapper to CAENVME_SetScaler_SWOpenGate()
        """
        lib.set_scaler_sw_open_gate(self.handle)

    def set_scaler_sw_close_gate(self) -> None:
        """
        Wrapper to CAENVME_SetScaler_SWCloseGate()
        """
        lib.set_scaler_sw_close_gate(self.handle)

    def blt_read_async(self, address: int, size: int, am: AddressModifiers, dw: DataWidth) -> Tuple[int, ...]:
        """
        Wrapper to CAENVME_BLTReadAsync()
        """
        l_data = (dw.ctypes * size)()
        lib.blt_read_async(self.handle, address, l_data, size, am, dw)
        return tuple(int(d) for d in l_data)

    def blt_read_wait(self) -> int:
        """
        Wrapper to CAENVME_BLTReadWait()
        """
        l_value = ct.c_int()
        lib.blt_read_wait(self.handle, l_value)
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
