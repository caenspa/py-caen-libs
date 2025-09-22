__author__ = 'Giovanni Cerretani'
__copyright__ = 'Copyright (C) 2024 CAEN SpA'
__license__ = 'LGPL-3.0-or-later'
# SPDX-License-Identifier: LGPL-3.0-or-later

import ctypes as ct
from dataclasses import dataclass, field
from enum import Enum, IntEnum, auto, unique
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
MAX_PROBENAMES_LEN = 50


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
    Binding of ::*_CODE
    """
    STANDARD_FW       = 0x00
    V1724_DPP_PHA     = 0x80
    V1720_DPP_CI      = 0x82
    V1720_DPP_PSD     = 0x83
    V1751_DPP_PSD     = 0x84
    V1751_DPP_ZLE     = 0x85
    V1743_DPP_CI      = 0x86
    V1740_DPP_QDC     = 0x87
    V1730_DPP_PSD     = 0x88
    V1724_DPP_DAW     = 0x89  # Not really supported by CAEN Digitizer
    V1730_DPP_PHA     = 0x8B
    V1730_DPP_ZLE     = 0x8C
    V1730_DPP_DAW     = 0x8D
    STANDARD_FW_X742  = 0x01  # Binding extension
    STANDARD_FW_X743  = 0x02  # Binding extension
    UNKNOWN           = 0xFF  # Binding extension

    @classmethod
    def _missing_(cls, value):
        """
        To avoid errors in case of unknown code, we return UNKNOWN
        """
        return cls.UNKNOWN


class Registers(IntEnum):
    """
    Binding of Digitizer Registers Address Map
    """
    MULTI_EVENT_BUFFER                          = 0x0000
    SAM_EEPROM_ACCESS                           = 0x100C
    CHANNEL_ZS_THRESHOLD_BASE_ADDRESS           = 0x1024
    CHANNEL_ZS_NSAMPLE_BASE_ADDRESS             = 0x1028
    CHANNEL_THRESHOLD_BASE_ADDRESS              = 0x1080
    CHANNEL_OV_UND_TRSH_BASE_ADDRESS            = 0x1084
    CHANNEL_STATUS_BASE_ADDRESS                 = 0x1088
    CHANNEL_AMC_FPGA_FW_BASE_ADDRESS            = 0x108C
    CHANNEL_BUFFER_OCC_BASE_ADDRESS             = 0x1094
    CHANNEL_DAC_BASE_ADDRESS                    = 0x1098
    CHANNEL_GROUP_V1740_BASE_ADDRESS            = 0x10A8
    GROUP_FASTTRG_THR_V1742_BASE_ADDRESS        = 0x10D4
    GROUP_FASTTRG_DCOFFSET_V1742_BASE_ADDRESS   = 0x10DC
    DRS4_FREQUENCY_REG                          = 0x10D8
    SAM_ENABLE_PULSE_REG                        = 0x102C
    SAM_TRIGGER_GATE_REG                        = 0x1038
    SAM_FREQUENCY_REG                           = 0x1040
    SAM_CHARGE_TRESHOLD_CH0                     = 0x1048
    SAM_CHARGE_TRESHOLD_CH1                     = 0x104C
    SAM_TRIGGER_REG_ADD                         = 0x103C
    SAM_FREQUENCY_REG_WRITE                     = 0x1040
    SAM_CHARGE_LENGTH_CH0                       = 0x1080
    SAM_CHARGE_LENGTH_CH1                       = 0x10A0
    SAM_REG_ADD                                 = 0x1084
    SAM_REG_VALUE                               = 0x1028
    SAM_DAC_SPI_DATA_ADD                        = 0x1054
    SAM_START_CELL_CH0                          = 0x1058
    SAM_START_CELL_CH1                          = 0x10A4
    SAM_CTRL_ADD                                = 0x1070
    SAM_EEPROM_WP_ADD                           = 0x1078
    SAM_START_ACQ_ADD                           = 0x1018
    SAM_RESET_ACQ_ADD                           = 0x105C
    SAM_NB_OF_COLS_2_READ_ADD                   = 0x1044
    SAM_POST_TRIGGER_ADD                        = 0x1030
    SAM_PULSE_PATTERN_ADD                       = 0x1034
    SAM_RATE_COUNTERS_CH0                       = 0x106C
    SAM_RATE_COUNTERS_CH1                       = 0x1094
    BROAD_CH_CTRL_ADD                           = 0x8000
    BROAD_CH_CONFIGBIT_SET_ADD                  = 0x8004
    BROAD_CH_CLEAR_CTRL_ADD                     = 0x8008
    BROAD_NUM_BLOCK_ADD                         = 0x800C
    CUSTOM_SIZE_REG                             = 0x8020
    DPP_NUM_EVENTS_PER_AGGREGATE                = 0x8034
    DRS4_FREQUENCY_REG_WRITE                    = 0x80D8
    SAM_BROAD_FREQUENCY_REG_WRITE               = 0x8040
    SAM_BROAD_REG_ADD                           = 0x8084
    SAM_BROAD_REG_VALUE                         = 0x8028
    SAM_BROAD_DAC_SPI_DATA_ADD                  = 0x8054
    SAM_BROAD_CTRL_ADD                          = 0x8070
    SAM_BROAD_PRETRIGGER_ADD                    = 0x8074
    SAM_BROAD_START_ACQ_ADD                     = 0x8018
    SAM_BROAD_RESET_ACQ_ADD                     = 0x805C
    DECIMATION_ADD                              = 0x8044
    SAM_BROAD_NB_OF_COLS_2_READ_ADD             = 0x8044
    SAM_BROAD_POST_TRIGGER_ADD                  = 0x8030
    SAM_BROAD_PBK_RESET                         = 0x8010
    SAM_BROAD_PULSE_CHANNELS                    = 0x801C
    SAM_START_RATE_COUNTERS                     = 0x8020
    SAM_BROAD_CHIP_RESET                        = 0x807C
    ACQ_CONTROL_ADD                             = 0x8100
    ACQ_STATUS_ADD                              = 0x8104
    SW_TRIGGER_ADD                              = 0x8108
    TRIGGER_SRC_ENABLE_ADD                      = 0x810C
    FP_TRIGGER_OUT_ENABLE_ADD                   = 0x8110
    POST_TRIG_ADD                               = 0x8114
    FRONT_PANEL_IO_ADD                          = 0x8118
    FRONT_PANEL_IO_CTRL_ADD                     = 0x811C
    CH_ENABLE_ADD                               = 0x8120
    FW_REV_ADD                                  = 0x8124
    DOWNSAMPLE_FACT_ADD                         = 0x8128
    EVENT_STORED_ADD                            = 0x812C
    MON_SET_ADD                                 = 0x8138
    SYNC_CMD                                    = 0x813C
    BOARD_INFO_ADD                              = 0x8140
    EVENT_SIZE_ADD                              = 0x814C
    MON_MODE_ADD                                = 0x8144
    ANALOG_MON_ADD                              = 0x8150
    TRIGGER_VETO_ADD                            = 0x817C
    VME_CONTROL_ADD                             = 0xEF00
    VME_STATUS_ADD                              = 0xEF04
    BOARD_ID_ADD                                = 0xEF08
    MCST_CBLT_ADD_CTRL_ADD                      = 0xEF0C
    RELOCATION_ADDRESS_ADD                      = 0xEF10
    INT_STATUS_ID_ADD                           = 0xEF14
    INT_EVENT_NUM_ADD                           = 0xEF18
    BLT_EVENT_NUM_ADD                           = 0xEF1C
    SCRATCH_ADD                                 = 0xEF20
    SW_RESET_ADD                                = 0xEF24
    SW_CLEAR_ADD                                = 0xEF28
    FLASH_EN_ADD                                = 0xEF2C
    FLASH_DATA_ADD                              = 0xEF30
    RELOAD_CONFIG_ADD                           = 0xEF34
    ROM_CHKSUM_ADD                              = 0xF000
    ROM_CHKSUM_LEN_2_ADD                        = 0xF004
    ROM_CHKSUM_LEN_1_ADD                        = 0xF008
    ROM_CHKSUM_LEN_0_ADD                        = 0xF00C
    ROM_CONST_2_ADD                             = 0xF010
    ROM_CONST_1_ADD                             = 0xF014
    ROM_CONST_0_ADD                             = 0xF018
    ROM_C_CODE_ADD                              = 0xF01C
    ROM_R_CODE_ADD                              = 0xF020
    ROM_OUI_2_ADD                               = 0xF024
    ROM_OUI_1_ADD                               = 0xF028
    ROM_OUI_0_ADD                               = 0xF02C
    ROM_VERSION_ADD                             = 0xF030
    ROM_BOARD_ID_2_ADD                          = 0xF034
    ROM_BOARD_ID_1_ADD                          = 0xF038
    ROM_BOARD_ID_0_ADD                          = 0xF03C
    ROM_REVISION_3_ADD                          = 0xF040
    ROM_REVISION_2_ADD                          = 0xF044
    ROM_REVISION_1_ADD                          = 0xF048
    ROM_REVISION_0_ADD                          = 0xF04C
    ROM_SERIAL_0_V2_ADD                         = 0xF070
    ROM_SERIAL_1_V2_ADD                         = 0xF074
    ROM_SERIAL_2_V2_ADD                         = 0xF078
    ROM_SERIAL_3_V2_ADD                         = 0xF07C
    ROM_SERIAL_1_ADD                            = 0xF080
    ROM_SERIAL_0_ADD                            = 0xF084
    ROM_VCXO_TYPE_ADD                           = 0xF088


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
        try:
            maj_amc_version = int(amc_version.split('.')[0])
        except (ValueError, IndexError):
            maj_amc_version = -1
        return cls(
            raw.ModelName.decode('ascii'),
            BoardModel(raw.Model),
            raw.Channels,
            BoardFormFactor(raw.FormFactor),
            BoardFamilyCode(raw.FamilyCode),
            raw.ROC_FirmwareRel.decode('ascii'),
            amc_version,
            raw.SerialNumber,
            [bytes(i).decode('ascii').rstrip('\x00') for i in raw.MezzanineSerNum],
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


@dataclass(**_utils.dataclass_slots)
class Uint16Event:
    """
    Binding of ::CAEN_DGTZ_UINT16_EVENT_t
    """
    raw: Uint16EventRaw = field(repr=False)

    def __get_data_channel(self, index: int) -> npt.NDArray[np.uint16]:
        if self.raw.ChSize[index] == 0:
            return np.array([], dtype=np.uint16)
        return np.ctypeslib.as_array(self.raw.DataChannel[index], shape=(self.raw.ChSize[index],))

    @property
    def data_channel(self) -> list[npt.NDArray[np.uint16]]:
        return [self.__get_data_channel(i) for i in range(MAX_UINT16_CHANNEL_SIZE)]


class Uint8EventRaw(ct.Structure):
    _fields_ = [
        ('ChSize', ct.c_uint32 * MAX_UINT8_CHANNEL_SIZE),
        ('DataChannel', ct.POINTER(ct.c_uint8) * MAX_UINT8_CHANNEL_SIZE),
    ]


@dataclass(**_utils.dataclass_slots)
class Uint8Event:
    """
    Binding of ::CAEN_DGTZ_UINT8_EVENT_t
    """
    raw: Uint8EventRaw = field(repr=False)

    def __get_data_channel(self, index: int) -> npt.NDArray[np.uint8]:
        if self.raw.ChSize[index] == 0:
            return np.array([], dtype=np.uint8)
        return np.ctypeslib.as_array(self.raw.DataChannel[index], shape=(self.raw.ChSize[index],))

    @property
    def data_channel(self) -> list[npt.NDArray[np.uint8]]:
        return [self.__get_data_channel(i) for i in range(MAX_UINT8_CHANNEL_SIZE)]


class X742GroupRaw(ct.Structure):
    _fields_ = [
        ('ChSize', ct.c_uint32 * MAX_X742_CHANNEL_SIZE),
        ('DataChannel', ct.POINTER(ct.c_float) * MAX_X742_CHANNEL_SIZE),
        ('TriggerTimeTag', ct.c_uint32),
        ('StartIndexCell', ct.c_uint16),
    ]


@dataclass(**_utils.dataclass_slots)
class X742Group:
    """
    Binding of ::CAEN_DGTZ_X742_GROUP_t
    """
    raw: X742GroupRaw = field(repr=False)

    def __get_data_channel(self, index: int) -> npt.NDArray[np.float32]:
        if self.raw.ChSize[index] == 0:
            return np.array([], dtype=np.float32)
        return np.ctypeslib.as_array(self.raw.DataChannel[index], shape=(self.raw.ChSize[index],))

    @property
    def data_channel(self) -> list[npt.NDArray[np.float32]]:
        return [self.__get_data_channel(i) for i in range(MAX_X742_CHANNEL_SIZE)]

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


@dataclass(**_utils.dataclass_slots)
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


@dataclass(**_utils.dataclass_slots)
class X743Group:
    """
    Binding of ::CAEN_DGTZ_X743_GROUP_t
    """
    raw: X743GroupRaw = field(repr=False)

    def __get_data_channel(self, index: int) -> npt.NDArray[np.float32]:
        if self.raw.ChSize[index] == 0:
            return np.array([], dtype=np.float32)
        return np.ctypeslib.as_array(self.raw.DataChannel[index], shape=(self.raw.ChSize[index],))

    @property
    def data_channel(self) -> list[npt.NDArray[np.float32]]:
        return [self.__get_data_channel(i) for i in range(MAX_X743_CHANNELS_X_GROUP)]

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


@dataclass(**_utils.dataclass_slots)
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


@dataclass(**_utils.dataclass_slots)
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


@dataclass(**_utils.dataclass_slots)
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


@dataclass(**_utils.dataclass_slots)
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


@dataclass(**_utils.dataclass_slots)
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


class ZLEWaveforms751Raw(ct.Structure):
    _fields_ = [
        ('Ns', ct.c_uint32),
        ('Trace1', ct.POINTER(ct.c_uint16)),
        ('Discarded', ct.POINTER(ct.c_uint8)),
    ]


@dataclass(**_utils.dataclass_slots)
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


class ZLEEvent751Raw(ct.Structure):
    _fields_ = [
        ('timeTag', ct.c_uint32),
        ('Baseline', ct.c_uint32),
        ('Waveforms', ct.POINTER(ct.c_uint32)),
    ]


@dataclass(**_utils.dataclass_slots)
class ZLEEvent751:
    """
    Binding of ::CAEN_DGTZ_751_ZLE_Event_t

    Also contains a reference to a waveforms to align the behavior to
    V1730 ZLE event, which has waveform inside the channel structure.
    """
    raw: ZLEEvent751Raw = field(repr=False)
    raw_waveforms: ZLEWaveforms751Raw = field(repr=False)

    @property
    def time_tag(self) -> int:
        return self.raw.timeTag

    @property
    def baseline(self) -> int:
        return self.raw.Baseline

    @property
    def waveforms(self) -> ZLEWaveforms751:
        return ZLEWaveforms751(self.raw_waveforms)


class ZLEWaveforms730Raw(ct.Structure):
    _fields_ = [
        ('TraceNumber', ct.c_uint32),
        ('Trace', ct.POINTER(ct.c_uint16)),
        ('TraceIndex', ct.POINTER(ct.c_uint32)),
    ]


@dataclass(**_utils.dataclass_slots)
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


@dataclass(**_utils.dataclass_slots)
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


@dataclass(**_utils.dataclass_slots)
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


@dataclass(**_utils.dataclass_slots)
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


@dataclass(**_utils.dataclass_slots)
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


@dataclass(**_utils.dataclass_slots)
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


@dataclass(**_utils.dataclass_slots)
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


@dataclass(**_utils.dataclass_slots)
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


@dataclass(**_utils.dataclass_slots)
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


@dataclass(**_utils.dataclass_slots)
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
class DPPAcqMode(IntEnum):
    """
    Binding of ::CAEN_DGTZ_DPP_AcqMode_t
    """
    OSCILLOSCOPE  = 0
    LIST          = 1
    MIXED         = 2


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
        ('trgwin', ct.c_int * MAX_DPP_PHA_CHANNEL_SIZE),
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


@dataclass(**_utils.dataclass_slots)
class DPPPHAParams:
    """
    Binding of ::CAEN_DGTZ_DPP_PHA_Params_t
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
    otrej: list[int] = field(default_factory=list)
    trgho: list[int] = field(default_factory=list)
    twwdt: list[int] = field(default_factory=list)
    trgwin: list[int] = field(default_factory=list)
    dgain: list[int] = field(default_factory=list)
    enf: list[float] = field(default_factory=list)
    decimation: list[int] = field(default_factory=list)
    enskim: list[int] = field(default_factory=list)
    eskimlld: list[int] = field(default_factory=list)
    eskimuld: list[int] = field(default_factory=list)
    blrclip: list[int] = field(default_factory=list)
    dcomp: list[int] = field(default_factory=list)
    trapbsl: list[int] = field(default_factory=list)

    def resize(self, n_channels: int):
        """
        Resize to n_channels.

        This method is required because this class is a class of lists,
        rather than a class used as member of a list in the parent class
        DgtzParams. In other words, the other members of DgtzParams are
        indexed like `params.x[ch].y`, while this like `params.x.y[ch]`.
        """
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
        self.otrej = [0] * n_channels
        self.trgho = [0] * n_channels
        self.twwdt = [0] * n_channels
        self.trgwin = [0] * n_channels
        self.dgain = [0] * n_channels
        self.enf = [0.] * n_channels
        self.decimation = [0] * n_channels
        self.enskim = [0] * n_channels
        self.eskimlld = [0] * n_channels
        self.eskimuld = [0] * n_channels
        self.blrclip = [0] * n_channels
        self.dcomp = [0] * n_channels
        self.trapbsl = [0] * n_channels

    def to_raw(self) -> DPPPHAParamsRaw:
        """Convert to raw data"""
        return DPPPHAParamsRaw(
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
            tuple(self.otrej),
            tuple(self.trgho),
            tuple(self.twwdt),
            tuple(self.trgwin),
            tuple(self.dgain),
            tuple(self.enf),
            tuple(self.decimation),
            tuple(self.enskim),
            tuple(self.eskimlld),
            tuple(self.eskimuld),
            tuple(self.blrclip),
            tuple(self.dcomp),
            tuple(self.trapbsl),
        )


