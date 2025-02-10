__author__ = 'Giovanni Cerretani'
__copyright__ = 'Copyright (C) 2024 CAEN SpA'
__license__ = 'LGPL-3.0-or-later'
# SPDX-License-Identifier: LGPL-3.0-or-later

import ctypes as ct
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import IntEnum, unique
from typing import Any, Optional, TypeVar, Union

from caen_libs import error, _utils


# Constants from CAENDigitizerType.h
MAX_UINT16_CHANNEL_SIZE = 64
MAX_UINT8_CHANNEL_SIZE = 8
MAX_V1724DPP_CHANNEL_SIZE = 8
MAX_V1720DPP_CHANNEL_SIZE = 8
MAX_V1751DPP_CHANNEL_SIZE = 8
MAX_V1730DPP_CHANNEL_SIZE = 16
MAX_V1740DPP_CHANNEL_SIZE = 64
MAX_X740_GROUP_SIZE = 8
MAX_V1730_CHANNEL_SIZE = 16
MAX_ZLE_CHANNEL_SIZE = MAX_V1751DPP_CHANNEL_SIZE
MAX_X742_CHANNEL_SIZE = 9
MAX_X742_GROUP_SIZE = 4
MAX_X743_CHANNELS_X_GROUP = 2
MAX_V1743_GROUP_SIZE = 8
MAX_DT5743_GROUP_SIZE = 4
MAX_DPP_CI_CHANNEL_SIZE = MAX_V1720DPP_CHANNEL_SIZE
MAX_DPP_PSD_CHANNEL_SIZE = MAX_V1730DPP_CHANNEL_SIZE
MAX_DPP_PHA_CHANNEL_SIZE = MAX_V1730DPP_CHANNEL_SIZE
MAX_DPP_QDC_CHANNEL_SIZE = MAX_V1740DPP_CHANNEL_SIZE
MAX_DPP_CHANNEL_SIZE = MAX_DPP_PSD_CHANNEL_SIZE
MAX_LICENSE_DIGITS = 8
MAX_LICENSE_LENGTH = MAX_LICENSE_DIGITS * 2 + 1


@unique
class ConnectionType(IntEnum):
    """
    Binding of ::CAEN_DGTZ_ConnectionType
    """
    USB = 0
    OPTICAL_LINK = 1
    USB_A4818 = 5
    ETH_V4718 = 6
    USB_V4718 = 7


class _BoardInfoRaw(ct.Structure):
    _fields_ = [
        ('ModelName', ct.c_char * 12),
        ('Model', ct.c_uint32),
        ('Channels', ct.c_uint32),
        ('FormFactor', ct.c_uint32),
        ('FamilyCode', ct.c_uint32),
        ('ROC_FirmwareRel', ct.c_char * 20),
        ('AMC_FirmwareRel', ct.c_char * 40),
        ('SerialNumber', ct.c_uint32),
        ('MezzanineSerNum', (ct.c_char * 8) * 4),
        ('PCB_Revision', ct.c_uint32),
        ('ADC_NBits', ct.c_uint32),
        ('SAMCorrectionDataLoaded', ct.c_uint32),
        ('CommHandle', ct.c_int),
        ('VMEHandle', ct.c_int),
        ('License', ct.c_char * MAX_LICENSE_LENGTH),
    ]


class _EventInfoRaw(ct.Structure):
    _fields_ = [
        ('EventSize', ct.c_uint32),
        ('BoardId', ct.c_uint32),
        ('Pattern', ct.c_uint32),
        ('ChannelMask', ct.c_uint32),
        ('EventCounter', ct.c_uint32),
        ('TriggerTimeTag', ct.c_uint32),
    ]


@dataclass(frozen=True, **_utils.dataclass_slots)
class EventInfo:
    """
    Binding of ::CAEN_DGTZ_EventInfo_t
    """
    event_size: int
    board_id: int
    pattern: int
    channel_mask: int
    event_counter: int
    trigger_time_tag: int

    @classmethod
    def from_raw(cls, raw: _EventInfoRaw):
        """Instantiate from raw data"""
        return cls(
            raw.EventSize,
            raw.BoardId,
            raw.Pattern,
            raw.ChannelMask,
            raw.EventCounter,
            raw.TriggerTimeTag,
        )


class _Uint16EventRaw(ct.Structure):
    _fields_ = [
        ('ChSize', ct.c_uint32 * MAX_UINT16_CHANNEL_SIZE),
        ('DataChannel', ct.POINTER(ct.c_uint16) * MAX_UINT16_CHANNEL_SIZE),
    ]


class _Uint8EventRaw(ct.Structure):
    _fields_ = [
        ('ChSize', ct.c_uint32 * MAX_UINT8_CHANNEL_SIZE),
        ('DataChannel', ct.POINTER(ct.c_uint8) * MAX_UINT8_CHANNEL_SIZE),
    ]


class _X742GroupRaw(ct.Structure):
    _fields_ = [
        ('ChSize', ct.c_uint32 * MAX_X742_CHANNEL_SIZE),
        ('DataChannel', ct.POINTER(ct.c_float) * MAX_X742_CHANNEL_SIZE),
        ('TriggerTimeTag', ct.c_uint32),
        ('StartIndexCell', ct.c_uint16),
    ]


class _X742EventRaw(ct.Structure):
    _fields_ = [
        ('GrPresent', ct.c_uint8 * MAX_X742_GROUP_SIZE),
        ('DataGroup', ct.POINTER(_X742GroupRaw) * MAX_X742_GROUP_SIZE),
    ]


class _X743GroupRaw(ct.Structure):
    _fields_ = [
        ('ChSize', ct.c_uint32),
        ('DataChannel', ct.POINTER(ct.c_float) * MAX_X743_CHANNELS_X_GROUP),
        ('TriggerCount', ct.c_uint16 * MAX_X743_CHANNELS_X_GROUP),
        ('TimeCount', ct.c_uint16 * MAX_X743_CHANNELS_X_GROUP),
        ('EventId', ct.c_uint8),
        ('StartIndexCell', ct.c_uint16),
        ('TDC', ct.c_uint64),
        ('PosEdgeTimeStamp', ct.c_float),
        ('NegEdgeTimeStamp', ct.c_float),
        ('PeakIndex', ct.c_uint16),
        ('Peak', ct.c_float),
        ('Baseline', ct.c_float),
        ('Charge', ct.c_float),
    ]


class _X743EventRaw(ct.Structure):
    _fields_ = [
        ('GrPresent', ct.c_uint8 * MAX_V1743_GROUP_SIZE),
        ('DataGroup', ct.POINTER(_X743GroupRaw) * MAX_V1743_GROUP_SIZE),
    ]


class _DPPPHAEvtRaw(ct.Structure):
    _fields_ = [
        ('Format', ct.c_uint32),
        ('TimeTag', ct.c_uint64),
        ('Energy', ct.c_uint16),
        ('Extras', ct.c_int16),
        ('Waveforms', ct.POINTER(ct.c_uint32)),
        ('Extras2', ct.c_uint32),
    ]


class _DPPPSDEvtRaw(ct.Structure):
    _fields_ = [
        ('Format', ct.c_uint32),
        ('Format2', ct.c_uint32),
        ('TimeTag', ct.c_uint32),
        ('ChargeShort', ct.c_int16),
        ('ChargeLong', ct.c_int16),
        ('Baseline', ct.c_int16),
        ('Pur', ct.c_int16),
        ('Waveforms', ct.POINTER(ct.c_uint32)),
        ('Extras', ct.c_uint32),
    ]


class _DPPCIEventRaw(ct.Structure):
    _fields_ = [
        ('Format', ct.c_uint32),
        ('TimeTag', ct.c_uint32),
        ('Charge', ct.c_int16),
        ('Baseline', ct.c_int16),
        ('Waveforms', ct.POINTER(ct.c_uint32)),
    ]


class _DPPQDCEventRaw(ct.Structure):
    _fields_ = [
        ('isExtendedTimeStamp', ct.c_uint8),
        ('Format', ct.c_uint32),
        ('TimeTag', ct.c_uint64),
        ('Charge', ct.c_uint16),
        ('Baseline', ct.c_int16),
        ('Pur', ct.c_uint16),
        ('Overrange', ct.c_uint16),
        ('SubChannel', ct.c_uint16),
        ('Waveforms', ct.POINTER(ct.c_uint32)),
        ('Extras', ct.c_uint32),
    ]


class _751ZLEEventRaw(ct.Structure):
    _fields_ = [
        ('timeTag', ct.c_uint32),
        ('Baseline', ct.c_uint32),
        ('Waveforms', ct.POINTER(ct.c_uint32)),
    ]


class _730ZLEWaveformsRaw(ct.Structure):
    _fields_ = [
        ('TraceNumber', ct.c_uint32),
        ('Trace', ct.POINTER(ct.c_uint16)),
        ('TraceIndex', ct.POINTER(ct.c_uint32)),
    ]


class _730ZLEChannelRaw(ct.Structure):
    _fields_ = [
        ('fifo_full', ct.c_uint32),
        ('size_wrd', ct.c_uint32),
        ('Baseline', ct.c_uint32),
        ('DataPtr', ct.POINTER(ct.c_uint32)),
        ('Waveforms', ct.POINTER(_730ZLEWaveformsRaw)),
    ]


class _730ZLEEventRaw(ct.Structure):
    _fields_ = [
        ('size', ct.c_uint32),
        ('chmask', ct.c_uint16),
        ('tcounter', ct.c_uint32),
        ('timeStamp', ct.c_uint64),
        ('Channel', ct.POINTER(_730ZLEChannelRaw) * MAX_V1730_CHANNEL_SIZE),
    ]


class _730DAWWaveformsRaw(ct.Structure):
    _fields_ = [
        ('Trace', ct.POINTER(ct.c_uint16)),
    ]


class _730DAWChannelRaw(ct.Structure):
    _fields_ = [
        ('truncate', ct.c_uint32),
        ('EvType', ct.c_uint32),
        ('size', ct.c_uint32),
        ('timeStamp', ct.c_uint64),
        ('baseline', ct.c_uint16),
        ('DataPtr', ct.POINTER(ct.c_uint16)),
        ('Waveforms', ct.POINTER(_730DAWWaveformsRaw)),
    ]


class _730DAWEventRaw(ct.Structure):
    _fields_ = [
        ('size', ct.c_uint32),
        ('chmask', ct.c_uint16),
        ('tcounter', ct.c_uint32),
        ('timeStamp', ct.c_uint64),
        ('Channel', ct.POINTER(_730DAWChannelRaw) * MAX_V1730_CHANNEL_SIZE),
    ]


class _DPPX743EventRaw(ct.Structure):
    _fields_ = [
        ('Charge', ct.c_float),
        ('StartIndexCell', ct.c_int),
    ]


