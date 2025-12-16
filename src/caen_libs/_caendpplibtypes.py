__author__ = 'Giovanni Cerretani'
__copyright__ = 'Copyright (C) 2024 CAEN SpA'
__license__ = 'LGPL-3.0-or-later'
# SPDX-License-Identifier: LGPL-3.0-or-later

import ctypes as ct
from dataclasses import dataclass, field
from enum import IntEnum, IntFlag, unique

import numpy as np
import numpy.typing as npt


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
    USB_A4818 = 5
    ETH_V4718 = 6
    USB_V4718 = 7


class ConnectionParamsRaw(ct.Structure):
    """Raw view of ::CAENDPP_ConnectionParams_t"""
    _fields_ = [
        ('LinkType', ct.c_int),
        ('LinkNum', ct.c_int32),
        ('ConetNode', ct.c_int32),
        ('VMEBaseAddress', ct.c_uint32),
        ('ETHAddress', ct.c_char * (IP_ADDR_LEN + 1)),
    ]


@dataclass(frozen=True, slots=True)
class ConnectionParams:
    """
    Binding of ::CAENDPP_ConnectionParams_t
    """
    link_type: ConnectionType
    link_num: int
    conet_node: int = 0
    vme_base_address: int = 0
    eth_address: str = ''

    def to_raw(self) -> ConnectionParamsRaw:
        """Convert to raw data"""
        return ConnectionParamsRaw(
            self.link_type,
            self.link_num,
            self.conet_node,
            self.vme_base_address,
            self.eth_address.encode('ascii'),
        )


class ParamInfoRaw(ct.Structure):
    """Raw view of ::CAENDPP_ParamInfo_t"""
    _fields_ = [
        ('type', ct.c_int),
        ('minimum', ct.c_double),
        ('maximum', ct.c_double),
        ('resolution', ct.c_double),
        ('values', ct.c_double * MAX_LIST_VALS),
        ('valuesCount', ct.c_uint32),
        ('units', ct.c_int),
    ]


@unique
class InfoType(IntEnum):
    """
    Binding of ::CAENDPP_InfoType_t
    """
    RANGE = 0
    LIST = 1


@unique
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


@dataclass(frozen=True, slots=True)
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
    def from_raw(cls, raw: ParamInfoRaw):
        """Instantiate from raw data"""
        return cls(
            InfoType(raw.type),
            raw.minimum,
            raw.maximum,
            raw.resolution,
            raw.values[:raw.valuesCount],
            Units(raw.units),
        )


class HVRangeInfoRaw(ct.Structure):
    """Raw view of ::CAENDPP_HVRangeInfo_t"""
    _fields_ = [
        ('VSetInfo', ParamInfoRaw),
        ('ISetInfo', ParamInfoRaw),
        ('RampUpInfo', ParamInfoRaw),
        ('RampDownInfo', ParamInfoRaw),
        ('VMaxInfo', ParamInfoRaw),
        ('VMonInfo', ParamInfoRaw),
        ('IMonInfo', ParamInfoRaw),
        ('VExtInfo', ParamInfoRaw),
        ('RTMPInfo', ParamInfoRaw),
        ('HVRangeCode', ct.c_int),
    ]


@unique
class HVRange(IntEnum):
    """
    Binding of ::CAENDPP_HVRange_t
    """
    HPGE = 0
    PMT = 1
    SD = 2


@dataclass(frozen=True, slots=True)
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
    def from_raw(cls, raw: HVRangeInfoRaw):
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


class HVChannelInfoRaw(ct.Structure):
    """Raw view of ::CAENDPP_HVChannelInfo_t"""
    _fields_ = [
        ('HVFamilyCode', ct.c_int),
        ('NumRanges', ct.c_int32),
        ('RangeInfos', HVRangeInfoRaw * MAX_HVRANGES),
    ]