class DPPPSDParamsRaw(ct.Structure):
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
        ('trgc', ct.c_int * MAX_DPP_PSD_CHANNEL_SIZE),
        ('purh', ct.c_int),
        ('purgap', ct.c_int),
    ]


@unique
class DPPTriggerConfig(IntEnum):
    """
    Binding of ::CAEN_DGTZ_DPP_TriggerConfig_t
    """
    PEAK       = 0
    THRESHOLD  = 1


@unique
class DPPPUR(IntEnum):
    """
    Binding of ::CAEN_DGTZ_DPP_PUR_t
    """
    DETECT_ONLY = 0
    ENABLED = 1


@dataclass(**_utils.dataclass_slots)
class DPPPSDParams:
    """
    Binding of ::CAEN_DGTZ_DPP_PSD_Params_t
    """
    blthr: int = field(default=0)
    bltmo: int = field(default=0)
    trgho: int = field(default=0)
    thr: list[int] = field(default_factory=list)
    selft: list[int] = field(default_factory=list)
    csens: list[int] = field(default_factory=list)
    sgate: list[int] = field(default_factory=list)
    lgate: list[int] = field(default_factory=list)
    pgate: list[int] = field(default_factory=list)
    tvaw: list[int] = field(default_factory=list)
    nsbl: list[int] = field(default_factory=list)
    discr: list[int] = field(default_factory=list)
    cfdf: list[int] = field(default_factory=list)
    cfdd: list[int] = field(default_factory=list)
    trgc: list[DPPTriggerConfig] = field(default_factory=list)
    purh: DPPPUR = field(default=DPPPUR.DETECT_ONLY)
    purgap: int = field(default=0)

    def resize(self, n_channels: int):
        """
        Resize to n_channels.
        """
        self.thr = [0] * n_channels
        self.selft = [0] * n_channels
        self.csens = [0] * n_channels
        self.sgate = [0] * n_channels
        self.lgate = [0] * n_channels
        self.pgate = [0] * n_channels
        self.tvaw = [0] * n_channels
        self.nsbl = [0] * n_channels
        self.discr = [0] * n_channels
        self.cfdf = [0] * n_channels
        self.cfdd = [0] * n_channels
        self.trgc = [DPPTriggerConfig.PEAK] * n_channels

    def to_raw(self) -> DPPPSDParamsRaw:
        """Convert to raw data"""
        return DPPPSDParamsRaw(
            self.blthr,
            self.bltmo,
            self.trgho,
            tuple(self.thr),
            tuple(self.selft),
            tuple(self.csens),
            tuple(self.sgate),
            tuple(self.lgate),
            tuple(self.pgate),
            tuple(self.tvaw),
            tuple(self.nsbl),
            tuple(self.discr),
            tuple(self.cfdf),
            tuple(self.cfdd),
            tuple(self.trgc),
            int(self.purh),
            self.purgap,
        )


