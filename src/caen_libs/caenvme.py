"""
Binding of CAEN VMELib
"""

__author__ = 'Giovanni Cerretani'
__copyright__ = 'Copyright (C) 2024 CAEN SpA'
__license__ = 'LGPL-3.0-or-later'
# SPDX-License-Identifier: LGPL-3.0-or-later

import ctypes as ct
import sys
from collections.abc import Callable, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import IntEnum, IntFlag, unique
from typing import TypeVar, Union

from caen_libs import error, _utils

@unique
class BoardType(IntEnum):
    """
    Binding of ::CVBoardTypes
    """
    # V1718
    V1718 = 0

    # V2718
    V2718 = 1
    USB_A4818_V2718_LOCAL = 5
    USB_A4818_V2718 = 6

    # V3718
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
    Binding of ::CVDataWidth
    """
    D8       = 0x01          # 8 bit
    D16      = 0x02          # 16 bit
    D32      = 0x04          # 32 bit
    D64      = 0x08          # 64 bit
    _DSWAP   = 0x10          # Swapped mask
    D16_SWAP = D16 | _DSWAP  # 16 bit, swapped
    D32_SWAP = D32 | _DSWAP  # 32 bit, swapped
    D64_SWAP = D64 | _DSWAP  # 64 bit, swapped


_DATA_WIDTH_TYPE = {
    DataWidth.D8:       ct.c_uint8,
    DataWidth.D16:      ct.c_uint16,
    DataWidth.D16_SWAP: ct.c_uint16,
    DataWidth.D32:      ct.c_uint32,
    DataWidth.D32_SWAP: ct.c_uint32,
    DataWidth.D64:      ct.c_uint64,
    DataWidth.D64_SWAP: ct.c_uint64,
}


@unique
class AddressModifiers(IntEnum):
    """
    Binding of ::CVAddressModifier
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
    A64          = 0x01  # A64 single transfer access @warning Not yet implemented
    A64_BLT      = 0x03  # A64 block transfer @warning Not yet implemented
    A64_MBLT     = 0x00  # A64 64-bit block transfer @warning Not yet implemented
    A64_LCK      = 0x04  # A64 lock command @warning Not yet implemented
    A3U_2EVME    = 0x21  # 2eVME for 3U modules @warning Not yet implemented
    A6U_2EVME    = 0x20  # 2eVME for 6U modules @warning Not yet implemented


@unique
class PulserSelect(IntEnum):
    """
    Binding of ::CVPulserSelect
    """
    A = 0
    B = 1


@unique
class OutputSelect(IntEnum):
    """
    Binding of ::CVOutputSelect
    """
    O0 = 0  # Output line 0
    O1 = 1  # Output line 1
    O2 = 2  # Output line 2
    O3 = 3  # Output line 3
    O4 = 4  # Output line 4


@unique
class InputSelect(IntEnum):
    """
    Binding of ::CVInputSelect
    """
    I0 = 0  # Input line 0
    I1 = 1  # Input line 1


@unique
class IOSources(IntEnum):
    """
    Binding of ::CVIOSources
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
    Binding of ::CVTimeUnits
    """
    T25_NS   = 0  # 25 nanoseconds
    T1600_NS = 1  # 1.6 microseconds
    T410_US  = 2  # 410 microseconds
    T104_MS  = 3  # 104 milliseconds
    T25_US   = 4  # 25 microseconds


@unique
class LEDPolarity(IntEnum):
    """
    Binding of ::CVLEDPolarity
    """
    ACTIVE_HIGH = 0  # LED emits on signal high level
    ACTIVE_LOW  = 1  # LED emits on signal low level


@unique
class IOPolarity(IntEnum):
    """
    Binding of ::CVIOPolarity
    """
    DIRECT   = 0  # Normal polarity
    INVERTED = 1  # Inverted polarity


if sys.platform == 'win32':
    _CaenBool = ct.c_short  # CAEN_BOOL
    _CAEN_TRUE = -1  # CAEN_TRUE
else:
    _CaenBool = ct.c_int  # CAEN_BOOL
    _CAEN_TRUE = 1  # CAEN_TRUE


class IRQLevels(IntFlag):
    """
    Binding of ::CVIRQLevels
    """
    L1 = 0x01
    L2 = 0x02
    L3 = 0x04
    L4 = 0x08
    L5 = 0x10
    L6 = 0x20
    L7 = 0x40


class _DisplayRaw(ct.Structure):
    _fields_ = [
        ('Address', ct.c_long),
        ('Data', ct.c_long),
        ('AM', ct.c_long),
        ('IRQ', ct.c_long),
        ('DS0', _CaenBool),
        ('DS1', _CaenBool),
        ('AS', _CaenBool),
        ('IACK', _CaenBool),
        ('WRITE', _CaenBool),
        ('LWORD', _CaenBool),
        ('DTACK', _CaenBool),
        ('BERR', _CaenBool),
        ('SYSRES', _CaenBool),
        ('BR', _CaenBool),
        ('BG', _CaenBool),
    ]


@dataclass(frozen=True, **_utils.dataclass_slots)
class Display:
    """
    Binding of ::CVDisplay
    """
    address: int          # VME Address
    data: int             # VME Data
    am: AddressModifiers  # Address modifier
    irq: IRQLevels        # IRQ levels
    ds0: bool             # Data Strobe 0 signal
    ds1: bool             # Data Strobe 1 signal
    as_: bool             # Address Strobe signal
    iack: bool            # Interrupt Acknowledge signal
    write: bool           # Write signal
    lword: bool           # Long Word signal
    dtack: bool           # Data Acknowledge signal
    berr: bool            # Bus Error signal
    sysres: bool          # System Reset signal
    br: bool              # Bus Request signal
    bg: bool              # Bus Grant signal

    @classmethod
    def from_raw(cls, raw: _DisplayRaw):
        """Instantiate from raw data"""
        return cls(
            raw.Address,
            raw.Data,
            AddressModifiers(raw.AM),
            IRQLevels(raw.IRQ),
            raw.DS0 == _CAEN_TRUE,
            raw.DS1 == _CAEN_TRUE,
            raw.AS == _CAEN_TRUE,
            raw.IACK == _CAEN_TRUE,
            raw.WRITE == _CAEN_TRUE,
            raw.LWORD == _CAEN_TRUE,
            raw.DTACK == _CAEN_TRUE,
            raw.BERR == _CAEN_TRUE,
            raw.SYSRES == _CAEN_TRUE,
            raw.BR == _CAEN_TRUE,
            raw.BG == _CAEN_TRUE,
        )


