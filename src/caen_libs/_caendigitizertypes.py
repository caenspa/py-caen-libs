__author__ = 'Giovanni Cerretani'
__copyright__ = 'Copyright (C) 2024 CAEN SpA'
__license__ = 'LGPL-3.0-or-later'
# SPDX-License-Identifier: LGPL-3.0-or-later

import ctypes as ct
from dataclasses import dataclass, field
from enum import IntEnum, unique
from typing import Optional

import numpy as np
import numpy.typing as npt

from caen_libs import _utils


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


@unique
class BoardModel(IntEnum):
    """
    Binding of ::CAEN_DGTZ_BoardModel_t
    """
    V1724     = 0
    V1721     = 1
    V1731     = 2
    V1720     = 3
    V1740     = 4
    V1751     = 5
    DT5724    = 6
    DT5721    = 7
    DT5731    = 8
    DT5720    = 9
    DT5740    = 10
    DT5751    = 11
    N6724     = 12
    N6721     = 13
    N6731     = 14
    N6720     = 15
    N6740     = 16
    N6751     = 17
    DT5742    = 18
    N6742     = 19
    V1742     = 20
    DT5780    = 21
    N6780     = 22
    V1780     = 23
    DT5761    = 24
    N6761     = 25
    V1761     = 26
    DT5743    = 27
    N6743     = 28
    V1743     = 29
    DT5730    = 30
    N6730     = 31
    V1730     = 32
    DT5790    = 33
    N6790     = 34
    V1790     = 35
    DT5781    = 36
    N6781     = 37
    V1781     = 38
    DT5725    = 39
    N6725     = 40
    V1725     = 41
    V1782     = 42
    V1784     = 43


@unique
class BoardFormFactor(IntEnum):
    """
    Binding of ::CAEN_DGTZ_BoardFormFactor_t
    """
    VME64         = 0
    VME64X        = 1
    DESKTOP       = 2
    NIM           = 3
    RACK          = 4


@unique
class BoardFamilyCode(IntEnum):
    """
    Binding of ::CAEN_DGTZ_BoardFamilyCode_t
    """
    XX724   = 0
    XX721   = 1
    XX731   = 2
    XX720   = 3
    XX740   = 4
    XX751   = 5
    XX742   = 6
    XX780   = 7
    XX761   = 8
    XX743   = 9
    XX730   = 11
    XX790   = 12
    XX781   = 13
    XX725   = 14
    XX782   = 16
    XX784   = 0x84


@unique
class FirmwareCode(IntEnum):
    """
    Firmware codes for various board types.
    Found on Major AMC Firmware version number.
    """
    STANDARD_FW      = 0x00
    V1724_DPP_PHA    = 0x80
    V1720_DPP_CI     = 0x82
    V1720_DPP_PSD    = 0x83
    V1751_DPP_PSD    = 0x84
    V1751_DPP_ZLE    = 0x85
    V1743_DPP_CI     = 0x86
    V1740_DPP_QDC    = 0x87
    V1730_DPP_PSD    = 0x88
    V1724_DPP_DAW    = 0x89
    V1730_DPP_PHA    = 0x8B
    V1730_DPP_ZLE    = 0x8C
    V1730_DPP_DAW    = 0x8D


class BoardInfoRaw(ct.Structure):
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


@dataclass(frozen=True, **_utils.dataclass_slots)
class BoardInfo:
    """
    Binding of ::CAEN_DGTZ_BoardInfo_t
    """
    model_name: str
    model: BoardModel
    channels: int
    form_factor: BoardFormFactor
    family_code: BoardFamilyCode
    roc_firmware_rel: str
    amc_firmware_rel: str
    serial_number: int
    mezzanine_ser_num: list[str]
    pcb_revision: int
    adc_n_bits: int
    sam_correction_data_loaded: int
    comm_handle: int
    vme_handle: int
    license: str
    firmware_code: FirmwareCode  # Binding extension

    @classmethod
    def from_raw(cls, raw: BoardInfoRaw):
        """Instantiate from raw data"""
        amc_version = raw.AMC_FirmwareRel.decode('ascii')
        maj_amc_version = int(amc_version.split('.')[0])
        return cls(
            raw.ModelName.decode('ascii'),
            BoardModel(raw.Model),
            raw.Channels,
            BoardFormFactor(raw.FormFactor),
            BoardFamilyCode(raw.FamilyCode),
            raw.ROC_FirmwareRel.decode('ascii'),
            amc_version,
            raw.SerialNumber,
            [i.decode('ascii') for i in raw.MezzanineSerNum],
            raw.PCB_Revision,
            raw.ADC_NBits,
            raw.SAMCorrectionDataLoaded,
            raw.CommHandle,
            raw.VMEHandle,
            raw.License.decode('ascii'),
            FirmwareCode(maj_amc_version),
        )