class DPPCIParamsRaw(ct.Structure):
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


@dataclass(**_utils.dataclass_slots)
class DPPCIParams:
    """
    Binding of ::CAEN_DGTZ_DPP_CI_Params_t
    """
    purgap: int = field(default=0)
    purh: int = field(default=0)
    blthr: int = field(default=0)
    bltmo: int = field(default=0)
    trgho: int = field(default=0)
    thr: list[int] = field(default_factory=list)
    selft: list[int] = field(default_factory=list)
    csens: list[int] = field(default_factory=list)
    gate: list[int] = field(default_factory=list)
    pgate: list[int] = field(default_factory=list)
    tvaw: list[int] = field(default_factory=list)
    nsbl: list[int] = field(default_factory=list)
    trgc: list[DPPTriggerConfig] = field(default_factory=list)

    def resize(self, n_channels: int):
        """
        Resize to n_channels.
        """
        self.thr = [0] * n_channels
        self.selft = [0] * n_channels
        self.csens = [0] * n_channels
        self.gate = [0] * n_channels
        self.pgate = [0] * n_channels
        self.tvaw = [0] * n_channels
        self.nsbl = [0] * n_channels
        self.trgc = [DPPTriggerConfig.PEAK] * n_channels
    def to_raw(self) -> DPPCIParamsRaw:
        """Convert to raw data"""
        return DPPCIParamsRaw(
            self.purgap,
            self.purh,
            self.blthr,
            self.bltmo,
            self.trgho,
            tuple(self.thr),
            tuple(self.selft),
            tuple(self.csens),
            tuple(self.gate),
            tuple(self.pgate),
            tuple(self.tvaw),
            tuple(self.nsbl),
            tuple(self.trgc),
        )


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


