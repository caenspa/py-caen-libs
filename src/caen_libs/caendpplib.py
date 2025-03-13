"""
Binding of CAEN DPP Library
"""

__author__ = 'Giovanni Cerretani'
__copyright__ = 'Copyright (C) 2024 CAEN SpA'
__license__ = 'LGPL-3.0-or-later'
# SPDX-License-Identifier: LGPL-3.0-or-later

import ctypes as ct
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import IntEnum, IntFlag, unique
import os
from pathlib import Path
import sys
from typing import Optional, TypeVar

import numpy as np
import numpy.typing as npt

from caen_libs import error, _utils


# Constants from CAENDPPLibTypes.h
MAX_BRDNAME_LEN = 12
MAX_FWVER_LENGTH = 20
MAX_LICENSE_DIGITS = 8
MAX_LICENSE_LENGTH = MAX_LICENSE_DIGITS * 2 + 1
MAX_LISTFILE_LENGTH = 155
MAX_LIST_BUFF_NEV = 8192
MAX_NUMB = 20
MAX_NUMCHB = 16
MAX_NTHR = MAX_NUMB
MAX_ALTHR_NAME_LEN = 50
MAX_NUMCHB_COINCIDENCE = MAX_NUMCHB + 1
MAX_GW = 1000
MAX_GPIO_NUM = 2
DEFAULT_HISTO_NUM = 1
CHANNEL_IDX_ALL = -1
HISTO_IDX_CURRENT = -1
HISTO_IDX_ALL = -2
X770_RECORDLENGTH = 2048
MAX_INRANGES = 15
MAX_PROBES_NUM = 20
IP_ADDR_LEN = 255
X7GS_RECORDLENGTH = 2040
X7GS_PRETRIGGER = 256
MAX_RUNNAME = 128
MAX_HVCHB = 2
MAX_HVRANGES = 3
MAX_HVSTATUS_LENGTH = 100
MAX_LIST_VALS = 15


@unique
class ConnectionType(IntEnum):
    """
    Binding of ::CAENDPP_ConnectionType
    """
    USB = 0
    PCI_OPTICAL_LINK = 1
    ETH = 2
    SERIAL = 3


class _ConnectionParamsRaw(ct.Structure):
    _fields_ = [
        ('LinkType', ct.c_int),
        ('LinkNum', ct.c_int32),
        ('ConetNode', ct.c_int32),
        ('VMEBaseAddress', ct.c_uint32),
        ('ETHAddress', ct.c_char * (IP_ADDR_LEN + 1)),
    ]


@dataclass(frozen=True, **_utils.dataclass_slots)
class ConnectionParams:
    """
    Binding of ::CAENDPP_ConnectionParams_t
    """
    link_type: ConnectionType
    link_num: int
    conet_node: int = field(default=0)
    vme_base_address: int = field(default=0)
    eth_address: str = field(default='')

    def to_raw(self) -> _ConnectionParamsRaw:
        """Convert to raw data"""
        return _ConnectionParamsRaw(
            self.link_type,
            self.link_num,
            self.conet_node,
            self.vme_base_address,
            self.eth_address.encode('ascii'),
        )


class _ParamInfoRaw(ct.Structure):
    _fields_ = [
        ('type', ct.c_int),
        ('minimum', ct.c_double),
        ('maximum', ct.c_double),
        ('resolution', ct.c_double),
        ('values', ct.c_double * MAX_LIST_VALS),
        ('valuesCount', ct.c_uint32),
        ('units', ct.c_int),
    ]


class InfoType(IntEnum):
    """
    Binding of ::CAENDPP_InfoType_t
    """
    RANGE = 0
    LIST = 1


class Units(IntEnum):
    """
    Binding of ::CAENDPP_Units_t
    """
    NANOSECONDS = 0
    SAMPLES = 1
    ADIMENSIONAL = 2
    MICROAMPERE = 3
    VOLT = 4
    VOLT_AT_SECOND = 5
    OHM = 6


@dataclass(frozen=True, **_utils.dataclass_slots)
class ParamInfo:
    """
    Binding of ::CAENDPP_ParamInfo_t
    """
    type: InfoType
    minimum: float
    maximum: float
    resolution: float
    values: tuple[float, ...]
    units: Units

    @classmethod
    def from_raw(cls, raw: _ParamInfoRaw):
        """Instantiate from raw data"""
        return cls(
            InfoType(raw.type),
            raw.minimum,
            raw.maximum,
            raw.resolution,
            raw.values[:raw.valuesCount],
            Units(raw.units),
        )


class _HVRangeInfoRaw(ct.Structure):
    _fields_ = [
        ('VSetInfo', _ParamInfoRaw),
        ('ISetInfo', _ParamInfoRaw),
        ('RampUpInfo', _ParamInfoRaw),
        ('RampDownInfo', _ParamInfoRaw),
        ('VMaxInfo', _ParamInfoRaw),
        ('VMonInfo', _ParamInfoRaw),
        ('IMonInfo', _ParamInfoRaw),
        ('VExtInfo', _ParamInfoRaw),
        ('RTMPInfo', _ParamInfoRaw),
        ('HVRangeCode', ct.c_int),
    ]


class HVRange(IntEnum):
    """
    Binding of ::CAENDPP_HVRange_t
    """
    HPGE = 0
    PMT = 1
    SD = 2


@dataclass(frozen=True, **_utils.dataclass_slots)
class HVRangeInfo:
    """
    Binding of ::CAENDPP_HVRangeInfo_t
    """
    v_set_info: ParamInfo
    i_set_info: ParamInfo
    ramp_up_info: ParamInfo
    ramp_down_info: ParamInfo
    v_max_info: ParamInfo
    v_mon_info: ParamInfo
    i_mon_info: ParamInfo
    v_ext_info: ParamInfo
    rtmp_info: ParamInfo
    hv_range_code: HVRange

    @classmethod
    def from_raw(cls, raw: _HVRangeInfoRaw):
        """Instantiate from raw data"""
        return cls(
            ParamInfo.from_raw(raw.VSetInfo),
            ParamInfo.from_raw(raw.ISetInfo),
            ParamInfo.from_raw(raw.RampUpInfo),
            ParamInfo.from_raw(raw.RampDownInfo),
            ParamInfo.from_raw(raw.VMaxInfo),
            ParamInfo.from_raw(raw.VMonInfo),
            ParamInfo.from_raw(raw.IMonInfo),
            ParamInfo.from_raw(raw.VExtInfo),
            ParamInfo.from_raw(raw.RTMPInfo),
            HVRange(raw.HVRangeCode),
        )


class _HVChannelInfoRaw(ct.Structure):
    _fields_ = [
        ('HVFamilyCode', ct.c_int),
        ('NumRanges', ct.c_int32),
        ('RangeInfos', _HVRangeInfoRaw * MAX_HVRANGES),
    ]


class HVFamilyCode(IntEnum):
    """
    Binding of ::CAENDPP_HVFamilyCode_t
    """
    V6521 = 0
    V6533 = 1
    V6519 = 2
    V6521H = 3
    V6534 = 4


@dataclass(frozen=True, **_utils.dataclass_slots)
class HVChannelInfo:
    """
    Binding of ::CAENDPP_HVChannelInfo_t
    """
    hv_family_code: HVFamilyCode
    range_infos: tuple[HVRangeInfo, ...]

    @classmethod
    def from_raw(cls, raw: _HVChannelInfoRaw):
        """Instantiate from raw data"""
        return cls(
            HVFamilyCode(raw.HVFamilyCode),
            tuple(map(HVRangeInfo.from_raw, raw.RangeInfos[:raw.NumRanges])),
        )


class _InfoRaw(ct.Structure):
    _fields_ = [
        ('ModelName', ct.c_char * MAX_BRDNAME_LEN),
        ('Model', ct.c_int32),
        ('Channels', ct.c_uint32),
        ('ROC_FirmwareRel', ct.c_char * MAX_FWVER_LENGTH),
        ('AMC_FirmwareRel', ct.c_char * MAX_FWVER_LENGTH),
        ('License', ct.c_char * MAX_LICENSE_LENGTH),
        ('SerialNumber', ct.c_uint32),
        ('Status', ct.c_uint8),
        ('FamilyCode', ct.c_int32),
        ('HVChannels', ct.c_uint32),
        ('FormFactor', ct.c_uint32),
        ('PCB_Revision', ct.c_uint32),
        ('ADC_NBits', ct.c_uint32),
        ('Energy_MaxNBits', ct.c_uint32),
        ('USBOption', ct.c_uint32),
        ('ETHOption', ct.c_uint32),
        ('WIFIOption', ct.c_uint32),
        ('BTOption', ct.c_uint32),
        ('POEOption', ct.c_uint32),
        ('GPSOption', ct.c_uint32),
        ('InputRangeNum', ct.c_uint32),
        ('InputRanges', ct.c_int * MAX_INRANGES),
        ('Tsample', ct.c_double),
        ('SupportedVirtualProbes1', ct.c_uint32 * MAX_PROBES_NUM),
        ('NumVirtualProbes1', ct.c_uint32),
        ('SupportedVirtualProbes2', ct.c_uint32 * MAX_PROBES_NUM),
        ('NumVirtualProbes2', ct.c_uint32),
        ('SupportedDigitalProbes1', ct.c_uint32 * MAX_PROBES_NUM),
        ('NumDigitalProbes1', ct.c_uint32),
        ('SupportedDigitalProbes2', ct.c_uint32 * MAX_PROBES_NUM),
        ('NumDigitalProbes2', ct.c_uint32),
        ('DPPCodeMaj', ct.c_int32),
        ('DPPCodeMin', ct.c_int32),
        ('HVChannelInfo', _HVChannelInfoRaw * MAX_HVCHB),
        ('NumMonOutProbes', ct.c_uint32),
        ('SupportedMonOutProbes', ct.c_uint32 * MAX_PROBES_NUM),
    ]


@unique
class BoardModel(IntEnum):
    """
    Binding of ::CAENDPP_BoardModel_t
    """
    V1724 = 0
    DT5724 = 6
    N6724 = 12
    DT5780 = 21
    N6780 = 22
    V1780 = 23
    DT5730 = 30
    N6730 = 31
    V1730 = 32
    DT5781 = 36
    N6781 = 37
    V1781 = 38
    DT5725 = 39
    N6725 = 40
    V1725 = 41
    V1782 = 42
    DT5770 = -1
    N6770 = -2
    V1770 = -3
    DT57GS = -4
    DT5000 = 5000
    DT6000 = 6000


@unique
class BoardFamilyCode(IntEnum):
    """
    Binding of ::CAENDPP_BoardFamilyCode_t
    """
    XX724 = 0
    XX780 = 7
    XX730 = 11
    XX781 = 13
    XX725 = 14
    XX782 = 16
    XX000 = 5000
    XX770 = -1
    XX7GS = -2


@unique
class BoardFormFactor(IntEnum):
    """
    Binding of ::CAENDPP_BoardFormFactor_t
    """
    VME64 = 0
    VME64X = 1
    DESKTOP = 2
    NIM = 3


class InputRange(IntEnum):
    """
    Binding of ::CAENDPP_InputRange_t
    """
    R_9_5VPP = 0
    R_3_7VPP = 1
    R_1_4VPP = 2
    R_0_6VPP = 3
    R_3_0VPP = 4
    R_1_0VPP = 5
    R_0_3VPP = 6
    R_10_0VPP = 7
    R_5_0VPP = 8
    R_2_0VPP = 9
    R_0_5VPP = 10
    R_2_5VPP = 11
    R_1_25VPP = 12
    R_0_1VPP = 13
    R_0_21VPP = 14
    R_0_45VPP = 15
    R_0_83VPP = 16
    R_1_6VPP = 17
    R_3_3VPP = 18
    R_6_6VPP = 19
    R_13_3VPP = 20
    R_X0_25 = 93
    R_X0_5 = 94
    R_X1 = 95
    R_X2 = 96
    R_X4 = 97
    R_X8 = 98
    R_X16 = 99
    R_X32 = 100
    R_X64 = 101
    R_X128 = 102
    R_X256 = 103
    R_X3 = 104
    R_X7 = 105
    R_X17 = 106
    R_X10 = 107
    R_X33 = 108
    R_UNKN = -1