@unique
class ArbiterTypes(IntEnum):
    """
    Binding of ::CVArbiterTypes
    """
    PRIORIZED  = 0  # Priority Arbiter
    ROUNDROBIN = 1  # Round-Robin Arbiter


@unique
class RequesterTypes(IntEnum):
    """
    Binding of ::CVRequesterTypes
    """
    FAIR   = 0  # Fair bus requester
    DEMAND = 1  # On demand bus requester


@unique
class ReleaseTypes(IntEnum):
    """
    Binding of ::CVReleaseTypes
    """
    RWD = 0  # Release When Done
    ROR = 1  # Release On Request


@unique
class BusReqLevels(IntEnum):
    """
    Binding of ::CVBusReqLevels
    """
    BR0 = 0  # Bus request level 0
    BR1 = 1  # Bus request level 1
    BR2 = 2  # Bus request level 2
    BR3 = 3  # Bus request level 3


@unique
class VMETimeouts(IntEnum):
    """
    Binding of ::CVVMETimeouts
    """
    T50_US  = 0  # Timeout is 50 microseconds
    T400_US = 1  # Timeout is 400 microseconds


@unique
class ScalerSource(IntEnum):
    """
    Binding of ::CVScalerSource
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
    Binding of ::CVScalerMode
    """
    GATE_MODE       = 0
    DWELL_TIME_MODE = 1
    MAX_HITS_MODE   = 2


@unique
class ContinuosRun(IntEnum):
    """
    Binding of ::CVContinuosRun
    """
    OFF = 1
    ON  = 0