@dataclass(**_utils.dataclass_slots)
class ZLEParams751:
    """
    Binding of ::CAEN_DGTZ_751_ZLE_Params_t
    """
    nsamp_bck: list[int] = field(default_factory=list)
    nsamp_ahe: list[int] = field(default_factory=list)
    zle_upp_thr: list[int] = field(default_factory=list)
    zle_und_thr: list[int] = field(default_factory=list)
    sel_num_samp_bsl: list[int] = field(default_factory=list)
    bsl_thrshld: list[int] = field(default_factory=list)
    bsl_time_out: list[int] = field(default_factory=list)
    pre_trgg: int = field(default=0)

    def resize(self, n_channels: int):
        """
        Resize to n_channels.
        """
        self.nsamp_bck = [0] * n_channels
        self.nsamp_ahe = [0] * n_channels
        self.zle_upp_thr = [0] * n_channels
        self.zle_und_thr = [0] * n_channels
        self.sel_num_samp_bsl = [0] * n_channels
        self.bsl_thrshld = [0] * n_channels
        self.bsl_time_out = [0] * n_channels

    def to_raw(self) -> ZLEParams751Raw:
        """Convert to raw data"""
        return ZLEParams751Raw(
            tuple(self.nsamp_bck),
            tuple(self.nsamp_ahe),
            tuple(self.zle_upp_thr),
            tuple(self.zle_und_thr),
            tuple(self.sel_num_samp_bsl),
            tuple(self.bsl_thrshld),
            tuple(self.bsl_time_out),
            self.pre_trgg,
        )