class EventInfoRaw(ct.Structure):
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
    def from_raw(cls, raw: EventInfoRaw):
        """Instantiate from raw data"""
        return cls(
            raw.EventSize,
            raw.BoardId,
            raw.Pattern,
            raw.ChannelMask,
            raw.EventCounter,
            raw.TriggerTimeTag,
        )


class Uint16EventRaw(ct.Structure):
    _fields_ = [
        ('ChSize', ct.c_uint32 * MAX_UINT16_CHANNEL_SIZE),
        ('DataChannel', ct.POINTER(ct.c_uint16) * MAX_UINT16_CHANNEL_SIZE),
    ]


@dataclass
class Uint16Event:
    """
    Binding of ::CAEN_DGTZ_UINT16_EVENT_t
    """
    raw: Uint16EventRaw = field(repr=False)

    @property
    def data_channel(self) -> list[npt.NDArray[np.uint16]]:
        return [np.ctypeslib.as_array(self.raw.DataChannel[i], shape=(self.raw.ChSize[i],)) for i in range(MAX_UINT16_CHANNEL_SIZE)]


class Uint8EventRaw(ct.Structure):
    _fields_ = [
        ('ChSize', ct.c_uint32 * MAX_UINT8_CHANNEL_SIZE),
        ('DataChannel', ct.POINTER(ct.c_uint8) * MAX_UINT8_CHANNEL_SIZE),
    ]


@dataclass
class Uint8Event:
    """
    Binding of ::CAEN_DGTZ_UINT8_EVENT_t
    """
    raw: Uint8EventRaw = field(repr=False)

    @property
    def data_channel(self) -> list[npt.NDArray[np.uint8]]:
        return [np.ctypeslib.as_array(self.raw.DataChannel[i], shape=(self.raw.ChSize[i],)) for i in range(MAX_UINT8_CHANNEL_SIZE)]


class X742GroupRaw(ct.Structure):
    _fields_ = [
        ('ChSize', ct.c_uint32 * MAX_X742_CHANNEL_SIZE),
        ('DataChannel', ct.POINTER(ct.c_float) * MAX_X742_CHANNEL_SIZE),
        ('TriggerTimeTag', ct.c_uint32),
        ('StartIndexCell', ct.c_uint16),
    ]


@dataclass
class X742Group:
    """
    Binding of ::CAEN_DGTZ_X742_GROUP_t
    """
    raw: X742GroupRaw = field(repr=False)

    @property
    def data_channel(self) -> list[npt.NDArray[np.float32]]:
        return [np.ctypeslib.as_array(self.raw.DataChannel[i], shape=(self.raw.ChSize[i],)) for i in range(MAX_X742_CHANNEL_SIZE)]

    @property
    def trigger_time_tag(self) -> int:
        return self.raw.TriggerTimeTag

    @property
    def start_index_cell(self) -> int:
        return self.raw.StartIndexCell


class X742EventRaw(ct.Structure):
    _fields_ = [
        ('GrPresent', ct.c_uint8 * MAX_X742_GROUP_SIZE),
        ('DataGroup', ct.POINTER(X742GroupRaw) * MAX_X742_GROUP_SIZE),
    ]


@dataclass
class X742Event:
    """
    Binding of ::CAEN_DGTZ_X742_EVENT_t
    """
    raw: X742EventRaw = field(repr=False)

    @property
    def data_group(self) -> list[Optional[X742Group]]:
        return [X742Group(self.raw.DataGroup[i].contents) if self.raw.GrPresent[i] else None for i in range(MAX_X742_GROUP_SIZE)]


class X743GroupRaw(ct.Structure):
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


