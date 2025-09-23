__author__ = 'Giovanni Cerretani'
__copyright__ = 'Copyright (C) 2024 CAEN SpA'
__license__ = 'LGPL-3.0-or-later'
# SPDX-License-Identifier: LGPL-3.0-or-later

import ctypes as ct
import sys
from dataclasses import dataclass
from enum import IntEnum, IntFlag, unique

from caen_libs import _utils

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


DATA_WIDTH_TYPE = {
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
else:
    _CaenBool = ct.c_int  # CAEN_BOOL

_CAEN_FALSE = 0  # CAEN_FALSE
_CAEN_TRUE = -1  # CAEN_TRUE


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


class DisplayRaw(ct.Structure):
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
    def from_raw(cls, raw: DisplayRaw):
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