@unique
class VirtualProbe1(IntEnum):
    """
    Binding of ::CAENDPP_PHA_VirtualProbe1_t
    """
    INPUT = 0
    DELTA = 1
    DELTA2 = 2
    TRAPEZOID = 3
    FAST_TRAP = 4
    TRAP_BASELINE = 5
    ENERGY_OUT = 6
    TRAP_BL_CORR = 7
    NONE = 8
    FAST_TRIGGER = 9
    SLOW_TRIGGER = 10


@unique
class VirtualProbe2(IntEnum):
    """
    Binding of ::CAENDPP_PHA_VirtualProbe2_t
    """
    INPUT = 0
    S3 = 1
    TRAP_BL_CORR = 2
    TRAP_BASELINE = 3
    NONE = 4
    DELTA = 5
    FAST_TRAP = 6
    DELTA2 = 7
    TRAPEZOID = 8
    ENERGY_OUT = 9
    FAST_TRIGGER = 10
    SLOW_TRIGGER = 11


@unique
class DigitalProbe1(IntEnum):
    """
    Binding of ::CAENDPP_PHA_DigitalProbe1_t
    """
    TRG_WIN = 0
    ARMED = 1
    PK_RUN = 2
    PUR_FLAG = 3
    PEAKING = 4
    TVAW = 5
    BL_HOLDOFF = 6
    TRG_HOLDOFF = 7
    TRG_VAL = 8
    ACQ_VETO = 9
    BFM_VETO = 10
    EXT_TRG = 11
    TRIGGER = 12
    NONE = 13
    ENERGY_ACCEPTED = 14
    SATURATION = 15
    RESET = 16
    BL_FREEZE = 17
    BUSY = 18
    PRG_VETO = 19
    INHIBIT = 20


@unique
class DigitalProbe2(IntEnum):
    """
    Binding of ::CAENDPP_PHA_DigitalProbe2_t
    """
    TRIGGER = 0
    NONE = 1
    PEAKING = 2
    BL_HOLDOFF = 3
    PUR_FLAG = 4
    ENERGY_ACCEPTED = 5
    SATURATION = 6
    RESET = 7


@unique
class DPPCode(IntEnum):
    """
    Binding of ::CAENDPP_DPPCode_t
    """
    UNKNOWN = 0xDEADFACE  # Special value for Python binding
    X7GS_V1 = 1  # Undocumented value returned by Gamma Stream
    PHA_X724 = 0x80
    PHA_X730 = 0x8B
    CI_X720 = 0x82
    PSD_X720 = 0x83
    PSD_X751 = 0x84
    ZLE_X751 = 0x85
    CI_X743 = 0x86
    PSD_X730 = 0x88
    PHA_XHEX = 0x8E

    @classmethod
    def _missing_(cls, _):
        """
        To avoid errors in case of unknown code, we return UNKNOWN
        """
        return cls.UNKNOWN


@unique
class PHAMonOutProbe(IntEnum):
    """
    Binding of ::CAENDPP_PHA_MonOutProbe_t
    """
    INPUT = 0
    FAST_TRIGGER = 1
    TRAPEZOID = 2
    TRAP_BL_CORR = 3


@dataclass(frozen=True, **_utils.dataclass_slots)
class Info:
    """
    Binding of ::CAENDPP_Info_t
    """
    model_name: str
    model: BoardModel
    channels: int
    roc_firmware_rel: str
    amc_firmware_rel: str
    license: str
    serial_number: int
    status: int
    family_code: BoardFamilyCode
    hv_channels: int
    form_factor: BoardFormFactor
    pcb_revision: int
    adc_nbits: int
    energy_max_nbits: int
    usb_option: bool
    eth_option: bool
    wifi_option: bool
    bt_option: bool
    poe_option: bool
    gps_option: bool
    input_ranges: tuple[InputRange, ...]
    tsample: float
    supported_virtual_probes1: tuple[VirtualProbe1, ...]
    supported_virtual_probes2: tuple[VirtualProbe2, ...]
    supported_digital_probes1: tuple[DigitalProbe1, ...]
    supported_digital_probes2: tuple[DigitalProbe2, ...]
    dpp_code_maj: DPPCode
    dpp_code_min: int
    hv_channel_info: tuple[HVChannelInfo, ...]
    supported_mon_out_probes: tuple[PHAMonOutProbe, ...]

    @classmethod
    def from_raw(cls, raw: _InfoRaw):
        """Instantiate from raw data"""
        return cls(
            raw.ModelName.decode('ascii'),
            BoardModel(raw.Model),
            raw.Channels,
            raw.ROC_FirmwareRel.decode('ascii'),
            raw.AMC_FirmwareRel.decode('ascii'),
            raw.License.decode('ascii'),
            raw.SerialNumber,
            raw.Status,
            BoardFamilyCode(raw.FamilyCode),
            raw.HVChannels,
            BoardFormFactor(raw.FormFactor),
            raw.PCB_Revision,
            raw.ADC_NBits,
            raw.Energy_MaxNBits,
            bool(raw.USBOption),
            bool(raw.ETHOption),
            bool(raw.WIFIOption),
            bool(raw.BTOption),
            bool(raw.POEOption),
            bool(raw.GPSOption),
            tuple(map(InputRange, raw.InputRanges[:raw.InputRangeNum])),
            raw.Tsample,
            tuple(map(VirtualProbe1, raw.SupportedVirtualProbes1[:raw.NumVirtualProbes1])),
            tuple(map(VirtualProbe2, raw.SupportedVirtualProbes2[:raw.NumVirtualProbes2])),
            tuple(map(DigitalProbe1, raw.SupportedDigitalProbes1[:raw.NumDigitalProbes1])),
            tuple(map(DigitalProbe2, raw.SupportedDigitalProbes2[:raw.NumDigitalProbes2])),
            DPPCode(raw.DPPCodeMaj),
            raw.DPPCodeMin,
            tuple(map(HVChannelInfo.from_raw, raw.HVChannelInfo[:raw.HVChannels])),
            tuple(map(PHAMonOutProbe, raw.SupportedMonOutProbes[:raw.NumMonOutProbes])),
        )


class _TempCorrParamsRaw(ct.Structure):
    _fields_ = [
        ('enabled', ct.c_int32),
        ('LLD', ct.c_int32),
        ('ULD', ct.c_int32),
    ]


@dataclass(**_utils.dataclass_slots)
class TempCorrParams:
    """
    Binding of ::CAENDPP_TempCorrParams_t
    """
    enabled: bool = field(default=False)
    lld: int = field(default=0)
    uld: int = field(default=0)

    @classmethod
    def from_raw(cls, raw: _TempCorrParamsRaw):
        """Instantiate from raw data"""
        return cls(bool(raw.enabled), raw.LLD, raw.ULD)

    def to_raw(self) -> _TempCorrParamsRaw:
        """Convert to raw data"""
        return _TempCorrParamsRaw(self.enabled, self.lld, self.uld)


class _GPIORaw(ct.Structure):
    _fields_ = [
        ('Mode', ct.c_int),
        ('SigOut', ct.c_int),
        ('DACInvert', ct.c_uint8),
        ('DACOffset', ct.c_uint32),
    ]


class GPIOMode(IntEnum):
    """
    Binding of ::CAENDPP_GPIOMode_t
    """
    OUT_SIGNAL = 0
    IN_TRIGGER = 2
    IN_RESET = 3


class OutSignal(IntEnum):
    """
    Binding of ::CAENDPP_OUTSignal_t
    """
    OFF = 0
    DIGITAL_TRIGGER = 1
    DIGITAL_ESAMPLE = 2
    DIGITAL_BLSAMPLE = 3
    DIGITAL_RESET_DETECTED = 4
    DIGITAL_RUNNING = 5
    DIGITAL_SATURATION = 6
    DIGITAL_PUR = 7
    DIGITAL_PUI = 8
    DIGITAL_TRESET_PERIODIC = 9
    DIGITAL_CLKHALF = 10
    DIGITAL_BLINHIBIT = 11
    DIGITAL_SCA1 = 12
    DIGITAL_SCA2 = 13
    ANALOG_INPUT = 100
    ANALOG_FAST_TRAP = 101
    ANALOG_BASELINE = 102
    ANALOG_TRAPEZOID = 103
    ANALOG_ENERGY = 104
    ANALOG_TRAP_CORRECTED = 105
    DIGITAL_FIRST = DIGITAL_TRIGGER
    DIGITAL_LAST = DIGITAL_SCA2
    ANALOG_FIRST = ANALOG_INPUT
    ANALOG_LAST = ANALOG_TRAP_CORRECTED


@dataclass(frozen=True, **_utils.dataclass_slots)
class GPIO:
    """
    Binding of ::CAENDPP_GPIO_t
    """
    mode: GPIOMode
    sig_out: OutSignal
    dac_invert: bool
    dac_offset: int

    @classmethod
    def from_raw(cls, raw: _GPIORaw):
        """Instantiate from raw data"""
        return cls(GPIOMode(raw.Mode), OutSignal(raw.SigOut), bool(raw.DACInvert), raw.DACOffset)

    def to_raw(self) -> _GPIORaw:
        """Convert to raw data"""
        return _GPIORaw(self.mode, self.sig_out, self.dac_invert, self.dac_offset)


class _GPIOConfigRaw(ct.Structure):
    _fields_ = [
        ('GPIOs', _GPIORaw * MAX_GPIO_NUM),
        ('TRGControl', ct.c_int),
        ('GPIOLogic', ct.c_int),
        ('TimeWindow', ct.c_uint32),
        ('TransResetLength', ct.c_uint32),
        ('TransResetPeriod', ct.c_uint32),
    ]


@unique
class TriggerControl(IntEnum):
    """
    Binding of ::CAENDPP_TriggerControl_t
    """
    INTERNAL = 0
    ON = 5
    OFF = 7
    GATE = 1
    GATE_WIN = 3
    COINCIDENCE = 6
    VETO = 2
    VETO_WIN = 4


@unique
class GPIOLogic(IntEnum):
    """
    Binding of ::CAENDPP_GPIOLogic_t
    """
    AND = 0
    OR = 1


@dataclass(**_utils.dataclass_slots)
class GPIOConfig:
    """
    Binding of ::CAENDPP_GPIOConfig_t
    """
    gpios: list[GPIO] = field(default_factory=list)
    trg_control: TriggerControl = field(default=TriggerControl.INTERNAL)
    gpio_logic: GPIOLogic = field(default=GPIOLogic.AND)
    time_window: int = field(default=0)
    trans_reset_length: int = field(default=0)
    trans_reset_period: int = field(default=0)

    @classmethod
    def from_raw(cls, raw: _GPIOConfigRaw):
        """Instantiate from raw data"""
        return cls(
            [GPIO.from_raw(i) for i in raw.GPIOs],
            TriggerControl(raw.TRGControl),
            GPIOLogic(raw.GPIOLogic),
            raw.TimeWindow,
            raw.TransResetLength,
            raw.TransResetPeriod,
        )

    def to_raw(self) -> _GPIOConfigRaw:
        """Convert to raw data"""
        return _GPIOConfigRaw(
            tuple(i.to_raw() for i in self.gpios),
            self.trg_control,
            self.gpio_logic,
            self.time_window,
            self.trans_reset_length,
            self.trans_reset_period,
        )


class _ExtraParametersRaw(ct.Structure):
    _fields_ = [
        ('trigK', ct.c_int32),
        ('trigm', ct.c_int32),
        ('trigMODE', ct.c_int32),
        ('energyFilterMode', ct.c_int32),
        ('InputImpedance', ct.c_int),
        ('CRgain', ct.c_uint32),
        ('TRgain', ct.c_uint32),
        ('SaturationHoldoff', ct.c_uint32),
        ('GPIOConfig', _GPIOConfigRaw),
    ]