@dataclass
class X743Group:
    """
    Binding of ::CAEN_DGTZ_X743_GROUP_t
    """
    raw: X743GroupRaw = field(repr=False)

    @property
    def data_channel(self) -> list[npt.NDArray[np.float32]]:
        return [np.ctypeslib.as_array(self.raw.DataChannel[i], shape=(self.raw.ChSize,)) for i in range(MAX_X743_CHANNELS_X_GROUP)]

    @property
    def trigger_count(self) -> list[int]:
        return list(self.raw.TriggerCount)

    @property
    def time_count(self) -> list[int]:
        return list(self.raw.TimeCount)

    @property
    def event_id(self) -> int:
        return self.raw.EventId

    @property
    def start_index_cell(self) -> int:
        return self.raw.StartIndexCell

    @property
    def tdc(self) -> int:
        return self.raw.TDC

    @property
    def pos_edge_time_stamp(self) -> float:
        return self.raw.PosEdgeTimeStamp

    @property
    def neg_edge_time_stamp(self) -> float:
        return self.raw.NegEdgeTimeStamp

    @property
    def peak_index(self) -> int:
        return self.raw.PeakIndex

    @property
    def peak(self) -> float:
        return self.raw.Peak

    @property
    def baseline(self) -> float:
        return self.raw.Baseline

    @property
    def charge(self) -> float:
        return self.raw.Charge


class X743EventRaw(ct.Structure):
    _fields_ = [
        ('GrPresent', ct.c_uint8 * MAX_V1743_GROUP_SIZE),
        ('DataGroup', ct.POINTER(X743GroupRaw) * MAX_V1743_GROUP_SIZE),
    ]


@dataclass
class X743Event:
    """
    Binding of ::CAEN_DGTZ_X743_EVENT_t
    """
    raw: X743EventRaw = field(repr=False)

    @property
    def data_group(self) -> list[Optional[X743Group]]:
        return [X743Group(self.raw.DataGroup[i].contents) if self.raw.GrPresent[i] else None for i in range(MAX_V1743_GROUP_SIZE)]


class DPPPHAEventRaw(ct.Structure):
    _fields_ = [
        ('Format', ct.c_uint32),
        ('TimeTag', ct.c_uint64),
        ('Energy', ct.c_uint16),
        ('Extras', ct.c_int16),
        ('Waveforms', ct.POINTER(ct.c_uint32)),
        ('Extras2', ct.c_uint32),
    ]


@dataclass
class DPPPHAEvent:
    """
    Binding of ::CAEN_DGTZ_DPP_PHA_Event_t
    """
    raw: DPPPHAEventRaw = field(repr=False)

    @property
    def format(self) -> int:
        return self.raw.Format

    @property
    def time_tag(self) -> int:
        return self.raw.TimeTag

    @property
    def energy(self) -> int:
        return self.raw.Energy

    @property
    def extras(self) -> int:
        return self.raw.Extras

    @property
    def extras2(self) -> int:
        return self.raw.Extras2


class DPPPSDEventRaw(ct.Structure):
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


@dataclass
class DPPPSDEvent:
    """
    Binding of ::CAEN_DGTZ_DPP_PSD_Event_t
    """
    raw: DPPPSDEventRaw = field(repr=False)

    @property
    def format(self) -> int:
        return self.raw.Format

    @property
    def format2(self) -> int:
        return self.raw.Format2

    @property
    def time_tag(self) -> int:
        return self.raw.TimeTag

    @property
    def charge_short(self) -> int:
        return self.raw.ChargeShort

    @property
    def charge_long(self) -> int:
        return self.raw.ChargeLong

    @property
    def baseline(self) -> int:
        return self.raw.Baseline

    @property
    def pur(self) -> int:
        return self.raw.Pur

    @property
    def extras(self) -> int:
        return self.raw.Extras


class DPPCIEventRaw(ct.Structure):
    _fields_ = [
        ('Format', ct.c_uint32),
        ('TimeTag', ct.c_uint32),
        ('Charge', ct.c_int16),
        ('Baseline', ct.c_int16),
        ('Waveforms', ct.POINTER(ct.c_uint32)),
    ]


@dataclass
class DPPCIEvent:
    """
    Binding of ::CAEN_DGTZ_DPP_CI_Event_t
    """
    raw: DPPCIEventRaw = field(repr=False)

    @property
    def format(self) -> int:
        return self.raw.Format

    @property
    def time_tag(self) -> int:
        return self.raw.TimeTag

    @property
    def charge(self) -> int:
        return self.raw.Charge

    @property
    def baseline(self) -> int:
        return self.raw.Baseline


class DPPQDCEventRaw(ct.Structure):
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