class DPPX743ParamsRaw(ct.Structure):
    _fields_ = [
        ('disableSuppressBaseline', ct.c_int),
        ('startCell', ct.c_uint * (MAX_X743_CHANNELS_X_GROUP * MAX_V1743_GROUP_SIZE)),
        ('chargeLength', ct.c_ushort * (MAX_X743_CHANNELS_X_GROUP * MAX_V1743_GROUP_SIZE)),
        ('enableChargeThreshold', ct.c_int * (MAX_X743_CHANNELS_X_GROUP * MAX_V1743_GROUP_SIZE)),
        ('chargeThreshold', ct.c_float * (MAX_X743_CHANNELS_X_GROUP * MAX_V1743_GROUP_SIZE)),
    ]


@dataclass(**_utils.dataclass_slots)
class DPPX743Params:
    """
    Binding of ::CAEN_DGTZ_DPP_X743_Params_t
    """
    disable_suppress_baseline: EnaDis = field(default=EnaDis.DISABLE)
    start_cell: list[int] = field(default_factory=list)
    charge_length: list[int] = field(default_factory=list)
    enable_charge_threshold: list[EnaDis] = field(default_factory=list)
    charge_threshold: list[float] = field(default_factory=list)

    def resize(self, n_channels: int):
        """
        Resize to n_channels.
        """
        self.start_cell = [0] * n_channels
        self.charge_length = [0] * n_channels
        self.enable_charge_threshold = [EnaDis.DISABLE] * n_channels
        self.charge_threshold = [0.] * n_channels

    def to_raw(self) -> DPPX743ParamsRaw:
        """Convert to raw data"""
        return DPPX743ParamsRaw(
            self.disable_suppress_baseline,
            tuple(self.start_cell),
            tuple(self.charge_length),
            tuple(self.enable_charge_threshold),
            tuple(self.charge_threshold),
        )


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