@unique
class InputImpedance(IntEnum):
    """
    Binding of ::CAENDPP_InputImpedance_t
    """
    O_50 = 0
    O_1K = 1


@dataclass(**_utils.dataclass_slots)
class ExtraParameters:
    """
    Binding of ::CAENDPP_ExtraParameters
    """
    trig_k: int = field(default=0)
    trigm: int = field(default=0)
    trig_mode: int = field(default=0)
    energy_filter_mode: int = field(default=0)
    input_impedance: InputImpedance = field(default=InputImpedance.O_1K)
    cr_gain: int = field(default=0)
    tr_gain: int = field(default=0)
    saturation_holdoff: int = field(default=0)
    gpio_config: GPIOConfig = field(default_factory=GPIOConfig)

    @classmethod
    def from_raw(cls, raw: _ExtraParametersRaw):
        """Instantiate from raw data"""
        return cls(
            raw.trigK,
            raw.trigm,
            raw.trigMODE,
            raw.energyFilterMode,
            InputImpedance(raw.InputImpedance),
            raw.CRgain,
            raw.TRgain,
            raw.SaturationHoldoff,
            GPIOConfig.from_raw(raw.GPIOConfig),
        )

    def to_raw(self) -> _ExtraParametersRaw:
        """Convert to raw data"""
        return _ExtraParametersRaw(
            self.trig_k,
            self.trigm,
            self.trig_mode,
            self.energy_filter_mode,
            self.input_impedance,
            self.cr_gain,
            self.tr_gain,
            self.saturation_holdoff,
            self.gpio_config.to_raw(),
        )


class _PHAParamsRaw(ct.Structure):
    _fields_ = [
        ('M', ct.c_int32 * MAX_NUMCHB),
        ('m', ct.c_int32 * MAX_NUMCHB),
        ('k', ct.c_int32 * MAX_NUMCHB),
        ('ftd', ct.c_int32 * MAX_NUMCHB),
        ('a', ct.c_int32 * MAX_NUMCHB),
        ('b', ct.c_int32 * MAX_NUMCHB),
        ('thr', ct.c_int32 * MAX_NUMCHB),
        ('nsbl', ct.c_int32 * MAX_NUMCHB),
        ('nspk', ct.c_int32 * MAX_NUMCHB),
        ('pkho', ct.c_int32 * MAX_NUMCHB),
        ('blho', ct.c_int32 * MAX_NUMCHB),
        ('trgho', ct.c_int32 * MAX_NUMCHB),
        ('dgain', ct.c_int32 * MAX_NUMCHB),
        ('enf', ct.c_float * MAX_NUMCHB),
        ('decimation', ct.c_int32 * MAX_NUMCHB),
        ('enskim', ct.c_int32 * MAX_NUMCHB),
        ('eskimlld', ct.c_int32 * MAX_NUMCHB),
        ('eskimuld', ct.c_int32 * MAX_NUMCHB),
        ('blrclip', ct.c_int32 * MAX_NUMCHB),
        ('dcomp', ct.c_int32 * MAX_NUMCHB),
        ('trapbsl', ct.c_int32 * MAX_NUMCHB),
        ('pz_dac', ct.c_uint32 * MAX_NUMCHB),
        ('inh_length', ct.c_uint32 * MAX_NUMCHB),
        ('X770_extraparameters', _ExtraParametersRaw * MAX_NUMCHB),
    ]


@dataclass(**_utils.dataclass_slots)
class PHAParams:
    """
    Binding of ::CAENDPP_PHA_Params_t
    """
    m_: list[int] = field(default_factory=list)
    m: list[int] = field(default_factory=list)
    k: list[int] = field(default_factory=list)
    ftd: list[int] = field(default_factory=list)
    a: list[int] = field(default_factory=list)
    b: list[int] = field(default_factory=list)
    thr: list[int] = field(default_factory=list)
    nsbl: list[int] = field(default_factory=list)
    nspk: list[int] = field(default_factory=list)
    pkho: list[int] = field(default_factory=list)
    blho: list[int] = field(default_factory=list)
    trgho: list[int] = field(default_factory=list)
    dgain: list[int] = field(default_factory=list)
    enf: list[float] = field(default_factory=list)
    decimation: list[int] = field(default_factory=list)
    enskim: list[int] = field(default_factory=list)
    eskimlld: list[int] = field(default_factory=list)
    eskimuld: list[int] = field(default_factory=list)
    blrclip: list[int] = field(default_factory=list)
    dcomp: list[int] = field(default_factory=list)
    trapbsl: list[int] = field(default_factory=list)
    pz_dac: list[int] = field(default_factory=list)
    inh_length: list[int] = field(default_factory=list)
    x770_extraparameters: list[ExtraParameters] = field(default_factory=list)

    def resize(self, n_channels: int):
        """Resize to n_channels"""
        self.m_ = [0] * n_channels
        self.m = [0] * n_channels
        self.k = [0] * n_channels
        self.ftd = [0] * n_channels
        self.a = [0] * n_channels
        self.b = [0] * n_channels
        self.thr = [0] * n_channels
        self.nsbl = [0] * n_channels
        self.nspk = [0] * n_channels
        self.pkho = [0] * n_channels
        self.blho = [0] * n_channels
        self.trgho = [0] * n_channels
        self.dgain = [0] * n_channels
        self.enf = [0.] * n_channels
        self.decimation = [0] * n_channels
        self.enskim = [0] * n_channels
        self.eskimlld = [0] * n_channels
        self.eskimuld = [0] * n_channels
        self.blrclip = [0] * n_channels
        self.dcomp = [0] * n_channels
        self.trapbsl = [0] * n_channels
        self.pz_dac = [0] * n_channels
        self.inh_length = [0] * n_channels
        self.x770_extraparameters = [ExtraParameters() for _ in range(n_channels)]

    @classmethod
    def from_raw(cls, raw: _PHAParamsRaw):
        """Instantiate from raw data"""
        return cls(
            raw.M,
            raw.m,
            raw.k,
            raw.ftd,
            raw.a,
            raw.b,
            raw.thr,
            raw.nsbl,
            raw.nspk,
            raw.pkho,
            raw.blho,
            raw.trgho,
            raw.dgain,
            raw.enf,
            raw.decimation,
            raw.enskim,
            raw.eskimlld,
            raw.eskimuld,
            raw.blrclip,
            raw.dcomp,
            raw.trapbsl,
            raw.pz_dac,
            raw.inh_length,
            list(map(ExtraParameters.from_raw, raw.X770_extraparameters)),
        )

    def to_raw(self) -> _PHAParamsRaw:
        """Convert to raw data"""
        return _PHAParamsRaw(
            tuple(self.m_),
            tuple(self.m),
            tuple(self.k),
            tuple(self.ftd),
            tuple(self.a),
            tuple(self.b),
            tuple(self.thr),
            tuple(self.nsbl),
            tuple(self.nspk),
            tuple(self.pkho),
            tuple(self.blho),
            tuple(self.trgho),
            tuple(self.dgain),
            tuple(self.enf),
            tuple(self.decimation),
            tuple(self.enskim),
            tuple(self.eskimlld),
            tuple(self.eskimuld),
            tuple(self.blrclip),
            tuple(self.dcomp),
            tuple(self.trapbsl),
            tuple(self.pz_dac),
            tuple(self.inh_length),
            tuple(i.to_raw() for i in self.x770_extraparameters),
        )


class _WaveformParamsRaw(ct.Structure):
    _fields_ = [
        ('dualTraceMode', ct.c_int32),
        ('vp1', ct.c_int),
        ('vp2', ct.c_int),
        ('dp1', ct.c_int),
        ('dp2', ct.c_int),
        ('recordLength', ct.c_int32),
        ('preTrigger', ct.c_int32),
        ('probeTrigger', ct.c_int),
        ('probeSelfTriggerVal', ct.c_int32),
    ]


@unique
class ProbeTrigger(IntEnum):
    """
    Binding of ::CAENDPP_PHA_ProbeTrigger_t
    """
    MAIN_TRIG = 0
    MAIN_TRIG_DELAY_COMPENSATED = 1
    MAIN_TRIG_ACCEPTED_PULSE = 2
    SELF_TRIG_MUX1 = 3
    SELF_TRIG_MUX2 = 4
    BASELINE_RESTORER = 5
    RESET_DETECTOR = 6
    FREE_RUNNING = 7


@dataclass(**_utils.dataclass_slots)
class WaveformParams:
    """
    Binding of ::CAENDPP_WaveformParams_t
    """
    dual_trace_mode: int = field(default=0)
    vp1: VirtualProbe1 = field(default=VirtualProbe1.INPUT)
    vp2: VirtualProbe2 = field(default=VirtualProbe2.NONE)
    dp1: DigitalProbe1 = field(default=DigitalProbe1.TRIGGER)
    dp2: DigitalProbe2 = field(default=DigitalProbe2.PEAKING)
    record_length: int = field(default=0)
    pre_trigger: int = field(default=0)
    probe_trigger: ProbeTrigger = field(default=ProbeTrigger.MAIN_TRIG)
    probe_self_trigger_val: int = field(default=0)

    @classmethod
    def from_raw(cls, raw: _WaveformParamsRaw):
        """Instantiate from raw data"""
        return cls(
            raw.dualTraceMode,
            VirtualProbe1(raw.vp1),
            VirtualProbe2(raw.vp2),
            DigitalProbe1(raw.dp1),
            DigitalProbe2(raw.dp2),
            raw.recordLength,
            raw.preTrigger,
            ProbeTrigger(raw.probeTrigger),
            raw.probeSelfTriggerVal,
        )

    def to_raw(self) -> _WaveformParamsRaw:
        """Convert to raw data"""
        return _WaveformParamsRaw(
            self.dual_trace_mode,
            self.vp1,
            self.vp2,
            self.dp1,
            self.dp2,
            self.record_length,
            self.pre_trigger,
            self.probe_trigger,
            self.probe_self_trigger_val,
        )


class _ListParamsRaw(ct.Structure):
    _fields_ = [
        ('enabled', ct.c_uint8),
        ('saveMode', ct.c_int),
        ('fileName', ct.c_char * MAX_LISTFILE_LENGTH),
        ('maxBuffNumEvents', ct.c_uint32),
        ('saveMask', ct.c_uint32),
        ('enableFakes', ct.c_uint8),
    ]


@unique
class ListSaveMode(IntEnum):
    """
    Binding of ::CAENDPP_ListSaveMode_t
    """
    MEMORY = 0
    FILE_BINARY = 1
    FILE_ASCII = 2


@unique
class DumpMask(IntFlag):
    """
    Binding of ::DUMP_MASK_*
    """
    TTT = 0x1
    ENERGY = 0x2
    EXTRAS = 0x4
    ENERGY_SHORT = 0x8
    ALL_ = TTT | ENERGY | EXTRAS | ENERGY_SHORT


@dataclass(**_utils.dataclass_slots)
class ListParams:
    """
    Binding of ::CAENDPP_ListParams_t
    """
    enabled: bool = field(default=False)
    save_mode: ListSaveMode = field(default=ListSaveMode.MEMORY)
    file_name: str = field(default='dummy.txt')
    max_buff_num_events: int = field(default=0)
    save_mask: DumpMask = field(default=DumpMask.TTT | DumpMask.ENERGY | DumpMask.EXTRAS)
    enable_fakes: bool = field(default=False)

    @classmethod
    def from_raw(cls, raw: _ListParamsRaw):
        """Instantiate from raw data"""
        return cls(
            bool(raw.enabled),
            ListSaveMode(raw.saveMode),
            raw.fileName.decode('ascii'),
            raw.maxBuffNumEvents,
            DumpMask(raw.saveMask),
            bool(raw.enableFakes),
        )

    def to_raw(self) -> _ListParamsRaw:
        """Convert to raw data"""
        return _ListParamsRaw(
            self.enabled,
            self.save_mode,
            self.file_name.encode('ascii'),
            self.max_buff_num_events,
            self.save_mask,
            self.enable_fakes,
        )


