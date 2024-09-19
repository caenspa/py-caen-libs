__author__ = 'Giovanni Cerretani'
__copyright__ = 'Copyright (C) 2024 CAEN SpA'
__license__ = 'LGPL-3.0-or-later'
# SPDX-License-Identifier: LGPL-3.0-or-later

import ctypes as ct
from contextlib import contextmanager
from dataclasses import dataclass
from enum import IntEnum, unique
from typing import Callable, Optional, Tuple, Type, TypeVar, Union

from caen_libs import _utils


@unique
class ErrorCode(IntEnum):
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
    """
    Binding of ::CAEN_DGTZ_BoardInfo_t
    """
    _fields_ = [
        ('ModelName', ct.c_char * 12),
        ('Model', ct.c_uint32),
        ('Channels', ct.c_uint32),
        ('FormFactor', ct.c_uint32),
        ('FamilyCode', ct.c_uint32),
        ('ROC_FirmwareRel', ct.c_char * 20),
        ('AMC_FirmwareRel', ct.c_char * 40),
        ('SerialNumber', ct.c_uint32),
        ('MezzanineSerNum', (ct.c_char * 4) * 8),
        ('PCB_Revision', ct.c_uint32),
        ('ADC_NBits', ct.c_uint32),
        ('SAMCorrectionDataLoaded', ct.c_uint32),
        ('CommHandle', ct.c_int),
        ('VMEHandle', ct.c_int),
        ('License', ct.c_char * 17),
    ]

class _EventInfoRaw(ct.Structure):
    """
    Binding of ::CAEN_DGTZ_EventInfo_t
    """
    _fields_ = [
        ('EventSize', ct.c_uint32),
        ('BoardId', ct.c_uint32),
        ('Pattern', ct.c_uint32),
        ('ChannelMask', ct.c_uint32),
        ('EventCounter', ct.c_uint32),
        ('TriggerTimeTag', ct.c_uint32),
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


class Error(RuntimeError):
    """
    Raised when a wrapped C API function returns
    negative values.
    """

    code: ErrorCode  ## Error code as instance of ErrorCode
    message: str  ## Message description
    func: str  ## Name of failed function

    def __init__(self, res: int, func: str) -> None:
        self.code = ErrorCode(res)
        self.func = func
        super().__init__(f'{self.func} failed: {self.code.name}')


# Utility definitions
_P = ct.POINTER
_c_char_p = _P(ct.c_char)  # ct.c_char_p is not fine due to its own memory management
_c_char_p_p = _P(_c_char_p)
_c_int_p = _P(ct.c_int)
_c_uint8_p = _P(ct.c_uint8)
_c_uint16_p = _P(ct.c_uint16)
_c_int32_p = _P(ct.c_int32)
_c_uint32_p = _P(ct.c_uint32)
_c_void_p_p = _P(ct.c_void_p)
_event_info_p = _P(_EventInfoRaw)

class _Lib(_utils.Lib):

    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.__load_api()

    def __load_api(self) -> None:
        # Load API not related to devices
        self.__sw_release = self.__get('SWRelease', ct.c_char_p)
        self.__free_readout_buffer = self.__get('FreeReadoutBuffer', _c_char_p_p)
        self.__get_dpp_virtual_probe_name = self.__get('GetDPP_VirtualProbeName', ct.c_int, _c_char_p)

        # Load API
        self.open_digitizer = self.__get('OpenDigitizer', ct.c_int, ct.c_int, ct.c_int, ct.c_uint32, _c_int_p)
        self.open_digitizer2 = self.__get('OpenDigitizer2', ct.c_int, ct.c_void_p, ct.c_int, ct.c_uint32, _c_int_p)
        self.close_digitizer = self.__get('CloseDigitizer', ct.c_int)
        self.write_register = self.__get('WriteRegister', ct.c_int, ct.c_uint32, ct.c_uint32)
        self.read_register = self.__get('ReadRegister', ct.c_int, ct.c_uint32, ct.c_uint16)
        self.get_info = self.__get('GetInfo', ct.c_int, _P(_BoardInfoRaw))
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
        # TODO
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
        self.set_num_events_per_aggregate = self.__get('SetNumEventsPerAggregate', ct.c_int, ct.c_uint32, variadic=True)
        self.get_num_events_per_aggregate = self.__get('GetNumEventsPerAggregate', ct.c_int, _c_uint32_p, variadic=True)
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

    def __api_errcheck(self, res: int, func: Callable, _: Tuple) -> int:
        if res < 0:
            raise Error(res, func.__name__)
        return res

    def __get(self, name: str, *args: Type, **kwargs) -> Callable[..., int]:
        l_lib = self.lib if not kwargs.get('variadic', False) else self.lib_variadic
        if kwargs.get('private', False):
            func_name = f'_CAEN_DGTZ_{name}'
        else:
            func_name = f'CAEN_DGTZ_{name}'
        func = getattr(l_lib, func_name)
        func.argtypes = args
        func.restype = ct.c_int
        func.errcheck = self.__api_errcheck
        return func

    # C API bindings

    def sw_release(self) -> str:
        """
        Binding of CAEN_DGTZ_SWRelease()
        """
        l_value = ct.create_string_buffer(16)
        self.__sw_release(l_value)
        return l_value.value.decode()


lib = _Lib('CAENDigitizer')


def _get_l_arg(connection_type: ConnectionType, arg: Union[int, str]):
    if connection_type is ConnectionType.ETH_V4718:
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
    connection_type: ConnectionType
    arg: Union[int, str]
    conet_node: int
    vme_base_address: int

    def __post_init__(self) -> None:
        self.__opened = True
        self.__registers = _utils.Registers(self.read_register, self.write_register)

    def __del__(self) -> None:
        if self.__opened:
            self.close()

    # C API bindings

    _T = TypeVar('_T', bound='Device')

    @classmethod
    def open(cls: Type[_T], connection_type: ConnectionType, arg: Union[int, str], conet_node: int, vme_base_address: int) -> _T:
        """
        Binding of CAEN_DGTZ_OpenDigitizer2()
        """
        l_arg = _get_l_arg(connection_type, arg)
        l_handle = ct.c_int()
        lib.open_digitizer2(connection_type, l_arg, conet_node, vme_base_address, l_handle)
        return cls(l_handle.value, connection_type, arg, conet_node, vme_base_address)

    def connect(self) -> None:
        """
        Binding of CAENComm_OpenDevice2()
        New instances should be created with open().
        This is meant to reconnect a device closed with close().
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

    def get_interrupt_config(self) -> Tuple[EnaDis, int, int, int, IRQMode]:
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

    def get_channel_zs_params(self, channel: int) -> Tuple[ThresholdWeight, int, int]:
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