@dataclass
class DPPQDCEvent:
    """
    Binding of ::CAEN_DGTZ_DPP_QDC_Event_t
    """
    raw: DPPQDCEventRaw = field(repr=False)

    @property
    def is_extended_time_stamp(self) -> bool:
        return bool(self.raw.isExtendedTimeStamp)

    @property
    def format(self) -> int:
        return self.raw.Format

    @property
    def time_tag(self) -> int:
        return self.raw.TimeTag

    @property
    def charge(self) -> int:
        return self.raw.Charge

    @property
    def baseline(self) -> int:
        return self.raw.Baseline

    @property
    def pur(self) -> int:
        return self.raw.Pur

    @property
    def overrange(self) -> int:
        return self.raw.Overrange

    @property
    def sub_channel(self) -> int:
        return self.raw.SubChannel

    @property
    def extras(self) -> int:
        return self.raw.Extras


class ZLEEvent751Raw(ct.Structure):
    _fields_ = [
        ('timeTag', ct.c_uint32),
        ('Baseline', ct.c_uint32),
        ('Waveforms', ct.POINTER(ct.c_uint32)),
    ]


@dataclass
class ZLEEvent751:
    """
    Binding of ::CAEN_DGTZ_751_ZLE_Event_t
    """
    raw: ZLEEvent751Raw = field(repr=False)

    @property
    def time_tag(self) -> int:
        return self.raw.timeTag

    @property
    def baseline(self) -> int:
        return self.raw.Baseline


class ZLEWaveforms730Raw(ct.Structure):
    _fields_ = [
        ('TraceNumber', ct.c_uint32),
        ('Trace', ct.POINTER(ct.c_uint16)),
        ('TraceIndex', ct.POINTER(ct.c_uint32)),
    ]


@dataclass
class ZLEWaveforms730:
    """
    Binding of ::CAEN_DGTZ_730_ZLE_Waveforms_t
    """
    raw: ZLEWaveforms730Raw = field(repr=False)

    @property
    def trace(self) -> npt.NDArray[np.uint16]:
        return np.ctypeslib.as_array(self.raw.Trace, shape=(self.raw.TraceNumber,))

    @property
    def trace_index(self) -> npt.NDArray[np.uint32]:
        return np.ctypeslib.as_array(self.raw.TraceIndex, shape=(self.raw.TraceNumber,))


class ZLEChannel730Raw(ct.Structure):
    _fields_ = [
        ('fifo_full', ct.c_uint32),
        ('size_wrd', ct.c_uint32),
        ('Baseline', ct.c_uint32),
        ('DataPtr', ct.POINTER(ct.c_uint32)),
        ('Waveforms', ct.POINTER(ZLEWaveforms730Raw)),
    ]


@dataclass
class ZLEChannel730:
    """
    Binding of ::CAEN_DGTZ_730_ZLE_Channel_t
    """
    raw: ZLEChannel730Raw = field(repr=False)

    @property
    def fifo_full(self) -> bool:
        return bool(self.raw.fifo_full)

    @property
    def baseline(self) -> int:
        return self.raw.Baseline

    @property
    def waveforms(self) -> ZLEWaveforms730:
        return ZLEWaveforms730(self.raw.Waveforms.contents)


class ZLEEvent730Raw(ct.Structure):
    _fields_ = [
        ('size', ct.c_uint32),
        ('chmask', ct.c_uint16),
        ('tcounter', ct.c_uint32),
        ('timeStamp', ct.c_uint64),
        ('Channel', ct.POINTER(ZLEChannel730Raw) * MAX_V1730_CHANNEL_SIZE),
    ]


@dataclass
class ZLEEvent730:
    """
    Binding of ::CAEN_DGTZ_730_ZLE_Event_t
    """
    raw: ZLEEvent730Raw = field(repr=False)

    @property
    def size(self) -> int:
        return self.raw.size

    @property
    def tcounter(self) -> int:
        return self.raw.tcounter

    @property
    def time_stamp(self) -> int:
        return self.raw.timeStamp

    @property
    def channel(self) -> list[Optional[ZLEChannel730]]:
        return [ZLEChannel730(self.raw.Channel[i].contents) if (self.raw.chmask & (1 << i)) else None for i in range(MAX_V1730_CHANNEL_SIZE)]


class DPPDAWWaveformsRaw(ct.Structure):
    _fields_ = [
        ('Trace', ct.POINTER(ct.c_uint16)),
    ]


@dataclass
class DPPDAWWaveforms:
    """
    Binding of ::CAEN_DGTZ_730_DAW_Waveforms_t
    """
    raw: DPPDAWWaveformsRaw = field(repr=False)
    _size: int = field(repr=False)

    @property
    def trace(self) -> npt.NDArray[np.uint16]:
        return np.ctypeslib.as_array(self.raw.Trace, shape=(self._size,))