class _RunSpecsRaw(ct.Structure):
    _fields_ = [
        ('RunName', ct.c_char * MAX_RUNNAME),
        ('RunDurationSec', ct.c_int32),
        ('PauseSec', ct.c_int32),
        ('CyclesCount', ct.c_int32),
        ('SaveLists', ct.c_uint8),
        ('GPSEnable', ct.c_uint8),
        ('ClearHistos', ct.c_uint8),
    ]


@dataclass(**_utils.dataclass_slots)
class RunSpecs:
    """
    Binding of ::CAENDPP_RunSpecs_t
    """
    run_name: str = field(default='dummy')
    run_duration_sec: int = field(default=0)
    pause_sec: int = field(default=0)
    cycles_count: int = field(default=1)
    save_lists: bool = field(default=False)
    gps_enable: bool = field(default=False)
    clear_histos: bool = field(default=False)

    @classmethod
    def from_raw(cls, raw: _RunSpecsRaw):
        """Instantiate from raw data"""
        return cls(
            raw.RunName.decode('ascii'),
            raw.RunDurationSec,
            raw.PauseSec,
            raw.CyclesCount,
            bool(raw.SaveLists),
            bool(raw.GPSEnable),
            bool(raw.ClearHistos),
        )

    def to_raw(self) -> _RunSpecsRaw:
        """Convert to raw data"""
        return _RunSpecsRaw(
            self.run_name.encode('ascii'),
            self.run_duration_sec,
            self.pause_sec,
            self.cycles_count,
            self.save_lists,
            self.gps_enable,
            self.clear_histos,
        )


class _CoincParamsRaw(ct.Structure):
    _fields_ = [
        ('CoincChMask', ct.c_uint32),
        ('MajLevel', ct.c_uint32),
        ('TrgWin', ct.c_uint32),
        ('CoincOp', ct.c_int),
        ('CoincLogic', ct.c_int),
    ]


@unique
class CoincOp(IntEnum):
    """
    Binding of ::CAENDPP_CoincOp_t
    """
    OR = 0
    AND = 1
    MAJ = 2


@unique
class CoincLogic(IntEnum):
    """
    Binding of ::CAENDPP_CoincLogic_t
    """
    NONE = 0
    COINCIDENCE = 2
    ANTICOINCIDENCE = 3


@dataclass(**_utils.dataclass_slots)
class CoincParams:
    """
    Binding of ::CAENDPP_CoincParams_t
    """
    coinc_ch_mask: int = field(default=0)
    maj_level: int = field(default=0)
    trg_win: int = field(default=0)
    coinc_op: CoincOp = field(default=CoincOp.OR)
    coinc_logic: CoincLogic = field(default=CoincLogic.NONE)

    @classmethod
    def from_raw(cls, raw: _CoincParamsRaw):
        """Instantiate from raw data"""
        return cls(
            raw.CoincChMask,
            raw.MajLevel,
            raw.TrgWin,
            CoincOp(raw.CoincOp),
            CoincLogic(raw.CoincLogic),
        )

    def to_raw(self) -> _CoincParamsRaw:
        """Convert to raw data"""
        return _CoincParamsRaw(
            self.coinc_ch_mask,
            self.maj_level,
            self.trg_win,
            self.coinc_op,
            self.coinc_logic,
        )


class _GateParamsRaw(ct.Structure):
    _fields_ = [
        ('GateEnable', ct.c_uint32),
        ('ShapeTime', ct.c_uint32),
        ('Polarity', ct.c_int),
        ('GateLogic', ct.c_int),
    ]


@unique
class PulsePolarity(IntEnum):
    """
    Binding of ::CAENDPP_PulsePolarity_t
    """
    POSITIVE = 0
    NEGATIVE = 1


@unique
class ExtLogic(IntEnum):
    """
    Binding of ::CAENDPP_ExtLogic_t
    """
    VETO = 0
    GATE = 1


@dataclass(**_utils.dataclass_slots)
class GateParams:
    """
    Binding of ::CAENDPP_GateParams_t
    """
    gate_enable: bool = field(default=False)
    shape_time: int = field(default=0)
    polarity: PulsePolarity = field(default=PulsePolarity.POSITIVE)
    gate_logic: ExtLogic = field(default=ExtLogic.VETO)

    @classmethod
    def from_raw(cls, raw: _GateParamsRaw):
        """Instantiate from raw data"""
        return cls(
            bool(raw.GateEnable),
            raw.ShapeTime,
            PulsePolarity(raw.Polarity),
            ExtLogic(raw.GateLogic),
        )

    def to_raw(self) -> _GateParamsRaw:
        """Convert to raw data"""
        return _GateParamsRaw(
            self.gate_enable,
            self.shape_time,
            self.polarity,
            self.gate_logic,
        )


class _SpectrumControlRaw(ct.Structure):
    _fields_ = [
        ('SpectrumMode', ct.c_int),
        ('TimeScale', ct.c_uint32),
    ]


class SpectrumMode(IntEnum):
    """
    Binding of ::CAENDPP_SpectrumMode_t
    """
    ENERGY = 0
    TIME = 1


@dataclass(**_utils.dataclass_slots)
class SpectrumControl:
    """
    Binding of ::CAENDPP_SpectrumControl
    """
    spectrum_mode: SpectrumMode = field(default=SpectrumMode.ENERGY)
    time_scale: int = field(default=0)

    @classmethod
    def from_raw(cls, raw: _SpectrumControlRaw):
        """Instantiate from raw data"""
        return cls(SpectrumMode(raw.SpectrumMode), raw.TimeScale)

    def to_raw(self) -> _SpectrumControlRaw:
        """Convert to raw data"""
        return _SpectrumControlRaw(self.spectrum_mode, self.time_scale)


class _TRResetRaw(ct.Structure):
    _fields_ = [
        ('Enabled', ct.c_uint32),
        ('ResetDetectionMode', ct.c_int),
        ('thrhold', ct.c_uint32),
        ('reslenmin', ct.c_uint32),
        ('reslength', ct.c_uint32),
    ]


@unique
class ResetDetectionMode(IntEnum):
    """
    Binding of ::CAENDPP_ResetDetectionMode_t
    """
    INTERNAL = 0
    GPIO = 1
    BOTH = 2


@dataclass(**_utils.dataclass_slots)
class TRReset:
    """
    Binding of ::CAENDPP_TRReset
    """
    enabled: bool = field(default=False)
    reset_detection_mode: ResetDetectionMode = field(default=ResetDetectionMode.INTERNAL)
    thrhold: int = field(default=0)
    reslenmin: int = field(default=0)
    reslength: int = field(default=0)

    @classmethod
    def from_raw(cls, raw: _TRResetRaw):
        """Instantiate from raw data"""
        return cls(
            bool(raw.Enabled),
            ResetDetectionMode(raw.ResetDetectionMode),
            raw.thrhold,
            raw.reslenmin,
            raw.reslength
        )

    def to_raw(self) -> _TRResetRaw:
        """Convert to raw data"""
        return _TRResetRaw(
            self.enabled,
            self.reset_detection_mode,
            self.thrhold,
            self.reslenmin,
            self.reslength
        )


class _MonOutParamsRaw(ct.Structure):
    _fields_ = [
        ('channel', ct.c_int32),
        ('enabled', ct.c_int32),
        ('probe', ct.c_int),
    ]


@dataclass(frozen=True, **_utils.dataclass_slots)
class MonOutParams:
    """
    Binding of ::CAENDPP_MonOutParams_t
    """
    channel: int = field(default=0)
    enabled: bool = field(default=False)
    probe: PHAMonOutProbe = field(default=PHAMonOutProbe.INPUT)

    @classmethod
    def from_raw(cls, raw: _MonOutParamsRaw):
        """Instantiate from raw data"""
        return cls(raw.channel, bool(raw.enabled), PHAMonOutProbe(raw.probe))

    def to_raw(self) -> _MonOutParamsRaw:
        """Convert to raw data"""
        return _MonOutParamsRaw(self.channel, self.enabled, self.probe)


class _DgtzParamsRaw(ct.Structure):
    _fields_ = [
        ('GWn', ct.c_int32),
        ('GWaddr', ct.c_uint32 * MAX_GW),
        ('GWdata', ct.c_uint32 * MAX_GW),
        ('GWmask', ct.c_uint32 * MAX_GW),
        ('ChannelMask', ct.c_int32),
        ('PulsePolarity', ct.c_int * MAX_NUMCHB),
        ('DCoffset', ct.c_int32 * MAX_NUMCHB),
        ('TempCorrParameters', _TempCorrParamsRaw * MAX_NUMCHB),
        ('InputCoupling', ct.c_int * MAX_NUMCHB),
        ('EventAggr', ct.c_int32),
        ('DPPParams', _PHAParamsRaw),
        ('IOlev', ct.c_int),
        ('WFParams', _WaveformParamsRaw),
        ('ListParams', _ListParamsRaw),
        ('RunSpecifications', _RunSpecsRaw),
        ('CoincParams', _CoincParamsRaw * MAX_NUMCHB_COINCIDENCE),
        ('GateParams', _GateParamsRaw * MAX_NUMCHB),
        ('SpectrumControl', _SpectrumControlRaw * MAX_NUMCHB),
        ('ResetDetector', _TRResetRaw * MAX_NUMCHB),
        ('MonOutParams', _MonOutParamsRaw),
    ]


@unique
class INCoupling(IntEnum):
    """
    Binding of ::CAENDPP_INCoupling_t
    """
    DC = 0
    AC_5US = 1
    AC_11US = 2
    AC_33US = 3


@unique
class IOLevel(IntEnum):
    """
    Binding of ::CAENDPP_IOLevel_t
    """
    NIM = 0
    TTL = 1


@dataclass(**_utils.dataclass_slots)
class DgtzParams:
    """
    Binding of ::CAENDPP_DgtzParams_t
    """
    gw_addr: list[int] = field(default_factory=list)
    gw_data: list[int] = field(default_factory=list)
    gw_mask: list[int] = field(default_factory=list)
    channel_mask: int = field(default=0)
    pulse_polarity: list[PulsePolarity] = field(default_factory=list)
    dc_offset: list[int] = field(default_factory=list)
    temp_corr_parameters: list[TempCorrParams] = field(default_factory=list)
    input_coupling: list[INCoupling] = field(default_factory=list)
    event_aggr: int = field(default=0)
    dpp_params: PHAParams = field(default_factory=PHAParams)
    iolev: IOLevel = field(default=IOLevel.NIM)
    wf_params: WaveformParams = field(default_factory=WaveformParams)
    list_params: ListParams = field(default_factory=ListParams)
    run_specifications: RunSpecs = field(default_factory=RunSpecs)
    coinc_params: list[CoincParams] = field(default_factory=list)
    gate_params: list[GateParams] = field(default_factory=list)
    spectrum_control: list[SpectrumControl] = field(default_factory=list)
    reset_detector: list[TRReset] = field(default_factory=list)
    mon_out_params: MonOutParams = field(default_factory=MonOutParams)

    def resize(self, n_channels: int):
        """Resize to n_channels"""
        self.pulse_polarity = [PulsePolarity.POSITIVE] * n_channels
        self.dc_offset = [0] * n_channels
        self.temp_corr_parameters = [TempCorrParams() for _ in range(n_channels)]
        self.input_coupling = [INCoupling.DC] * n_channels
        self.dpp_params.resize(n_channels)
        self.coinc_params = [CoincParams() for _ in range(n_channels)]
        self.gate_params = [GateParams() for _ in range(n_channels)]
        self.spectrum_control = [SpectrumControl() for _ in range(n_channels)]
        self.reset_detector = [TRReset() for _ in range(n_channels)]

    @classmethod
    def from_raw(cls, raw: _DgtzParamsRaw):
        """Instantiate from raw data"""
        return cls(
            raw.GWaddr[:raw.GWn],
            raw.GWdata[:raw.GWn],
            raw.GWmask[:raw.GWn],
            raw.ChannelMask,
            [PulsePolarity(i) for i in raw.PulsePolarity],
            raw.DCoffset,
            [TempCorrParams.from_raw(i) for i in raw.TempCorrParameters],
            [INCoupling(i) for i in raw.InputCoupling],
            raw.EventAggr,
            PHAParams.from_raw(raw.DPPParams),
            IOLevel(raw.IOlev),
            WaveformParams.from_raw(raw.WFParams),
            ListParams.from_raw(raw.ListParams),
            RunSpecs.from_raw(raw.RunSpecifications),
            [CoincParams.from_raw(i) for i in raw.CoincParams],
            [GateParams.from_raw(i) for i in raw.GateParams],
            [SpectrumControl.from_raw(i) for i in raw.SpectrumControl],
            [TRReset.from_raw(i) for i in raw.ResetDetector],
            MonOutParams.from_raw(raw.MonOutParams),
        )

    def to_raw(self) -> _DgtzParamsRaw:
        """Convert to raw data"""
        return _DgtzParamsRaw(
            len(self.gw_addr),
            tuple(self.gw_addr),
            tuple(self.gw_data),
            tuple(self.gw_mask),
            self.channel_mask,
            tuple(self.pulse_polarity),
            tuple(self.dc_offset),
            tuple(i.to_raw() for i in self.temp_corr_parameters),
            tuple(self.input_coupling),
            self.event_aggr,
            self.dpp_params.to_raw(),
            self.iolev,
            self.wf_params.to_raw(),
            self.list_params.to_raw(),
            self.run_specifications.to_raw(),
            tuple(i.to_raw() for i in self.coinc_params),
            tuple(i.to_raw() for i in self.gate_params),
            tuple(i.to_raw() for i in self.spectrum_control),
            tuple(i.to_raw() for i in self.reset_detector),
            self.mon_out_params.to_raw(),
        )