@dataclass(**_utils.dataclass_slots)
class DPPQDCParams:
    """
    Binding of ::CAEN_DGTZ_DPP_QDC_Params_t
    """
    trgho: list[int] = field(default_factory=list)
    gate_width: list[int] = field(default_factory=list)
    pre_gate: list[int] = field(default_factory=list)
    fixed_baseline: list[int] = field(default_factory=list)
    dis_trig_hist: list[bool] = field(default_factory=list)
    dis_self_trigger: list[bool] = field(default_factory=list)
    baseline_mode: list[int] = field(default_factory=list)
    trg_mode: list[int] = field(default_factory=list)
    charge_sensitivity: list[int] = field(default_factory=list)
    pulse_pol: list[PulsePolarity] = field(default_factory=list)
    en_charge_ped: list[bool] = field(default_factory=list)
    test_pulses_rate: list[int] = field(default_factory=list)
    en_test_pulses: list[bool] = field(default_factory=list)
    input_smoothing: list[int] = field(default_factory=list)
    enable_extended_time_stamp: bool = field(default=False)

    def resize(self, n_channels: int):
        """
        Resize to n_channels.
        """
        self.trgho = [0] * n_channels
        self.gate_width = [0] * n_channels
        self.pre_gate = [0] * n_channels
        self.fixed_baseline = [0] * n_channels
        self.dis_trig_hist = [False] * n_channels
        self.dis_self_trigger = [False] * n_channels
        self.baseline_mode = [0] * n_channels
        self.trg_mode = [0] * n_channels
        self.charge_sensitivity = [0] * n_channels
        self.pulse_pol = [PulsePolarity.POSITIVE] * n_channels
        self.en_charge_ped = [False] * n_channels
        self.test_pulses_rate = [0] * n_channels
        self.en_test_pulses = [False] * n_channels
        self.input_smoothing = [0] * n_channels

    def to_raw(self) -> DPPQDCParamsRaw:
        """Convert to raw data"""
        return DPPQDCParamsRaw(
            tuple(self.trgho),
            tuple(self.gate_width),
            tuple(self.pre_gate),
            tuple(self.fixed_baseline),
            tuple(self.dis_trig_hist),
            tuple(self.dis_self_trigger),
            tuple(self.baseline_mode),
            tuple(self.trg_mode),
            tuple(self.charge_sensitivity),
            tuple(self.pulse_pol),
            tuple(self.en_charge_ped),
            tuple(self.test_pulses_rate),
            tuple(self.en_test_pulses),
            tuple(self.input_smoothing),
            self.enable_extended_time_stamp,
        )