@unique
class HVFamilyCode(IntEnum):
    """
    Binding of ::CAENDPP_HVFamilyCode_t
    """
    V6521 = 0
    V6533 = 1
    V6519 = 2
    V6521H = 3
    V6534 = 4


@dataclass(frozen=True, slots=True)
class HVChannelInfo:
    """
    Binding of ::CAENDPP_HVChannelInfo_t
    """
    hv_family_code: HVFamilyCode
    range_infos: tuple[HVRangeInfo, ...]

    @classmethod
    def from_raw(cls, raw: HVChannelInfoRaw):
        """Instantiate from raw data"""
        return cls(
            HVFamilyCode(raw.HVFamilyCode),
            tuple(map(HVRangeInfo.from_raw, raw.RangeInfos[:raw.NumRanges])),
        )


class InfoRaw(ct.Structure):
    """Raw view of ::CAENDPP_Info_t"""
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
        ('HVChannelInfo', HVChannelInfoRaw * MAX_HVCHB),
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


@unique
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


@dataclass(frozen=True, slots=True)
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
    def from_raw(cls, raw: InfoRaw):
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


class TempCorrParamsRaw(ct.Structure):
    """Raw view of ::CAENDPP_TempCorrParams_t"""
    _fields_ = [
        ('enabled', ct.c_int32),
        ('LLD', ct.c_int32),
        ('ULD', ct.c_int32),
    ]


@dataclass(slots=True)
class TempCorrParams:
    """
    Binding of ::CAENDPP_TempCorrParams_t
    """
    enabled: bool = False
    lld: int = 0
    uld: int = 0

    @classmethod
    def from_raw(cls, raw: TempCorrParamsRaw):
        """Instantiate from raw data"""
        return cls(bool(raw.enabled), raw.LLD, raw.ULD)

    def to_raw(self) -> TempCorrParamsRaw:
        """Convert to raw data"""
        return TempCorrParamsRaw(self.enabled, self.lld, self.uld)


class GPIORaw(ct.Structure):
    """Raw view of ::CAENDPP_GPIO_t"""
    _fields_ = [
        ('Mode', ct.c_int),
        ('SigOut', ct.c_int),
        ('DACInvert', ct.c_uint8),
        ('DACOffset', ct.c_uint32),
    ]


@unique
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


@dataclass(frozen=True, slots=True)
class GPIO:
    """
    Binding of ::CAENDPP_GPIO_t
    """
    mode: GPIOMode
    sig_out: OutSignal
    dac_invert: bool
    dac_offset: int

    @classmethod
    def from_raw(cls, raw: GPIORaw):
        """Instantiate from raw data"""
        return cls(
            GPIOMode(raw.Mode),
            OutSignal(raw.SigOut),
            bool(raw.DACInvert),
            raw.DACOffset,
        )

    def to_raw(self) -> GPIORaw:
        """Convert to raw data"""
        return GPIORaw(
            self.mode,
            self.sig_out,
            self.dac_invert,
            self.dac_offset,
        )