class DPPDAWChannelRaw(ct.Structure):
    _fields_ = [
        ('truncate', ct.c_uint32),
        ('EvType', ct.c_uint32),
        ('size', ct.c_uint32),
        ('timeStamp', ct.c_uint64),
        ('baseline', ct.c_uint16),
        ('DataPtr', ct.POINTER(ct.c_uint16)),
        ('Waveforms', ct.POINTER(DPPDAWWaveformsRaw)),
    ]


@dataclass
class DPPDAWChannel:
    """
    Binding of ::CAEN_DGTZ_730_DAW_Channel_t
    """
    raw: DPPDAWChannelRaw = field(repr=False)

    @property
    def truncate(self) -> bool:
        return bool(self.raw.truncate)

    @property
    def ev_type(self) -> int:
        return self.raw.EvType

    @property
    def size(self) -> int:
        return self.raw.size

    @property
    def time_stamp(self) -> int:
        return self.raw.timeStamp

    @property
    def baseline(self) -> int:
        return self.raw.baseline

    @property
    def waveforms(self) -> DPPDAWWaveforms:
        return DPPDAWWaveforms(self.raw.Waveforms.contents, self.size)


class DPPDAWEventRaw(ct.Structure):
    _fields_ = [
        ('size', ct.c_uint32),
        ('chmask', ct.c_uint16),
        ('tcounter', ct.c_uint32),
        ('timeStamp', ct.c_uint64),
        ('Channel', ct.POINTER(DPPDAWChannelRaw) * MAX_V1730_CHANNEL_SIZE),
    ]


@dataclass
class DPPDAWEvent:
    """
    Binding of ::CAEN_DGTZ_730_DAW_Event_t
    """
    raw: DPPDAWEventRaw = field(repr=False)

    @property
    def size(self) -> int:
        return self.raw.size

    @property
    def tcounter(self) -> int:
        return self.raw.tcounter

    @property
    def time_stamp(self) -> int:
        return self.raw.timeStamp

    @property
    def channel(self) -> list[Optional[DPPDAWChannel]]:
        return [DPPDAWChannel(self.raw.Channel[i].contents) if (self.raw.chmask & (1 << i)) else None for i in range(MAX_V1730_CHANNEL_SIZE)]


class DPPX743EventRaw(ct.Structure):
    _fields_ = [
        ('Charge', ct.c_float),
        ('StartIndexCell', ct.c_int),
    ]


@dataclass
class DPPX743Event:
    """
    Binding of ::CAEN_DGTZ_DPP_X743_Event_t
    """
    raw: DPPX743EventRaw = field(repr=False)

    @property
    def charge(self) -> float:
        return self.raw.Charge

    @property
    def start_index_cell(self) -> int:
        return self.raw.StartIndexCell


class DPPPHAWaveformsRaw(ct.Structure):
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


@dataclass
class DPPPHAWaveforms:
    """
    Binding of ::CAEN_DGTZ_DPP_PHA_Waveforms_t
    """
    raw: DPPPHAWaveformsRaw = field(repr=False)

    @property
    def ns(self) -> int:
        return self.raw.Ns

    @property
    def dual_trace(self) -> bool:
        return bool(self.raw.DualTrace)

    @property
    def v_probe1(self) -> int:
        return self.raw.VProbe1

    @property
    def v_probe2(self) -> int:
        return self.raw.VProbe2

    @property
    def vd_probe(self) -> int:
        return self.raw.VDProbe

    @property
    def trace1(self) -> npt.NDArray[np.int16]:
        return np.ctypeslib.as_array(self.raw.Trace1, shape=(self.ns,))

    @property
    def trace2(self) -> npt.NDArray[np.int16]:
        return np.ctypeslib.as_array(self.raw.Trace2, shape=(self.ns,))

    @property
    def d_trace1(self) -> npt.NDArray[np.uint8]:
        return np.ctypeslib.as_array(self.raw.DTrace1, shape=(self.ns,))

    @property
    def d_trace2(self) -> npt.NDArray[np.uint8]:
        return np.ctypeslib.as_array(self.raw.DTrace2, shape=(self.ns,))


class DPPPSDWaveformsRaw(ct.Structure):
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