class DRS4CorrectionRaw(ct.Structure):
    _fields_ = [
        ('cell', (ct.c_int16 * 1024) * MAX_X742_CHANNEL_SIZE),
        ('nsample', (ct.c_int8 * 1024) * MAX_X742_CHANNEL_SIZE),
        ('time', ct.c_float * 1024),
    ]


@dataclass(**_utils.dataclass_slots)
class DRS4Correction:
    """
    Binding of ::CAEN_DGTZ_DRS4Correction_t
    """
    cell: list[list[int]] = field(default_factory=list, repr=False)
    nsample: list[list[int]] = field(default_factory=list, repr=False)
    time: list[float] = field(default_factory=list, repr=False)

    @classmethod
    def from_raw(cls, raw: DRS4CorrectionRaw):
        """Instantiate from raw data"""
        return cls(
            list(map(list, raw.cell)),
            list(map(list, raw.nsample)),
            list(raw.time),
        )


@unique
class DPPTrace(IntEnum):
    """
    Binding of trace types
    """
    ANALOG_1 = 0
    ANALOG_2 = 1
    DIGITAL_1 = 2
    DIGITAL_2 = 3
    DIGITAL_3 = 4
    DIGITAL_4 = 5


@unique
class DPPProbe(IntEnum):
    """
    Binding of ::CAEN_DGTZ_DPP_*PROBE_*
    """
    VIRTUAL_INVALID = -1
    VIRTUAL_INPUT = 0
    VIRTUAL_DELTA = 1
    VIRTUAL_DELTA2 = 2
    VIRTUAL_TRAPEZOID = 3
    VIRTUAL_TRAPEZOID_REDUCED = 4
    VIRTUAL_BASELINE = 5
    VIRTUAL_THRESHOLD = 6
    VIRTUAL_CFD = 7
    VIRTUAL_SMOOTHED_INPUT = 8
    VIRTUAL_NONE = 9
    DIGITAL_TRG_WIN = 10
    DIGITAL_ARMED = 11
    DIGITAL_PK_RUN = 12
    DIGITAL_PEAKING = 13
    DIGITAL_COINC_WIN = 14
    DIGITAL_BL_HOLDOFF = 15
    DIGITAL_TRG_HOLDOFF = 16
    DIGITAL_TRG_VAL = 17
    DIGITAL_ACQ_VETO = 18
    DIGITAL_BFM_VETO = 19
    DIGITAL_EXT_TRG = 20
    DIGITAL_OVER_THR = 21
    DIGITAL_TRG_OUT = 22
    DIGITAL_COINCIDENCE = 23
    DIGITAL_PILE_UP = 24
    DIGITAL_GATE = 25
    DIGITAL_GATE_SHORT = 26
    DIGITAL_TRIGGER = 27
    DIGITAL_NONE = 28
    DIGITAL_BL_FREEZE = 29
    DIGITAL_BUSY = 30
    DIGITAL_PRG_VETO = 31


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