class _DPPPHAWaveformsRaw(ct.Structure):
    _fields_ = [
        ('Ns', ct.c_uint32),
        ('DualTrace', ct.c_uint8),
        ('VProbe1', ct.c_uint8),
        ('VProbe2', ct.c_uint8),
        ('VDProbe', ct.c_uint8),
        ('Trace1', ct.POINTER(ct.c_int16)),
        ('Trace2', ct.POINTER(ct.c_int16)),
        ('DTrace1', ct.POINTER(ct.c_uint8)),
        ('DTrace2', ct.POINTER(ct.c_uint8)),
    ]


class _DPPPSDWaveformsRaw(ct.Structure):
    _fields_ = [
        ('Ns', ct.c_uint32),
        ('dualTrace', ct.c_uint8),
        ('anlgProbe', ct.c_uint8),
        ('dgtProbe1', ct.c_uint8),
        ('dgtProbe2', ct.c_uint8),
        ('Trace1', ct.POINTER(ct.c_int16)),
        ('Trace2', ct.POINTER(ct.c_int16)),
        ('DTrace1', ct.POINTER(ct.c_uint8)),
        ('DTrace2', ct.POINTER(ct.c_uint8)),
        ('DTrace3', ct.POINTER(ct.c_uint8)),
        ('DTrace4', ct.POINTER(ct.c_uint8)),
    ]


class _751ZLEWaveformsRaw(ct.Structure):
    _fields_ = [
        ('Ns', ct.c_uint32),
        ('Trace1', ct.POINTER(ct.c_uint16)),
        ('Discarded', ct.POINTER(ct.c_uint8)),
    ]


_DPPCIWaveformsRaw = _DPPPSDWaveformsRaw


class _DPPQDCWaveformsRaw(ct.Structure):
    _fields_ = [
        ('Ns', ct.c_uint32),
        ('dualTrace', ct.c_uint8),
        ('anlgProbe', ct.c_uint8),
        ('dgtProbe1', ct.c_uint8),
        ('dgtProbe2', ct.c_uint8),
        ('Trace1', ct.POINTER(ct.c_uint16)),
        ('Trace2', ct.POINTER(ct.c_uint16)),
        ('DTrace1', ct.POINTER(ct.c_uint8)),
        ('DTrace2', ct.POINTER(ct.c_uint8)),
        ('DTrace3', ct.POINTER(ct.c_uint8)),
        ('DTrace4', ct.POINTER(ct.c_uint8)),
    ]


@unique
class EnaDis(IntEnum):
    """
    Binding of ::CAEN_DGTZ_EnaDis_t
    """
    ENABLE  = 1
    DISABLE = 0


@unique
class IRQMode(IntEnum):
    """
    Binding of ::CAEN_DGTZ_IRQMode_t
    """
    RORA = 0
    ROAK = 1


@unique
class TriggerMode(IntEnum):
    """
    Binding of ::CAEN_DGTZ_TriggerMode_t
    """
    DISABLED         = 0
    EXTOUT_ONLY      = 2
    ACQ_ONLY         = 1
    ACQ_AND_EXTOUT   = 3


@unique
class TriggerPolarity(IntEnum):
    """
    Binding of ::CAEN_DGTZ_TriggerPolarity_t
    """
    ON_RISING_EDGE  = 0
    ON_FALLING_EDGE = 1


@unique
class PulsePolarity(IntEnum):
    """
    Binding of ::CAEN_DGTZ_PulsePolarity_t
    """
    POSITIVE = 0
    NEGATIVE = 1


@unique
class ZSMode(IntEnum):
    """
    Binding of ::CAEN_DGTZ_ZS_Mode_t
    """
    NO  = 0
    INT = 1
    ZLE = 2
    AMP = 3


@unique
class ThresholdWeight(IntEnum):
    """
    Binding of ::CAEN_DGTZ_ThresholdWeight_t
    """
    FINE    = 0
    COARSE  = 1


@unique
class AcqMode(IntEnum):
    """
    Binding of ::CAEN_DGTZ_AcqMode_t
    """
    SW_CONTROLLED           = 0
    S_IN_CONTROLLED         = 1
    FIRST_TRG_CONTROLLED    = 2
    LVDS_CONTROLLED         = 3


@unique
class TriggerLogic(IntEnum):
    """
    Binding of ::CAEN_DGTZ_TriggerLogic_t
    """
    OR            = 0
    AND           = 1
    MAJORITY      = 2


@unique
class RunSyncMode(IntEnum):
    """
    Binding of ::CAEN_DGTZ_RunSyncMode_t
    """
    DISABLED                    = 0
    TRG_OUT_TRG_IN_DAISY_CHAIN  = 1
    TRG_OUT_SIN_DAISY_CHAIN     = 2
    SIN_FANOUT                  = 3
    GPIO_GPIO_DAISY_CHAIN       = 4


@unique
class AnalogMonitorOutputMode(IntEnum):
    """
    Binding of ::CAEN_DGTZ_AnalogMonitorOutputMode_t
    """
    TRIGGER_MAJORITY    = 0
    TEST                = 1
    ANALOG_INSPECTION   = 2
    BUFFER_OCCUPANCY    = 3
    VOLTAGE_LEVEL       = 4


@unique
class AnalogMonitorMagnify(IntEnum):
    """
    Binding of ::CAEN_DGTZ_AnalogMonitorMagnify_t
    """
    MAGNIFY_1X  = 0
    MAGNIFY_2X  = 1
    MAGNIFY_4X  = 2
    MAGNIFY_8X  = 3


@unique
class AnalogMonitorInspectorInverter(IntEnum):
    """
    Binding of ::CAEN_DGTZ_AnalogMonitorInspectorInverter_t
    """
    P_1X  = 0
    N_1X  = 1


@unique
class ReadMode(IntEnum):
    """
    Binding of ::CAEN_DGTZ_ReadMode_t
    """
    SLAVE_TERMINATED_READOUT_MBLT   = 0
    SLAVE_TERMINATED_READOUT_2eVME  = 1
    SLAVE_TERMINATED_READOUT_2eSST  = 2
    POLLING_MBLT                    = 3
    POLLING_2eVME                   = 4
    POLLING_2eSST                   = 5


@unique
class DPPFirmware(IntEnum):
    """
    Binding of ::CAEN_DGTZ_DPPFirmware_t
    """
    PHA = 0
    PSD = 1
    CI  = 2
    ZLE = 3
    QDC = 4
    DAW = 5
    NOT_DPP = -1


class _DPPPHAParamsRaw(ct.Structure):
    _fields_ = [
        ('M', ct.c_int * MAX_DPP_PHA_CHANNEL_SIZE),
        ('m', ct.c_int * MAX_DPP_PHA_CHANNEL_SIZE),
        ('k', ct.c_int * MAX_DPP_PHA_CHANNEL_SIZE),
        ('ftd', ct.c_int * MAX_DPP_PHA_CHANNEL_SIZE),
        ('a', ct.c_int * MAX_DPP_PHA_CHANNEL_SIZE),
        ('b', ct.c_int * MAX_DPP_PHA_CHANNEL_SIZE),
        ('thr', ct.c_int * MAX_DPP_PHA_CHANNEL_SIZE),
        ('nsbl', ct.c_int * MAX_DPP_PHA_CHANNEL_SIZE),
        ('nspk', ct.c_int * MAX_DPP_PHA_CHANNEL_SIZE),
        ('pkho', ct.c_int * MAX_DPP_PHA_CHANNEL_SIZE),
        ('blho', ct.c_int * MAX_DPP_PHA_CHANNEL_SIZE),
        ('otrej', ct.c_int * MAX_DPP_PHA_CHANNEL_SIZE),
        ('trgho', ct.c_int * MAX_DPP_PHA_CHANNEL_SIZE),
        ('twwdt', ct.c_int * MAX_DPP_PHA_CHANNEL_SIZE),
        ('dgain', ct.c_int * MAX_DPP_PHA_CHANNEL_SIZE),
        ('enf', ct.c_float * MAX_DPP_PHA_CHANNEL_SIZE),
        ('decimation', ct.c_int * MAX_DPP_PHA_CHANNEL_SIZE),
        ('enskim', ct.c_int * MAX_DPP_PHA_CHANNEL_SIZE),
        ('eskimlld', ct.c_int * MAX_DPP_PHA_CHANNEL_SIZE),
        ('eskimuld', ct.c_int * MAX_DPP_PHA_CHANNEL_SIZE),
        ('blrclip', ct.c_int * MAX_DPP_PHA_CHANNEL_SIZE),
        ('dcomp', ct.c_int * MAX_DPP_PHA_CHANNEL_SIZE),
        ('trapbsl', ct.c_int * MAX_DPP_PHA_CHANNEL_SIZE),
    ]


class _DPPPSDParamsRaw(ct.Structure):
    _fields_ = [
        ('blthr', ct.c_int),
        ('bltmo', ct.c_int),
        ('trgho', ct.c_int),
        ('thr', ct.c_int * MAX_DPP_PSD_CHANNEL_SIZE),
        ('selft', ct.c_int * MAX_DPP_PSD_CHANNEL_SIZE),
        ('csens', ct.c_int * MAX_DPP_PSD_CHANNEL_SIZE),
        ('sgate', ct.c_int * MAX_DPP_PSD_CHANNEL_SIZE),
        ('lgate', ct.c_int * MAX_DPP_PSD_CHANNEL_SIZE),
        ('pgate', ct.c_int * MAX_DPP_PSD_CHANNEL_SIZE),
        ('tvaw', ct.c_int * MAX_DPP_PSD_CHANNEL_SIZE),
        ('nsbl', ct.c_int * MAX_DPP_PSD_CHANNEL_SIZE),
        ('discr', ct.c_int * MAX_DPP_PSD_CHANNEL_SIZE),
        ('cfdf', ct.c_int * MAX_DPP_PSD_CHANNEL_SIZE),
        ('cfdd', ct.c_int * MAX_DPP_PSD_CHANNEL_SIZE),
        ('trgc', ct.POINTER(ct.c_int) * MAX_DPP_PSD_CHANNEL_SIZE),
        ('purh', ct.c_int),
        ('purgap', ct.c_int),
    ]


class _DPPCIParamsRaw(ct.Structure):
    _fields_ = [
        ('purgap', ct.c_int),
        ('purh', ct.c_int),
        ('blthr', ct.c_int),
        ('bltmo', ct.c_int),
        ('trgho', ct.c_int),
        ('thr', ct.c_int * MAX_DPP_CI_CHANNEL_SIZE),
        ('selft', ct.c_int * MAX_DPP_CI_CHANNEL_SIZE),
        ('csens', ct.c_int * MAX_DPP_CI_CHANNEL_SIZE),
        ('gate', ct.c_int * MAX_DPP_CI_CHANNEL_SIZE),
        ('pgate', ct.c_int * MAX_DPP_CI_CHANNEL_SIZE),
        ('tvaw', ct.c_int * MAX_DPP_CI_CHANNEL_SIZE),
        ('nsbl', ct.c_int * MAX_DPP_CI_CHANNEL_SIZE),
        ('trgc', ct.POINTER(ct.c_int) * MAX_DPP_CI_CHANNEL_SIZE),
    ]