class _ListEventRaw(ct.Structure):
    _fields_ = [
        ('TimeTag', ct.c_uint64),
        ('Energy', ct.c_uint16),
        ('Extras', ct.c_uint16),
    ]


@dataclass(frozen=True, **_utils.dataclass_slots)
class ListEvent:
    """
    Binding of ::CAENDPP_ListEvent_t
    """
    time_tag: int
    energy: int
    extras: int

    @classmethod
    def from_raw(cls, raw: _ListEventRaw):
        """Instantiate from raw data"""
        return cls(raw.TimeTag, raw.Energy, raw.Extras)


class _StatisticsRaw(ct.Structure):
    _fields_ = [
        ('ThroughputRate', ct.c_double),
        ('SaturationFlag', ct.c_uint32),
        ('SaturationPerc', ct.c_double),
        ('PulseDeadTime', ct.c_double),
        ('RealRate', ct.c_double),
        ('PeakingTime', ct.c_uint32),
    ]


@dataclass(frozen=True, **_utils.dataclass_slots)
class Statistics:
    """
    Binding of ::statistics_t
    """
    throughput_rate: float
    saturation_flag: int
    saturation_perc: float
    pulse_dead_time: float
    real_rate: float
    peaking_time: int

    @classmethod
    def from_raw(cls, raw: _StatisticsRaw):
        """Instantiate from raw data"""
        return cls(
            raw.ThroughputRate,
            raw.SaturationFlag,
            raw.SaturationPerc,
            raw.PulseDeadTime,
            raw.RealRate,
            raw.PeakingTime,
        )


class _DAQInfoRaw(ct.Structure):
    _fields_ = [
        ('ACQStatus', ct.c_int),
        ('RunLoop', ct.c_int32),
        ('RunState', ct.c_int),
        ('RunElapsedTimeSec', ct.c_int64),
        ('TotEvtCount', ct.c_int32),
        ('DeadTimeNs', ct.c_int64),
        ('GainStatus', ct.c_int),
        ('RunID', ct.c_int32),
    ]


@unique
class RunState(IntEnum):
    """
    Binding of ::CAENDPP_RunState_t
    """
    STOP = 0
    START = 1
    PAUSE = 2


@unique
class GainStabilizationStatus(IntEnum):
    """
    Binding of ::CAENDPP_GainStabilizationStatus_t
    """
    OFF = 0
    SEARCHING = 1
    FOUND = 2
    LOST = 3
    FOLLOWING = 4


@dataclass(frozen=True, **_utils.dataclass_slots)
class DAQInfo:
    """
    Binding of ::CAENDPP_DAQInfo_t
    """
    acq_status: RunState
    run_loop: int
    run_state: RunState
    run_elapsed_time_sec: int
    tot_evt_count: int
    dead_time_ns: int
    gain_status: GainStabilizationStatus
    run_id: int

    @classmethod
    def from_raw(cls, raw: _DAQInfoRaw):
        """Instantiate from raw data"""
        return cls(
            RunState(raw.ACQStatus),
            raw.RunLoop,
            RunState(raw.RunState),
            raw.RunElapsedTimeSec,
            raw.TotEvtCount,
            raw.DeadTimeNs,
            GainStabilizationStatus(raw.GainStatus),
            raw.RunID,
        )


class _HVChannelConfigRaw(ct.Structure):
    _fields_ = [
        ('VSet', ct.c_double),
        ('ISet', ct.c_double),
        ('RampUp', ct.c_double),
        ('RampDown', ct.c_double),
        ('VMax', ct.c_double),
        ('PWDownMode', ct.c_int),
    ]


@unique
class PWDownMode(IntEnum):
    """
    Binding of ::CAENDPP_PWDownMode_t
    """
    RAMP = 0
    KILL = 1


@dataclass(**_utils.dataclass_slots)
class HVChannelConfig:
    """
    Binding of ::CAENDPP_HVChannelConfig_t
    """
    v_set: float
    i_set: float
    ramp_up: float
    ramp_down: float
    v_max: float
    pw_down_mode: PWDownMode

    @classmethod
    def from_raw(cls, raw: _HVChannelConfigRaw):
        """Instantiate from raw data"""
        return cls(
            raw.VSet,
            raw.ISet,
            raw.RampUp,
            raw.RampDown,
            raw.VMax,
            PWDownMode(raw.PWDownMode),
        )

    def to_raw(self) -> _HVChannelConfigRaw:
        """Convert to raw data"""
        return _HVChannelConfigRaw(
            self.v_set,
            self.i_set,
            self.ramp_up,
            self.ramp_down,
            self.v_max,
            self.pw_down_mode,
        )


@dataclass(frozen=True, **_utils.dataclass_slots)
class HVChannelMonitoring:
    """
    Return value for ::CAENDPP_ReadHVChannelMonitoring binding
    """
    v_mon: float
    i_mon: float


@dataclass(frozen=True, **_utils.dataclass_slots)
class HVChannelExternals:
    """
    Return value for ::CAENDPP_ReadHVChannelExternals binding
    """
    v_ext: float
    t_res: float


class _EnumerationSingleDeviceRaw(ct.Structure):
    _fields_ = [
        ('id', ct.c_uint32),
        ('ConnectionMode', ct.c_int),
        ('SerialNUMBER', ct.c_char * 128),
        ('ProductDescription', ct.c_char * 256),
        ('ETHAddress', ct.c_char * 256),
        ('TCPPORT', ct.c_uint16),
        ('UDPPORT', ct.c_uint16),
        ('cStatus', ct.c_int),
    ]


@unique
class COMStatus(IntEnum):
    """
    Binding of ::CAENDPP_COMStatus_t
    """
    ONLINE = 0
    NOT_AVAILABLE = 1
    ERROR = 2
    BOOT_LOADER = 3


@dataclass(frozen=True, **_utils.dataclass_slots)
class EnumerationSingleDevice:
    """
    Binding of ::CAENDPP_EnumerationSingleDevice_t
    """
    id: int
    connection_mode: ConnectionType
    serial_number: str
    product_description: str
    eth_address: str
    tcp_port: int
    udp_port: int
    com_status: COMStatus

    @classmethod
    def from_raw(cls, raw: _EnumerationSingleDeviceRaw):
        """Instantiate from raw data"""
        return cls(
            raw.id,
            ConnectionType(raw.ConnectionMode),
            raw.SerialNUMBER.decode('ascii'),
            raw.ProductDescription.decode('ascii'),
            raw.ETHAddress.decode('ascii'),
            raw.TCPPORT,
            raw.UDPPORT,
            COMStatus(raw.cStatus),
        )


class _EnumeratedDevicesRaw(ct.Structure):
    _fields_ = [
        ('ddcount', ct.c_int),
        ('Device', _EnumerationSingleDeviceRaw * 64),
    ]


@dataclass(frozen=True, **_utils.dataclass_slots)
class EnumeratedDevices:
    """
    Binding of ::CAENDPP_EnumeratedDevices_t
    """
    devices: tuple[EnumerationSingleDevice, ...]

    @classmethod
    def from_raw(cls, raw: _EnumeratedDevicesRaw):
        """Instantiate from raw data"""
        return cls(
            tuple(map(EnumerationSingleDevice.from_raw, raw.Device[:raw.ddcount])),
        )


class LogMask(IntFlag):
    """
    Binding of ::DPPLIB_LOGMASK_*
    """
    NONE = 0x0
    INFO = 0x1
    ERROR = 0x2
    WARNING = 0x4
    DEBUG = 0x8
    ALL = INFO | ERROR | WARNING | DEBUG


@unique
class GuessConfigStatus(IntEnum):
    """
    Binding of ::CAENDPP_GuessConfigStatus_t
    """
    NOT_RUNNING = 0
    STARTED = 1
    PULSE_POLARITY = 2
    DC_OFFSET = 3
    SIGNAL_RISE = 4
    THRESHOLD = 5
    DECAY_TIME = 6
    TRAPEZOID = 7
    BASELINE = 8
    READY = 9


@unique
class AcqMode(IntEnum):
    """
    Binding of ::CAENDPP_AcqMode_t
    """
    WAVEFORM = 0
    HISTOGRAM = 1


@unique
class AcqStatus(IntEnum):
    """
    Binding of ::CAENDPP_AcqStatus_t
    """
    STOPPED = 0
    RUNNING = 1
    ARMED = 2
    UNKNOWN = 3


@unique
class MultiHistoCondition(IntEnum):
    """
    Binding of ::CAENDPP_MultiHistoCondition_t
    """
    SOFTWARE_ONLY = 1
    TIMESTAMP_RESET = 2


@unique
class StopCriteria(IntEnum):
    """
    Binding of ::CAENDPP_StopCriteria_t
    """
    MANUAL = 0
    LIVE_TIME = 1
    REAL_TIME = 2
    COUNTS = 3


@dataclass(**_utils.dataclass_slots)
class Waveforms:
    """
    Class to store waveforms data.
    """
    samples: int
    at1: npt.NDArray[np.int16] = field(init=False)
    at2: npt.NDArray[np.int16] = field(init=False)
    dt1: npt.NDArray[np.uint8] = field(init=False)
    dt2: npt.NDArray[np.uint8] = field(init=False)

    def __post_init__(self):
        self.at1 = np.empty(self.samples, dtype=np.int16)
        self.at2 = np.empty(self.samples, dtype=np.int16)
        self.dt1 = np.empty(self.samples, dtype=np.uint8)
        self.dt2 = np.empty(self.samples, dtype=np.uint8)


@dataclass(**_utils.dataclass_slots)
class Histogram:
    """
    Class to store histogram data.
    """
    histo: npt.NDArray[np.uint32]
    counts: int
    realtime: int
    deadtime: int


@unique
class ParamID(IntEnum):
    """
    Binding of ::CAENDPP_ParamID_t
    """
    RECORD_LENGTH = 0
    PRE_TRIGGER = 1
    DECAY = 2
    TRAP_RISE = 3
    TRAP_FLAT = 4
    TRAP_FLAT_DELAY = 5
    SMOOTHING = 6
    INPUT_RISE = 7
    THRESHOLD = 8
    NSBL = 9
    NSPK = 10
    PKHO = 11
    BLHO = 12
    TRGHO = 13
    DGAIN = 14
    ENF = 15
    DECIMATION = 16
    TWWDT = 17
    TRGWIN = 18
    PULSE_POL = 19
    DC_OFFSET = 20
    IOLEV = 21
    TRGAIN = 22


