__author__ = 'Giovanni Cerretani'
__copyright__ = 'Copyright (C) 2024 CAEN SpA'
__license__ = 'LGPL-3.0-or-later'
# SPDX-License-Identifier: LGPL-3.0-or-later

import ctypes as ct
import sys
from dataclasses import dataclass
from enum import IntEnum, IntFlag, unique


@dataclass(slots=True)
class ReadResult:
    """
    Result of a block transfer read operation.

    BUS_ERROR is not considered fatal during BLT/MBLT reads - it typically
    indicates the end of a transfer when the device has no more data available.
    The data field contains all successfully read bytes before the error.
    """
    data: bytes
    bus_error: bool


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


DATA_WIDTH_TYPE: dict[DataWidth, type[ct._SimpleCData]] = {
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
    A16_S = 0x2D
    A16_U = 0x29
    A16_LCK = 0x2C
    A24_S_BLT = 0x3F
    A24_S_PGM = 0x3E
    A24_S_DATA = 0x3D
    A24_S_MBLT = 0x3C
    A24_U_BLT = 0x3B
    A24_U_PGM = 0x3A
    A24_U_DATA = 0x39
    A24_U_MBLT = 0x38
    A24_LCK = 0x32
    A32_S_BLT = 0x0F
    A32_S_PGM = 0x0E
    A32_S_DATA = 0x0D
    A32_S_MBLT = 0x0C
    A32_U_BLT = 0x0B
    A32_U_PGM = 0x0A
    A32_U_DATA = 0x09
    A32_U_MBLT = 0x08
    A32_LCK = 0x05
    CR_CSR = 0x2F

    # The following address modifiers are not yet implemented.
    A40_BLT = 0x37
    A40_LCK = 0x35
    A40 = 0x34
    A64 = 0x01
    A64_BLT = 0x03
    A64_MBLT = 0x00
    A64_LCK = 0x04
    A3U_2EVME = 0x21
    A6U_2EVME = 0x20


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
    O0 = 0
    O1 = 1
    O2 = 2
    O3 = 3
    O4 = 4


@unique
class InputSelect(IntEnum):
    """
    Binding of ::CVInputSelect
    """
    I0 = 0
    I1 = 1


@unique
class IOSources(IntEnum):
    """
    Binding of ::CVIOSources
    """
    MANUAL_SW = 0
    INPUT_SRC_0 = 1
    INPUT_SRC_1 = 2
    COINCIDENCE = 3
    VME_SIGNALS = 4
    MISC_SIGNALS = 6
    PULSER_V3718A = 7
    PULSER_V3718B = 8
    SCALER_END = 9


@unique
class TimeUnits(IntEnum):
    """
    Binding of ::CVTimeUnits
    """
    T25_NS = 0
    T1600_NS = 1
    T410_US  = 2
    T104_MS  = 3
    T25_US   = 4


@unique
class LEDPolarity(IntEnum):
    """
    Binding of ::CVLEDPolarity
    """
    ACTIVE_HIGH = 0
    ACTIVE_LOW = 1


@unique
class IOPolarity(IntEnum):
    """
    Binding of ::CVIOPolarity
    """
    DIRECT = 0
    INVERTED = 1


if sys.platform == 'win32':
    _CaenBool = ct.c_short
else:
    _CaenBool = ct.c_int

_CAEN_FALSE = 0
_CAEN_TRUE = -1


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
    """Raw view of ::CVDisplay"""
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


@dataclass(frozen=True, slots=True)
class Display:
    """
    Binding of ::CVDisplay
    """
    address: int
    data: int
    am: AddressModifiers
    irq: IRQLevels
    ds0: bool
    ds1: bool
    as_: bool
    iack: bool
    write: bool
    lword: bool
    dtack: bool
    berr: bool
    sysres: bool
    br: bool
    bg: bool

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
    PRIORIZED = 0
    ROUNDROBIN = 1


@unique
class RequesterTypes(IntEnum):
    """
    Binding of ::CVRequesterTypes
    """
    FAIR = 0
    DEMAND = 1


@unique
class ReleaseTypes(IntEnum):
    """
    Binding of ::CVReleaseTypes
    """
    RWD = 0
    ROR = 1


@unique
class BusReqLevels(IntEnum):
    """
    Binding of ::CVBusReqLevels
    """
    BR0 = 0
    BR1 = 1
    BR2 = 2
    BR3 = 3


@unique
class VMETimeouts(IntEnum):
    """
    Binding of ::CVVMETimeouts
    """
    T50_US = 0
    T400_US = 1


@unique
class ScalerSource(IntEnum):
    """
    Binding of ::CVScalerSource
    """
    IN0 = 0x0002
    IN1 = 0x0003
    DTACK = 0x0006
    BERR = 0x0007
    DS = 0x0004
    AS = 0x0005
    SW = 0x0008
    FP_BUTTON = 0x0009
    COINC = 0x000A
    INOR = 0x000B


@unique
class ScalerMode(IntEnum):
    """
    Binding of ::CVScalerMode
    """
    GATE_MODE = 0
    DWELL_TIME_MODE = 1
    MAX_HITS_MODE = 2


@unique
class ContinuosRun(IntEnum):
    """
    Binding of ::CVContinuosRun
    """
    OFF = 1
    ON = 0