class _751ZLEParamsRaw(ct.Structure):
    _fields_ = [
        ('NSampBck', ct.c_int * MAX_ZLE_CHANNEL_SIZE),
        ('NSampAhe', ct.c_int * MAX_ZLE_CHANNEL_SIZE),
        ('ZleUppThr', ct.c_int * MAX_ZLE_CHANNEL_SIZE),
        ('ZleUndThr', ct.c_int * MAX_ZLE_CHANNEL_SIZE),
        ('selNumSampBsl', ct.c_int * MAX_ZLE_CHANNEL_SIZE),
        ('bslThrshld', ct.c_int * MAX_ZLE_CHANNEL_SIZE),
        ('bslTimeOut', ct.c_int * MAX_ZLE_CHANNEL_SIZE),
        ('preTrgg', ct.c_int),
    ]


class _DPPQDCParamsRaw(ct.Structure):
    _fields_ = [
        ('trgho', ct.c_int * MAX_DPP_QDC_CHANNEL_SIZE),
        ('GateWidth', ct.c_int * MAX_DPP_QDC_CHANNEL_SIZE),
        ('PreGate', ct.c_int * MAX_DPP_QDC_CHANNEL_SIZE),
        ('FixedBaseline', ct.c_int * MAX_DPP_QDC_CHANNEL_SIZE),
        ('DisTrigHist', ct.c_int * MAX_DPP_QDC_CHANNEL_SIZE),
        ('DisSelfTrigger', ct.c_int * MAX_DPP_QDC_CHANNEL_SIZE),
        ('BaselineMode', ct.c_int * MAX_DPP_QDC_CHANNEL_SIZE),
        ('TrgMode', ct.c_int * MAX_DPP_QDC_CHANNEL_SIZE),
        ('ChargeSensitivity', ct.c_int * MAX_DPP_QDC_CHANNEL_SIZE),
        ('PulsePol', ct.c_int * MAX_DPP_QDC_CHANNEL_SIZE),
        ('EnChargePed', ct.c_int * MAX_DPP_QDC_CHANNEL_SIZE),
        ('TestPulsesRate', ct.c_int * MAX_DPP_QDC_CHANNEL_SIZE),
        ('EnTestPulses', ct.c_int * MAX_DPP_QDC_CHANNEL_SIZE),
        ('InputSmoothing', ct.c_int * MAX_DPP_QDC_CHANNEL_SIZE),
        ('EnableExtendedTimeStamp', ct.c_int),
    ]


class _DRS4CorrectionRaw(ct.Structure):
    _fields_ = [
        ('cell', (ct.c_int16 * 1024) * MAX_X742_CHANNEL_SIZE),
        ('nsample', (ct.c_int8 * 1024) * MAX_X742_CHANNEL_SIZE),
        ('time', ct.c_float * 1024),
    ]


@unique
class DPPSaveParam(IntEnum):
    """
    Binding of ::CAEN_DGTZ_DPP_SaveParam_t
    """
    ENERGY_ONLY     = 0
    TIME_ONLY       = 1
    ENERGY_AND_TIME = 2
    CHARGE_AND_TIME = 4
    NONE            = 3


@unique
class DPPTriggerMode(IntEnum):
    """
    Binding of ::CAEN_DGTZ_DPP_TriggerMode_t
    """
    NORMAL      = 0
    COINCIDENCE = 1


@unique
class IOLevel(IntEnum):
    """
    Binding of ::CAEN_DGTZ_IOLevel_t
    """
    NIM = 0
    TTL = 1


@unique
class DRS4Frequency(IntEnum):
    """
    Binding of ::CAEN_DGTZ_DRS4Frequency_t
    """
    F_5GHz  = 0
    F_2_5GHz  = 1
    F_1GHz  = 2
    F_750MHz  = 3


@unique
class OutputSignalMode(IntEnum):
    """
    Binding of ::CAEN_DGTZ_OutputSignalMode_t
    """
    TRIGGER                  = 0
    FASTTRG_ALL              = 1
    FASTTRG_ACCEPTED         = 2
    BUSY                     = 3
    CLK_OUT                  = 4
    RUN                      = 5
    TRGPULSE                 = 6
    OVERTHRESHOLD            = 7


@unique
class SAMCorrectionLevel(IntEnum):
    """
    Binding of ::CAEN_DGTZ_SAM_CORRECTION_LEVEL_t
    """
    DISABLED        = 0
    PEDESTAL_ONLY   = 1
    INL             = 2
    ALL             = 3


@unique
class SAMPulseSourceType(IntEnum):
    """
    Binding of ::CAEN_DGTZ_SAMPulseSourceType_t
    """
    SOFTWARE    = 0
    CONT        = 1


@unique
class SAMFrequency(IntEnum):
    """
    Binding of ::CAEN_DGTZ_SAMFrequency_t
    """
    F_3_2GHz  = 0
    F_1_6GHz  = 1
    F_800MHz  = 2
    F_400MHz  = 3


class Error(error.Error):
    """
    Raised when a wrapped C API function returns negative values.
    """

    @unique
    class Code(IntEnum):
        """
        Binding of ::CAEN_DGTZ_ErrorCode
        """
        SUCCESS                         = 0
        COMM_ERROR                      = -1
        GENERIC_ERROR                   = -2
        INVALID_PARAM                   = -3
        INVALID_LINK_TYPE               = -4
        INVALID_HANDLE                  = -5
        MAX_DEVICES_ERROR               = -6
        BAD_BOARD_TYPE                  = -7
        BAD_INTERRUPT_LEV               = -8
        BAD_EVENT_NUMBER                = -9
        READ_DEVICE_REGISTER_FAIL       = -10
        WRITE_DEVICE_REGISTER_FAIL      = -11
        INVALID_CHANNEL_NUMBER          = -13
        CHANNEL_BUSY                    = -14
        FPIO_MODE_INVALID               = -15
        WRONG_ACQ_MODE                  = -16
        FUNCTION_NOT_ALLOWED            = -17
        TIMEOUT                         = -18
        INVALID_BUFFER                  = -19
        EVENT_NOT_FOUND                 = -20
        INVALID_EVENT                   = -21
        OUT_OF_MEMORY                   = -22
        CALIBRATION_ERROR               = -23
        DIGITIZER_NOT_FOUND             = -24
        DIGITIZER_ALREADY_OPEN          = -25
        DIGITIZER_NOT_READY             = -26
        INTERRUPT_NOT_CONFIGURED        = -27
        DIGITIZER_MEMORY_CORRUPTED      = -28
        DPP_FIRMWARE_NOT_SUPPORTED      = -29
        INVALID_LICENSE                 = -30
        INVALID_DIGITIZER_STATUS        = -31
        UNSUPPORTED_TRACE               = -32
        INVALID_PROBE                   = -33
        UNSUPPORTED_BASE_ADDRESS        = -34
        NOT_YET_IMPLEMENTED             = -99

    code: Code

    def __init__(self, message: str, res: int, func: str) -> None:
        self.code = Error.Code(res)
        super().__init__(message, self.code.name, func)


# For backward compatibility. Deprecated.
ErrorCode = Error.Code


# Utility definitions
_c_char_p = ct.POINTER(ct.c_char)  # ct.c_char_p is not fine due to its own memory management
_c_char_p_p = ct.POINTER(_c_char_p)
_c_int_p = ct.POINTER(ct.c_int)
_c_uint8_p = ct.POINTER(ct.c_uint8)
_c_uint16_p = ct.POINTER(ct.c_uint16)
_c_int32_p = ct.POINTER(ct.c_int32)
_c_uint32_p = ct.POINTER(ct.c_uint32)
_c_void_p_p = ct.POINTER(ct.c_void_p)
_board_info_p = ct.POINTER(_BoardInfoRaw)
_event_info_p = ct.POINTER(_EventInfoRaw)


