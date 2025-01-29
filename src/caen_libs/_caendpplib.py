"""
Binding of CAEN DPP Library
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
from enum import IntEnum, IntFlag, unique
from typing import Optional, TypeVar

from caen_libs import error, _utils


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
        ('ETHAddress', ct.c_char * 8),
    ]


@dataclass(frozen=True, **_utils.dataclass_slots)
class ConnectionParams:
    """
    Binding of ::CAENDPP_ConnectionParams_t
    """
    link_type: ConnectionType
    link_num: int
    conet_node: int
    vme_base_address: int
    eth_address: str


class _ParamInfoRaw(ct.Structure):
    _fields_ = [
        ('type', ct.c_int),
        ('minimum', ct.c_double),
        ('maximum', ct.c_double),
        ('resolution', ct.c_double),
        ('values', ct.c_double * 15),
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


@dataclass
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
            tuple(raw.values[:raw.valuesCount]),
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
        ('RangeInfos', _HVRangeInfoRaw * 3),
    ]


@dataclass(frozen=True, **_utils.dataclass_slots)
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
            tuple(HVRangeInfo.from_raw(i) for i in raw.RangeInfos[:raw.NumRanges]),
        )


class _InfoRaw(ct.Structure):
    _fields_ = [
        ('ModelName', ct.c_char * 12),
        ('Model', ct.c_int32),
        ('Channels', ct.c_uint32),
        ('ROC_FirmwareRel', ct.c_char * 20),
        ('AMC_FirmwareRel', ct.c_char * 20),
        ('License', ct.c_char * 17),
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
        ('InputRanges', ct.c_int * 15),
        ('Tsample', ct.c_double),
        ('SupportedVirtualProbes1', ct.c_uint32 * 20),
        ('NumVirtualProbes1', ct.c_uint32),
        ('SupportedVirtualProbes2', ct.c_uint32 * 20),
        ('NumVirtualProbes2', ct.c_uint32),
        ('SupportedDigitalProbes1', ct.c_uint32 * 20),
        ('NumDigitalProbes1', ct.c_uint32),
        ('SupportedDigitalProbes2', ct.c_uint32 * 20),
        ('NumDigitalProbes2', ct.c_uint32),
        ('DPPCodeMaj', ct.c_int32),
        ('DPPCodeMin', ct.c_int32),
        ('HVChannelInfo', _HVChannelInfoRaw * 2),
        ('NumMonOutProbes', ct.c_uint32),
        ('SupportedMonOutProbes', ct.c_uint32 * 20),
    ]


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


@dataclass(frozen=True, **_utils.dataclass_slots)
class Info:
    """
    Binding of ::CAENDPP_Info_t
    """
    model_name: str
    model: int
    channels: int
    roc_firmware_rel: str
    amc_firmware_rel: str
    license: str
    serial_number: int
    status: int
    family_code: int
    hv_channels: int
    form_factor: int
    pcb_revision: int
    adc_nbits: int
    energy_max_nbits: int
    usb_option: int
    eth_option: int
    wifi_option: int
    bt_option: int
    poe_option: int
    gps_option: int
    input_ranges: tuple[InputRange, ...]
    tsample: float
    supported_virtual_probes1: tuple[int, ...]
    supported_virtual_probes2: tuple[int, ...]
    supported_digital_probes1: tuple[int, ...]
    supported_digital_probes2: tuple[int, ...]
    dpp_code_maj: int
    dpp_code_min: int
    hv_channel_info: tuple[HVChannelInfo, ...]
    supported_mon_out_probes: tuple[int, ...]

    @classmethod
    def from_raw(cls, raw: _InfoRaw):
        """Instantiate from raw data"""
        return cls(
            raw.ModelName.decode(),
            raw.Model,
            raw.Channels,
            raw.ROC_FirmwareRel.decode(),
            raw.AMC_FirmwareRel.decode(),
            raw.License.decode(),
            raw.SerialNumber,
            raw.Status,
            raw.FamilyCode,
            raw.HVChannels,
            raw.FormFactor,
            raw.PCB_Revision,
            raw.ADC_NBits,
            raw.Energy_MaxNBits,
            raw.USBOption,
            raw.ETHOption,
            raw.WIFIOption,
            raw.BTOption,
            raw.POEOption,
            raw.GPSOption,
            tuple(InputRange(r) for r in raw.InputRanges[:raw.InputRangeNum]),
            raw.Tsample,
            tuple(raw.SupportedVirtualProbes1[:raw.NumVirtualProbes1]),
            tuple(raw.SupportedVirtualProbes2[:raw.NumVirtualProbes2]),
            tuple(raw.SupportedDigitalProbes1[:raw.NumDigitalProbes1]),
            tuple(raw.SupportedDigitalProbes2[:raw.NumDigitalProbes2]),
            raw.DPPCodeMaj,
            raw.DPPCodeMin,
            tuple(HVChannelInfo.from_raw(l) for l in raw.HVChannelInfo[:raw.HVChannels]),
            tuple(raw.SupportedMonOutProbes[:raw.NumMonOutProbes]),
        )


class _TempCorrParamsRaw(ct.Structure):
    _fields_ = [
        ('enabled', ct.c_int32),
        ('LLD', ct.c_int32),
        ('ULD', ct.c_int32),
    ]


@dataclass(frozen=True, **_utils.dataclass_slots)
class TempCorrParams:
    """
    Binding of ::CAENDPP_TempCorrParams_t
    """
    enabled: bool
    lld: int
    uld: int

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
    ANALOG_INPUT = 100
    ANALOG_FAST_TRAP = 101
    ANALOG_BASELINE = 102
    ANALOG_TRAPEZOID = 103
    ANALOG_ENERGY = 104
    ANALOG_TRAP_CORRECTED = 105


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
        ('GPIOs', _GPIORaw * 2),
        ('TRGControl', ct.c_int),
        ('GPIOLogic', ct.c_int),
        ('TimeWindow', ct.c_uint32),
        ('TransResetLength', ct.c_uint32),
        ('TransResetPeriod', ct.c_uint32),
    ]


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


class GPIOLogic(IntEnum):
    """
    Binding of ::CAENDPP_GPIOLogic_t
    """
    AND = 0
    OR = 1


@dataclass(frozen=True, **_utils.dataclass_slots)
class GPIOConfig:
    """
    Binding of ::CAENDPP_GPIOConfig_t
    """
    gpios: tuple[GPIO, ...]
    trg_control: TriggerControl
    gpio_logic: GPIOLogic
    time_window: int
    trans_reset_length: int
    trans_reset_period: int

    @classmethod
    def from_raw(cls, raw: _GPIOConfigRaw):
        """Instantiate from raw data"""
        return cls(
            tuple(GPIO.from_raw(i) for i in raw.GPIOs),
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


class InputImpedance(IntEnum):
    """
    Binding of ::CAENDPP_InputImpedance_t
    """
    O_50 = 0
    O_1K = 1


@dataclass(frozen=True, **_utils.dataclass_slots)
class ExtraParameters:
    """
    Binding of ::CAENDPP_ExtraParameters
    """
    trig_k: int
    trigm: int
    trig_mode: int
    energy_filter_mode: int
    input_impedance: InputImpedance
    cr_gain: int
    tr_gain: int
    saturation_holdoff: int
    gpio_config: GPIOConfig

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
        ('M', ct.c_int32 * 16),
        ('m', ct.c_int32 * 16),
        ('k', ct.c_int32 * 16),
        ('ftd', ct.c_int32 * 16),
        ('a', ct.c_int32 * 16),
        ('b', ct.c_int32 * 16),
        ('thr', ct.c_int32 * 16),
        ('nsbl', ct.c_int32 * 16),
        ('nspk', ct.c_int32 * 16),
        ('pkho', ct.c_int32 * 16),
        ('blho', ct.c_int32 * 16),
        ('trgho', ct.c_int32 * 16),
        ('dgain', ct.c_int32 * 16),
        ('enf', ct.c_float * 16),
        ('decimation', ct.c_int32 * 16),
        ('enskim', ct.c_int32 * 16),
        ('eskimlld', ct.c_int32 * 16),
        ('eskimuld', ct.c_int32 * 16),
        ('blrclip', ct.c_int32 * 16),
        ('dcomp', ct.c_int32 * 16),
        ('trapbsl', ct.c_int32 * 16),
        ('pz_dac', ct.c_uint32 * 16),
        ('inh_length', ct.c_uint32 * 16),
        ('X770_extraparameters', _ExtraParametersRaw * 16),
    ]


@dataclass(frozen=True, **_utils.dataclass_slots)
class PHAParams:
    """
    Binding of ::CAENDPP_PHA_Params_t
    """
    m: tuple[int, ...]
    k: tuple[int, ...]
    ftd: tuple[int, ...]
    a: tuple[int, ...]
    b: tuple[int, ...]
    thr: tuple[int, ...]
    nsbl: tuple[int, ...]
    nspk: tuple[int, ...]
    pkho: tuple[int, ...]
    blho: tuple[int, ...]
    trgho: tuple[int, ...]
    dgain: tuple[int, ...]
    enf: tuple[float, ...]
    decimation: tuple[int, ...]
    enskim: tuple[int, ...]
    eskimlld: tuple[int, ...]
    eskimuld: tuple[int, ...]
    blrclip: tuple[int, ...]
    dcomp: tuple[int, ...]
    trapbsl: tuple[int, ...]
    pz_dac: tuple[int, ...]
    inh_length: tuple[int, ...]
    x770_extraparameters: tuple[ExtraParameters, ...]

    @classmethod
    def from_raw(cls, raw: _PHAParamsRaw):
        """Instantiate from raw data"""
        return cls(
            tuple(raw.m),
            tuple(raw.k),
            tuple(raw.ftd),
            tuple(raw.a),
            tuple(raw.b),
            tuple(raw.thr),
            tuple(raw.nsbl),
            tuple(raw.nspk),
            tuple(raw.pkho),
            tuple(raw.blho),
            tuple(raw.trgho),
            tuple(raw.dgain),
            tuple(raw.enf),
            tuple(raw.decimation),
            tuple(raw.enskim),
            tuple(raw.eskimlld),
            tuple(raw.eskimuld),
            tuple(raw.blrclip),
            tuple(raw.dcomp),
            tuple(raw.trapbsl),
            tuple(raw.pz_dac),
            tuple(raw.inh_length),
            tuple(ExtraParameters.from_raw(e) for e in raw.X770_extraparameters),
        )

    def to_raw(self) -> _PHAParamsRaw:
        """Convert to raw data"""
        return _PHAParamsRaw(
            self.m,
            self.k,
            self.ftd,
            self.a,
            self.b,
            self.thr,
            self.nsbl,
            self.nspk,
            self.pkho,
            self.blho,
            self.trgho,
            self.dgain,
            self.enf,
            self.decimation,
            self.enskim,
            self.eskimlld,
            self.eskimuld,
            self.blrclip,
            self.dcomp,
            self.trapbsl,
            self.pz_dac,
            self.inh_length,
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


@dataclass(frozen=True, **_utils.dataclass_slots)
class WaveformParams:
    """
    Binding of ::CAENDPP_WaveformParams_t
    """
    dual_trace_mode: int
    vp1: VirtualProbe1
    vp2: VirtualProbe2
    dp1: DigitalProbe1
    dp2: DigitalProbe2
    record_length: int
    pre_trigger: int
    probe_trigger: ProbeTrigger
    probe_self_trigger_val: int

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
        ('fileName', ct.c_char * 155),
        ('maxBuffNumEvents', ct.c_uint32),
        ('saveMask', ct.c_uint32),
        ('enableFakes', ct.c_uint8),
    ]


class ListSaveMode(IntEnum):
    """
    Binding of ::CAENDPP_ListSaveMode_t
    """
    MEMORY = 0
    FILE_BINARY = 1
    FILE_ASCII = 2


class DumpMask(IntFlag):
    """
    Binding of ::DUMP_MASK_*
    """
    TTT = 0x1
    ENERGY = 0x2
    EXTRAS = 0x4
    ENERGY_SHORT = 0x8


@dataclass(frozen=True, **_utils.dataclass_slots)
class ListParams:
    """
    Binding of ::CAENDPP_ListParams_t
    """
    enabled: bool
    save_mode: ListSaveMode
    file_name: str
    max_buff_num_events: int
    save_mask: DumpMask
    enable_fakes: bool

    @classmethod
    def from_raw(cls, raw: _ListParamsRaw):
        """Instantiate from raw data"""
        return cls(
            bool(raw.enabled),
            ListSaveMode(raw.saveMode),
            raw.fileName.decode(),
            raw.maxBuffNumEvents,
            DumpMask(raw.saveMask),
            bool(raw.enableFakes),
        )

    def to_raw(self) -> _ListParamsRaw:
        """Convert to raw data"""
        return _ListParamsRaw(
            self.enabled,
            self.save_mode,
            self.file_name.encode(),
            self.max_buff_num_events,
            self.save_mask,
            self.enable_fakes,
        )


class _RunSpecsRaw(ct.Structure):
    _fields_ = [
        ('RunName', ct.c_char * 128),
        ('RunDurationSec', ct.c_int32),
        ('PauseSec', ct.c_int32),
        ('CyclesCount', ct.c_int32),
        ('SaveLists', ct.c_uint8),
        ('GPSEnable', ct.c_uint8),
        ('ClearHistos', ct.c_uint8),
    ]


@dataclass(frozen=True, **_utils.dataclass_slots)
class RunSpecs:
    """
    Binding of ::CAENDPP_RunSpecs_t
    """
    run_name: str
    run_duration_sec: int
    pause_sec: int
    cycles_count: int
    save_lists: bool
    gps_enable: bool
    clear_histos: bool

    @classmethod
    def from_raw(cls, raw: _RunSpecsRaw):
        """Instantiate from raw data"""
        return cls(
            raw.RunName.decode(),
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
            self.run_name.encode(),
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


class CoincOp(IntEnum):
    """
    Binding of ::CAENDPP_CoincOp_t
    """
    OR = 0
    AND = 1
    MAJ = 2


class CoincLogic(IntEnum):
    """
    Binding of ::CAENDPP_CoincLogic_t
    """
    NONE = 0
    COINCIDENCE = 2
    ANTICOINCIDENCE = 3


@dataclass(frozen=True, **_utils.dataclass_slots)
class CoincParams:
    """
    Binding of ::CAENDPP_CoincParams_t
    """
    coinc_ch_mask: int
    maj_level: int
    trg_win: int
    coinc_op: CoincOp
    coinc_logic: CoincLogic

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


class PulsePolarity(IntEnum):
    """
    Binding of ::CAENDPP_PulsePolarity_t
    """
    POSITIVE = 0
    NEGATIVE = 1


class ExtLogic(IntEnum):
    """
    Binding of ::CAENDPP_ExtLogic_t
    """
    VETO = 0
    GATE = 1


@dataclass(frozen=True, **_utils.dataclass_slots)
class GateParams:
    """
    Binding of ::CAENDPP_GateParams_t
    """
    gate_enable: bool
    shape_time: int
    polarity: PulsePolarity
    gate_logic: ExtLogic

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


@dataclass(frozen=True, **_utils.dataclass_slots)
class SpectrumControl:
    """
    Binding of ::CAENDPP_SpectrumControl
    """
    spectrum_mode: SpectrumMode
    time_scale: int

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


class ResetDetectionMode(IntEnum):
    """
    Binding of ::CAENDPP_ResetDetectionMode_t
    """
    INTERNAL = 0
    GPIO = 1
    BOTH = 2


@dataclass(frozen=True, **_utils.dataclass_slots)
class TRReset:
    """
    Binding of ::CAENDPP_TRReset
    """
    enabled: bool
    reset_detection_mode: ResetDetectionMode
    thrhold: int
    reslenmin: int
    reslength: int

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


class PHA_MonOutProbe(IntEnum):
    """
    Binding of ::CAENDPP_PHA_MonOutProbe_t
    """
    INPUT = 0
    FAST_TRIGGER = 1
    TRAPEZOID = 2
    TRAP_BL_CORR = 3


@dataclass(frozen=True, **_utils.dataclass_slots)
class MonOutParams:
    """
    Binding of ::CAENDPP_MonOutParams_t
    """
    channel: int
    enabled: bool
    probe: PHA_MonOutProbe

    @classmethod
    def from_raw(cls, raw: _MonOutParamsRaw):
        """Instantiate from raw data"""
        return cls(raw.channel, bool(raw.enabled), PHA_MonOutProbe(raw.probe))

    def to_raw(self) -> _MonOutParamsRaw:
        """Convert to raw data"""
        return _MonOutParamsRaw(self.channel, self.enabled, self.probe)


class _DgtzParamsRaw(ct.Structure):
    _fields_ = [
        ('GWn', ct.c_int32),
        ('GWaddr', ct.c_uint32 * 1000),
        ('GWdata', ct.c_uint32 * 1000),
        ('GWmask', ct.c_uint32 * 1000),
        ('ChannelMask', ct.c_int32),
        ('PulsePolarity', ct.c_int * 16),
        ('DCoffset', ct.c_int32 * 16),
        ('TempCorrParameters', _TempCorrParamsRaw * 16),
        ('InputCoupling', ct.c_int * 16),
        ('EventAggr', ct.c_int32),
        ('DPPParams', _PHAParamsRaw),
        ('IOlev', ct.c_int),
        ('WFParams', _WaveformParamsRaw),
        ('ListParams', _ListParamsRaw),
        ('RunSpecifications', _RunSpecsRaw),
        ('CoincParams', _CoincParamsRaw * 17),
        ('GateParams', _GateParamsRaw * 16),
        ('SpectrumControl', _SpectrumControlRaw * 16),
        ('ResetDetector', _TRResetRaw * 16),
        ('MonOutParams', _MonOutParamsRaw),
    ]


class INCoupling(IntEnum):
    """
    Binding of ::CAENDPP_INCoupling_t
    """
    DC = 0
    AC_5US = 1
    AC_11US = 2
    AC_33US = 3


@dataclass(frozen=True, **_utils.dataclass_slots)
class DgtzParams:
    """
    Binding of ::CAENDPP_DgtzParams_t
    """
    gw_addr: tuple[int, ...]
    gw_data: tuple[int, ...]
    gw_mask: tuple[int, ...]
    channel_mask: int
    pulse_polarity: tuple[PulsePolarity, ...]
    dc_offset: tuple[int, ...]
    temp_corr_parameters: tuple[TempCorrParams, ...]
    input_coupling: tuple[INCoupling, ...]
    event_aggr: int
    dpp_params: PHAParams
    iolev: int
    wf_params: WaveformParams
    list_params: ListParams
    run_specifications: RunSpecs
    coinc_params: tuple[CoincParams, ...]
    gate_params: tuple[GateParams, ...]
    spectrum_control: tuple[SpectrumControl, ...]
    reset_detector: tuple[TRReset, ...]
    mon_out_params: MonOutParams

    @classmethod
    def from_raw(cls, raw: _DgtzParamsRaw):
        """Instantiate from raw data"""
        return cls(
            tuple(raw.GWaddr[:raw.GWn]),
            tuple(raw.GWdata[:raw.GWn]),
            tuple(raw.GWmask[:raw.GWn]),
            raw.ChannelMask,
            tuple(PulsePolarity(i) for i in raw.PulsePolarity),
            tuple(raw.DCoffset),
            tuple(TempCorrParams.from_raw(i) for i in raw.TempCorrParameters),
            tuple(INCoupling(i) for i in raw.InputCoupling),
            raw.EventAggr,
            PHAParams.from_raw(raw.DPPParams),
            raw.IOlev,
            WaveformParams.from_raw(raw.WFParams),
            ListParams.from_raw(raw.ListParams),
            RunSpecs.from_raw(raw.RunSpecifications),
            tuple(CoincParams.from_raw(i) for i in raw.CoincParams),
            tuple(GateParams.from_raw(i) for i in raw.GateParams),
            tuple(SpectrumControl.from_raw(i) for i in raw.SpectrumControl),
            tuple(TRReset.from_raw(i) for i in raw.ResetDetector),
            MonOutParams.from_raw(raw.MonOutParams),
        )

    def to_raw(self) -> _DgtzParamsRaw:
        """Convert to raw data"""
        return _DgtzParamsRaw(
            len(self.gw_addr),
            self.gw_addr,
            self.gw_data,
            self.gw_mask,
            self.channel_mask,
            self.pulse_polarity,
            self.dc_offset,
            tuple(i.to_raw() for i in self.temp_corr_parameters),
            self.input_coupling,
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


class _StatisticsRaw(ct.Structure):
    _fields_ = [
        ('ThroughputRate', ct.c_double),
        ('SaturationFlag', ct.c_uint32),
        ('SaturationPerc', ct.c_double),
        ('PulseDeadTime', ct.c_double),
        ('RealRate', ct.c_double),
        ('PeakingTime', ct.c_uint32),
    ]


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


class _HVChannelConfigRaw(ct.Structure):
    _fields_ = [
        ('VSet', ct.c_double),
        ('ISet', ct.c_double),
        ('RampUp', ct.c_double),
        ('RampDown', ct.c_double),
        ('VMax', ct.c_double),
        ('PWDownMode', ct.c_int),
    ]


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


class _EnumeratedDevicesRaw(ct.Structure):
    _fields_ = [
        ('ddcount', ct.c_int),
        ('Device', _EnumerationSingleDeviceRaw * 64),
    ]


class LogMask(IntFlag):
    """
    Binding of ::CAENDPP_LogMask
    """
    NONE = 0x0
    INFO = 0x1
    ERROR = 0x2
    WARNING = 0x4
    DEBUG = 0x8
    ALL = INFO | ERROR | WARNING | DEBUG


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
_P = ct.POINTER
_c_int_p = _P(ct.c_int)
_c_uint_p = _P(ct.c_uint)
_c_int16_p = _P(ct.c_int16)
_c_int32_p = _P(ct.c_int32)
_c_uint8_p = _P(ct.c_uint8)
_c_uint16_p = _P(ct.c_uint16)
_c_uint32_p = _P(ct.c_uint32)
_c_uint64_p = _P(ct.c_uint64)
_c_double_p = _P(ct.c_double)
_connection_params_p = _P(_ConnectionParamsRaw)
_info_p = _P(_InfoRaw)
_dgtz_params_p = _P(_DgtzParamsRaw)
_list_event_p = _P(_ListEventRaw)
_statistics_p = _P(_StatisticsRaw)
_param_info_p = _P(_ParamInfoRaw)
_daq_info_p = _P(_DAQInfoRaw)
_hv_channel_config_p = _P(_HVChannelConfigRaw)
_enumerated_devices_p = _P(_EnumeratedDevicesRaw)


class _Lib(_utils.Lib):

    def __init__(self, name: str) -> None:
        super().__init__(name, False)
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
        self.set_hv_channel_vset = self.__get('SetHVChannelVSet', ct.c_int32, ct.c_int32, ct.c_int, ct.c_double)
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
            raise Error(self.decode_error(res), res, func.__name__)
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

    def decode_error(self, error_code: int) -> str:
        """
        There is no function to decode error, we just use the
        enumeration name.
        """
        return Error.Code(error_code).name


# Library name is platform dependent
if sys.platform == 'win32':
    _LIB_NAME = 'CAEN_PLULib'
else:
    _LIB_NAME = 'CAEN_PLU'


lib = _Lib(_LIB_NAME)


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
        lib.attach_boards(ip.encode(), port, l_handle, l_num_board, l_board_ids)
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
        l_params = _ConnectionParamsRaw(params.link_type, params.link_num, params.conet_node, params.vme_base_address, params.eth_address.encode())
        return lib.add_board(self.handle, l_params)
    
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