class GPIOConfigRaw(ct.Structure):
    """Raw view of ::CAENDPP_GPIOConfig_t"""
    _fields_ = [
        ('GPIOs', GPIORaw * MAX_GPIO_NUM),
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


@dataclass(slots=True)
class GPIOConfig:
    """
    Binding of ::CAENDPP_GPIOConfig_t
    """
    gpios: list[GPIO] = field(default_factory=list)
    trg_control: TriggerControl = TriggerControl.INTERNAL
    gpio_logic: GPIOLogic = GPIOLogic.AND
    time_window: int = 0
    trans_reset_length: int = 0
    trans_reset_period: int = 0

    @classmethod
    def from_raw(cls, raw: GPIOConfigRaw):
        """Instantiate from raw data"""
        return cls(
            list(map(GPIO.from_raw, raw.GPIOs)),
            TriggerControl(raw.TRGControl),
            GPIOLogic(raw.GPIOLogic),
            raw.TimeWindow,
            raw.TransResetLength,
            raw.TransResetPeriod,
        )

    def to_raw(self) -> GPIOConfigRaw:
        """Convert to raw data"""
        return GPIOConfigRaw(
            tuple(i.to_raw() for i in self.gpios),
            self.trg_control,
            self.gpio_logic,
            self.time_window,
            self.trans_reset_length,
            self.trans_reset_period,
        )


class ExtraParametersRaw(ct.Structure):
    """Raw view of ::CAENDPP_ExtraParameters_t"""
    _fields_ = [
        ('trigK', ct.c_int32),
        ('trigm', ct.c_int32),
        ('trigMODE', ct.c_int32),
        ('energyFilterMode', ct.c_int32),
        ('InputImpedance', ct.c_int),
        ('CRgain', ct.c_uint32),
        ('TRgain', ct.c_uint32),
        ('SaturationHoldoff', ct.c_uint32),
        ('GPIOConfig', GPIOConfigRaw),
    ]


@unique
class InputImpedance(IntEnum):
    """
    Binding of ::CAENDPP_InputImpedance_t
    """
    O_50 = 0
    O_1K = 1


@dataclass(slots=True)
class ExtraParameters:
    """
    Binding of ::CAENDPP_ExtraParameters
    """
    trig_k: int = 0
    trigm: int = 0
    trig_mode: int = 0
    energy_filter_mode: int = 0
    input_impedance: InputImpedance = InputImpedance.O_1K
    cr_gain: int = 0
    tr_gain: int = 0
    saturation_holdoff: int = 0
    gpio_config: GPIOConfig = field(default_factory=GPIOConfig)

    @classmethod
    def from_raw(cls, raw: ExtraParametersRaw):
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

    def to_raw(self) -> ExtraParametersRaw:
        """Convert to raw data"""
        return ExtraParametersRaw(
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


class PHAParamsRaw(ct.Structure):
    """Raw view of ::CAENDPP_PHA_Params_t"""
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
        ('X770_extraparameters', ExtraParametersRaw * MAX_NUMCHB),
    ]


@dataclass(slots=True)
class PHAParams:
    """
    Binding of ::CAENDPP_PHA_Params_t
    """

    @dataclass(slots=True)
    class _ChData:
        m_: int = 0
        m: int = 0
        k: int = 0
        ftd: int = 0
        a: int = 0
        b: int = 0
        thr: int = 0
        nsbl: int = 0
        nspk: int = 0
        pkho: int = 0
        blho: int = 0
        trgho: int = 0
        dgain: int = 0
        enf: float = 0.0
        decimation: int = 0
        enskim: int = 0
        eskimlld: int = 0
        eskimuld: int = 0
        blrclip: int = 0
        dcomp: int = 0
        trapbsl: int = 0
        pz_dac: int = 0
        inh_length: int = 0
        x770_extraparameters: ExtraParameters = field(default_factory=ExtraParameters)

    ch: list[_ChData] = field(default_factory=list)

    def resize(self, n_channels: int):
        """
        Resize to n_channels.

        This method is required because this class is a class of lists,
        rather than a class used as member of a list in the parent class
        DgtzParams. In other words, the other members of DgtzParams are
        indexed like `params.x[ch].y`, while this like `params.x.y[ch]`.
        """
        self.ch = [self._ChData() for _ in range(n_channels)]

    @classmethod
    def from_raw(cls, raw: PHAParamsRaw):
        """Instantiate from raw data"""
        ch = [cls._ChData(
            raw.M[i],
            raw.m[i],
            raw.k[i],
            raw.ftd[i],
            raw.a[i],
            raw.b[i],
            raw.thr[i],
            raw.nsbl[i],
            raw.nspk[i],
            raw.pkho[i],
            raw.blho[i],
            raw.trgho[i],
            raw.dgain[i],
            raw.enf[i],
            raw.decimation[i],
            raw.enskim[i],
            raw.eskimlld[i],
            raw.eskimuld[i],
            raw.blrclip[i],
            raw.dcomp[i],
            raw.trapbsl[i],
            raw.pz_dac[i],
            raw.inh_length[i],
            ExtraParameters.from_raw(raw.X770_extraparameters[i]),
        ) for i in range(MAX_NUMCHB)]
        return cls(ch)

    def to_raw(self) -> PHAParamsRaw:
        """Convert to raw data"""
        return PHAParamsRaw(
            tuple(ch.m_ for ch in self.ch),
            tuple(ch.m for ch in self.ch),
            tuple(ch.k for ch in self.ch),
            tuple(ch.ftd for ch in self.ch),
            tuple(ch.a for ch in self.ch),
            tuple(ch.b for ch in self.ch),
            tuple(ch.thr for ch in self.ch),
            tuple(ch.nsbl for ch in self.ch),
            tuple(ch.nspk for ch in self.ch),
            tuple(ch.pkho for ch in self.ch),
            tuple(ch.blho for ch in self.ch),
            tuple(ch.trgho for ch in self.ch),
            tuple(ch.dgain for ch in self.ch),
            tuple(ch.enf for ch in self.ch),
            tuple(ch.decimation for ch in self.ch),
            tuple(ch.enskim for ch in self.ch),
            tuple(ch.eskimlld for ch in self.ch),
            tuple(ch.eskimuld for ch in self.ch),
            tuple(ch.blrclip for ch in self.ch),
            tuple(ch.dcomp for ch in self.ch),
            tuple(ch.trapbsl for ch in self.ch),
            tuple(ch.pz_dac for ch in self.ch),
            tuple(ch.inh_length for ch in self.ch),
            tuple(ch.x770_extraparameters.to_raw() for ch in self.ch),
        )


class WaveformParamsRaw(ct.Structure):
    """Raw view of ::CAENDPP_WaveformParams_t"""
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


@dataclass(slots=True)
class WaveformParams:
    """
    Binding of ::CAENDPP_WaveformParams_t
    """
    dual_trace_mode: int = 0
    vp1: VirtualProbe1 = VirtualProbe1.INPUT
    vp2: VirtualProbe2 = VirtualProbe2.NONE
    dp1: DigitalProbe1 = DigitalProbe1.TRIGGER
    dp2: DigitalProbe2 = DigitalProbe2.PEAKING
    record_length: int = 0
    pre_trigger: int = 0
    probe_trigger: ProbeTrigger = ProbeTrigger.MAIN_TRIG
    probe_self_trigger_val: int = 0

    @classmethod
    def from_raw(cls, raw: WaveformParamsRaw):
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

    def to_raw(self) -> WaveformParamsRaw:
        """Convert to raw data"""
        return WaveformParamsRaw(
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


class ListParamsRaw(ct.Structure):
    """Raw view of ::CAENDPP_ListParams_t"""
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


@dataclass(slots=True)
class ListParams:
    """
    Binding of ::CAENDPP_ListParams_t
    """
    enabled: bool = False
    save_mode: ListSaveMode = ListSaveMode.MEMORY
    file_name: str = 'py_dpplib_default.txt'
    max_buff_num_events: int = 0
    save_mask: DumpMask = DumpMask.TTT | DumpMask.ENERGY | DumpMask.EXTRAS
    enable_fakes: bool = False

    @classmethod
    def from_raw(cls, raw: ListParamsRaw):
        """Instantiate from raw data"""
        return cls(
            bool(raw.enabled),
            ListSaveMode(raw.saveMode),
            raw.fileName.decode('ascii'),
            raw.maxBuffNumEvents,
            DumpMask(raw.saveMask),
            bool(raw.enableFakes),
        )

    def to_raw(self) -> ListParamsRaw:
        """Convert to raw data"""
        return ListParamsRaw(
            self.enabled,
            self.save_mode,
            self.file_name.encode('ascii'),
            self.max_buff_num_events,
            self.save_mask,
            self.enable_fakes,
        )


class RunSpecsRaw(ct.Structure):
    """Raw view of ::CAENDPP_RunSpecs_t"""
    _fields_ = [
        ('RunName', ct.c_char * MAX_RUNNAME),
        ('RunDurationSec', ct.c_int32),
        ('PauseSec', ct.c_int32),
        ('CyclesCount', ct.c_int32),
        ('SaveLists', ct.c_uint8),
        ('GPSEnable', ct.c_uint8),
        ('ClearHistos', ct.c_uint8),
    ]


@dataclass(slots=True)
class RunSpecs:
    """
    Binding of ::CAENDPP_RunSpecs_t
    """
    run_name: str = 'py_dpplib_default'
    run_duration_sec: int = 0
    pause_sec: int = 0
    cycles_count: int = 1
    save_lists: bool = False
    gps_enable: bool = False
    clear_histos: bool = False

    @classmethod
    def from_raw(cls, raw: RunSpecsRaw):
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

    def to_raw(self) -> RunSpecsRaw:
        """Convert to raw data"""
        return RunSpecsRaw(
            self.run_name.encode('ascii'),
            self.run_duration_sec,
            self.pause_sec,
            self.cycles_count,
            self.save_lists,
            self.gps_enable,
            self.clear_histos,
        )


class CoincParamsRaw(ct.Structure):
    """Raw view of ::CAENDPP_CoincParams_t"""
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


@dataclass(slots=True)
class CoincParams:
    """
    Binding of ::CAENDPP_CoincParams_t
    """
    coinc_ch_mask: int = 0
    maj_level: int = 0
    trg_win: int = 0
    coinc_op: CoincOp = CoincOp.OR
    coinc_logic: CoincLogic = CoincLogic.NONE

    @classmethod
    def from_raw(cls, raw: CoincParamsRaw):
        """Instantiate from raw data"""
        return cls(
            raw.CoincChMask,
            raw.MajLevel,
            raw.TrgWin,
            CoincOp(raw.CoincOp),
            CoincLogic(raw.CoincLogic),
        )

    def to_raw(self) -> CoincParamsRaw:
        """Convert to raw data"""
        return CoincParamsRaw(
            self.coinc_ch_mask,
            self.maj_level,
            self.trg_win,
            self.coinc_op,
            self.coinc_logic,
        )


class GateParamsRaw(ct.Structure):
    """Raw view of ::CAENDPP_GateParams_t"""
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


@dataclass(slots=True)
class GateParams:
    """
    Binding of ::CAENDPP_GateParams_t
    """
    gate_enable: bool = False
    shape_time: int = 0
    polarity: PulsePolarity = PulsePolarity.POSITIVE
    gate_logic: ExtLogic = ExtLogic.VETO

    @classmethod
    def from_raw(cls, raw: GateParamsRaw):
        """Instantiate from raw data"""
        return cls(
            bool(raw.GateEnable),
            raw.ShapeTime,
            PulsePolarity(raw.Polarity),
            ExtLogic(raw.GateLogic),
        )

    def to_raw(self) -> GateParamsRaw:
        """Convert to raw data"""
        return GateParamsRaw(
            self.gate_enable,
            self.shape_time,
            self.polarity,
            self.gate_logic,
        )


class SpectrumControlRaw(ct.Structure):
    """Raw view of ::CAENDPP_SpectrumControl_t"""
    _fields_ = [
        ('SpectrumMode', ct.c_int),
        ('TimeScale', ct.c_uint32),
    ]


@unique
class SpectrumMode(IntEnum):
    """
    Binding of ::CAENDPP_SpectrumMode_t
    """
    ENERGY = 0
    TIME = 1


@dataclass(slots=True)
class SpectrumControl:
    """
    Binding of ::CAENDPP_SpectrumControl
    """
    spectrum_mode: SpectrumMode = SpectrumMode.ENERGY
    time_scale: int = 0

    @classmethod
    def from_raw(cls, raw: SpectrumControlRaw):
        """Instantiate from raw data"""
        return cls(SpectrumMode(raw.SpectrumMode), raw.TimeScale)

    def to_raw(self) -> SpectrumControlRaw:
        """Convert to raw data"""
        return SpectrumControlRaw(self.spectrum_mode, self.time_scale)


class TRResetRaw(ct.Structure):
    """Raw view of ::CAENDPP_TRReset_t"""
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


@dataclass(slots=True)
class TRReset:
    """
    Binding of ::CAENDPP_TRReset
    """
    enabled: bool = False
    reset_detection_mode: ResetDetectionMode = ResetDetectionMode.INTERNAL
    thrhold: int = 0
    reslenmin: int = 0
    reslength: int = 0

    @classmethod
    def from_raw(cls, raw: TRResetRaw):
        """Instantiate from raw data"""
        return cls(
            bool(raw.Enabled),
            ResetDetectionMode(raw.ResetDetectionMode),
            raw.thrhold,
            raw.reslenmin,
            raw.reslength,
        )

    def to_raw(self) -> TRResetRaw:
        """Convert to raw data"""
        return TRResetRaw(
            self.enabled,
            self.reset_detection_mode,
            self.thrhold,
            self.reslenmin,
            self.reslength,
        )


class MonOutParamsRaw(ct.Structure):
    """Raw view of ::CAENDPP_MonOutParams_t"""
    _fields_ = [
        ('channel', ct.c_int32),
        ('enabled', ct.c_int32),
        ('probe', ct.c_int),
    ]


@dataclass(frozen=True, slots=True)
class MonOutParams:
    """
    Binding of ::CAENDPP_MonOutParams_t
    """
    channel: int = 0
    enabled: bool = False
    probe: PHAMonOutProbe = PHAMonOutProbe.INPUT

    @classmethod
    def from_raw(cls, raw: MonOutParamsRaw):
        """Instantiate from raw data"""
        return cls(
            raw.channel,
            bool(raw.enabled),
            PHAMonOutProbe(raw.probe),
        )

    def to_raw(self) -> MonOutParamsRaw:
        """Convert to raw data"""
        return MonOutParamsRaw(
            self.channel,
            self.enabled,
            self.probe,
        )


class DgtzParamsRaw(ct.Structure):
    """Raw view of ::CAENDPP_DgtzParams_t"""
    _fields_ = [
        ('GWn', ct.c_int32),
        ('GWaddr', ct.c_uint32 * MAX_GW),
        ('GWdata', ct.c_uint32 * MAX_GW),
        ('GWmask', ct.c_uint32 * MAX_GW),
        ('ChannelMask', ct.c_int32),
        ('PulsePolarity', ct.c_int * MAX_NUMCHB),
        ('DCoffset', ct.c_int32 * MAX_NUMCHB),
        ('TempCorrParameters', TempCorrParamsRaw * MAX_NUMCHB),
        ('InputCoupling', ct.c_int * MAX_NUMCHB),
        ('EventAggr', ct.c_int32),
        ('DPPParams', PHAParamsRaw),
        ('IOlev', ct.c_int),
        ('WFParams', WaveformParamsRaw),
        ('ListParams', ListParamsRaw),
        ('RunSpecifications', RunSpecsRaw),
        ('CoincParams', CoincParamsRaw * MAX_NUMCHB_COINCIDENCE),  # Note: different size!
        ('GateParams', GateParamsRaw * MAX_NUMCHB),
        ('SpectrumControl', SpectrumControlRaw * MAX_NUMCHB),
        ('ResetDetector', TRResetRaw * MAX_NUMCHB),
        ('MonOutParams', MonOutParamsRaw),
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


@dataclass(slots=True)
class DgtzParams:
    """
    Binding of ::CAENDPP_DgtzParams_t
    """

    @dataclass(slots=True)
    class _ChData:
        pulse_polarity: PulsePolarity = PulsePolarity.POSITIVE
        dc_offset: int = 0
        temp_corr_parameters: TempCorrParams = field(default_factory=TempCorrParams)
        input_coupling: INCoupling = INCoupling.DC
        gate_params: GateParams = field(default_factory=GateParams)
        spectrum_control: SpectrumControl = field(default_factory=SpectrumControl)
        reset_detector: TRReset = field(default_factory=TRReset)

    gw_addr: list[int] = field(default_factory=list)
    gw_data: list[int] = field(default_factory=list)
    gw_mask: list[int] = field(default_factory=list)
    channel_mask: int = 0
    event_aggr: int = 0
    dpp_params: PHAParams = field(default_factory=PHAParams)
    iolev: IOLevel = IOLevel.NIM
    wf_params: WaveformParams = field(default_factory=WaveformParams)
    list_params: ListParams = field(default_factory=ListParams)
    run_specifications: RunSpecs = field(default_factory=RunSpecs)
    mon_out_params: MonOutParams = field(default_factory=MonOutParams)
    ch: list[_ChData] = field(default_factory=list)
    coinc_params: list[CoincParams] = field(default_factory=list)  # Not part of ch because it has a different size to support external channel

    def resize(self, n_channels: int):
        """Resize to n_channels"""
        self.ch = [self._ChData() for _ in range(n_channels)]
        self.dpp_params.resize(n_channels)  # Weird because it a class of lists rather than a list of classes
        self.coinc_params = [CoincParams() for _ in range(MAX_NUMCHB_COINCIDENCE)]  # Always this size to support external channel

    @classmethod
    def from_raw(cls, raw: DgtzParamsRaw):
        """Instantiate from raw data"""
        ch = [cls._ChData(
            PulsePolarity(raw.PulsePolarity[i]),
            raw.DCoffset[i],
            TempCorrParams.from_raw(raw.TempCorrParameters[i]),
            INCoupling(raw.InputCoupling[i]),
            GateParams.from_raw(raw.GateParams[i]),
            SpectrumControl.from_raw(raw.SpectrumControl[i]),
            TRReset.from_raw(raw.ResetDetector[i]),
        ) for i in range(MAX_NUMCHB)]
        return cls(
            raw.GWaddr[:raw.GWn],
            raw.GWdata[:raw.GWn],
            raw.GWmask[:raw.GWn],
            raw.ChannelMask,
            raw.EventAggr,
            PHAParams.from_raw(raw.DPPParams),
            IOLevel(raw.IOlev),
            WaveformParams.from_raw(raw.WFParams),
            ListParams.from_raw(raw.ListParams),
            RunSpecs.from_raw(raw.RunSpecifications),
            MonOutParams.from_raw(raw.MonOutParams),
            ch,
            list(map(CoincParams.from_raw, raw.CoincParams)),
        )

    def to_raw(self) -> DgtzParamsRaw:
        """Convert to raw data"""
        if not len(self.gw_addr) == len(self.gw_data) == len(self.gw_mask):
            raise ValueError('gw_addr, gw_data and gw_mask must have the same length.')
        return DgtzParamsRaw(
            len(self.gw_addr),
            tuple(self.gw_addr),
            tuple(self.gw_data),
            tuple(self.gw_mask),
            self.channel_mask,
            tuple(ch.pulse_polarity for ch in self.ch),
            tuple(ch.dc_offset for ch in self.ch),
            tuple(ch.temp_corr_parameters.to_raw() for ch in self.ch),
            tuple(ch.input_coupling for ch in self.ch),
            self.event_aggr,
            self.dpp_params.to_raw(),
            self.iolev,
            self.wf_params.to_raw(),
            self.list_params.to_raw(),
            self.run_specifications.to_raw(),
            tuple(par.to_raw() for par in self.coinc_params),
            tuple(ch.gate_params.to_raw() for ch in self.ch),
            tuple(ch.spectrum_control.to_raw() for ch in self.ch),
            tuple(ch.reset_detector.to_raw() for ch in self.ch),
            self.mon_out_params.to_raw(),
        )


class ListEventRaw(ct.Structure):
    """Raw view of ::CAENDPP_ListEvent_t"""
    _fields_ = [
        ('TimeTag', ct.c_uint64),
        ('Energy', ct.c_uint16),
        ('Extras', ct.c_uint16),
    ]


@dataclass(frozen=True, slots=True)
class ListEvent:
    """
    Binding of ::CAENDPP_ListEvent_t
    """
    time_tag: int
    energy: int
    extras: int

    @classmethod
    def from_raw(cls, raw: ListEventRaw):
        """Instantiate from raw data"""
        return cls(raw.TimeTag, raw.Energy, raw.Extras)


class StatisticsRaw(ct.Structure):
    """Raw view of ::statistics_t"""
    _fields_ = [
        ('ThroughputRate', ct.c_double),
        ('SaturationFlag', ct.c_uint32),
        ('SaturationPerc', ct.c_double),
        ('PulseDeadTime', ct.c_double),
        ('RealRate', ct.c_double),
        ('PeakingTime', ct.c_uint32),
    ]


@dataclass(frozen=True, slots=True)
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
    def from_raw(cls, raw: StatisticsRaw):
        """Instantiate from raw data"""
        return cls(
            raw.ThroughputRate,
            raw.SaturationFlag,
            raw.SaturationPerc,
            raw.PulseDeadTime,
            raw.RealRate,
            raw.PeakingTime,
        )


class DAQInfoRaw(ct.Structure):
    """Raw view of ::CAENDPP_DAQInfo_t"""
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


@dataclass(frozen=True, slots=True)
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
    def from_raw(cls, raw: DAQInfoRaw):
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


class HVChannelConfigRaw(ct.Structure):
    """Raw view of ::CAENDPP_HVChannelConfig_t"""
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


@dataclass(slots=True)
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
    def from_raw(cls, raw: HVChannelConfigRaw):
        """Instantiate from raw data"""
        return cls(
            raw.VSet,
            raw.ISet,
            raw.RampUp,
            raw.RampDown,
            raw.VMax,
            PWDownMode(raw.PWDownMode),
        )

    def to_raw(self) -> HVChannelConfigRaw:
        """Convert to raw data"""
        return HVChannelConfigRaw(
            self.v_set,
            self.i_set,
            self.ramp_up,
            self.ramp_down,
            self.v_max,
            self.pw_down_mode,
        )


@dataclass(frozen=True, slots=True)
class HVChannelMonitoring:
    """
    Return value for ::CAENDPP_ReadHVChannelMonitoring binding
    """
    v_mon: float
    i_mon: float


@dataclass(frozen=True, slots=True)
class HVChannelExternals:
    """
    Return value for ::CAENDPP_ReadHVChannelExternals binding
    """
    v_ext: float
    t_res: float


class EnumerationSingleDeviceRaw(ct.Structure):
    """Raw view of ::CAENDPP_EnumerationSingleDevice_t"""
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


@dataclass(frozen=True, slots=True)
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
    def from_raw(cls, raw: EnumerationSingleDeviceRaw):
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


class EnumeratedDevicesRaw(ct.Structure):
    """Raw view of ::CAENDPP_EnumeratedDevices_t"""
    _fields_ = [
        ('ddcount', ct.c_int),
        ('Device', EnumerationSingleDeviceRaw * 64),
    ]


@dataclass(frozen=True, slots=True)
class EnumeratedDevices:
    """
    Binding of ::CAENDPP_EnumeratedDevices_t
    """
    devices: tuple[EnumerationSingleDevice, ...]

    @classmethod
    def from_raw(cls, raw: EnumeratedDevicesRaw):
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


@dataclass(slots=True)
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


@dataclass(slots=True)
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