class Error(error.Error):
    """
    Raised when a wrapped C API function returns negative values.
    """

    @unique
    class Code(IntEnum):
        """
        Binding of ::CVErrorCodes
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

    code: Code

    def __init__(self, message: str, res: int, func: str) -> None:
        self.code = Error.Code(res)
        super().__init__(message, self.code.name, func)


# For backward compatibility. Deprecated.
ErrorCode = Error.Code


# Utility definitions
_c_ubyte_p = ct.POINTER(ct.c_ubyte)
_c_short_p = ct.POINTER(ct.c_short)
_c_int_p = ct.POINTER(ct.c_int)
_c_uint_p = ct.POINTER(ct.c_uint)
_c_uint16_p = ct.POINTER(ct.c_uint16)
_c_int32_p = ct.POINTER(ct.c_int32)
_c_uint32_p = ct.POINTER(ct.c_uint32)
_display_p = ct.POINTER(_DisplayRaw)


class _Lib(_utils.Lib):

    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.__load_api()

    def __load_api(self) -> None:
        # Load API not related to devices
        self.__decode_error = self.__get_str('DecodeError', ct.c_int)
        self.__sw_release = self.__get('SWRelease', ct.c_char_p)

        # Load API
        self.init = self.__get('Init', ct.c_int, ct.c_short, ct.c_short, _c_int32_p)
        self.init2 = self.__get('Init2', ct.c_int, ct.c_void_p, ct.c_short, _c_int32_p)
        self.end = self.__get('End', ct.c_int32)
        self.board_fw_release = self.__get('BoardFWRelease', ct.c_int32, ct.c_char_p)
        self.driver_release = self.__get('DriverRelease', ct.c_int32, ct.c_char_p)
        self.device_reset = self.__get('DeviceReset', ct.c_int32)
        self.read_cycle = self.__get('ReadCycle', ct.c_int32, ct.c_uint32, ct.c_void_p, ct.c_int, ct.c_int)
        self.rmw_cycle = self.__get('RMWCycle', ct.c_int32, ct.c_uint32, ct.c_void_p, ct.c_int, ct.c_int)
        self.write_cycle = self.__get('WriteCycle', ct.c_int32, ct.c_uint32, ct.c_void_p, ct.c_int, ct.c_int)
        self.multi_read = self.__get('MultiRead', ct.c_int32, _c_uint32_p, _c_uint32_p, ct.c_int, _c_int_p, _c_int_p, _c_int_p)
        self.multi_write = self.__get('MultiWrite', ct.c_int32, _c_uint32_p, _c_uint32_p, ct.c_int, _c_int_p, _c_int_p, _c_int_p)
        self.blt_read_cycle = self.__get('BLTReadCycle', ct.c_int32, ct.c_uint32, ct.c_void_p, ct.c_int, ct.c_int, ct.c_int, _c_int_p)
        self.fifo_blt_read_cycle = self.__get('FIFOBLTReadCycle', ct.c_int32, ct.c_uint32, ct.c_void_p, ct.c_int, ct.c_int, ct.c_int, _c_int_p)
        self.mblt_read_cycle = self.__get('MBLTReadCycle', ct.c_int32, ct.c_uint32, ct.c_void_p, ct.c_int, ct.c_int, _c_int_p)
        self.fifo_mblt_read_cycle = self.__get('FIFOMBLTReadCycle', ct.c_int32, ct.c_uint32, ct.c_void_p, ct.c_int, ct.c_int, _c_int_p)
        self.blt_write_cycle = self.__get('BLTWriteCycle', ct.c_int32, ct.c_uint32, ct.c_void_p, ct.c_int, ct.c_int, ct.c_int, _c_int_p)
        self.fifo_blt_write_cycle = self.__get('FIFOBLTWriteCycle', ct.c_int32, ct.c_uint32, ct.c_void_p, ct.c_int, ct.c_int, ct.c_int, _c_int_p)
        self.mblt_write_cycle = self.__get('MBLTWriteCycle', ct.c_int32, ct.c_uint32, ct.c_void_p, ct.c_int, ct.c_int, _c_int_p)
        self.fifo_mblt_write_cycle = self.__get('FIFOMBLTWriteCycle', ct.c_int32, ct.c_uint32, ct.c_void_p, ct.c_int, ct.c_int, _c_int_p)
        self.ado_cycle = self.__get('ADOCycle', ct.c_int32, ct.c_uint32, ct.c_int)
        self.adoh_cycle = self.__get('ADOHCycle', ct.c_int32, ct.c_uint32, ct.c_int)
        self.iack_cycle = self.__get('IACKCycle', ct.c_int32, ct.c_int, ct.c_void_p, ct.c_int)
        self.irq_check = self.__get('IRQCheck', ct.c_int32, _c_ubyte_p)
        self.irq_enable = self.__get('IRQEnable', ct.c_int32, ct.c_uint32)
        self.irq_disable = self.__get('IRQDisable', ct.c_int32, ct.c_uint32)
        self.irq_wait = self.__get('IRQWait', ct.c_int32, ct.c_uint32, ct.c_uint32)
        self.set_pulser_conf = self.__get('SetPulserConf', ct.c_int32, ct.c_int, ct.c_ubyte, ct.c_ubyte, ct.c_int, ct.c_ubyte, ct.c_int, ct.c_int)
        self.set_scaler_conf = self.__get('SetScalerConf', ct.c_int32, ct.c_short, ct.c_short, ct.c_int, ct.c_int, ct.c_int)
        self.set_output_conf = self.__get('SetOutputConf', ct.c_int32, ct.c_int, ct.c_int, ct.c_int, ct.c_int)
        self.set_input_conf = self.__get('SetInputConf', ct.c_int32, ct.c_int, ct.c_int, ct.c_int)
        self.get_pulser_conf = self.__get('GetPulserConf', ct.c_int32, ct.c_int, _c_ubyte_p, _c_ubyte_p, _c_int_p, _c_ubyte_p, _c_int_p, _c_int_p)
        self.get_scaler_conf = self.__get('GetScalerConf', ct.c_int32, _c_short_p, _c_short_p, _c_int_p, _c_int_p, _c_int_p)
        self.get_output_conf = self.__get('GetOutputConf', ct.c_int32, ct.c_int, _c_int_p, _c_int_p, _c_int_p)
        self.get_input_conf = self.__get('GetInputConf', ct.c_int32, ct.c_int, _c_int_p, _c_int_p)
        self.read_register = self.__get('ReadRegister', ct.c_int32, ct.c_int, _c_uint_p)
        self.write_register = self.__get('WriteRegister', ct.c_int32, ct.c_int, ct.c_uint)
        self.set_output_register = self.__get('SetOutputRegister', ct.c_int32, ct.c_ushort)
        self.clear_output_register = self.__get('ClearOutputRegister', ct.c_int32, ct.c_ushort)
        self.pulse_output_register = self.__get('PulseOutputRegister', ct.c_int32, ct.c_ushort)
        self.read_display = self.__get('ReadDisplay', ct.c_int32, _display_p)
        self.set_arbiter_type = self.__get('SetArbiterType', ct.c_int32, ct.c_int)
        self.set_requester_type = self.__get('SetRequesterType', ct.c_int32, ct.c_int)
        self.set_release_type = self.__get('SetReleaseType', ct.c_int32, ct.c_int)
        self.set_bus_req_level = self.__get('SetBusReqLevel', ct.c_int32, ct.c_int)
        self.set_timeout = self.__get('SetTimeout', ct.c_int32, ct.c_int)
        self.set_location_monitor = self.__get('SetLocationMonitor', ct.c_int32, ct.c_uint32, ct.c_int, ct.c_short, ct.c_short, ct.c_short)
        self.set_fifo_mode = self.__get('SetFIFOMode', ct.c_int32, ct.c_short)
        self.get_arbiter_type = self.__get('GetArbiterType', ct.c_int32, _c_int_p)
        self.get_requester_type = self.__get('GetRequesterType', ct.c_int32, _c_int_p)
        self.get_release_type = self.__get('GetReleaseType', ct.c_int32, _c_int_p)
        self.get_bus_req_level = self.__get('GetBusReqLevel', ct.c_int32, _c_int_p)
        self.get_timeout = self.__get('GetTimeout', ct.c_int32, _c_int_p)
        self.get_fifo_mode = self.__get('GetFIFOMode', ct.c_int32, _c_short_p)
        self.system_reset = self.__get('SystemReset', ct.c_int32)
        self.reset_scaler_count = self.__get('ResetScalerCount', ct.c_int32)
        self.enable_scaler_gate = self.__get('EnableScalerGate', ct.c_int32)
        self.disable_scaler_gate = self.__get('DisableScalerGate', ct.c_int32)
        self.start_pulser = self.__get('StartPulser', ct.c_int32, ct.c_int)
        self.stop_pulser = self.__get('StopPulser', ct.c_int32, ct.c_int)
        self.write_flash_page = self.__get('WriteFlashPage', ct.c_int32, _c_ubyte_p, ct.c_int)
        self.read_flash_page = self.__get('ReadFlashPage', ct.c_int32, _c_ubyte_p, ct.c_int)
        self.erase_flash_page = self.__get('EraseFlashPage', ct.c_int32, ct.c_int)
        self.set_scaler_input_source = self.__get('SetScaler_InputSource', ct.c_int32, ct.c_int)
        self.get_scaler_input_source = self.__get('GetScaler_InputSource', ct.c_int32, _c_int_p)
        self.set_scaler_gate_source = self.__get('SetScaler_GateSource', ct.c_int32, ct.c_int)
        self.get_scaler_gate_source = self.__get('GetScaler_GateSource', ct.c_int32, _c_int_p)
        self.set_scaler_mode = self.__get('SetScaler_Mode', ct.c_int32, ct.c_int)
        self.get_scaler_mode = self.__get('GetScaler_Mode', ct.c_int32, _c_int_p)
        self.set_scaler_clear_source = self.__get('SetScaler_ClearSource', ct.c_int32, ct.c_int)
        self.set_scaler_start_source = self.__get('SetScaler_StartSource', ct.c_int32, ct.c_int)
        self.get_scaler_start_source = self.__get('GetScaler_StartSource', ct.c_int32, _c_int_p)
        self.set_scaler_continuous_run = self.__get('SetScaler_ContinuousRun', ct.c_int32, ct.c_int)
        self.get_scaler_continuous_run = self.__get('GetScaler_ContinuousRun', ct.c_int32, _c_int_p)
        self.set_scaler_max_hits = self.__get('SetScaler_MaxHits', ct.c_int32, ct.c_uint16)
        self.get_scaler_max_hits = self.__get('GetScaler_MaxHits', ct.c_int32, _c_uint16_p)
        self.set_scaler_dwell_time = self.__get('SetScaler_DWellTime', ct.c_int32, ct.c_uint16)
        self.get_scaler_dwell_time = self.__get('GetScaler_DWellTime', ct.c_int32, _c_uint16_p)
        self.set_scaler_sw_start = self.__get('SetScaler_SWStart', ct.c_int32)
        self.set_scaler_sw_stop = self.__get('SetScaler_SWStop', ct.c_int32)
        self.set_scaler_sw_reset = self.__get('SetScaler_SWReset', ct.c_int32)
        self.set_scaler_sw_open_gate = self.__get('SetScaler_SWOpenGate', ct.c_int32)
        self.set_scaler_sw_close_gate = self.__get('SetScaler_SWCloseGate', ct.c_int32)
        self.blt_read_async = self.__get('BLTReadAsync', ct.c_int32, ct.c_uint32, ct.c_void_p, ct.c_int, ct.c_int, ct.c_int, linux_only=True)
        self.blt_read_wait = self.__get('BLTReadWait', ct.c_int32, _c_int_p, linux_only=True)

    def __api_errcheck(self, res: int, func, _: tuple) -> int:
        if res < 0:
            raise Error(self.__decode_error(res), res, func.__name__)
        return res

    def __get(self, name: str, *args: type, **kwargs) -> Callable[..., int]:
        if kwargs.get('linux_only', False) and sys.platform == 'win32':
            def fallback_win(*args, **kwargs):
                raise RuntimeError(f'{name} function is Linux only.')
            return fallback_win
        func = self.get(f'CAENVME_{name}')
        func.argtypes = args
        func.restype = ct.c_int
        func.errcheck = self.__api_errcheck  # type: ignore
        return func

    def __get_str(self, name: str, *args) -> Callable[..., str]:
        func = self.get(f'CAENVME_{name}')
        func.argtypes = args
        func.restype = ct.c_char_p
        # cannot fail, errcheck improperly used to cast bytes to str
        func.errcheck = lambda res, *_: res.decode('ascii')  # type: ignore
        return func

    # C API bindings

    def sw_release(self) -> str:
        """
        Binding of CAENVME_SWRelease()
        """
        l_value = ct.create_string_buffer(32)  # Undocumented but, hopefully, long enough
        self.__sw_release(l_value)
        return l_value.value.decode('ascii')


# Library name is platform dependent
if sys.platform == 'win32':
    _LIB_NAME = 'CAENVMElib'
else:
    _LIB_NAME = 'CAENVME'


lib = _Lib(_LIB_NAME)


def _get_l_arg(board_type: BoardType, arg: Union[int, str]):
    if board_type in (BoardType.ETH_V4718, BoardType.ETH_V4718_LOCAL):
        assert isinstance(arg, str), 'arg expected to be a string'
        return arg.encode('ascii')
    else:
        l_link_number = int(arg)
        l_link_number_ct = ct.c_uint32(l_link_number)
        return ct.pointer(l_link_number_ct)


@dataclass(**_utils.dataclass_slots)
class Device:
    """
    Class representing a device.
    """

    # Public members
    handle: int
    board_type: BoardType
    arg: Union[int, str]
    conet_node: int

    # Private members
    __opened: bool = field(default=True, repr=False)
    __registers: _utils.Registers = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.__registers = _utils.Registers(self.read_register, self.write_register)

    def __del__(self) -> None:
        if self.__opened:
            self.close()

    # C API bindings

    _T = TypeVar('_T', bound='Device')

    @classmethod
    def open(cls: type[_T], board_type: BoardType, arg: Union[int, str], conet_node: int = 0) -> _T:
        """
        Binding of CAENVME_Init2()
        """
        l_arg = _get_l_arg(board_type, arg)
        l_handle = ct.c_int32()
        lib.init2(board_type, l_arg, conet_node, l_handle)
        return cls(l_handle.value, board_type, arg, conet_node)

    def connect(self) -> None:
        """
        Binding of CAENVME_Init2()

        New instances should be created with open(). This is meant to
        reconnect a device closed with close().
        """
        if self.__opened:
            raise RuntimeError('Already connected.')
        l_arg = _get_l_arg(self.board_type, self.arg)
        l_handle = ct.c_int32()
        lib.init2(self.board_type, l_arg, self.conet_node, l_handle)
        self.handle = l_handle.value
        self.__opened = True

    def close(self) -> None:
        """
        Binding of CAENVME_End()
        """
        lib.end(self.handle)
        self.__opened = False

    def board_fw_release(self) -> str:
        """
        Binding of CAENVME_BoardFWRelease()
        """
        l_value = ct.create_string_buffer(32)  # Undocumented but, hopefully, long enough
        lib.board_fw_release(self.handle, l_value)
        return l_value.value.decode('ascii')

    def driver_release(self) -> str:
        """
        Binding of CAENVME_DriverRelease()
        """
        l_value = ct.create_string_buffer(32)  # Undocumented but, hopefully, long enough
        lib.driver_release(self.handle, l_value)
        return l_value.value.decode('ascii')

    def device_reset(self) -> None:
        """
        Binding of CAENVME_DeviceReset()
        """
        lib.device_reset(self.handle)

    def read_cycle(self, address: int, am: AddressModifiers, dw: DataWidth) -> int:
        """
        Binding of CAENVME_ReadCycle()
        """
        l_value = _DATA_WIDTH_TYPE[dw]()
        lib.read_cycle(self.handle, address, ct.byref(l_value), am, dw)
        return l_value.value

    def rmw_cycle(self, address: int, value: int, am: AddressModifiers, dw: DataWidth) -> int:
        """
        Binding of CAENVME_RMWCycle()
        """
        l_value = _DATA_WIDTH_TYPE[dw](value)
        lib.rmw_cycle(self.handle, address, ct.byref(l_value), am, dw)
        return l_value.value

    def write_cycle(self, address: int, value: int, am: AddressModifiers, dw: DataWidth) -> None:
        """
        Binding of CAENVME_WriteCycle()
        """
        l_value = _DATA_WIDTH_TYPE[dw](value)
        lib.write_cycle(self.handle, address, ct.byref(l_value), am, dw)

    def multi_read(self, addrs: Sequence[int], ams: Sequence[AddressModifiers], dws: Sequence[DataWidth]) -> list[int]:
        """
        Binding of CAENVME_MultiRead()
        """
        n_cycles = len(addrs)
        l_addrs = (ct.c_uint32 * n_cycles)(*addrs)
        l_data = (ct.c_uint32 * n_cycles)()
        l_ams = (ct.c_int * n_cycles)(*ams)
        l_dws = (ct.c_int * n_cycles)(*dws)
        l_ecs = (ct.c_int * n_cycles)()
        lib.multi_read(self.handle, l_addrs, l_data, n_cycles, l_ams, l_dws, l_ecs)
        failed_cycles = {i: Error.Code(ec).name for i, ec in enumerate(l_ecs) if ec}
        if failed_cycles:
            raise RuntimeError(f'multi_read failed at cycles {failed_cycles}')
        return l_data[:]

    def multi_write(self, addrs: Sequence[int], data: Sequence[int], ams: Sequence[AddressModifiers], dws: Sequence[DataWidth]) -> None:
        """
        Binding of CAENVME_MultiWrite()
        """
        n_cycles = len(addrs)
        l_addrs = (ct.c_uint32 * n_cycles)(*addrs)
        l_data = (ct.c_uint32 * n_cycles)(*data)
        l_ams = (ct.c_int * n_cycles)(*ams)
        l_dws = (ct.c_int * n_cycles)(*dws)
        l_ecs = (ct.c_int * n_cycles)()
        lib.multi_write(self.handle, l_addrs, l_data, n_cycles, l_ams, l_dws, l_ecs)
        failed_cycles = {i: Error.Code(ec).name for i, ec in enumerate(l_ecs) if ec}
        if failed_cycles:
            raise RuntimeError(f'multi_write failed at cycles {failed_cycles}')

    def blt_read_cycle(self, address: int, size: int, am: AddressModifiers, dw: DataWidth) -> list[int]:
        """
        Binding of CAENVME_BLTReadCycle()
        """
        n_data = size // ct.sizeof(_DATA_WIDTH_TYPE[dw])
        l_data = (_DATA_WIDTH_TYPE[dw] * n_data)()
        l_count = ct.c_int()
        lib.blt_read_cycle(self.handle, address, l_data, size, am, dw, l_count)
        return l_data[:l_count.value]  # type: ignore

    def fifo_blt_read_cycle(self, address: int, size: int, am: AddressModifiers, dw: DataWidth) -> list[int]:
        """
        Binding of CAENVME_FIFOBLTReadCycle()
        """
        n_data = size // ct.sizeof(_DATA_WIDTH_TYPE[dw])
        l_data = (_DATA_WIDTH_TYPE[dw] * n_data)()
        l_count = ct.c_int()
        lib.fifo_blt_read_cycle(self.handle, address, l_data, size, am, dw, l_count)
        return l_data[:l_count.value]  # type: ignore

    def mblt_read_cycle(self, address: int, size: int, am: AddressModifiers) -> bytes:
        """
        Binding of CAENVME_MBLTReadCycle()
        """
        l_data = (ct.c_ubyte * size)()
        l_count = ct.c_int()
        lib.mblt_read_cycle(self.handle, address, l_data, size, am, l_count)
        return bytes(l_data[:l_count.value])

    def fifo_mblt_read_cycle(self, address: int, size: int, am: AddressModifiers) -> bytes:
        """
        Binding of CAENVME_FIFOMBLTReadCycle()
        """
        l_data = (ct.c_ubyte * size)()
        l_count = ct.c_int()
        lib.fifo_mblt_read_cycle(self.handle, address, l_data, size, am, l_count)
        return bytes(l_data[:l_count.value])

    def blt_write_cycle(self, address: int, data: Sequence[int], am: AddressModifiers, dw: DataWidth) -> int:
        """
        Binding of CAENVME_BLTWriteCycle()
        """
        n_data = len(data)
        size = n_data * ct.sizeof(_DATA_WIDTH_TYPE[dw])  # in bytes
        l_data = (_DATA_WIDTH_TYPE[dw] * n_data)(*data)
        l_count = ct.c_int()
        lib.blt_write_cycle(self.handle, address, l_data, size, am, dw, l_count)
        return l_count.value

    def fifo_blt_write_cycle(self, address: int, data: Sequence[int], am: AddressModifiers, dw: DataWidth) -> int:
        """
        Binding of CAENVME_FIFOBLTWriteCycle()
        """
        n_data = len(data)
        size = n_data * ct.sizeof(_DATA_WIDTH_TYPE[dw])  # in bytes
        l_data = (_DATA_WIDTH_TYPE[dw] * n_data)(*data)
        l_count = ct.c_int()
        lib.fifo_blt_write_cycle(self.handle, address, l_data, size, am, dw, l_count)
        return l_count.value

    def mblt_write_cycle(self, address: int, data: bytes, am: AddressModifiers) -> int:
        """
        Binding of CAENVME_MBLTWriteCycle()
        """
        l_count = ct.c_int()
        lib.mblt_write_cycle(self.handle, address, data, len(data), am, l_count)
        return l_count.value

    def fifo_mblt_write_cycle(self, address: int, data: bytes, am: AddressModifiers) -> int:
        """
        Binding of CAENVME_FIFOMBLTWriteCycle()
        """
        l_count = ct.c_int()
        lib.fifo_mblt_write_cycle(self.handle, address, data, len(data), am, l_count)
        return l_count.value

    def ado_cycle(self, address: int, am: AddressModifiers) -> None:
        """
        Binding of CAENVME_ADOCycle()
        """
        lib.ado_cycle(self.handle, address, am)

    def adoh_cycle(self, address: int, am: AddressModifiers) -> None:
        """
        Binding of CAENVME_ADOHCycle()
        """
        lib.adoh_cycle(self.handle, address, am)

    def iack_cycle(self, levels: IRQLevels, dw: DataWidth) -> int:
        """
        Binding of CAENVME_IACKCycle()
        """
        l_data = _DATA_WIDTH_TYPE[dw]()
        lib.iack_cycle(self.handle, levels, l_data, dw)
        return l_data.value

    def irq_check(self) -> IRQLevels:
        """
        Binding of CAENVME_IRQCheck()
        """
        l_data = ct.c_ubyte()
        lib.irq_check(self.handle, l_data)
        return IRQLevels(l_data.value)

    def irq_enable(self, mask: IRQLevels) -> None:
        """
        Binding of CAENVME_IRQEnable()
        """
        lib.irq_enable(self.handle, mask)

    def irq_disable(self, mask: IRQLevels) -> None:
        """
        Binding of CAENVME_IRQDisable()
        """
        lib.irq_disable(self.handle, mask)

    def irq_wait(self, mask: IRQLevels, timeout: int) -> None:
        """
        Binding of CAENVME_IRQWait()
        """
        lib.irq_wait(self.handle, mask, timeout)

    def set_pulser_conf(self, pul_sel: PulserSelect, period: int, width: int, unit: TimeUnits, pulse_no: int, start: IOSources, reset: IOSources) -> None:
        """
        Binding of CAENVME_SetPulserConf()
        """
        lib.set_pulser_conf(self.handle, pul_sel, period, width, unit, pulse_no, start, reset)

    def set_scaler_conf(self, limit: int, auto_reset: int, hit: IOSources, gate: IOSources, reset: IOSources) -> None:
        """
        Binding of CAENVME_SetScalerConf()
        """
        lib.set_scaler_conf(self.handle, limit, auto_reset, hit, gate, reset)

    def set_output_conf(self, out_sel: OutputSelect, out_pol: IOPolarity, led_pol: LEDPolarity, source: IOSources) -> None:
        """
        Binding of CAENVME_SetOutputConf()
        """
        lib.set_output_conf(self.handle, out_sel, out_pol, led_pol, source)

    def set_input_conf(self, in_sel: InputSelect, in_pol: IOPolarity, led_pol: LEDPolarity) -> None:
        """
        Binding of CAENVME_SetInputConf()
        """
        lib.set_input_conf(self.handle, in_sel, in_pol, led_pol)

    def get_pulser_conf(self, pul_sel: PulserSelect) -> tuple[int, int, TimeUnits, int, IOSources, IOSources]:
        """
        Binding of CAENVME_GetPulserConf()
        """
        l_period = ct.c_ubyte()
        l_width = ct.c_ubyte()
        l_unit = ct.c_int()
        l_pulse_no = ct.c_ubyte()
        l_start = ct.c_int()
        l_reset = ct.c_int()
        lib.get_pulser_conf(self.handle, pul_sel, l_period, l_width, l_unit, l_pulse_no, l_start, l_reset)
        return l_period.value, l_width.value, TimeUnits(l_unit.value), l_pulse_no.value, IOSources(l_start.value), IOSources(l_reset.value)

    def get_scaler_conf(self) -> tuple[int, int, IOSources, IOSources, IOSources]:
        """
        Binding of CAENVME_GetScalerConf()
        """
        l_limit = ct.c_short()
        l_auto_reset = ct.c_short()
        l_hit = ct.c_int()
        l_gate = ct.c_int()
        l_reset = ct.c_int()
        lib.get_scaler_conf(self.handle, l_limit, l_auto_reset, l_hit, l_gate, l_reset)
        return l_limit.value, l_auto_reset.value, IOSources(l_hit.value), IOSources(l_gate.value), IOSources(l_reset.value)

    def get_output_conf(self, out_sel: OutputSelect) -> tuple[IOPolarity, LEDPolarity, IOSources]:
        """
        Binding of CAENVME_GetOutputConf()
        """
        l_out_pol = ct.c_int()
        l_led_pol = ct.c_int()
        l_source = ct.c_int()
        lib.get_output_conf(self.handle, out_sel, l_out_pol, l_led_pol, l_source)
        return IOPolarity(l_out_pol.value), LEDPolarity(l_led_pol.value), IOSources(l_source.value)

    def get_input_conf(self, in_sel: InputSelect) -> tuple[IOPolarity, LEDPolarity]:
        """
        Binding of CAENVME_GetInputConf()
        """
        l_in_pol = ct.c_int()
        l_led_pol = ct.c_int()
        lib.get_input_conf(self.handle, in_sel, l_in_pol, l_led_pol)
        return IOPolarity(l_in_pol.value), LEDPolarity(l_led_pol.value)

    def read_register(self, address: int) -> int:
        """
        Binding of CAENVME_ReadRegister()
        """
        l_value = ct.c_uint()
        lib.read_register(self.handle, address, l_value)
        return l_value.value

    def write_register(self, address: int, value: int) -> None:
        """
        Binding of CAENVME_WriteRegister()
        """
        lib.write_register(self.handle, address, value)

    @property
    def registers(self) -> _utils.Registers:
        """Utility to simplify register access"""
        return self.__registers

    def write_flash_page(self, page_num: int, data: bytes) -> None:
        """
        Binding of CAENVME_WriteFlashPage()
        """
        # Size could be either 264 or 256
        size = len(data)
        l_data = (ct.c_ubyte * size).from_buffer_copy(data)
        lib.write_flash_page(self.handle, l_data, page_num)

    def set_output_register(self, mask: int) -> None:
        """
        Binding of CAENVME_SetOutputRegister()
        """
        lib.set_output_register(self.handle, mask)

    def clear_output_register(self, mask: int) -> None:
        """
        Binding of CAENVME_ClearOutputRegister()
        """
        lib.clear_output_register(self.handle, mask)

    def pulse_output_register(self, mask: int) -> None:
        """
        Binding of CAENVME_PulseOutputRegister()
        """
        lib.pulse_output_register(self.handle, mask)

    def read_display(self) -> Display:
        """
        Binding of CAENVME_ReadDisplay()
        """
        l_d = _DisplayRaw()
        lib.read_display(self.handle, l_d)
        return Display.from_raw(l_d)

    def set_arbiter_type(self, value: ArbiterTypes) -> None:
        """
        Binding of CAENVME_SetArbiterType()
        """
        lib.set_arbiter_type(self.handle, value)

    def set_requester_type(self, value: RequesterTypes) -> None:
        """
        Binding of CAENVME_SetRequesterType()
        """
        lib.set_requester_type(self.handle, value)

    def set_release_type(self, value: ReleaseTypes) -> None:
        """
        Binding of CAENVME_SetReleaseType()
        """
        lib.set_release_type(self.handle, value)

    def set_bus_req_level(self, value: BusReqLevels) -> None:
        """
        Binding of CAENVME_SetBusReqLevel()
        """
        lib.set_bus_req_level(self.handle, value)

    def set_timeout(self, value: VMETimeouts) -> None:
        """
        Binding of CAENVME_SetTimeout()
        """
        lib.set_timeout(self.handle, value)

    def set_location_monitor(self, addr: int, am: AddressModifiers, write: int, lword: int, iack: int) -> None:
        """
        Binding of CAENVME_SetLocationMonitor()
        """
        lib.set_location_monitor(self.handle, addr, am, write, lword, iack)

    def set_fifo_mode(self, value: int) -> None:
        """
        Binding of CAENVME_SetFIFOMode()
        """
        lib.set_fifo_mode(self.handle, value)

    def get_arbiter_type(self) -> ArbiterTypes:
        """
        Binding of CAENVME_GetArbiterType()
        """
        l_value = ct.c_int()
        lib.get_arbiter_type(self.handle, l_value)
        return ArbiterTypes(l_value.value)

    def get_requester_type(self) -> RequesterTypes:
        """
        Binding of CAENVME_GetRequesterType()
        """
        l_value = ct.c_int()
        lib.get_requester_type(self.handle, l_value)
        return RequesterTypes(l_value.value)

    def get_release_type(self, value: ReleaseTypes) -> ReleaseTypes:
        """
        Binding of CAENVME_GetReleaseType()
        """
        l_value = ct.c_int()
        lib.get_release_type(self.handle, value)
        return ReleaseTypes(l_value.value)

    def get_bus_req_level(self) -> BusReqLevels:
        """
        Binding of CAENVME_GetBusReqLevel()
        """
        l_value = ct.c_int()
        lib.get_bus_req_level(self.handle, l_value)
        return BusReqLevels(l_value.value)

    def get_timeout(self) -> VMETimeouts:
        """
        Binding of CAENVME_GetTimeout()
        """
        l_value = ct.c_int()
        lib.get_timeout(self.handle, l_value)
        return VMETimeouts(l_value.value)

    def get_fifo_mode(self) -> int:
        """
        Binding of CAENVME_GetFIFOMode()
        """
        l_value = ct.c_short()
        lib.get_fifo_mode(self.handle, l_value)
        return l_value.value

    def system_reset(self) -> None:
        """
        Binding of CAENVME_SystemReset()
        """
        lib.system_reset(self.handle)

    def reset_scaler_count(self) -> None:
        """
        Binding of CAENVME_ResetScalerCount()
        """
        lib.reset_scaler_count(self.handle)

    def enable_scaler_gate(self) -> None:
        """
        Binding of CAENVME_EnableScalerGate()
        """
        lib.enable_scaler_gate(self.handle)

    def disable_scaler_gate(self) -> None:
        """
        Binding of CAENVME_DisableScalerGate()
        """
        lib.disable_scaler_gate(self.handle)

    def start_pulser(self, pulsel: PulserSelect) -> None:
        """
        Binding of CAENVME_StartPulser()
        """
        lib.start_pulser(self.handle, pulsel)

    def stop_pulser(self, pulsel: PulserSelect) -> None:
        """
        Binding of CAENVME_StopPulser()
        """
        lib.stop_pulser(self.handle, pulsel)

    def read_flash_page(self, page_num: int) -> bytes:
        """
        Binding of CAENVME_ReadFlashPage()
        """
        # Allocate maximum size, there is no way to get the read size from API
        l_data = (ct.c_ubyte * 264)()
        lib.read_flash_page(self.handle, l_data, page_num)
        return bytes(l_data)

    def erase_flash_page(self, page_num: int) -> None:
        """
        Binding of CAENVME_EraseFlashPage()
        """
        lib.erase_flash_page(self.handle, page_num)

    def set_scaler_input_source(self, source: ScalerSource) -> None:
        """
        Binding of CAENVME_SetScaler_InputSource()
        """
        lib.set_scaler_input_source(self.handle, source)

    def get_scaler_input_source(self) -> ScalerSource:
        """
        Binding of CAENVME_GetScaler_InputSource()
        """
        l_value = ct.c_int()
        lib.get_scaler_input_source(self.handle, l_value)
        return ScalerSource(l_value.value)

    def set_scaler_gate_source(self, source: ScalerSource) -> None:
        """
        Binding of CAENVME_SetScaler_GateSource()
        """
        lib.set_scaler_gate_source(self.handle, source)

    def get_scaler_gate_source(self) -> ScalerSource:
        """
        Binding of CAENVME_GetScaler_GateSource()
        """
        l_value = ct.c_int()
        lib.get_scaler_gate_source(self.handle, l_value)
        return ScalerSource(l_value.value)

    def set_scaler_mode(self, mode: ScalerMode) -> None:
        """
        Binding of CAENVME_SetScaler_Mode()
        """
        lib.set_scaler_mode(self.handle, mode)

    def get_scaler_mode(self) -> ScalerMode:
        """
        Binding of CAENVME_GetScaler_Mode()
        """
        l_value = ct.c_int()
        lib.get_scaler_mode(self.handle, l_value)
        return ScalerMode(l_value.value)

    def set_scaler_clear_source(self, source: ScalerSource) -> None:
        """
        Binding of CAENVME_SetScaler_ClearSource()
        """
        lib.set_scaler_clear_source(self.handle, source)

    def set_scaler_start_source(self, source: ScalerSource) -> None:
        """
        Binding of CAENVME_SetScaler_StartSource()
        """
        lib.set_scaler_start_source(self.handle, source)

    def get_scaler_start_source(self) -> ScalerSource:
        """
        Binding of CAENVME_GetScaler_StartSource()
        """
        l_value = ct.c_int()
        lib.get_scaler_start_source(self.handle, l_value)
        return ScalerSource(l_value.value)

    def set_scaler_continuous_run(self, value: ContinuosRun) -> None:
        """
        Binding of CAENVME_SetScaler_ContinuousRun()
        """
        lib.set_scaler_continuous_run(self.handle, value)

    def get_scaler_continuous_run(self) -> ContinuosRun:
        """
        Binding of CAENVME_GetScaler_ContinuousRun()
        """
        l_value = ct.c_int()
        lib.get_scaler_continuous_run(self.handle, l_value)
        return ContinuosRun(l_value.value)

    def set_scaler_max_hits(self, value: int) -> None:
        """
        Binding of CAENVME_SetScaler_MaxHits()
        """
        lib.set_scaler_max_hits(self.handle, value)

    def get_scaler_max_hits(self) -> int:
        """
        Binding of CAENVME_GetScaler_MaxHits()
        """
        l_value = ct.c_uint16()
        lib.get_scaler_max_hits(self.handle, l_value)
        return l_value.value

    def set_scaler_dwell_time(self, value: int) -> None:
        """
        Binding of CAENVME_SetScaler_DWellTime()
        """
        lib.set_scaler_dwell_time(self.handle, value)

    def get_scaler_dwell_time(self) -> int:
        """
        Binding of CAENVME_GetScaler_DWellTime()
        """
        l_value = ct.c_uint16()
        lib.get_scaler_dwell_time(self.handle, l_value)
        return l_value.value

    def set_scaler_sw_start(self) -> None:
        """
        Binding of CAENVME_SetScaler_SWStart()
        """
        lib.set_scaler_sw_start(self.handle)

    def set_scaler_sw_stop(self) -> None:
        """
        Binding of CAENVME_SetScaler_SWStop()
        """
        lib.set_scaler_sw_stop(self.handle)

    def set_scaler_sw_reset(self) -> None:
        """
        Binding of CAENVME_SetScaler_SWReset()
        """
        lib.set_scaler_sw_reset(self.handle)

    def set_scaler_sw_open_gate(self) -> None:
        """
        Binding of CAENVME_SetScaler_SWOpenGate()
        """
        lib.set_scaler_sw_open_gate(self.handle)

    def set_scaler_sw_close_gate(self) -> None:
        """
        Binding of CAENVME_SetScaler_SWCloseGate()
        """
        lib.set_scaler_sw_close_gate(self.handle)

    def blt_read_async(self, address: int, size: int, am: AddressModifiers, dw: DataWidth) -> list[int]:
        """
        Binding of CAENVME_BLTReadAsync()
        """
        n_data = size // ct.sizeof(_DATA_WIDTH_TYPE[dw])
        l_data = (_DATA_WIDTH_TYPE[dw] * n_data)()
        lib.blt_read_async(self.handle, address, l_data, size, am, dw)
        return l_data[:]  # type: ignore

    def blt_read_wait(self) -> int:
        """
        Binding of CAENVME_BLTReadWait()
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
        if self.__opened:
            self.close()