class _Lib(_utils.Lib):

    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.__load_api()

    def __load_api(self) -> None:
        # Load API not related to devices
        self.__sw_release = self.__get('SWRelease', ct.c_char_p)
        self.free_readout_buffer = self.__get('FreeReadoutBuffer', _c_char_p_p)
        self.__get_dpp_virtual_probe_name = self.__get('GetDPP_VirtualProbeName', ct.c_int, _c_char_p)

        # Load API
        self.open_digitizer = self.__get('OpenDigitizer', ct.c_int, ct.c_int, ct.c_int, ct.c_uint32, _c_int_p)
        self.open_digitizer2 = self.__get('OpenDigitizer2', ct.c_int, ct.c_void_p, ct.c_int, ct.c_uint32, _c_int_p)
        self.close_digitizer = self.__get('CloseDigitizer', ct.c_int)
        self.write_register = self.__get('WriteRegister', ct.c_int, ct.c_uint32, ct.c_uint32)
        self.read_register = self.__get('ReadRegister', ct.c_int, ct.c_uint32, ct.c_uint16)
        self.get_info = self.__get('GetInfo', ct.c_int, _board_info_p)
        self.reset = self.__get('Reset', ct.c_int)
        self.clear_data = self.__get('ClearData', ct.c_int)
        self.send_sw_trigger = self.__get('SendSWtrigger', ct.c_int)
        self.sw_start_acquisition = self.__get('SWStartAcquisition', ct.c_int)
        self.sw_stop_acquisition = self.__get('SWStopAcquisition', ct.c_int)
        self.set_interrupt_config = self.__get('SetInterruptConfig', ct.c_int, ct.c_int, ct.c_uint8, ct.c_uint32, ct.c_uint16, ct.c_int)
        self.get_interrupt_config = self.__get('GetInterruptConfig', ct.c_int, _c_int_p, _c_uint8_p, _c_uint32_p, _c_uint16_p, _c_int_p)
        self.irq_wait = self.__get('IRQWait', ct.c_int, ct.c_uint32)
        self.set_des_mode = self.__get('SetDESMode', ct.c_int, ct.c_int)
        self.get_des_mode = self.__get('GetDESMode', ct.c_int, _c_int_p)
        self.set_record_length = self.__get('SetRecordLength', ct.c_int, ct.c_uint32, variadic=True)
        self.get_record_length = self.__get('GetRecordLength', ct.c_int, _c_uint32_p, variadic=True)
        self.set_channel_enable_mask = self.__get('SetChannelEnableMask', ct.c_int, ct.c_uint32)
        self.get_channel_enable_mask = self.__get('GetChannelEnableMask', ct.c_int, _c_uint32_p)
        self.set_group_enable_mask = self.__get('SetGroupEnableMask', ct.c_int, ct.c_uint32)
        self.get_group_enable_mask = self.__get('GetGroupEnableMask', ct.c_int, _c_uint32_p)
        self.set_sw_trigger_mode = self.__get('SetSWTriggerMode', ct.c_int, ct.c_int)
        self.get_sw_trigger_mode = self.__get('GetSWTriggerMode', ct.c_int, _c_int_p)
        self.set_ext_trigger_input_mode = self.__get('SetExtTriggerInputMode', ct.c_int, ct.c_int)
        self.get_ext_trigger_input_mode = self.__get('GetExtTriggerInputMode', ct.c_int, _c_int_p)
        self.set_channel_self_trigger = self.__get('SetChannelSelfTrigger', ct.c_int, ct.c_int, ct.c_uint32)
        self.get_channel_self_trigger = self.__get('GetChannelSelfTrigger', ct.c_int, ct.c_uint32, _c_int_p)
        self.set_group_self_trigger = self.__get('SetGroupSelfTrigger', ct.c_int, ct.c_int, ct.c_uint32)
        self.get_group_self_trigger = self.__get('GetGroupSelfTrigger', ct.c_int, ct.c_uint32, _c_int_p)
        self.set_post_trigger_size = self.__get('SetPostTriggerSize', ct.c_int, ct.c_uint32)
        self.get_post_trigger_size = self.__get('GetPostTriggerSize', ct.c_int, _c_uint32_p)
        self.set_dpp_pre_trigger_size = self.__get('SetDPPPreTriggerSize', ct.c_int, ct.c_int, ct.c_uint32)
        self.get_dpp_pre_trigger_size = self.__get('GetDPPPreTriggerSize', ct.c_int, ct.c_int, _c_uint32_p)
        self.set_channel_dc_offset = self.__get('SetChannelDCOffset', ct.c_int, ct.c_uint32, ct.c_uint32)
        self.get_channel_dc_offset = self.__get('GetChannelDCOffset', ct.c_int, ct.c_uint32, _c_uint32_p)
        self.set_group_dc_offset = self.__get('SetGroupDCOffset', ct.c_int, ct.c_uint32, ct.c_uint32)
        self.get_group_dc_offset = self.__get('GetGroupDCOffset', ct.c_int, ct.c_uint32, _c_uint32_p)
        self.set_channel_trigger_threshold = self.__get('SetChannelTriggerThreshold', ct.c_int, ct.c_uint32, ct.c_uint32)
        self.get_channel_trigger_threshold = self.__get('GetChannelTriggerThreshold', ct.c_int, ct.c_uint32, _c_uint32_p)
        self.set_channel_pulse_polarity = self.__get('SetChannelPulsePolarity', ct.c_int, ct.c_uint32, ct.c_int)
        self.get_channel_pulse_polarity = self.__get('GetChannelPulsePolarity', ct.c_int, ct.c_uint32, _c_int_p)
        self.set_group_trigger_threshold = self.__get('SetGroupTriggerThreshold', ct.c_int, ct.c_uint32, ct.c_uint32)
        self.get_group_trigger_threshold = self.__get('GetGroupTriggerThreshold', ct.c_int, ct.c_uint32, _c_uint32_p)
        self.set_zero_suppression_mode = self.__get('SetZeroSuppressionMode', ct.c_int, ct.c_int)
        self.get_zero_suppression_mode = self.__get('GetZeroSuppressionMode', ct.c_int, _c_int_p)
        self.set_channel_zs_params = self.__get('SetChannelZSParams', ct.c_int, ct.c_uint32, ct.c_int, ct.c_int32, ct.c_int32)
        self.get_channel_zs_params = self.__get('GetChannelZSParams', ct.c_int, ct.c_uint32, _c_int_p, _c_int32_p, _c_int32_p)
        self.set_acquisition_mode = self.__get('SetAcquisitionMode', ct.c_int, ct.c_int)
        self.get_acquisition_mode = self.__get('GetAcquisitionMode', ct.c_int, _c_int_p)
        self.set_run_synchronization_mode = self.__get('SetRunSynchronizationMode', ct.c_int, ct.c_int)
        self.get_run_synchronization_mode = self.__get('GetRunSynchronizationMode', ct.c_int, _c_int_p)
        self.set_analog_mon_output = self.__get('SetAnalogMonOutput', ct.c_int, ct.c_int)
        self.get_analog_mon_output = self.__get('GetAnalogMonOutput', ct.c_int, _c_int_p)
        self.set_analog_inspection_mon_params = self.__get('SetAnalogInspectionMonParams', ct.c_int, ct.c_uint32, ct.c_uint32, ct.c_int, ct.c_int)
        self.get_analog_inspection_mon_params = self.__get('GetAnalogInspectionMonParams', ct.c_int, _c_uint32_p, _c_uint32_p, _c_int_p, _c_int_p)
        self.disable_event_aligned_readout = self.__get('DisableEventAlignedReadout', ct.c_int)
        self.set_event_packaging = self.__get('SetEventPackaging', ct.c_int, ct.c_int)
        self.get_event_packaging = self.__get('GetEventPackaging', ct.c_int, _c_int_p)
        self.set_max_num_aggregates_blt = self.__get('SetMaxNumAggregatesBLT', ct.c_int, ct.c_uint32)
        self.get_max_num_aggregates_blt = self.__get('GetMaxNumAggregatesBLT', ct.c_int, _c_uint32_p)
        self.set_max_num_events_blt = self.__get('SetMaxNumEventsBLT', ct.c_int, ct.c_uint32)
        self.get_max_num_events_blt = self.__get('GetMaxNumEventsBLT', ct.c_int, _c_uint32_p)
        self.malloc_readout_buffer = self.__get('MallocReadoutBuffer', ct.c_int, _c_char_p_p, _c_uint32_p)
        self.read_data = self.__get('ReadData', ct.c_int, ct.c_int, _c_char_p, _c_uint32_p)
        self.get_num_events = self.__get('GetNumEvents', ct.c_int, _c_char_p, ct.c_uint32, _c_uint32_p)
        self.get_event_info = self.__get('GetEventInfo', ct.c_int, _c_char_p, ct.c_uint32, ct.c_int32, _event_info_p, _c_char_p_p)
        self.decode_event = self.__get('DecodeEvent', ct.c_int, _c_char_p, _c_void_p_p)
        self.free_event = self.__get('FreeEvent', ct.c_int, _c_void_p_p)
        self.get_dpp_events = self.__get('GetDPPEvents', ct.c_int, _c_char_p, ct.c_uint32, _c_void_p_p, _c_uint32_p)
        self.malloc_dpp_events = self.__get('MallocDPPEvents', ct.c_int, _c_void_p_p, _c_uint32_p)
        self.free_dpp_events = self.__get('FreeDPPEvents', ct.c_int, _c_void_p_p)
        self.malloc_dpp_waveforms = self.__get('MallocDPPWaveforms', ct.c_int, _c_void_p_p, _c_uint32_p)
        self.free_dpp_waveforms = self.__get('FreeDPPWaveforms', ct.c_int, ct.c_void_p)
        self.decode_dpp_waveforms = self.__get('DecodeDPPWaveforms', ct.c_int, ct.c_void_p, ct.c_void_p)
        self.set_num_events_per_aggregate = self.__get('SetNumEventsPerAggregate', ct.c_int, ct.c_uint32, ct.c_int, variadic=True)
        self.get_num_events_per_aggregate = self.__get('GetNumEventsPerAggregate', ct.c_int, _c_uint32_p, ct.c_int, variadic=True)
        self.set_dpp_event_aggregation = self.__get('SetDPPEventAggregation', ct.c_int, ct.c_int, ct.c_int)
        self.set_dpp_parameters = self.__get('SetDPPParameters', ct.c_int, ct.c_uint32, ct.c_void_p)
        self.set_dpp_acquisition_mode = self.__get('SetDPPAcquisitionMode', ct.c_int, ct.c_int, ct.c_int)
        self.get_dpp_acquisition_mode = self.__get('GetDPPAcquisitionMode', ct.c_int, _c_int_p, _c_int_p)
        self.set_dpp_trigger_mode = self.__get('SetDPPTriggerMode', ct.c_int, ct.c_int)
        self.get_dpp_trigger_mode = self.__get('GetDPPTriggerMode', ct.c_int, _c_int_p)
        self.set_dpp_virtual_probe = self.__get('SetDPP_VirtualProbe', ct.c_int, ct.c_int, ct.c_int)
        self.get_dpp_virtual_probe = self.__get('GetDPP_VirtualProbe', ct.c_int, ct.c_int, _c_int_p)
        self.get_dpp_supported_virtual_probes = self.__get('GetDPP_SupportedVirtualProbes', ct.c_int, ct.c_int, _c_int_p, _c_int_p)
        self.allocate_event = self.__get('AllocateEvent', ct.c_int, _c_void_p_p)
        self.set_io_level = self.__get('SetIOLevel', ct.c_int)
        self.get_io_level = self.__get('GetIOLevel', _c_int_p)
        self.set_trigger_polarity = self.__get('SetTriggerPolarity', ct.c_int, ct.c_uint32, ct.c_int)
        self.get_trigger_polarity = self.__get('GetTriggerPolarity', ct.c_int, ct.c_uint32, _c_int_p)
        self.rearm_interrupt = self.__get('RearmInterrupt', ct.c_int)
        self.set_drs4_sampling_frequency = self.__get('SetDRS4SamplingFrequency', ct.c_int, ct.c_int)
        self.get_drs4_sampling_frequency = self.__get('GetDRS4SamplingFrequency', ct.c_int, _c_int_p)
        self.set_output_signal_mode = self.__get('SetOutputSignalMode', ct.c_int, ct.c_int)
        self.get_output_signal_mode = self.__get('GetOutputSignalMode', ct.c_int, _c_int_p)
        self.set_group_fast_trigger_threshold = self.__get('SetGroupFastTriggerThreshold', ct.c_int, ct.c_uint32, ct.c_uint32)
        self.get_group_fast_trigger_threshold = self.__get('GetGroupFastTriggerThreshold', ct.c_int, ct.c_uint32, _c_uint32_p)
        self.set_group_fast_trigger_dc_offset = self.__get('SetGroupFastTriggerDCOffset', ct.c_int, ct.c_uint32, ct.c_uint32)
        self.get_group_fast_trigger_dc_offset = self.__get('GetGroupFastTriggerDCOffset', ct.c_int, ct.c_uint32, _c_uint32_p)
        self.set_fast_trigger_digitizing = self.__get('SetFastTriggerDigitizing', ct.c_int, ct.c_int)
        self.get_fast_trigger_digitizing = self.__get('GetFastTriggerDigitizing', ct.c_int, _c_int_p)
        self.set_fast_trigger_mode = self.__get('SetFastTriggerMode', ct.c_int, ct.c_int)
        self.get_fast_trigger_mode = self.__get('GetFastTriggerMode', ct.c_int, _c_int_p)
        self.load_drs4_correction_data = self.__get('LoadDRS4CorrectionData', ct.c_int, ct.c_int)
        self.get_correction_tables = self.__get('GetCorrectionTables', ct.c_int, ct.c_int, ct.c_void_p)
        self.enable_drs4_correction = self.__get('EnableDRS4Correction', ct.c_int)
        self.disable_drs4_correction = self.__get('DisableDRS4Correction', ct.c_int)
        self.decode_zle_waveforms = self.__get('DecodeZLEWaveforms', ct.c_int, ct.c_void_p, ct.c_void_p)
        self.free_zle_waveforms = self.__get('FreeZLEWaveforms', ct.c_int, ct.c_void_p)
        self.malloc_zle_waveforms = self.__get('MallocZLEWaveforms', ct.c_int, _c_void_p_p, _c_uint32_p)
        self.free_zle_events = self.__get('FreeZLEEvents', ct.c_int, _c_void_p_p)
        self.malloc_zle_events = self.__get('MallocZLEEvents', ct.c_int, _c_void_p_p, _c_uint32_p)
        self.get_zle_events = self.__get('GetZLEEvents', ct.c_int, _c_char_p, ct.c_uint32, _c_void_p_p, _c_uint32_p)
        self.set_zle_parameters = self.__get('SetZLEParameters', ct.c_int, ct.c_uint32, ct.c_void_p)
        self.get_sam_correction_level = self.__get('GetSAMCorrectionLevel', ct.c_int, _c_int_p)
        self.set_sam_correction_level = self.__get('SetSAMCorrectionLevel', ct.c_int, ct.c_int)
        self.enable_sam_pulse_gen = self.__get('EnableSAMPulseGen', ct.c_int, ct.c_int, ct.c_ushort, ct.c_int)
        self.disable_sam_pulse_gen = self.__get('DisableSAMPulseGen', ct.c_int, ct.c_int)
        self.set_sam_post_trigger_size = self.__get('SetSAMPostTriggerSize', ct.c_int, ct.c_int, ct.c_uint8)
        self.get_sam_post_trigger_size = self.__get('GetSAMPostTriggerSize', ct.c_int, ct.c_int, _c_uint32_p)
        self.set_sam_sampling_frequency = self.__get('SetSAMSamplingFrequency', ct.c_int, ct.c_int)
        self.get_sam_sampling_frequency = self.__get('GetSAMSamplingFrequency', ct.c_int, _c_int_p)
        self.read_eeprom = self.__get('Read_EEPROM', ct.c_int, ct.c_int, ct.c_ushort, ct.c_int, _c_uint8_p, private=True)
        self.write_eeprom = self.__get('Write_EEPROM', ct.c_int, ct.c_int, ct.c_ushort, ct.c_int, ct.c_void_p, private=True)
        self.load_sam_correction_data = self.__get('LoadSAMCorrectionData', ct.c_int)
        self.trigger_threshold = self.__get('TriggerThreshold', ct.c_int, ct.c_int, private=True)
        self.send_sam_pulse = self.__get('SendSAMPulse', ct.c_int)
        self.set_sam_acquisition_mode = self.__get('SetSAMAcquisitionMode', ct.c_int, ct.c_int)
        self.get_sam_acquisition_mode = self.__get('GetSAMAcquisitionMode', ct.c_int, _c_int_p)
        self.set_trigger_logic = self.__get('SetTriggerLogic', ct.c_int, ct.c_int, ct.c_uint32)
        self.get_trigger_logic = self.__get('GetTriggerLogic', ct.c_int, _c_int_p, _c_uint32_p)
        self.get_channel_pair_trigger_logic = self.__get('GetChannelPairTriggerLogic', ct.c_int, ct.c_uint32, ct.c_uint32, _c_int_p, _c_uint16_p)
        self.set_channel_pair_trigger_logic = self.__get('SetChannelPairTriggerLogic', ct.c_int, ct.c_uint32, ct.c_uint32, ct.c_int, ct.c_uint16)
        self.set_decimation_factor = self.__get('SetDecimationFactor', ct.c_int, ct.c_uint16)
        self.get_decimation_factor = self.__get('GetDecimationFactor', ct.c_int, _c_uint16_p)
        self.set_sam_trigger_count_veto_param = self.__get('SetSAMTriggerCountVetoParam', ct.c_int, ct.c_int, ct.c_int, ct.c_uint32)
        self.get_sam_trigger_count_veto_param = self.__get('GetSAMTriggerCountVetoParam', ct.c_int, ct.c_int, _c_int_p, _c_uint32_p)
        self.set_trigger_in_as_gate = self.__get('SetTriggerInAsGate', ct.c_int, ct.c_int)
        self.calibrate = self.__get('Calibrate', ct.c_int)
        self.read_temperature = self.__get('ReadTemperature', ct.c_int, ct.c_int32, _c_uint32_p)
        self.get_dpp_firmware_type = self.__get('GetDPPFirmwareType', ct.c_int, _c_int_p)

        # Load API related to CAENVME wrappers
        self.vme_irq_wait = self.__get('VMEIRQWait', ct.c_int, ct.c_int, ct.c_int, ct.c_uint8, ct.c_uint32, _c_int_p)
        self.vme_irq_check = self.__get('VMEIRQCheck', ct.c_int, _c_uint8_p)
        self.vme_iack_cycle = self.__get('VMEIACKCycle', ct.c_int, ct.c_uint8, _c_int32_p)

    def __api_errcheck(self, res: int, func, _: tuple) -> int:
        if res < 0:
            raise Error(self.decode_error(res), res, func.__name__)
        return res

    def __get(self, name: str, *args: type, **kwargs) -> Callable[..., int]:
        if kwargs.get('private', False):
            func_name = f'_CAEN_DGTZ_{name}'
        else:
            func_name = f'CAEN_DGTZ_{name}'
        func = self.get(func_name, kwargs.get('variadic', False))
        func.argtypes = args
        func.restype = ct.c_int
        func.errcheck = self.__api_errcheck  # type: ignore
        return func

    # C API bindings

    def decode_error(self, error_code: int) -> str:
        """
        There is no function to decode error, we just use the enumeration name.
        """
        return Error.Code(error_code).name

    def sw_release(self) -> str:
        """
        Binding of CAEN_DGTZ_SWRelease()
        """
        l_value = ct.create_string_buffer(16)
        self.__sw_release(l_value)
        return l_value.value.decode('ascii')

    def get_dpp_virtual_probe_name(self, probe: int) -> str:
        """
        Binding of CAEN_DGTZ_GetDPP_VirtualProbeName()
        """
        l_value = ct.create_string_buffer(32)  # Undocumented but, hopefully, long enoug
        self.__get_dpp_virtual_probe_name(probe, l_value)
        return l_value.value.decode('ascii')