class Error(error.Error):
    """
    Raised when a wrapped C API function returns negative values.
    """

    @unique
    class Code(IntEnum):
        """
        Binding of ::CAENDPP_RetCode_t
        """
        OK = 0
        GENERIC_ERROR = -100
        TOO_MANY_INSTANCES = -101
        PROCESS_FAIL = -102
        READ_FAIL = -103
        WRITE_FAIL = -104
        BAD_MESSAGE = -105
        INVALID_HANDLE = -106
        CONFIG_ERROR = -107
        BOARD_INIT_FAIL = -108
        TIMEOUT_ERROR = -109
        INVALID_PARAMETER = -110
        NOT_IN_WAVE_MODE = -111
        NOT_IN_HISTO_MODE = -112
        NOT_IN_LIST_MODE = -113
        NOT_YET_IMPLEMENTED = -114
        BOARD_NOT_CONFIGURED = -115
        INVALID_BOARD_INDEX = -116
        INVALID_CHANNEL_INDEX = -117
        UNSUPPORTED_FIRMWARE = -118
        NO_BOARDS_ADDED = -119
        ACQUISITION_RUNNING = -120
        OUT_OF_MEMORY = -121
        BOARD_CHANNEL_INDEX = -122
        HISTO_ALLOC = -123
        OPEN_DUMPER = -124
        BOARD_START = -125
        CHANNEL_ENABLE = -126
        INVALID_COMMAND = -127
        NUM_BINS = -128
        HISTO_INDEX = -129
        UNSUPPORTED_FEATURE = -130
        BAD_HISTO_STATE = -131
        NO_MORE_HISTOGRAMS = -132
        NOT_HV_BOARD = -133
        INVALID_HV_CHANNEL = -134
        SOCKET_SEND = -135
        SOCKET_RECEIVE = -136
        BOARD_THREAD = -137
        DECODE_WAVEFORM = -138
        OPEN_DIGITIZER = -139
        BOARD_MODEL = -140
        AUTOSET_STATUS = -141
        AUTOSET = -142
        CALIBRATION = -143
        EVENT_READ = -144

    code: Code

    def __init__(self, message: str, res: int, func: str) -> None:
        self.code = Error.Code(res)
        super().__init__(message, self.code.name, func)


# For backward compatibility. Deprecated.
ErrorCode = Error.Code


# Utility definitions
_c_int_p = ct.POINTER(ct.c_int)
_c_int16_p = ct.POINTER(ct.c_int16)
_c_int32_p = ct.POINTER(ct.c_int32)
_c_uint8_p = ct.POINTER(ct.c_uint8)
_c_uint16_p = ct.POINTER(ct.c_uint16)
_c_uint32_p = ct.POINTER(ct.c_uint32)
_c_uint64_p = ct.POINTER(ct.c_uint64)
_c_double_p = ct.POINTER(ct.c_double)
_connection_params_p = ct.POINTER(_ConnectionParamsRaw)
_info_p = ct.POINTER(_InfoRaw)
_dgtz_params_p = ct.POINTER(_DgtzParamsRaw)
_list_event_p = ct.POINTER(_ListEventRaw)
_statistics_p = ct.POINTER(_StatisticsRaw)
_param_info_p = ct.POINTER(_ParamInfoRaw)
_daq_info_p = ct.POINTER(_DAQInfoRaw)
_hv_channel_config_p = ct.POINTER(_HVChannelConfigRaw)
_enumerated_devices_p = ct.POINTER(_EnumeratedDevicesRaw)


def _default_log_file_path() -> Path:
    """Generate file log path"""
    # Platform dependent stuff
    if sys.platform == 'win32':
        app_data = os.getenv('LOCALAPPDATA')
        assert app_data is not None
        user_path = Path(app_data) / 'CAEN'
    else:
        home = os.getenv('HOME')
        assert home is not None
        user_path = Path(home) / '.CAEN'
    os.makedirs(user_path, exist_ok=True)
    return user_path / 'caendpplib-python.log'


class _Lib(_utils.Lib):

    def __init__(self, name: str) -> None:
        self.__log_path = _default_log_file_path()
        env = {'CAEN_LOG_FILENAME': str(self.__log_path)}  # Used by CAEN Utility to set the log file name
        super().__init__(name, False, env)
        self.__load_api()

    def __load_api(self) -> None:
        # Load API not related to devices
        self.attach_boards = self.__get('AttachBoards', ct.c_char_p, ct.c_uint16, _c_int32_p, _c_int32_p, _c_int32_p)

        # Load API
        self.init_library = self.__get('InitLibrary', _c_int32_p, ct.c_int32)
        self.end_library = self.__get('EndLibrary', ct.c_int32)
        self.add_board = self.__get('AddBoard', ct.c_int32, _connection_params_p, _c_int32_p)
        self.get_dpp_info = self.__get('GetDPPInfo', ct.c_int32, ct.c_int32, _info_p)
        self.start_board_parameters_guess = self.__get('StartBoardParametersGuess', ct.c_int32, ct.c_int32, ct.c_uint32, _dgtz_params_p)
        self.get_board_parameters_guess_status = self.__get('GetBoardParametersGuessStatus', ct.c_int32, ct.c_int32, _c_int_p)
        self.get_board_parameters_guess_result = self.__get('GetBoardParametersGuessResult', ct.c_int32, ct.c_int32, _dgtz_params_p, _c_uint32_p)
        self.stop_board_parameters_guess = self.__get('StopBoardParametersGuess', ct.c_int32, ct.c_int32)
        self.set_board_configuration = self.__get('SetBoardConfiguration', ct.c_int32, ct.c_int32, ct.c_int, _DgtzParamsRaw)
        self.get_board_configuration = self.__get('GetBoardConfiguration', ct.c_int32, ct.c_int32, _c_int_p, _dgtz_params_p)
        self.is_channel_enabled = self.__get('IsChannelEnabled', ct.c_int32, ct.c_int32, _c_int32_p)
        self.is_channel_acquiring = self.__get('IsChannelAcquiring', ct.c_int32, ct.c_int32, _c_int_p)
        self.start_acquisition = self.__get('StartAcquisition', ct.c_int32, ct.c_int32)
        self.arm_acquisition = self.__get('ArmAcquisition', ct.c_int32, ct.c_int32)
        self.stop_acquisition = self.__get('StopAcquisition', ct.c_int32, ct.c_int32)
        self.is_board_acquiring = self.__get('IsBoardAcquiring', ct.c_int32, ct.c_int32, _c_int32_p)
        self.set_histo_switch_mode = self.__get('SetHistoSwitchMode', ct.c_int32, ct.c_int)
        self.get_histo_switch_mode = self.__get('GetHistoSwitchMode', ct.c_int32, _c_int_p)
        self.set_stop_criteria = self.__get('SetStopCriteria', ct.c_int32, ct.c_int32, ct.c_int, ct.c_uint64)
        self.get_stop_criteria = self.__get('GetStopCriteria', ct.c_int32, ct.c_int32, _c_int_p, _c_uint64_p)
        self.get_total_number_of_histograms = self.__get('GetTotalNumberOfHistograms', ct.c_int32, ct.c_int32, _c_int32_p)
        self.get_number_of_completed_histograms = self.__get('GetNumberOfCompletedHistograms', ct.c_int32, ct.c_int32, _c_int32_p)
        self.get_list_events = self.__get('GetListEvents', ct.c_int32, ct.c_int32, _list_event_p, _c_uint32_p)
        self.get_waveform = self.__get('GetWaveform', ct.c_int32, ct.c_int32, ct.c_int16, _c_int16_p, _c_int16_p, _c_uint8_p, _c_uint8_p, _c_uint32_p, _c_double_p)
        self.get_histogram = self.__get('GetHistogram', ct.c_int32, ct.c_int32, ct.c_int32, ct.c_void_p, _c_uint32_p, _c_uint64_p, _c_uint64_p)
        self.set_histogram = self.__get('SetHistogram', ct.c_int32, ct.c_int32, ct.c_int32, ct.c_uint64, ct.c_uint64, ct.c_uint32, _c_uint32_p)
        self.get_current_histogram = self.__get('GetCurrentHistogram', ct.c_int32, ct.c_int32, ct.c_void_p, _c_uint32_p, _c_uint64_p, _c_uint64_p, _c_int_p)
        self.save_histogram = self.__get('SaveHistogram', ct.c_int32, ct.c_int32, ct.c_int32, ct.c_char_p)
        self.load_histogram = self.__get('LoadHistogram', ct.c_int32, ct.c_int32, ct.c_int32, ct.c_char_p)
        self.clear_histogram = self.__get('ClearHistogram', ct.c_int32, ct.c_int32, ct.c_int32)
        self.clear_current_histogram = self.__get('ClearCurrentHistogram', ct.c_int32, ct.c_int32)
        self.clear_all_histograms = self.__get('ClearAllHistograms', ct.c_int32, ct.c_int32)
        self.reset_histogram = self.__get('ResetHistogram', ct.c_int32, ct.c_int32, ct.c_int32)
        self.reset_all_histograms = self.__get('ResetAllHistograms', ct.c_int32, ct.c_int32)
        self.force_new_histogram = self.__get('ForceNewHistogram', ct.c_int32, ct.c_int32)
        self.set_histogram_size = self.__get('SetHistogramSize', ct.c_int32, ct.c_int32, ct.c_int32, ct.c_int32)
        self.get_histogram_size = self.__get('GetHistogramSize', ct.c_int32, ct.c_int32, ct.c_int32, _c_int32_p)
        self.add_histogram = self.__get('AddHistogram', ct.c_int32, ct.c_int32, ct.c_int32)
        self.set_current_histogram_index = self.__get('SetCurrentHistogramIndex', ct.c_int32, ct.c_int32, ct.c_int32)
        self.get_current_histogram_index = self.__get('GetCurrentHistogramIndex', ct.c_int32, ct.c_int32, _c_int32_p)
        self.set_histogram_status = self.__get('SetHistogramStatus', ct.c_int32, ct.c_int32, ct.c_int32, ct.c_int32)
        self.get_histogram_status = self.__get('GetHistogramStatus', ct.c_int32, ct.c_int32, ct.c_int32, _c_int32_p)
        self.set_histogram_range = self.__get('SetHistogramRange', ct.c_int32, ct.c_int32, ct.c_int32, ct.c_int32)
        self.get_histogram_range = self.__get('GetHistogramRange', ct.c_int32, ct.c_int32, _c_int32_p, _c_int32_p)
        self.get_acq_stats = self.__get('GetAcqStats', ct.c_int32, ct.c_int32, _statistics_p)
        self.set_input_range = self.__get('SetInputRange', ct.c_int32, ct.c_int32, ct.c_int)
        self.get_input_range = self.__get('GetInputRange', ct.c_int32, ct.c_int32, _c_int_p)
        self.get_waveform_length = self.__get('GetWaveformLength', ct.c_int32, ct.c_int32, _c_uint32_p)
        self.check_board_communication = self.__get('CheckBoardCommunication', ct.c_int32, ct.c_int32)
        self.get_parameter_info = self.__get('GetParameterInfo', ct.c_int32, ct.c_int32, ct.c_int, _param_info_p)
        self.board_adc_calibration = self.__get('BoardADCCalibration', ct.c_int32, ct.c_int32)
        self.get_channel_temperature = self.__get('GetChannelTemperature', ct.c_int32, ct.c_int32, _c_double_p)
        self.get_daq_info = self.__get('GetDAQInfo', ct.c_int32, ct.c_int32, _daq_info_p)
        self.reset_configuration = self.__get('ResetConfiguration', ct.c_int32, ct.c_int32)
        self.set_hv_channel_configuration = self.__get('SetHVChannelConfiguration', ct.c_int32, ct.c_int32, ct.c_int, _HVChannelConfigRaw)
        self.get_hv_channel_configuration = self.__get('GetHVChannelConfiguration', ct.c_int32, ct.c_int32, ct.c_int, _hv_channel_config_p)
        self.set_hv_channel_vmax = self.__get('SetHVChannelVMax', ct.c_int32, ct.c_int32, ct.c_int, ct.c_double)
        self.get_hv_channel_status = self.__get('GetHVChannelStatus', ct.c_int32, ct.c_int32, ct.c_int, _c_uint16_p)
        self.set_hv_channel_power_on = self.__get('SetHVChannelPowerOn', ct.c_int32, ct.c_int32, ct.c_int32, ct.c_int32)
        self.get_hv_channel_power_on = self.__get('GetHVChannelPowerOn', ct.c_int32, ct.c_int32, ct.c_int32, _c_uint32_p)
        self.read_hv_channel_monitoring = self.__get('ReadHVChannelMonitoring', ct.c_int32, ct.c_int32, ct.c_int32, _c_double_p, _c_double_p)
        self.read_hv_channel_externals = self.__get('ReadHVChannelExternals', ct.c_int32, ct.c_int32, ct.c_int32, _c_double_p, _c_double_p)
        self.enumerate_devices = self.__get('EnumerateDevices', ct.c_int32, _enumerated_devices_p)
        self.get_hv_status_string = self.__get('GetHVStatusString', ct.c_int32, ct.c_int32, ct.c_uint16, ct.c_char_p)
        self.set_hv_range = self.__get('SetHVRange', ct.c_int32, ct.c_int32, ct.c_int, ct.c_int)
        self.get_hv_range = self.__get('GetHVRange', ct.c_int32, ct.c_int32, ct.c_int, _c_int_p)
        self.set_logger_severity_mask = self.__get('SetLoggerSeverityMask', ct.c_int32, ct.c_int32)
        self.get_logger_severity_mask = self.__get('GetLoggerSeverityMask', ct.c_int32, _c_int_p)
        self.set_hv_inhibit_polarity = self.__get('SetHVInhibitPolarity', ct.c_int32, ct.c_int32, ct.c_int32, ct.c_int)
        self.get_hv_inhibit_polarity = self.__get('GetHVInhibitPolarity', ct.c_int32, ct.c_int32, ct.c_int32, _c_int_p)

    def __api_errcheck(self, res: int, func, _: tuple) -> int:
        if res < 0:
            raise Error(self.check_log_hint(), res, func.__name__)
        return res

    def __get(self, name: str, *args: type) -> Callable[..., int]:
        func = self.get(f'CAENDPP_{name}')
        func.argtypes = args
        func.restype = ct.c_int
        func.errcheck = self.__api_errcheck  # type: ignore
        return func

    # C API bindings

    def sw_release(self) -> str:
        """
        No equivalent function on CAENDPPLib
        """
        raise NotImplementedError('Not available on CAENDPPLib')

    def check_log_hint(self) -> str:
        """
        User should check log for further details.
        """
        return f'Check log at {self.log_path} for further details.'

    @property
    def log_path(self) -> Path:
        """Get log file path"""
        return self.__log_path