@unique
class FirmwareType(Enum):
    """
    Alternative to ::CAEN_DGTZ_GetDPPFirmwareType() and ::CAEN_DGTZ_DPPFirmware_t,
    not used since pretty bugged at least before v2.19.0

    Internal use only.
    """
    STANDARD = auto()
    DPP = auto()
    ZLE = auto()
    DAW = auto()  # DAW firmware uses DPP functions with ZLE calling convention
    UNKNOWN = auto()

    @classmethod
    def from_code(cls, code: FirmwareCode):
        """Internal use only."""
        F = FirmwareCode
        match code:
            case F.STANDARD_FW | F.STANDARD_FW_X742 | F.STANDARD_FW_X743:
                return cls.STANDARD
            case F.V1720_DPP_CI | F.V1720_DPP_PSD | F.V1751_DPP_PSD | F.V1743_DPP_CI | F.V1740_DPP_QDC | F.V1730_DPP_PSD | F.V1724_DPP_PHA | F.V1730_DPP_PHA:
                return cls.DPP
            case F.V1751_DPP_ZLE | F.V1730_DPP_ZLE:
                return cls.ZLE
            case F.V1724_DPP_DAW | F.V1730_DPP_DAW:
                return cls.DAW
            case _:
                return cls.UNKNOWN


@dataclass(**_utils.dataclass_slots)
class ReadoutBuffer:
    """
    Internal representation of readout buffer.
    """
    data: 'ct._Pointer[ct.c_char]' = field(default_factory=ct.POINTER(ct.c_char), repr=False)
    size: ct.c_uint32 = field(default_factory=ct.c_uint32, repr=False)
    occupancy: ct.c_uint32 = field(default_factory=ct.c_uint32, repr=False)

    def as_buffer(self) -> npt.NDArray[np.byte]:
        """Return the buffer as a numpy array of bytes."""
        return np.ctypeslib.as_array(self.data, shape=(self.occupancy.value,))