lib = _Lib('CAENDigitizer')


def _get_l_arg(connection_type: ConnectionType, arg: Union[int, str]):
    if connection_type is ConnectionType.ETH_V4718:
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
    connection_type: ConnectionType
    arg: Union[int, str]
    conet_node: int
    vme_base_address: int

    # Private members
    __opened: bool = field(default=True, repr=False)
    __ro_buff: Any = field(default_factory=_c_char_p, repr=False)
    __ro_buff_size: int = field(default=0, repr=False)
    __ro_buff_occupancy: int = field(default=0, repr=False)
    __registers: _utils.Registers = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.__registers = _utils.Registers(self.read_register, self.write_register)

    def __del__(self) -> None:
        if self.__opened:
            self.close()

    # C API bindings

    _T = TypeVar('_T', bound='Device')

    @classmethod
    def open(cls: type[_T], connection_type: ConnectionType, arg: Union[int, str], conet_node: int, vme_base_address: int) -> _T:
        """
        Binding of CAEN_DGTZ_OpenDigitizer2()
        """
        l_arg = _get_l_arg(connection_type, arg)
        l_handle = ct.c_int()
        lib.open_digitizer2(connection_type, l_arg, conet_node, vme_base_address, l_handle)
        return cls(l_handle.value, connection_type, arg, conet_node, vme_base_address)

    def connect(self) -> None:
        """
        Binding of CAEN_DGTZ_OpenDigitizer2()

        New instances should be created with open(). This is meant to
        reconnect a device closed with close().
        """
        if self.__opened:
            raise RuntimeError('Already connected.')
        l_arg = _get_l_arg(self.connection_type, self.arg)
        l_handle = ct.c_int()
        lib.open_digitizer2(self.connection_type, l_arg, self.conet_node, self.vme_base_address, l_handle)
        self.handle = l_handle.value
        self.__opened = True

    def close(self) -> None:
        """
        Binding of CAEN_DGTZ_CloseDigitizer()
        """
        lib.close_digitizer(self.handle)
        self.__opened = False

    def write_register(self, address: int, value: int) -> None:
        """
        Binding of CAEN_DGTZ_WriteRegister()
        """
        lib.write_register(self.handle, address, value)

    def read_register(self, address: int) -> int:
        """
        Binding of CAEN_DGTZ_ReadRegister()
        """
        l_value = ct.c_uint32()
        lib.read_register(self.handle, address, l_value)
        return l_value.value

    @property
    def registers(self) -> _utils.Registers:
        """Utility to simplify register access"""
        return self.__registers

    def get_info(self) -> _BoardInfoRaw:
        """
        Binding of CAEN_DGTZ_GetInfo()
        """
        l_data = _BoardInfoRaw()
        lib.get_info(self.handle, l_data)
        return l_data

    def reset(self) -> None:
        """
        Binding of CAEN_DGTZ_Reset()
        """
        lib.reset(self.handle)

    def clear_data(self) -> None:
        """
        Binding of CAEN_DGTZ_ClearData()
        """
        lib.clear_data(self.handle)

    def send_sw_trigger(self) -> None:
        """
        Binding of CAEN_DGTZ_SendSWtrigger()
        """
        lib.send_sw_trigger(self.handle)

    def sw_start_acquisition(self) -> None:
        """
        Binding of CAEN_DGTZ_SWStartAcquisition()
        """
        lib.sw_start_acquisition(self.handle)

    def sw_stop_acquisition(self) -> None:
        """
        Binding of CAEN_DGTZ_SWStopAcquisition()
        """
        lib.sw_stop_acquisition(self.handle)

    def set_interrupt_config(self, state: EnaDis, level: int, status_id: int, event_number: int, mode: IRQMode) -> None:
        """
        Binding of CAEN_DGTZ_SetInterruptConfig()
        """
        lib.set_interrupt_config(self.handle, state, level, status_id, event_number, mode)

    def get_interrupt_config(self) -> tuple[EnaDis, int, int, int, IRQMode]:
        """
        Binding of CAEN_DGTZ_GetInterruptConfig()
        """
        l_state = ct.c_int()
        l_level = ct.c_uint8()
        l_status_id = ct.c_uint32()
        l_event_number = ct.c_uint16()
        l_mode = ct.c_int()
        lib.get_interrupt_config(self.handle, l_state, l_level, l_status_id, l_event_number, l_mode)
        return EnaDis(l_state.value), l_level.value, l_status_id.value, l_event_number.value, IRQMode(l_mode.value)

    def irq_wait(self, timeout: int) -> None:
        """
        Binding of CAEN_DGTZ_IRQWait()
        """
        lib.irq_wait(self.handle, timeout)

    def set_des_mode(self, value: int) -> None:
        """
        Binding of CAEN_DGTZ_SetDESMode()
        """
        lib.set_des_mode(self.handle, value)

    def get_des_mode(self) -> int:
        """
        Binding of CAEN_DGTZ_GetDESMode()
        """
        l_value = ct.c_int()
        lib.get_des_mode(self.handle, l_value)
        return l_value.value

    def set_record_length(self, value: int, channel: Optional[int] = None) -> None:
        """
        Binding of CAEN_DGTZ_SetRecordLength()
        """
        if channel is None:
            lib.set_record_length(self.handle, value)
        else:
            l_channel = ct.c_int32(channel)
            lib.set_record_length(self.handle, value, l_channel)

    def get_record_length(self, channel: Optional[int] = None) -> int:
        """
        Binding of CAEN_DGTZ_GetRecordLength()
        """
        l_value = ct.c_uint32()
        if channel is None:
            lib.get_record_length(self.handle, l_value)
        else:
            l_channel = ct.c_int32(channel)
            lib.get_record_length(self.handle, l_value, l_channel)
        return l_value.value

    def set_channel_enable_mask(self, value: int) -> None:
        """
        Binding of CAEN_DGTZ_SetChannelEnableMask()
        """
        lib.set_channel_enable_mask(self.handle, value)

    def get_channel_enable_mask(self) -> int:
        """
        Binding of CAEN_DGTZ_GetChannelEnableMask()
        """
        l_value = ct.c_uint32()
        lib.get_channel_enable_mask(self.handle, l_value)
        return l_value.value

    def set_group_enable_mask(self, value: int) -> None:
        """
        Binding of CAEN_DGTZ_SetGroupEnableMask()
        """
        lib.set_group_enable_mask(self.handle, value)

    def get_group_enable_mask(self) -> int:
        """
        Binding of CAEN_DGTZ_GetGroupEnableMask()
        """
        l_value = ct.c_uint32()
        lib.get_group_enable_mask(self.handle, l_value)
        return l_value.value

    def set_sw_trigger_mode(self, value: TriggerMode) -> None:
        """
        Binding of CAEN_DGTZ_SetSWTriggerMode()
        """
        lib.set_sw_trigger_mode(self.handle, value)

    def get_sw_trigger_mode(self) -> TriggerMode:
        """
        Binding of CAEN_DGTZ_GetSWTriggerMode()
        """
        l_value = ct.c_int()
        lib.get_sw_trigger_mode(self.handle, l_value)
        return TriggerMode(l_value.value)

    def set_ext_trigger_input_mode(self, value: TriggerMode) -> None:
        """
        Binding of CAEN_DGTZ_SetExtTriggerInputMode()
        """
        lib.set_ext_trigger_input_mode(self.handle, value)

    def get_ext_trigger_input_mode(self) -> TriggerMode:
        """
        Binding of CAEN_DGTZ_GetExtTriggerInputMode()
        """
        l_value = ct.c_int()
        lib.get_ext_trigger_input_mode(self.handle, l_value)
        return TriggerMode(l_value.value)

    def set_channel_self_trigger(self, mode: TriggerMode, channel_mask: int) -> None:
        """
        Binding of CAEN_DGTZ_SetChannelSelfTrigger()
        """
        lib.set_channel_self_trigger(self.handle, mode, channel_mask)

    def get_channel_self_trigger(self, channel: int) -> TriggerMode:
        """
        Binding of CAEN_DGTZ_GetChannelSelfTrigger()
        """
        l_value = ct.c_int()
        lib.get_channel_self_trigger(self.handle, channel, l_value)
        return TriggerMode(l_value.value)

    def set_group_self_trigger(self, mode: TriggerMode, group_mask: int) -> None:
        """
        Binding of CAEN_DGTZ_SetGroupSelfTrigger()
        """
        lib.set_group_self_trigger(self.handle, mode, group_mask)

    def get_group_self_trigger(self, group: int) -> TriggerMode:
        """
        Binding of CAEN_DGTZ_GetGroupSelfTrigger()
        """
        l_value = ct.c_int()
        lib.get_group_self_trigger(self.handle, group, l_value)
        return TriggerMode(l_value.value)

    def set_post_trigger_size(self, value: int) -> None:
        """
        Binding of CAEN_DGTZ_SetPostTriggerSize()
        """
        lib.set_post_trigger_size(self.handle, value)

    def get_post_trigger_size(self) -> int:
        """
        Binding of CAEN_DGTZ_GetPostTriggerSize()
        """
        l_value = ct.c_uint32()
        lib.get_post_trigger_size(self.handle, l_value)
        return l_value.value

    def set_dpp_pre_trigger_size(self, channel: int, value: int) -> None:
        """
        Binding of CAEN_DGTZ_SetDPPPreTriggerSize()
        """
        lib.set_dpp_pre_trigger_size(self.handle, channel, value)

    def get_dpp_pre_trigger_size(self, channel: int) -> int:
        """
        Binding of CAEN_DGTZ_GetDPPPreTriggerSize()
        """
        l_value = ct.c_uint32()
        lib.get_dpp_pre_trigger_size(self.handle, channel, l_value)
        return l_value.value

    def set_channel_dc_offset(self, channel: int, value: int) -> None:
        """
        Binding of CAEN_DGTZ_SetChannelDCOffset()
        """
        lib.set_channel_dc_offset(self.handle, channel, value)

    def get_channel_dc_offset(self, channel: int) -> int:
        """
        Binding of CAEN_DGTZ_GetChannelDCOffset()
        """
        l_value = ct.c_uint32()
        lib.get_channel_dc_offset(self.handle, channel, l_value)
        return l_value.value

    def set_group_dc_offset(self, channel: int, value: int) -> None:
        """
        Binding of CAEN_DGTZ_SetGroupDCOffset()
        """
        lib.set_group_dc_offset(self.handle, channel, value)

    def get_group_dc_offset(self, channel: int) -> int:
        """
        Binding of CAEN_DGTZ_GetGroupDCOffset()
        """
        l_value = ct.c_uint32()
        lib.get_group_dc_offset(self.handle, channel, l_value)
        return l_value.value

    def set_channel_trigger_threshold(self, channel: int, value: int) -> None:
        """
        Binding of CAEN_DGTZ_SetChannelTriggerThreshold()
        """
        lib.set_channel_trigger_threshold(self.handle, channel, value)

    def get_channel_trigger_threshold(self, channel: int) -> int:
        """
        Binding of CAEN_DGTZ_GetChannelTriggerThreshold()
        """
        l_value = ct.c_uint32()
        lib.get_channel_trigger_threshold(self.handle, channel, l_value)
        return l_value.value

    def set_channel_pulse_polarity(self, channel: int, pol: PulsePolarity) -> None:
        """
        Binding of CAEN_DGTZ_SetChannelPulsePolarity()
        """
        lib.set_channel_pulse_polarity(self.handle, channel, pol)

    def get_channel_pulse_polarity(self, channel: int) -> PulsePolarity:
        """
        Binding of CAEN_DGTZ_GetChannelPulsePolarity()
        """
        l_value = ct.c_int()
        lib.get_channel_pulse_polarity(self.handle, channel, l_value)
        return PulsePolarity(l_value.value)

    def set_group_trigger_threshold(self, channel: int, value: int) -> None:
        """
        Binding of CAEN_DGTZ_SetGroupTriggerThreshold()
        """
        lib.set_group_trigger_threshold(self.handle, channel, value)

    def get_group_trigger_threshold(self, channel: int) -> int:
        """
        Binding of CAEN_DGTZ_GetGroupTriggerThreshold()
        """
        l_value = ct.c_uint32()
        lib.get_group_trigger_threshold(self.handle, channel, l_value)
        return l_value.value

    def set_zero_suppression_mode(self, channel: int, mode: ZSMode) -> None:
        """
        Binding of CAEN_DGTZ_SetZeroSuppressionMode()
        """
        lib.set_zero_suppression_mode(self.handle, channel, mode)

    def get_zero_suppression_mode(self, channel: int) -> ZSMode:
        """
        Binding of CAEN_DGTZ_GetZeroSuppressionMode()
        """
        l_value = ct.c_int()
        lib.get_zero_suppression_mode(self.handle, channel, l_value)
        return ZSMode(l_value.value)

    def set_channel_zs_params(self, channel: int, weight: ThresholdWeight, threshold: int, n_samples: int) -> None:
        """
        Binding of CAEN_DGTZ_SetChannelZSParams()
        """
        lib.set_channel_zs_params(self.handle, channel, weight, threshold, n_samples)

    def get_channel_zs_params(self, channel: int) -> tuple[ThresholdWeight, int, int]:
        """
        Binding of CAEN_DGTZ_GetChannelZSParams()
        """
        l_weigth = ct.c_int()
        l_threshold = ct.c_int32()
        l_n_samples = ct.c_int32()
        lib.get_channel_zs_params(self.handle, channel, l_weigth, l_threshold, l_n_samples)
        return ThresholdWeight(l_weigth.value), l_threshold.value, l_n_samples.value

    def set_acquisition_mode(self, channel: int, mode: AcqMode) -> None:
        """
        Binding of CAEN_DGTZ_SetAcquisitionMode()
        """
        lib.set_acquisition_mode(self.handle, channel, mode)

    def get_acquisition_mode(self, channel: int) -> AcqMode:
        """
        Binding of CAEN_DGTZ_GetAcquisitionMode()
        """
        l_value = ct.c_int()
        lib.get_acquisition_mode(self.handle, channel, l_value)
        return AcqMode(l_value.value)

    def set_run_synchronization_mode(self, channel: int, mode: RunSyncMode) -> None:
        """
        Binding of CAEN_DGTZ_SetRunSynchronizationMode()
        """
        lib.set_run_synchronization_mode(self.handle, channel, mode)

    def get_run_synchronization_mode(self, channel: int) -> RunSyncMode:
        """
        Binding of CAEN_DGTZ_GetRunSynchronizationMode()
        """
        l_value = ct.c_int()
        lib.get_run_synchronization_mode(self.handle, channel, l_value)
        return RunSyncMode(l_value.value)

    def set_analog_mon_output(self, channel: int, mode: AnalogMonitorOutputMode) -> None:
        """
        Binding of CAEN_DGTZ_SetAnalogMonOutput()
        """
        lib.set_analog_mon_output(self.handle, channel, mode)

    def get_analog_mon_output(self, channel: int) -> AnalogMonitorOutputMode:
        """
        Binding of CAEN_DGTZ_GetAnalogMonOutput()
        """
        l_value = ct.c_int()
        lib.get_analog_mon_output(self.handle, channel, l_value)
        return AnalogMonitorOutputMode(l_value.value)

    def set_analog_inspection_mon_params(self, channelmask: int, offset: int, mf: AnalogMonitorMagnify, ami: AnalogMonitorInspectorInverter) -> None:
        """
        Binding of CAEN_DGTZ_SetAnalogInspectionMonParams()
        """
        lib.set_analog_inspection_mon_params(self.handle, channelmask, offset, mf, ami)

    def get_analog_inspection_mon_params(self, channelmask: int, offset: int) -> tuple[AnalogMonitorMagnify, AnalogMonitorInspectorInverter]:
        """
        Binding of CAEN_DGTZ_GetAnalogInspectionMonParams()
        """
        l_mf = ct.c_int()
        l_ami = ct.c_int()
        lib.get_analog_inspection_mon_params(self.handle, channelmask, offset, l_mf, l_ami)
        return AnalogMonitorMagnify(l_mf.value), AnalogMonitorInspectorInverter(l_ami.value)

    def disable_event_aligned_readout(self) -> None:
        """
        Binding of CAEN_DGTZ_DisableEventAlignedReadout()
        """
        lib.get_analog_inspection_mon_params(self.handle)

    def set_event_packaging(self, mode: EnaDis) -> None:
        """
        Binding of CAEN_DGTZ_SetEventPackaging()
        """
        lib.set_event_packaging(self.handle, mode)

    def get_event_packaging(self) -> EnaDis:
        """
        Binding of CAEN_DGTZ_GetEventPackaging()
        """
        l_value = ct.c_int()
        lib.get_event_packaging(self.handle, l_value)
        return EnaDis(l_value.value)

    def set_max_num_aggregates_blt(self, num_aggr: int) -> None:
        """
        Binding of CAEN_DGTZ_SetMaxNumAggregatesBLT()
        """
        lib.set_max_num_aggregates_blt(self.handle, num_aggr)

    def get_max_num_aggregates_blt(self) -> int:
        """
        Binding of CAEN_DGTZ_GetMaxNumAggregatesBLT()
        """
        l_value = ct.c_uint32()
        lib.get_max_num_aggregates_blt(self.handle, l_value)
        return l_value.value

    def set_max_num_events_blt(self, num_events: int) -> None:
        """
        Binding of CAEN_DGTZ_SetMaxNumEventsBLT()
        """
        lib.set_max_num_events_blt(self.handle, num_events)

    def get_max_num_events_blt(self) -> int:
        """
        Binding of CAEN_DGTZ_GetMaxNumEventsBLT()
        """
        l_value = ct.c_uint32()
        lib.get_max_num_events_blt(self.handle, l_value)
        return l_value.value

    def malloc_readout_buffer(self) -> None:
        """
        Binding of CAEN_DGTZ_MallocReadoutBuffer()
        """
        l_buffer = _c_char_p()
        l_size = ct.c_uint32()
        lib.malloc_readout_buffer(self.handle, l_buffer, l_size)
        self.__ro_buff = l_buffer
        self.__ro_buff_size = l_size.value

    def free_readout_buffer(self) -> None:
        """
        Binding of CAEN_DGTZ_FreeReadoutBuffer()
        """
        lib.free_readout_buffer(self.__ro_buff)

    def read_data(self, mode: ReadMode) -> None:
        """
        Binding of CAEN_DGTZ_ReadData()
        """
        l_size = ct.c_uint32()
        lib.read_data(self.handle, mode, self.__ro_buff, l_size)
        self.__ro_buff_occupancy = l_size.value
        assert self.__ro_buff_occupancy <= self.__ro_buff_size

    def get_num_events(self) -> int:
        """
        Binding of GetNumEvents()
        """
        l_value = ct.c_uint32()
        lib.get_num_events(self.handle, self.__ro_buff, self.__ro_buff_occupancy, l_value)
        return l_value.value

    def get_event_info(self, num_event: int) -> tuple[EventInfo, bytes]:
        """
        Binding of CAEN_DGTZ_GetEventInfo()
        """
        l_event_ptr = _c_char_p_p()
        l_event_info = _EventInfoRaw()
        lib.get_event_info(self.handle, self.__ro_buff, self.__ro_buff_occupancy, num_event, l_event_info, l_event_ptr)
        event_info = EventInfo.from_raw(l_event_info)
        data = ct.string_at(l_event_ptr.contents, event_info.event_size)
        return event_info, data

    def decode_event(self, *args) -> None:
        """
        Binding of CAEN_DGTZ_DecodeEvent()
        """
        raise NotImplementedError()

    def free_event(self, *args) -> None:
        """
        Binding of CAEN_DGTZ_FreeEvent()
        """
        raise NotImplementedError()

    def get_dpp_events(self, *args) -> None:
        """
        Binding of CAEN_DGTZ_GetDPPEvents()
        """
        raise NotImplementedError()

    def malloc_dpp_events(self, *args) -> None:
        """
        Binding of CAEN_DGTZ_MallocDPPEvents()
        """
        raise NotImplementedError()

    def free_dpp_events(self, *args) -> None:
        """
        Binding of CAEN_DGTZ_FreeDPPEvents()
        """
        raise NotImplementedError()

    def malloc_dpp_waveforms(self, *args) -> None:
        """
        Binding of CAEN_DGTZ_MallocDPPWaveforms()
        """
        raise NotImplementedError()

    def free_dpp_waveforms(self, *args) -> None:
        """
        Binding of CAEN_DGTZ_FreeDPPWaveforms()
        """
        raise NotImplementedError()

    # Missing decode functions here

    def set_num_events_per_aggregate(self, num_events: int, channel: int = -1) -> None:
        """
        Binding of CAEN_DGTZ_SetNumEventsPerAggregate()
        """
        lib.set_num_events_per_aggregate(self.handle, num_events, channel)

    def get_num_events_per_aggregate(self, channel: int = -1) -> int:
        """
        Binding of CAEN_DGTZ_GetNumEventsPerAggregate()
        """
        l_value = ct.c_uint32()
        lib.get_num_events_per_aggregate(self.handle, l_value, channel)
        return l_value.value

    def set_dpp_event_aggregation(self, threshold: int, max_size: int) -> None:
        """
        Binding of CAEN_DGTZ_SetDPPEventAggregation()
        """
        lib.set_dpp_event_aggregation(self.handle, threshold, max_size)

    def set_dpp_parameters(self, *args) -> None:
        """
        Binding of CAEN_DGTZ_SetDPPParameters()
        """
        raise NotImplementedError()

    def set_dpp_acquisition_mode(self, mode: AcqMode, param: DPPSaveParam) -> None:
        """
        Binding of CAEN_DGTZ_SetDPPAcquisitionMode()
        """
        lib.set_dpp_acquisition_mode(self.handle, mode, param)

    def get_dpp_acquisition_mode(self) -> tuple[AcqMode, DPPSaveParam]:
        """
        Binding of CAEN_DGTZ_GetDPPAcquisitionMode()
        """
        l_mode = ct.c_int()
        l_param = ct.c_int()
        lib.get_dpp_acquisition_mode(self.handle, l_mode, l_param)
        return AcqMode(l_mode.value), DPPSaveParam(l_param.value)

    def set_dpp_trigger_mode(self, mode: DPPTriggerMode) -> None:
        """
        Binding of CAEN_DGTZ_SetDPPTriggerMode()
        """
        lib.set_dpp_trigger_mode(self.handle, mode)

    def get_dpp_trigger_mode(self) -> DPPTriggerMode:
        """
        Binding of CAEN_DGTZ_GetDPPTriggerMode()
        """
        l_value = ct.c_int()
        lib.get_dpp_trigger_mode(self.handle, l_value)
        return DPPTriggerMode(l_value.value)

    def set_dpp_virtual_probe(self, trace: int, probe: int) -> None:
        """
        Binding of CAEN_DGTZ_SetDPP_VirtualProbe()
        """
        lib.set_dpp_virtual_probe(self.handle, trace, probe)

    def get_dpp_virtual_probe(self, trace: int) -> int:
        """
        Binding of CAEN_DGTZ_GetDPP_VirtualProbe()
        """
        l_value = ct.c_int()
        lib.get_dpp_virtual_probe(self.handle, trace, l_value)
        return l_value.value

    def get_dpp_supported_virtual_probes(self, trace: int) -> tuple[int, ...]:
        """
        Binding of CAEN_DGTZ_GetDPP_SupportedVirtualProbes()
        """
        l_value = (ct.c_int * 32)()  # Undocumented but, hopefully, long enough
        l_num_probes = ct.c_int()
        lib.get_dpp_supported_virtual_probes(self.handle, trace, l_value, l_num_probes)
        return tuple(l_value[:l_num_probes.value])

    def allocate_event(self, *args) -> None:
        """
        Binding of CAEN_DGTZ_AllocateEvent()
        """
        raise NotImplementedError()

    def set_io_level(self, level: IOLevel) -> None:
        """
        Binding of CAEN_DGTZ_SetIOLevel()
        """
        lib.set_io_level(self.handle, level)

    def get_io_level(self) -> IOLevel:
        """
        Binding of CAEN_DGTZ_GetIOLevel()
        """
        l_value = ct.c_int()
        lib.get_io_level(self.handle, l_value)
        return IOLevel(l_value.value)

    def set_trigger_polarity(self, channel: int, polarity: TriggerPolarity) -> None:
        """
        Binding of CAEN_DGTZ_SetTriggerPolarity()
        """
        lib.set_trigger_polarity(self.handle, channel, polarity)

    def get_trigger_polarity(self, channel: int) -> TriggerPolarity:
        """
        Binding of CAEN_DGTZ_GetTriggerPolarity()
        """
        l_value = ct.c_int()
        lib.get_trigger_polarity(self.handle, channel, l_value)
        return TriggerPolarity(l_value.value)

    def rearm_interrupt(self) -> None:
        """
        Binding of CAEN_DGTZ_RearmInterrupt()
        """
        lib.rearm_interrupt(self.handle)

    def set_drs4_sampling_frequency(self, frequency: DRS4Frequency) -> None:
        """
        Binding of CAEN_DGTZ_SetDRS4SamplingFrequency()
        """
        lib.set_drs4_sampling_frequency(self.handle, frequency)

    def get_drs4_sampling_frequency(self) -> DRS4Frequency:
        """
        Binding of CAEN_DGTZ_GetDRS4SamplingFrequency()
        """
        l_value = ct.c_int()
        lib.get_drs4_sampling_frequency(self.handle, l_value)
        return DRS4Frequency(l_value.value)

    def set_output_signal_mode(self, mode: OutputSignalMode) -> None:
        """
        Binding of CAEN_DGTZ_SetOutputSignalMode()
        """
        lib.set_output_signal_mode(self.handle, mode)

    def get_output_signal_mode(self) -> OutputSignalMode:
        """
        Binding of CAEN_DGTZ_GetOutputSignalMode()
        """
        l_value = ct.c_int()
        lib.get_output_signal_mode(self.handle, l_value)
        return OutputSignalMode(l_value.value)

    def set_group_fast_trigger_threshold(self, group: int, t_value: int) -> None:
        """
        Binding of CAEN_DGTZ_SetGroupFastTriggerThreshold()
        """
        lib.set_group_fast_trigger_threshold(self.handle, group, t_value)

    def get_group_fast_trigger_threshold(self, group: int) -> int:
        """
        Binding of CAEN_DGTZ_GetGroupFastTriggerThreshold()
        """
        l_value = ct.c_uint32()
        lib.get_group_fast_trigger_threshold(self.handle, group, l_value)
        return l_value.value

    def set_group_fast_trigger_dc_offset(self, group: int, dc_value) -> None:
        """
        Binding of CAEN_DGTZ_SetGroupFastTriggerDCOffset()
        """
        lib.set_group_fast_trigger_dc_offset(self.handle, group, dc_value)

    def get_group_fast_trigger_dc_offset(self, group: int) -> int:
        """
        Binding of CAEN_DGTZ_GetGroupFastTriggerDCOffset()
        """
        l_value = ct.c_uint32()
        lib.get_group_fast_trigger_dc_offset(self.handle, group, l_value)
        return l_value.value

    def set_fast_trigger_digitizing(self, enable: EnaDis) -> None:
        """
        Binding of CAEN_DGTZ_SetFastTriggerDigitizing()
        """
        lib.set_fast_trigger_digitizing(self.handle, enable)

    def get_fast_trigger_digitizing(self) -> EnaDis:
        """
        Binding of CAEN_DGTZ_GetFastTriggerDigitizing()
        """
        l_value = ct.c_int()
        lib.get_fast_trigger_digitizing(self.handle, l_value)
        return EnaDis(l_value.value)

    def set_fast_trigger_mode(self, mode: TriggerMode) -> None:
        """
        Binding of CAEN_DGTZ_SetFastTriggerMode()
        """
        lib.set_fast_trigger_mode(self.handle, mode)

    def get_fast_trigger_mode(self) -> TriggerMode:
        """
        Binding of CAEN_DGTZ_GetFastTriggerMode()
        """
        l_value = ct.c_int()
        lib.get_fast_trigger_mode(self.handle, l_value)
        return TriggerMode(l_value.value)

    def load_drs4_correction_data(self) -> None:
        """
        Binding of CAEN_DGTZ_LoadDRS4CorrectionData()
        """
        lib.load_drs4_correction_data(self.handle)

    def get_correction_tables(self) -> None:
        """
        Binding of CAEN_DGTZ_GetCorrectionTables()
        """
        raise NotImplementedError()

    def enable_drs4_correction(self) -> None:
        """
        Binding of CAEN_DGTZ_EnableDRS4Correction()
        """
        lib.enable_drs4_correction(self.handle)

    def disable_drs4_correction(self) -> None:
        """
        Binding of CAEN_DGTZ_DisableDRS4Correction()
        """
        lib.disable_drs4_correction(self.handle)

    def decode_zle_waveforms(self) -> None:
        """
        Binding of CAEN_DGTZ_DecodeZLEWaveforms()
        """
        raise NotImplementedError()

    def free_zle_waveforms(self) -> None:
        """
        Binding of CAEN_DGTZ_FreeZLEWaveforms()
        """
        raise NotImplementedError()

    def malloc_zle_waveforms(self) -> None:
        """
        Binding of CAEN_DGTZ_MallocZLEWaveforms()
        """
        raise NotImplementedError()

    def free_zle_events(self) -> None:
        """
        Binding of CAEN_DGTZ_FreeZLEEvents()
        """
        raise NotImplementedError()

    def malloc_zle_events(self) -> None:
        """
        Binding of CAEN_DGTZ_MallocZLEEvents()
        """
        raise NotImplementedError()

    def get_zle_events(self) -> None:
        """
        Binding of CAEN_DGTZ_GetZLEEvents()
        """
        raise NotImplementedError()

    def set_zle_parameters(self) -> None:
        """
        Binding of CAEN_DGTZ_SetZLEParameters()
        """
        raise NotImplementedError()

    def get_sam_correction_level(self) -> SAMCorrectionLevel:
        """
        Binding of CAEN_DGTZ_GetSAMCorrectionLevel()
        """
        l_value = ct.c_int()
        lib.get_sam_correction_level(self.handle, l_value)
        return SAMCorrectionLevel(l_value.value)

    def set_sam_correction_level(self, level: SAMCorrectionLevel) -> None:
        """
        Binding of CAEN_DGTZ_SetSAMCorrectionLevel()
        """
        lib.set_sam_correction_level(self.handle, level)

    def enable_sam_pulse_gen(self, channel: int, pulse_pattern: int, pulse_source: SAMPulseSourceType) -> None:
        """
        Binding of CAEN_DGTZ_EnableSAMPulseGen()
        """
        lib.enable_sam_pulse_gen(self.handle, channel, pulse_pattern, pulse_source)

    def disable_sam_pulse_gen(self, channel: int) -> None:
        """
        Binding of CAEN_DGTZ_DisableSAMPulseGen()
        """
        lib.disable_sam_pulse_gen(self.handle, channel)

    def set_sam_post_trigger_size(self, channel: int, value: int) -> None:
        """
        Binding of CAEN_DGTZ_SetSAMPostTriggerSize()
        """
        lib.set_sam_post_trigger_size(self.handle, channel, value)

    def get_sam_post_trigger_size(self, channel: int) -> int:
        """
        Binding of CAEN_DGTZ_GetSAMPostTriggerSize()
        """
        l_value = ct.c_uint32()
        lib.get_sam_post_trigger_size(self.handle, channel, l_value)
        return l_value.value

    def set_sam_sampling_frequency(self, freq: SAMFrequency) -> None:
        """
        Binding of CAEN_DGTZ_SetSAMSamplingFrequency()
        """
        lib.set_sam_sampling_frequency(self.handle, freq)

    def get_sam_sampling_frequency(self) -> SAMFrequency:
        """
        Binding of CAEN_DGTZ_GetSAMSamplingFrequency()
        """
        l_value = ct.c_int()
        lib.get_sam_sampling_frequency(self.handle, l_value)
        return SAMFrequency(l_value.value)

    def read_eeprom(self) -> None:
        """
        Binding of _CAEN_DGTZ_Read_EEPROM()
        """
        raise NotImplementedError()

    def write_eeprom(self) -> None:
        """
        Binding of _CAEN_DGTZ_Write_EEPROM()
        """
        raise NotImplementedError()

    def load_sam_correction_data(self) -> None:
        """
        Binding of CAEN_DGTZ_LoadSAMCorrectionData()
        """
        lib.load_sam_correction_data(self.handle)

    def trigger_threshold(self, enable: EnaDis) -> None:
        """
        Binding of _CAEN_DGTZ_TriggerThreshold()
        """
        lib.trigger_threshold(self.handle, enable)

    def send_sam_pulse(self) -> None:
        """
        Binding of CAEN_DGTZ_SendSAMPulse()
        """
        lib.send_sam_pulse(self.handle)

    def set_sam_acquisition_mode(self, mode: AcqMode) -> None:
        """
        Binding of CAEN_DGTZ_SetSAMAcquisitionMode()
        """
        lib.set_sam_acquisition_mode(self.handle, mode)

    def get_sam_acquisition_mode(self) -> AcqMode:
        """
        Binding of CAEN_DGTZ_GetSAMAcquisitionMode()
        """
        l_value = ct.c_int()
        lib.get_sam_acquisition_mode(self.handle, l_value)
        return AcqMode(l_value.value)

    def set_trigger_logic(self, logic: TriggerLogic, majority_level: int) -> None:
        """
        Binding of CAEN_DGTZ_SetTriggerLogic()
        """
        lib.set_trigger_logic(self.handle, logic, majority_level)

    def get_trigger_logic(self) -> tuple[TriggerLogic, int]:
        """
        Binding of CAEN_DGTZ_GetTriggerLogic()
        """
        l_logic = ct.c_int()
        l_majority_level = ct.c_uint32()
        lib.get_trigger_logic(self.handle, l_logic, l_majority_level)
        return TriggerLogic(l_logic.value), l_majority_level.value

    def get_channel_pair_trigger_logic(self, channel_a: int, channel_b: int) -> tuple[TriggerLogic, int]:
        """
        Binding of CAEN_DGTZ_GetChannelPairTriggerLogic()
        """
        l_logic = ct.c_int()
        l_coincidence_window = ct.c_uint16()
        lib.get_channel_pair_trigger_logic(self.handle, channel_a, channel_b, l_logic, l_coincidence_window)
        return TriggerLogic(l_logic.value), l_coincidence_window.value

    def set_channel_pair_trigger_logic(self, channel_a: int, channel_b: int, logic: TriggerLogic, coincidence_window: int) -> None:
        """
        Binding of CAEN_DGTZ_SetChannelPairTriggerLogic()
        """
        lib.set_channel_pair_trigger_logic(self.handle, channel_a, channel_b, logic, coincidence_window)

    def set_decimation_factor(self, factor: int) -> None:
        """
        Binding of CAEN_DGTZ_SetDecimationFactor()
        """
        lib.set_decimation_factor(self.handle, factor)

    def get_decimation_factor(self) -> int:
        """
        Binding of CAEN_DGTZ_GetDecimationFactor()
        """
        l_value = ct.c_uint16()
        lib.get_decimation_factor(self.handle, l_value)
        return l_value.value

    def set_sam_trigger_count_veto_param(self, channel: int, enable: EnaDis, veto_window: int) -> None:
        """
        Binding of CAEN_DGTZ_SetSAMTriggerCountVetoParam()
        """
        lib.set_sam_trigger_count_veto_param(self.handle, channel, enable, veto_window)

    def get_sam_trigger_count_veto_param(self, channel: int) -> tuple[EnaDis, int]:
        """
        Binding of CAEN_DGTZ_GetSAMTriggerCountVetoParam()
        """
        l_enable = ct.c_int()
        l_veto_window = ct.c_uint32()
        lib.get_sam_trigger_count_veto_param(self.handle, channel, l_enable, l_veto_window)
        return EnaDis(l_enable.value), l_veto_window.value

    def set_trigger_in_as_gate(self, mode: EnaDis) -> None:
        """
        Binding of CAEN_DGTZ_SetTriggerInAsGate()
        """
        lib.set_trigger_in_as_gate(self.handle, mode)

    def calibrate(self) -> None:
        """
        Binding of CAEN_DGTZ_Calibrate()
        """
        lib.calibrate(self.handle)

    def read_temperature(self, channel: int) -> int:
        """
        Binding of CAEN_DGTZ_ReadTemperature()
        """
        l_temp = ct.c_uint32()
        lib.read_temperature(self.handle, channel, l_temp)
        return l_temp.value

    def get_dpp_firmware_type(self) -> DPPFirmware:
        """
        Binding of CAEN_DGTZ_GetDPPFirmwareType()
        """
        l_value = ct.c_int()
        lib.get_dpp_firmware_type(self.handle, l_value)
        return DPPFirmware(l_value.value)

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