@dataclass
class DPPPSDWaveforms:
    """
    Binding of ::CAEN_DGTZ_DPP_PSD_Waveforms_t
    """
    raw: DPPPSDWaveformsRaw = field(repr=False)

    @property
    def ns(self) -> int:
        return self.raw.Ns

    @property
    def dual_trace(self) -> bool:
        return bool(self.raw.dualTrace)

    @property
    def anlg_probe(self) -> int:
        return self.raw.anlgProbe

    @property
    def dgt_probe1(self) -> int:
        return self.raw.dgtProbe1

    @property
    def dgt_probe2(self) -> int:
        return self.raw.dgtProbe2

    @property
    def trace1(self) -> npt.NDArray[np.int16]:
        return np.ctypeslib.as_array(self.raw.Trace1, shape=(self.ns,))

    @property
    def trace2(self) -> npt.NDArray[np.int16]:
        return np.ctypeslib.as_array(self.raw.Trace2, shape=(self.ns,))

    @property
    def d_trace1(self) -> npt.NDArray[np.uint8]:
        return np.ctypeslib.as_array(self.raw.DTrace1, shape=(self.ns,))

    @property
    def d_trace2(self) -> npt.NDArray[np.uint8]:
        return np.ctypeslib.as_array(self.raw.DTrace2, shape=(self.ns,))

    @property
    def d_trace3(self) -> npt.NDArray[np.uint8]:
        return np.ctypeslib.as_array(self.raw.DTrace3, shape=(self.ns,))

    @property
    def d_trace4(self) -> npt.NDArray[np.uint8]:
        return np.ctypeslib.as_array(self.raw.DTrace4, shape=(self.ns,))


class ZLEWaveforms751Raw(ct.Structure):
    _fields_ = [
        ('Ns', ct.c_uint32),
        ('Trace1', ct.POINTER(ct.c_uint16)),
        ('Discarded', ct.POINTER(ct.c_uint8)),
    ]


@dataclass
class ZLEWaveforms751:
    """
    Binding of ::CAEN_DGTZ_751_ZLE_Waveforms_t
    """
    raw: ZLEWaveforms751Raw = field(repr=False)

    @property
    def ns(self) -> int:
        return self.raw.Ns

    @property
    def trace1(self) -> npt.NDArray[np.uint16]:
        return np.ctypeslib.as_array(self.raw.Trace1, shape=(self.ns,))

    @property
    def discarded(self) -> npt.NDArray[np.uint8]:
        return np.ctypeslib.as_array(self.raw.Discarded, shape=(self.ns,))


DPPCIWaveformsRaw = DPPPSDWaveformsRaw
DPPCIWaveforms = DPPPSDWaveforms


class DPPQDCWaveformsRaw(ct.Structure):
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


@dataclass
class DPPQDCWaveforms:
    """
    Binding of ::CAEN_DGTZ_DPP_QDC_Waveforms_t
    """
    raw: DPPQDCWaveformsRaw = field(repr=False)

    @property
    def ns(self) -> int:
        return self.raw.Ns

    @property
    def dual_trace(self) -> bool:
        return bool(self.raw.dualTrace)

    @property
    def anlg_probe(self) -> int:
        return self.raw.anlgProbe

    @property
    def dgt_probe1(self) -> int:
        return self.raw.dgtProbe1

    @property
    def dgt_probe2(self) -> int:
        return self.raw.dgtProbe2

    @property
    def trace1(self) -> npt.NDArray[np.uint16]:
        return np.ctypeslib.as_array(self.raw.Trace1, shape=(self.ns,))

    @property
    def trace2(self) -> npt.NDArray[np.uint16]:
        return np.ctypeslib.as_array(self.raw.Trace2, shape=(self.ns,))

    @property
    def d_trace1(self) -> npt.NDArray[np.uint8]:
        return np.ctypeslib.as_array(self.raw.DTrace1, shape=(self.ns,))

    @property
    def d_trace2(self) -> npt.NDArray[np.uint8]:
        return np.ctypeslib.as_array(self.raw.DTrace2, shape=(self.ns,))

    @property
    def d_trace3(self) -> npt.NDArray[np.uint8]:
        return np.ctypeslib.as_array(self.raw.DTrace3, shape=(self.ns,))

    @property
    def d_trace4(self) -> npt.NDArray[np.uint8]:
        return np.ctypeslib.as_array(self.raw.DTrace4, shape=(self.ns,))


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


class DPPPHAParamsRaw(ct.Structure):
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


class ZLEParams751Raw(ct.Structure):
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


class DPPQDCParamsRaw(ct.Structure):
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


class DRS4CorrectionRaw(ct.Structure):
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