lib = _Lib('CAENDPPLib')


@dataclass(**_utils.dataclass_slots)
class Device:
    """
    Class representing a device.
    """

    # Public members
    handle: int
    log_severity_mask: Optional[LogMask] = field(default=None)

    # Private members
    __opened: bool = field(default=True, repr=False)

    def __del__(self) -> None:
        if self.__opened:
            self.close()

    # C API bindings

    _T = TypeVar('_T', bound='Device')

    @classmethod
    def open(cls: type[_T], log_severity_mask: LogMask = LogMask.NONE) -> _T:
        """
        Binding of CAENDPP_InitLibrary()
        """
        l_handle = ct.c_int32()
        lib.init_library(l_handle, log_severity_mask)
        return cls(l_handle.value, log_severity_mask)

    @classmethod
    def attach_boards(cls: type[_T], ip: str, port: int) -> tuple[_T, tuple[int, ...]]:
        """
        Binding of CAENDPP_AttachBoards()
        """
        l_handle = ct.c_int32()
        l_num_board = ct.c_int32()
        l_board_ids = (ct.c_int32 * 20)()
        lib.attach_boards(ip.encode('ascii'), port, l_handle, l_num_board, l_board_ids)
        device = cls(l_handle.value)
        boards_ids = tuple(l_board_ids[:l_num_board.value])
        return device, boards_ids

    def connect(self) -> None:
        """
        Binding of CAENDPP_InitLibrary()

        New instances should be created with open(). This is meant to
        reconnect a device closed with close().
        """
        if self.__opened:
            raise RuntimeError('Already connected.')
        l_handle = ct.c_int()
        lib.init_library(l_handle, self.log_severity_mask)
        self.handle = l_handle.value
        self.__opened = True

    def close(self) -> None:
        """
        Binding of CAENDPP_EndLibrary()
        """
        lib.end_library(self.handle)
        self.__opened = False

    def add_board(self, params: ConnectionParams) -> int:
        """
        Binding of CAENDPP_AddBoard()
        """
        l_params = params.to_raw()
        l_board_id = ct.c_int32()
        lib.add_board(self.handle, l_params, l_board_id)
        return l_board_id.value

    def get_dpp_info(self, board_id: int) -> Info:
        """
        Binding of CAENDPP_GetDPPInfo()
        """
        l_i = _InfoRaw()
        lib.get_dpp_info(self.handle, board_id, l_i)
        return Info.from_raw(l_i)

    def start_board_parameters_guess(self, board_id: int, channel_mask: int, params: DgtzParams):
        """
        Binding of CAENDPP_StartBoardParametersGuess()
        """
        l_params = params.to_raw()
        lib.start_board_parameters_guess(self.handle, board_id, channel_mask, l_params)

    def get_board_parameters_guess_status(self, board_id: int) -> GuessConfigStatus:
        """
        Binding of CAENDPP_GetBoardParametersGuessStatus()
        """
        l_status = ct.c_int()
        lib.get_board_parameters_guess_status(self.handle, board_id, l_status)
        return GuessConfigStatus(l_status.value)

    def get_board_parameters_guess_result(self, board_id: int) -> tuple[DgtzParams, int]:
        """
        Binding of CAENDPP_GetBoardParametersGuessResult()
        """
        l_params = _DgtzParamsRaw()
        l_channel_mask = ct.c_uint32()
        lib.get_board_parameters_guess_result(self.handle, board_id, l_params, l_channel_mask)
        return DgtzParams.from_raw(l_params), l_channel_mask.value

    def stop_board_parameters_guess(self, board_id: int) -> None:
        """
        Binding of CAENDPP_StopBoardParametersGuess()
        """
        lib.stop_board_parameters_guess(self.handle, board_id)

    def set_board_configuration(self, board_id: int, acq_mode: AcqMode, params: DgtzParams) -> None:
        """
        Binding of CAENDPP_SetBoardConfiguration()
        """
        l_params = params.to_raw()
        lib.set_board_configuration(self.handle, board_id, acq_mode, l_params)

    def get_board_configuration(self, board_id: int) -> tuple[AcqMode, DgtzParams]:
        """
        Binding of CAENDPP_GetBoardConfiguration()
        """
        l_acq_mode = ct.c_int()
        l_params = _DgtzParamsRaw()
        lib.get_board_configuration(self.handle, board_id, l_acq_mode, l_params)
        params = DgtzParams.from_raw(l_params)
        return AcqMode(l_acq_mode.value), params

    def is_channel_enabled(self, channel: int) -> bool:
        """
        Binding of CAENDPP_IsChannelEnabled()
        """
        l_enabled = ct.c_int32()
        lib.is_channel_enabled(self.handle, channel, l_enabled)
        return bool(l_enabled.value)

    def is_channel_acquiring(self, channel: int) -> AcqStatus:
        """
        Binding of CAENDPP_IsChannelAcquiring()
        """
        l_acquiring = ct.c_int()
        lib.is_channel_acquiring(self.handle, channel, l_acquiring)
        return AcqStatus(l_acquiring.value)

    def start_acquisition(self, channel: int = -1) -> None:
        """
        Binding of CAENDPP_StartAcquisition()
        """
        lib.start_acquisition(self.handle, channel)

    def arm_acquisition(self, channel: int = -1) -> None:
        """
        Binding of CAENDPP_ArmAcquisition()
        """
        lib.arm_acquisition(self.handle, channel)

    def stop_acquisition(self, channel: int = -1) -> None:
        """
        Binding of CAENDPP_StopAcquisition()
        """
        lib.stop_acquisition(self.handle, channel)

    def is_board_acquiring(self, board_id: int) -> bool:
        """
        Binding of CAENDPP_IsBoardAcquiring()
        """
        l_acquiring = ct.c_int32()
        lib.is_board_acquiring(self.handle, board_id, l_acquiring)
        return bool(l_acquiring.value)

    def set_histo_switch_mode(self, mode: MultiHistoCondition) -> None:
        """
        Binding of CAENDPP_SetHistoSwitchMode()
        """
        lib.set_histo_switch_mode(self.handle, mode)

    def get_histo_switch_mode(self) -> MultiHistoCondition:
        """
        Binding of CAENDPP_GetHistoSwitchMode()
        """
        l_mode = ct.c_int()
        lib.get_histo_switch_mode(self.handle, l_mode)
        return MultiHistoCondition(l_mode.value)

    def set_stop_criteria(self, channel: int, crit: StopCriteria, value: int) -> None:
        """
        Binding of CAENDPP_SetStopCriteria()
        """
        lib.set_stop_criteria(self.handle, channel, crit, value)

    def get_stop_criteria(self, channel: int) -> tuple[StopCriteria, int]:
        """
        Binding of CAENDPP_GetStopCriteria()
        """
        l_crit = ct.c_int()
        l_value = ct.c_uint64()
        lib.get_stop_criteria(self.handle, channel, l_crit, l_value)
        return StopCriteria(l_crit.value), l_value.value

    def get_total_number_of_histograms(self, channel: int) -> int:
        """
        Binding of CAENDPP_GetTotalNumberOfHistograms()
        """
        l_total = ct.c_int32()
        lib.get_total_number_of_histograms(self.handle, channel, l_total)
        return l_total.value

    def get_number_of_completed_histograms(self, channel: int) -> int:
        """
        Binding of CAENDPP_GetNumberOfCompletedHistograms()
        """
        l_completed = ct.c_int32()
        lib.get_number_of_completed_histograms(self.handle, channel, l_completed)
        return l_completed.value

    def get_list_events(self, channel: int) -> tuple[ListEvent]:
        """
        Binding of CAENDPP_GetListEvents()
        """
        l_events = (_ListEventRaw * 8192)()
        l_count = ct.c_uint32()
        lib.get_list_events(self.handle, channel, l_events, l_count)
        return tuple(map(ListEvent.from_raw, l_events[:l_count.value]))

    def allocate_waveform(self, channel: int) -> Waveforms:
        """
        Allocate memory for waveforms data

        This method does not bind any C API function. It is just a helper
        method to allocate memory for waveforms data to be used as
        argument for get_waveform().
        """
        l_length = self.get_waveform_length(channel)
        return Waveforms(l_length)

    def get_waveform(self, channel: int, auto: bool, waveforms: Waveforms) -> tuple[int, float]:
        """
        Binding of CAENDPP_GetWaveform()

        Waveforms data should be allocated with allocate_waveform().
        """
        l_auto = ct.c_int16(auto)
        l_at1 = waveforms.at1.ctypes.data_as(_c_int16_p)
        l_at2 = waveforms.at2.ctypes.data_as(_c_int16_p)
        l_dt1 = waveforms.dt1.ctypes.data_as(_c_uint8_p)
        l_dt2 = waveforms.dt2.ctypes.data_as(_c_uint8_p)
        l_ns = ct.c_uint32()
        l_tsample = ct.c_double()
        lib.get_waveform(self.handle, channel, l_auto, l_at1, l_at2, l_dt1, l_dt2, l_ns, l_tsample)
        return l_ns.value, l_tsample.value

    def get_histogram(self, channel: int, index: int) -> Histogram:
        """
        Binding of CAENDPP_GetHistogram()
        """
        n_bins = self.get_histogram_size(channel, index)
        histo = np.empty(n_bins, dtype=np.uint32)
        l_counts = ct.c_uint32()
        l_realtime = ct.c_uint64()
        l_deadtime = ct.c_uint64()
        lib.get_histogram(self.handle, channel, index, histo.ctypes, l_counts, l_realtime, l_deadtime)
        return Histogram(histo, l_counts.value, l_realtime.value, l_deadtime.value)

    def set_histogram(self, channel: int, index: int, histogram: Histogram) -> None:
        """
        Binding of CAENDPP_SetHistogram()
        """
        lib.set_histogram(self.handle, channel, index, histogram.realtime, histogram.deadtime, len(histogram.histo), histogram.histo.ctypes.data)

    def get_current_histogram(self, channel: int) -> tuple[Histogram, AcqStatus]:
        """
        Binding of CAENDPP_GetCurrentHistogram()
        """
        current_index = self.get_current_histogram_index(channel)
        n_bins = self.get_histogram_size(channel, current_index)
        histo = np.empty(n_bins, dtype=np.uint32)
        l_counts = ct.c_uint32()
        l_realtime = ct.c_uint64()
        l_deadtime = ct.c_uint64()
        l_status = ct.c_int()
        lib.get_current_histogram(self.handle, channel, histo.ctypes, l_counts, l_realtime, l_deadtime, l_status)
        return Histogram(histo, l_counts.value, l_realtime.value, l_deadtime.value), AcqStatus(l_status.value)

    def save_histogram(self, channel: int, index: int, filename: str) -> None:
        """
        Binding of CAENDPP_SaveHistogram()
        """
        lib.save_histogram(self.handle, channel, index, filename.encode('ascii'))

    def load_histogram(self, channel: int, index: int, filename: str) -> None:
        """
        Binding of CAENDPP_LoadHistogram()
        """
        lib.load_histogram(self.handle, channel, index, filename.encode('ascii'))

    def clear_histogram(self, channel: int, index: int) -> None:
        """
        Binding of CAENDPP_ClearHistogram()
        """
        lib.clear_histogram(self.handle, channel, index)

    def clear_current_histogram(self, channel: int) -> None:
        """
        Binding of CAENDPP_ClearCurrentHistogram()
        """
        lib.clear_current_histogram(self.handle, channel)

    def clear_all_histograms(self, channel: int) -> None:
        """
        Binding of CAENDPP_ClearAllHistograms()
        """
        lib.clear_all_histograms(self.handle, channel)

    def reset_histogram(self, channel: int, index: int) -> None:
        """
        Binding of CAENDPP_ResetHistogram()
        """
        lib.reset_histogram(self.handle, channel, index)

    def reset_all_histograms(self, channel: int) -> None:
        """
        Binding of CAENDPP_ResetAllHistograms()
        """
        lib.reset_all_histograms(self.handle, channel)

    def force_new_histogram(self, channel: int) -> None:
        """
        Binding of CAENDPP_ForceNewHistogram()
        """
        lib.force_new_histogram(self.handle, channel)

    def set_histogram_size(self, channel: int, index: int, size: int) -> None:
        """
        Binding of CAENDPP_SetHistogramSize()
        """
        lib.set_histogram_size(self.handle, channel, index, size)

    def get_histogram_size(self, channel: int, index: int) -> int:
        """
        Binding of CAENDPP_GetHistogramSize()
        """
        l_size = ct.c_int32()
        lib.get_histogram_size(self.handle, channel, index, l_size)
        return l_size.value

    def add_histogram(self, channel: int, size: int) -> None:
        """
        Binding of CAENDPP_AddHistogram()
        """
        lib.add_histogram(self.handle, channel, size)

    def set_current_histogram_index(self, channel: int, index: int) -> None:
        """
        Binding of CAENDPP_SetCurrentHistogramIndex()
        """
        lib.set_current_histogram_index(self.handle, channel, index)

    def get_current_histogram_index(self, channel: int) -> int:
        """
        Binding of CAENDPP_GetCurrentHistogramIndex()
        """
        l_index = ct.c_int32()
        lib.get_current_histogram_index(self.handle, channel, l_index)
        return l_index.value

    def set_histogram_status(self, channel: int, index: int, completed: bool) -> None:
        """
        Binding of CAENDPP_SetHistogramStatus()
        """
        lib.set_histogram_status(self.handle, channel, index, completed)

    def get_histogram_status(self, channel: int, index: int) -> bool:
        """
        Binding of CAENDPP_GetHistogramStatus()
        """
        l_completed = ct.c_int32()
        lib.get_histogram_status(self.handle, channel, index, l_completed)
        return bool(l_completed.value)

    def set_histogram_range(self, channel: int, lower: int, upper: int) -> None:
        """
        Binding of CAENDPP_SetHistogramRange()
        """
        lib.set_histogram_range(self.handle, channel, lower, upper)

    def get_histogram_range(self, channel: int) -> tuple[int, int]:
        """
        Binding of CAENDPP_GetHistogramRange()
        """
        l_lower = ct.c_int32()
        l_upper = ct.c_int32()
        lib.get_histogram_range(self.handle, channel, l_lower, l_upper)
        return l_lower.value, l_upper.value

    def get_acq_stats(self, channel: int) -> Statistics:
        """
        Binding of CAENDPP_GetAcqStats()
        """
        l_stats = _StatisticsRaw()
        lib.get_acq_stats(self.handle, channel, l_stats)
        return Statistics.from_raw(l_stats)

    def set_input_range(self, channel: int, value: InputRange) -> None:
        """
        Binding of CAENDPP_SetInputRange()
        """
        lib.set_input_range(self.handle, channel, value)

    def get_input_range(self, channel: int) -> InputRange:
        """
        Binding of CAENDPP_GetInputRange()
        """
        l_value = ct.c_int()
        lib.get_input_range(self.handle, channel, l_value)
        return InputRange(l_value.value)

    def get_waveform_length(self, channel: int) -> int:
        """
        Binding of CAENDPP_GetWaveformLength()
        """
        l_length = ct.c_uint32()
        lib.get_waveform_length(self.handle, channel, l_length)
        return l_length.value

    def check_board_communication(self, board_id: int) -> None:
        """
        Binding of CAENDPP_CheckBoardCommunication()
        """
        lib.check_board_communication(self.handle, board_id)

    def get_parameter_info(self, board_id: int, param: ParamID) -> ParamInfo:
        """
        Binding of CAENDPP_GetParameterInfo()
        """
        l_info = _ParamInfoRaw()
        lib.get_parameter_info(self.handle, board_id, param, l_info)
        return ParamInfo.from_raw(l_info)

    def board_adc_calibration(self, board_id: int) -> None:
        """
        Binding of CAENDPP_BoardADCCalibration()
        """
        lib.board_adc_calibration(self.handle, board_id)

    def get_channel_temperature(self, channel: int) -> float:
        """
        Binding of CAENDPP_GetChannelTemperature()
        """
        l_temp = ct.c_double()
        lib.get_channel_temperature(self.handle, channel, l_temp)
        return l_temp.value

    def get_daq_info(self, board_id: int) -> DAQInfo:
        """
        Binding of CAENDPP_GetDAQInfo()
        """
        l_info = _DAQInfoRaw()
        lib.get_daq_info(self.handle, board_id, l_info)
        return DAQInfo.from_raw(l_info)

    def reset_configuration(self, board_id: int) -> None:
        """
        Binding of CAENDPP_ResetConfiguration()
        """
        lib.reset_configuration(self.handle, board_id)

    def set_hv_channel_configuration(self, board_id: int, channel: int, config: HVChannelConfig) -> None:
        """
        Binding of CAENDPP_SetHVChannelConfiguration()
        """
        l_config = config.to_raw()
        lib.set_hv_channel_configuration(self.handle, board_id, channel, l_config)

    def get_hv_channel_configuration(self, board_id: int, channel: int) -> HVChannelConfig:
        """
        Binding of CAENDPP_GetHVChannelConfiguration()
        """
        l_config = _HVChannelConfigRaw()
        lib.get_hv_channel_configuration(self.handle, board_id, channel, l_config)
        return HVChannelConfig.from_raw(l_config)

    def set_hv_channel_vmax(self, board_id: int, channel: int, value: float) -> None:
        """
        Binding of CAENDPP_SetHVChannelVMax()
        """
        lib.set_hv_channel_vmax(self.handle, board_id, channel, value)

    def get_hv_channel_status(self, board_id: int, channel: int) -> int:
        """
        Binding of CAENDPP_GetHVChannelStatus()
        """
        l_status = ct.c_uint16()
        lib.get_hv_channel_status(self.handle, board_id, channel, l_status)
        return l_status.value

    def set_hv_channel_power_on(self, board_id: int, channel: int, value: bool) -> None:
        """
        Binding of CAENDPP_SetHVChannelPowerOn()
        """
        lib.set_hv_channel_power_on(self.handle, board_id, channel, value)

    def get_hv_channel_power_on(self, board_id: int, channel: int) -> bool:
        """
        Binding of CAENDPP_GetHVChannelPowerOn()
        """
        l_value = ct.c_uint32()
        lib.get_hv_channel_power_on(self.handle, board_id, channel, l_value)
        return bool(l_value.value)

    def read_hv_channel_monitoring(self, board_id: int, channel: int) -> HVChannelMonitoring:
        """
        Binding of CAENDPP_ReadHVChannelMonitoring()
        """
        l_vmon = ct.c_double()
        l_imon = ct.c_double()
        lib.read_hv_channel_monitoring(self.handle, board_id, channel, l_vmon, l_imon)
        return HVChannelMonitoring(l_vmon.value, l_imon.value)

    def read_hv_channel_externals(self, board_id: int, channel: int) -> HVChannelExternals:
        """
        Binding of CAENDPP_ReadHVChannelExternals()
        """
        l_vext = ct.c_double()
        l_tres = ct.c_double()
        lib.read_hv_channel_externals(self.handle, board_id, channel, l_vext, l_tres)
        return HVChannelExternals(l_vext.value, l_tres.value)

    def enumerate_devices(self) -> EnumeratedDevices:
        """
        Binding of CAENDPP_EnumerateDevices()
        """
        l_devices = _EnumeratedDevicesRaw()
        lib.enumerate_devices(l_devices)
        return EnumeratedDevices.from_raw(l_devices)

    def get_hv_status_string(self, board_id: int, status: int) -> str:
        """
        Binding of CAENDPP_GetHVStatusString()
        """
        l_status = ct.create_string_buffer(128)  # Undocumented but, hopefully, long enough
        lib.get_hv_status_string(self.handle, board_id, status, l_status)
        return l_status.value.decode('ascii')

    def set_hv_range(self, board_id: int, channel: int, value: HVRange) -> None:
        """
        Binding of CAENDPP_SetHVRange()
        """
        lib.set_hv_range(self.handle, board_id, channel, value)

    def get_hv_range(self, board_id: int, channel: int) -> HVRange:
        """
        Binding of CAENDPP_GetHVRange()
        """
        l_value = ct.c_int()
        lib.get_hv_range(self.handle, board_id, channel, l_value)
        return HVRange(l_value.value)

    def set_logger_severity_mask(self, mask: LogMask) -> None:
        """
        Binding of CAENDPP_SetLoggerSeverityMask()
        """
        lib.set_logger_severity_mask(self.handle, mask)

    def get_logger_severity_mask(self) -> LogMask:
        """
        Binding of CAENDPP_GetLoggerSeverityMask()
        """
        l_mask = ct.c_int()
        lib.get_logger_severity_mask(l_mask)
        return LogMask(l_mask.value)

    def set_hv_inhibit_polarity(self, board_id: int, channel: int, value: PulsePolarity) -> None:
        """
        Binding of CAENDPP_SetHVInhibitPolarity()
        """
        lib.set_hv_inhibit_polarity(self.handle, board_id, channel, value)

    def get_hv_inhibit_polarity(self, board_id: int, channel: int) -> PulsePolarity:
        """
        Binding of CAENDPP_GetHVInhibitPolarity()
        """
        l_value = ct.c_int()
        lib.get_hv_inhibit_polarity(self.handle, board_id, channel, l_value)
        return PulsePolarity(l_value.value)

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
