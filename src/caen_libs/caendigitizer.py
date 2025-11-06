"""
Binding of CAEN Digitizer
"""

__author__ = 'Giovanni Cerretani'
__copyright__ = 'Copyright (C) 2024 CAEN SpA'
__license__ = 'LGPL-3.0-or-later'
# SPDX-License-Identifier: LGPL-3.0-or-later

import ctypes as ct
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import IntEnum, unique
from typing import TypeVar

from caen_libs import error, _utils
import caen_libs._caendigitizertypes as _types

# Add some types to the module namespace
from caen_libs._caendigitizertypes import (  # pylint: disable=W0611
    AcqMode,
    AcquisitionMode,
    AnalogMonitorInspectorInverter,
    AnalogMonitorMagnify,
    AnalogMonitorOutputMode,
    BoardFamilyCode,
    BoardInfo,
    Buffer as _Buffer,
    ConnectionType,
    DPPAcqMode,
    DPPCIEvent,
    DPPCIParams,
    DPPCIWaveforms,
    DPPDAWEvent,
    DPPDAWWaveforms,
    DPPFirmware,
    DPPPHAEvent,
    DPPPHAParams,
    DPPPHAWaveforms,
    DPPProbe,
    DPPPSDEvent,
    DPPPSDParams,
    DPPPSDWaveforms,
    DPPQDCEvent,
    DPPQDCParams,
    DPPQDCWaveforms,
    DPPSaveParam,
    DPPTrace,
    DPPTriggerConfig,
    DPPTriggerMode,
    DPPX743Event,
    DPPX743Params,
    DRS4Correction,
    DRS4Frequency,
    EnaDis,
    EventInfo,
    EventTypes as _EventTypes,
    EventsBuffer as _EventsBuffer,
    FirmwareCode,
    FirmwareType as _FirmwareType,
    Never as _Never,
    IOLevel,
    IRQMode,
    OutputSignalMode,
    PulsePolarity,
    ReadMode,
    RunSyncMode,
    SAMCorrectionLevel,
    SAMFrequency,
    SAMPulseSourceType,
    ThresholdWeight,
    TriggerLogic,
    TriggerMode,
    TriggerPolarity,
    Uint16Event,
    Uint8Event,
    X742Event,
    X743Event,
    ZLEEvent730,
    ZLEEvent751,
    ZLEParams751,
    ZLEWaveforms730,
    ZLEWaveforms751,
    ZSMode,
)


class Error(error.Error):
    """
    Raised when a wrapped C API function returns negative values.
    """

    @unique
    class Code(IntEnum):
        """
        Binding of ::CAEN_DGTZ_ErrorCode
        """
        UNKNOWN = 0xDEADFACE  # Special value for Python binding
        SUCCESS = 0
        COMM_ERROR = -1
        GENERIC_ERROR = -2
        INVALID_PARAM = -3
        INVALID_LINK_TYPE = -4
        INVALID_HANDLE = -5
        MAX_DEVICES_ERROR = -6
        BAD_BOARD_TYPE = -7
        BAD_INTERRUPT_LEV = -8
        BAD_EVENT_NUMBER = -9
        READ_DEVICE_REGISTER_FAIL = -10
        WRITE_DEVICE_REGISTER_FAIL = -11
        INVALID_CHANNEL_NUMBER = -13
        CHANNEL_BUSY = -14
        FPIO_MODE_INVALID = -15
        WRONG_ACQ_MODE = -16
        FUNCTION_NOT_ALLOWED = -17
        TIMEOUT = -18
        INVALID_BUFFER = -19
        EVENT_NOT_FOUND = -20
        INVALID_EVENT = -21
        OUT_OF_MEMORY = -22
        CALIBRATION_ERROR = -23
        DIGITIZER_NOT_FOUND = -24
        DIGITIZER_ALREADY_OPEN = -25
        DIGITIZER_NOT_READY = -26
        INTERRUPT_NOT_CONFIGURED = -27
        DIGITIZER_MEMORY_CORRUPTED = -28
        DPP_FIRMWARE_NOT_SUPPORTED = -29
        INVALID_LICENSE = -30
        INVALID_DIGITIZER_STATUS = -31
        UNSUPPORTED_TRACE = -32
        INVALID_PROBE = -33
        UNSUPPORTED_BASE_ADDRESS = -34
        NOT_YET_IMPLEMENTED = -99

        @classmethod
        def _missing_(cls, _):
            """
            Sometimes library returns values not contained in the
            enumerator, due to errors in the library itself. We
            catch them and return UNKNOWN.
            """
            return cls.UNKNOWN

    code: Code

    def __init__(self, message: str, res: int, func: str) -> None:
        self.code = Error.Code(res)
        super().__init__(message, self.code.name, func)


# Utility definitions
_c_char_p = ct.POINTER(ct.c_char)  # ct.c_char_p is not fine due to its own memory management
_c_char_p_p = ct.POINTER(_c_char_p)
_c_int_p = ct.POINTER(ct.c_int)
_c_uint8_p = ct.POINTER(ct.c_uint8)
_c_uint16_p = ct.POINTER(ct.c_uint16)
_c_int32_p = ct.POINTER(ct.c_int32)
_c_uint32_p = ct.POINTER(ct.c_uint32)
_c_void_p_p = ct.POINTER(ct.c_void_p)
_board_info_p = ct.POINTER(_types.BoardInfoRaw)
_event_info_p = ct.POINTER(_types.EventInfoRaw)


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
        self.read_register = self.__get('ReadRegister', ct.c_int, ct.c_uint32, _c_uint32_p)
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
        self.set_io_level = self.__get('SetIOLevel', ct.c_int, ct.c_int)
        self.get_io_level = self.__get('GetIOLevel', ct.c_int, _c_int_p)
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
        self.__vme_irq_wait = self.__get('VMEIRQWait', ct.c_int, ct.c_int, ct.c_int, ct.c_uint8, ct.c_uint32, _c_int_p)
        self.__vme_irq_check = self.__get('VMEIRQCheck', ct.c_int, _c_uint8_p)
        self.__vme_iack_cycle = self.__get('VMEIACKCycle', ct.c_int, ct.c_uint8, _c_int32_p)

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

    def get_dpp_virtual_probe_name(self, probe: DPPProbe) -> str:
        """
        Binding of CAEN_DGTZ_GetDPP_VirtualProbeName()
        """
        l_value = ct.create_string_buffer(_types.MAX_PROBENAMES_LEN)
        self.__get_dpp_virtual_probe_name(probe, l_value)
        return l_value.value.decode('ascii')

    def vme_irq_wait(self, connection_type: ConnectionType, link_num: int, conet_node: int, irq_mask: int, timeout: int) -> int:
        """
        Binding of CAEN_DGTZ_VMEIRQWait()
        """
        l_vme_handle = ct.c_int()
        self.__vme_irq_wait(connection_type, link_num, conet_node, irq_mask, timeout, l_vme_handle)
        return l_vme_handle.value

    def vme_irq_check(self, vme_handle: int) -> int:
        """
        Binding of CAEN_DGTZ_VMEIRQCheck()
        """
        l_irq_mask = ct.c_ubyte()
        self.__vme_irq_check(vme_handle, l_irq_mask)
        return l_irq_mask.value

    def vme_iack_cycle(self, vme_handle: int, level: int) -> int:
        """
        Binding of CAEN_DGTZ_VMEIACKCycle()
        """
        l_board_id = ct.c_int32()
        self.__vme_iack_cycle(vme_handle, level, l_board_id)
        return l_board_id.value


lib = _Lib('CAENDigitizer')


def _get_l_arg(connection_type: ConnectionType, arg: int | str):
    match connection_type:
        case ConnectionType.ETH_V4718:
            if not isinstance(arg, str):
                raise TypeError(f'arg expected to be a string for {connection_type.name} connection type')
            return arg.encode('ascii')
        case _:
            l_link_number = int(arg)
            l_link_number_ct = ct.c_uint32(l_link_number)
            return ct.pointer(l_link_number_ct)


@dataclass(slots=True)
class Device:
    """
    Class representing a device.
    """

    # Public members
    handle: int
    connection_type: ConnectionType
    arg: int | str
    conet_node: int
    vme_base_address: int

    # Private members
    __opened: bool = field(default=True, repr=False)
    __registers: _utils.Registers = field(init=False, repr=False)
    __ro_buff: _types.ReadoutBuffer | None = field(default=None, repr=False)
    __info: BoardInfo = field(init=False, repr=False)
    __firmware_type: _FirmwareType = field(init=False, repr=False)

    # Private members for internal firmware-specific event representation
    __types: _EventTypes = field(init=False, repr=False)

    # Private members for internal firmware-specific memory management
    __scope_event: ct.c_void_p | None = field(default=None, repr=False)  # Standard firmware
    __dpp_events: ct.Array[ct.c_void_p] | None = field(default=None, repr=False)  # DPP
    __dpp_waveforms: ct.c_void_p | None = field(default=None, repr=False)  # DPP
    __daw_events: _EventsBuffer | None = field(default=None, repr=False)  # DAW firmware
    __zle_events: _EventsBuffer | None = field(default=None, repr=False)  # ZLE firmware
    __zle_waveforms: ct.Array[ct.Structure] | None = field(default=None, repr=False)  # 751 ZLE firmware

    def __post_init__(self) -> None:
        self.__registers = _utils.Registers(self.read_register, self.write_register)
        self.__info = self.get_info()
        self.__firmware_type = _FirmwareType.from_code(self.__info.firmware_code)
        self.__types = self.__get_event_types()

    def __del__(self) -> None:
        if self.__opened:
            self.close()

    @property
    def __e(self) -> _types.BindingType:
        """
        Convenience property to access event type.
        """
        return self.__types.event

    @property
    def __w(self) -> _types.BindingType:
        """
        Convenience property to access waveform type, should not be used
        if firmware does not support waveforms.
        """
        assert self.__types.waveforms is not _Never
        return self.__types.waveforms

    def __get_event_types(self) -> _EventTypes:
        # Some comments:
        # - Standard firmware waveforms are rather stored in the event structure; event information
        #     is also stored in EventInfo returned by get_event_info()
        # - DPPX743Event is not supported by CAEN_DGTZ_DecodeDPPWaveforms
        F = FirmwareCode
        B = BoardFamilyCode
        match self.__info.firmware_code, self.__info.family_code:
            case F.STANDARD_FW, B.XX721 | B.XX731:
                return _EventTypes(Uint8Event, _Never)
            case F.STANDARD_FW, _:
                return _EventTypes(Uint16Event, _Never)
            case F.STANDARD_FW_X742, B.XX742:
                return _EventTypes(X742Event, _Never)
            case F.STANDARD_FW_X743, B.XX743:
                return _EventTypes(X743Event, _Never)
            case F.V1724_DPP_PHA | F.V1730_DPP_PHA, _:
                return _EventTypes(DPPPHAEvent, DPPPHAWaveforms)
            case F.V1720_DPP_PSD | F.V1730_DPP_PSD | F.V1751_DPP_PSD, _:
                return _EventTypes(DPPPSDEvent, DPPPSDWaveforms)
            case F.V1720_DPP_CI, _:
                return _EventTypes(DPPCIEvent, DPPCIWaveforms)
            case F.V1743_DPP_CI, _:
                return _EventTypes(DPPX743Event, _Never)
            case F.V1740_DPP_QDC, _:
                return _EventTypes(DPPQDCEvent, DPPQDCWaveforms)
            case F.V1730_DPP_ZLE, _:
                return _EventTypes(ZLEEvent730, ZLEWaveforms730)
            case F.V1751_DPP_ZLE, _:
                return _EventTypes(ZLEEvent751, ZLEWaveforms751)
            case F.V1724_DPP_DAW | F.V1730_DPP_DAW, _:
                return _EventTypes(DPPDAWEvent, DPPDAWWaveforms)
            case _:
                raise RuntimeError('Unknown firmware')

    # C API bindings

    _T = TypeVar('_T', bound='Device')

    @classmethod
    def open(cls: type[_T], connection_type: ConnectionType, arg: int | str, conet_node: int, vme_base_address: int) -> _T:
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

        Also frees all allocated resources.
        """
        match self.__firmware_type:
            case _FirmwareType.STANDARD:
                self.free_event()
            case _FirmwareType.DPP:
                self.free_dpp_events()
                self.free_dpp_waveforms()
            case _FirmwareType.ZLE:
                self.free_zle_events_and_waveforms()
            case _FirmwareType.DAW:
                self.free_daw_events_and_waveforms()
        self.free_readout_buffer()
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

    def get_info(self) -> BoardInfo:
        """
        Binding of CAEN_DGTZ_GetInfo()
        """
        l_data = _types.BoardInfoRaw()
        lib.get_info(self.handle, l_data)
        return BoardInfo.from_raw(l_data)

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

    def set_record_length(self, value: int, channel: int | None = None) -> None:
        """
        Binding of CAEN_DGTZ_SetRecordLength()
        """
        if channel is None:
            lib.set_record_length(self.handle, value)
        else:
            l_channel = ct.c_int32(channel)
            lib.set_record_length(self.handle, value, l_channel)

    def get_record_length(self, channel: int | None = None) -> int:
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

    def set_group_dc_offset(self, group: int, value: int) -> None:
        """
        Binding of CAEN_DGTZ_SetGroupDCOffset()
        """
        lib.set_group_dc_offset(self.handle, group, value)

    def get_group_dc_offset(self, group: int) -> int:
        """
        Binding of CAEN_DGTZ_GetGroupDCOffset()
        """
        l_value = ct.c_uint32()
        lib.get_group_dc_offset(self.handle, group, l_value)
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

    def set_group_trigger_threshold(self, group: int, value: int) -> None:
        """
        Binding of CAEN_DGTZ_SetGroupTriggerThreshold()
        """
        lib.set_group_trigger_threshold(self.handle, group, value)

    def get_group_trigger_threshold(self, group: int) -> int:
        """
        Binding of CAEN_DGTZ_GetGroupTriggerThreshold()
        """
        l_value = ct.c_uint32()
        lib.get_group_trigger_threshold(self.handle, group, l_value)
        return l_value.value

    def set_zero_suppression_mode(self, mode: ZSMode) -> None:
        """
        Binding of CAEN_DGTZ_SetZeroSuppressionMode()
        """
        lib.set_zero_suppression_mode(self.handle, mode)

    def get_zero_suppression_mode(self) -> ZSMode:
        """
        Binding of CAEN_DGTZ_GetZeroSuppressionMode()
        """
        l_value = ct.c_int()
        lib.get_zero_suppression_mode(self.handle, l_value)
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

    def set_acquisition_mode(self, mode: AcqMode) -> None:
        """
        Binding of CAEN_DGTZ_SetAcquisitionMode()
        """
        lib.set_acquisition_mode(self.handle, mode)

    def get_acquisition_mode(self) -> AcqMode:
        """
        Binding of CAEN_DGTZ_GetAcquisitionMode()
        """
        l_value = ct.c_int()
        lib.get_acquisition_mode(self.handle, l_value)
        return AcqMode(l_value.value)

    def set_run_synchronization_mode(self, mode: RunSyncMode) -> None:
        """
        Binding of CAEN_DGTZ_SetRunSynchronizationMode()
        """
        lib.set_run_synchronization_mode(self.handle, mode)

    def get_run_synchronization_mode(self) -> RunSyncMode:
        """
        Binding of CAEN_DGTZ_GetRunSynchronizationMode()
        """
        l_value = ct.c_int()
        lib.get_run_synchronization_mode(self.handle, l_value)
        return RunSyncMode(l_value.value)

    def set_analog_mon_output(self, mode: AnalogMonitorOutputMode) -> None:
        """
        Binding of CAEN_DGTZ_SetAnalogMonOutput()
        """
        lib.set_analog_mon_output(self.handle, mode)

    def get_analog_mon_output(self) -> AnalogMonitorOutputMode:
        """
        Binding of CAEN_DGTZ_GetAnalogMonOutput()
        """
        l_value = ct.c_int()
        lib.get_analog_mon_output(self.handle, l_value)
        return AnalogMonitorOutputMode(l_value.value)

    def set_analog_inspection_mon_params(self, channel_mask: int, offset: int, mf: AnalogMonitorMagnify, ami: AnalogMonitorInspectorInverter) -> None:
        """
        Binding of CAEN_DGTZ_SetAnalogInspectionMonParams()
        """
        lib.set_analog_inspection_mon_params(self.handle, channel_mask, offset, mf, ami)

    def get_analog_inspection_mon_params(self) -> tuple[int, int, AnalogMonitorMagnify, AnalogMonitorInspectorInverter]:
        """
        Binding of CAEN_DGTZ_GetAnalogInspectionMonParams()
        """
        l_channel_mask = ct.c_uint32()
        l_offset = ct.c_uint32()
        l_mf = ct.c_int()
        l_ami = ct.c_int()
        lib.get_analog_inspection_mon_params(self.handle, l_channel_mask, l_offset, l_mf, l_ami)
        return l_channel_mask.value, l_offset.value, AnalogMonitorMagnify(l_mf.value), AnalogMonitorInspectorInverter(l_ami.value)

    def disable_event_aligned_readout(self) -> None:
        """
        Binding of CAEN_DGTZ_DisableEventAlignedReadout()
        """
        lib.disable_event_aligned_readout(self.handle)

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

    def malloc_readout_buffer(self) -> int:
        """
        Binding of CAEN_DGTZ_MallocReadoutBuffer()
        """
        if self.__ro_buff is not None:
            raise RuntimeError('Readout buffer already allocated')
        l_buffer = _types.ReadoutBuffer()
        lib.malloc_readout_buffer(self.handle, l_buffer.data, l_buffer.size)
        self.__ro_buff = l_buffer
        return self.__ro_buff.size.value

    def free_readout_buffer(self) -> None:
        """
        Binding of CAEN_DGTZ_FreeReadoutBuffer()
        """
        # C API fails if __ro_buff is NULL
        if self.__ro_buff is None:
            return
        lib.free_readout_buffer(self.__ro_buff.data)
        self.__ro_buff = None

    @property
    def readout_buffer(self) -> memoryview:
        """
        Get content of the readout buffer as a memoryview

        Useful to access raw data, e.g. for saving to a file.

        The content is valid until the next call to one of:
        - read_data()
        - free_readout_buffer()
        """
        if self.__ro_buff is None:
            raise RuntimeError('Readout buffer not allocated')
        return self.__ro_buff.as_memoryview()

    def read_data(self, mode: ReadMode) -> None:
        """
        Binding of CAEN_DGTZ_ReadData()
        """
        if self.__ro_buff is None:
            raise RuntimeError('Readout buffer not allocated')
        lib.read_data(self.handle, mode, self.__ro_buff.data, self.__ro_buff.occupancy)

    def get_num_events(self) -> int:
        """
        Binding of CAEN_DGTZ_GetNumEvents()
        """
        if self.__ro_buff is None:
            raise RuntimeError('Readout buffer not allocated')
        l_value = ct.c_uint32()
        lib.get_num_events(self.handle, self.__ro_buff.data, self.__ro_buff.occupancy, l_value)
        return l_value.value

    def get_event_info(self, num_event: int) -> tuple[EventInfo, _Buffer]:
        """
        Binding of CAEN_DGTZ_GetEventInfo()

        The content of buffer is valid until the next call to one of:
        - read_data()
        - free_readout_buffer()
        """
        if self.__firmware_type is not _FirmwareType.STANDARD:
            raise RuntimeError('Not a Standard firmware')
        if self.__ro_buff is None:
            raise RuntimeError('Readout buffer not allocated')
        l_event_p = _c_char_p()
        l_event_info = _types.EventInfoRaw()
        lib.get_event_info(self.handle, self.__ro_buff.data, self.__ro_buff.occupancy, num_event, l_event_info, l_event_p)
        event_info = EventInfo.from_raw(l_event_info)
        return event_info, _Buffer(l_event_p)

    def decode_event(self, event_data: _Buffer) -> Uint16Event | Uint8Event | X742Event | X743Event:
        """
        Binding of CAEN_DGTZ_DecodeEvent()

        The content is valid until the next call to one of:
        - decode_event() (this method)
        - free_event()
        - read_data()
        - free_readout_buffer()
        """
        if self.__scope_event is None:
            raise RuntimeError('Event not allocated')
        lib.decode_event(self.handle, event_data.data, self.__scope_event)
        evt_p = ct.cast(self.__scope_event, self.__e.raw_p)
        return self.__e.native(evt_p.contents)

    def free_event(self) -> None:
        """
        Binding of CAEN_DGTZ_FreeEvent()
        """
        if self.__firmware_type is not _FirmwareType.STANDARD:
            raise RuntimeError('Not a Standard firmware')
        if self.__scope_event is None:
            return
        lib.free_event(self.handle, self.__scope_event)
        self.__scope_event = None

    def get_dpp_events(self) -> list[list[DPPPHAEvent]] | list[list[DPPPSDEvent]] | list[list[DPPCIEvent]] | list[list[DPPX743Event]] | list[list[DPPQDCEvent]]:
        """
        Binding of CAEN_DGTZ_GetDPPEvents() for DPP only

        Note: for DAW firmware use get_daw_events()

        The content is valid until the next call to one of:
        - read_data()
        - free_dpp_events()
        - free_readout_buffer()
        """
        if self.__firmware_type is not _FirmwareType.DPP:
            raise RuntimeError('Not a DPP firmware')
        if self.__ro_buff is None:
            raise RuntimeError('Readout buffer not allocated')
        if self.__dpp_events is None:
            raise RuntimeError('DPP events not allocated')
        l_n_events_ch = (ct.c_uint32 * self.__info.channels)()
        lib.get_dpp_events(self.handle, self.__ro_buff.data, self.__ro_buff.occupancy, self.__dpp_events, l_n_events_ch)
        evts_p_p = ct.cast(self.__dpp_events, self.__e.raw_p_p)
        # Safe to use zip because l_n_events_ch has the size of
        # self.__info.channels: this will constrain the iteration of the
        # unbound evts_p_p too.
        ch_data = zip(evts_p_p, l_n_events_ch)  # type: ignore
        return [list(map(self.__e.native, evts_p[:n_events])) for evts_p, n_events in ch_data]

    def get_daw_events(self) -> list[DPPDAWEvent]:
        """
        Binding of CAEN_DGTZ_GetDPPEvents() for DAW only

        The content is valid until the next call to one of:
        - read_data()
        - free_daw_events_and_waveforms()
        - free_readout_buffer()
        """
        if self.__firmware_type is not _FirmwareType.DAW:
            raise RuntimeError('Not a DAW firmware')
        if self.__ro_buff is None:
            raise RuntimeError('Readout buffer not allocated')
        if self.__daw_events is None:
            raise RuntimeError('DAW events not allocated')
        n_words = self.__ro_buff.occupancy.value // 4
        if n_words == 0:
            return []  # Workaround for empty buffer, causes a segfault in the C API
        l_n_events = ct.c_uint32()
        lib.get_dpp_events(self.handle, self.__ro_buff.data, n_words, self.__daw_events.data, l_n_events)
        evts_p = ct.cast(self.__daw_events.data, self.__e.raw_p)
        return list(map(self.__e.native, evts_p[:l_n_events.value]))

    def malloc_dpp_events(self) -> int:
        """
        Binding of CAEN_DGTZ_MallocDPPEvents() for DPP only

        Note: for DAW firmware use malloc_daw_events_and_waveforms()
        """
        if self.__firmware_type is not _FirmwareType.DPP:
            raise RuntimeError('Not a DPP firmware')
        if self.__dpp_events is not None:
            raise RuntimeError('DPP events already allocated')
        l_dpp_events = (ct.c_void_p * self.__info.channels)()
        l_size = ct.c_uint32()
        lib.malloc_dpp_events(self.handle, l_dpp_events, l_size)
        self.__dpp_events = l_dpp_events
        return l_size.value

    def malloc_daw_events_and_waveforms(self) -> None:
        """
        Binding of CAEN_DGTZ_MallocDPPEvents() and CAEN_DGTZ_MallocDPPWaveforms() for DAW only

        See malloc_zle_events_and_waveforms() for the rationale of this
        combined method.
        """
        if self.__firmware_type is not _FirmwareType.DAW:
            raise RuntimeError('Not a DAW firmware')
        if self.__daw_events is not None:
            raise RuntimeError('DAW events already allocated')
        n_events = self.get_max_num_events_blt()
        # Allocate events
        l_daw_events = ct.c_void_p()
        l_size = ct.c_uint32()  # Unused, pretty useless in the C API too
        lib.malloc_dpp_events(self.handle, l_daw_events, l_size)
        # Allocate waveforms
        match self.__info.firmware_code:
            case FirmwareCode.V1730_DPP_DAW:
                # Waveforms are allocated inside each event/channel structure
                evts_p = ct.cast(l_daw_events, self.__e.raw_p)
                for evt in evts_p[:n_events]:
                    for ch in evt.Channel[:self.__info.channels]:
                        l_value = ct.c_void_p()
                        lib.malloc_dpp_waveforms(self.handle, l_value, l_size)
                        ch.contents.Waveforms = ct.cast(l_value, self.__w.raw_p)
            case FirmwareCode.V1724_DPP_DAW:
                raise RuntimeError('Firmware not supported by the C API')
            case _:
                raise RuntimeError('Not a DAW firmware')
        self.__daw_events = _EventsBuffer(l_daw_events, n_events)

    def free_dpp_events(self) -> None:
        """
        Binding of CAEN_DGTZ_FreeDPPEvents() for DPP only

        Note: for DAW firmware use free_daw_events_and_waveforms()
        """
        if self.__firmware_type is not _FirmwareType.DPP:
            raise RuntimeError('Not a DPP firmware')
        if self.__dpp_events is None:
            return
        lib.free_dpp_events(self.handle, self.__dpp_events)
        self.__dpp_events = None

    def free_daw_events_and_waveforms(self) -> None:
        """
        Binding of CAEN_DGTZ_FreeDPPEvents() and CAEN_DGTZ_FreeDPPWaveforms() for DAW only

        See malloc_zle_events_and_waveforms() for the rationale of this
        combined method.
        """
        if self.__firmware_type is not _FirmwareType.DAW:
            raise RuntimeError('Not a DAW firmware')
        if self.__daw_events is None:
            return
        # Free waveforms, with a workaround for a bug in the C API, fixed in v2.19.0, that will lead to a memory leak
        match self.__info.firmware_code:
            case FirmwareCode.V1730_DPP_DAW:
                evts_p = ct.cast(self.__daw_events.data, self.__e.raw_p)
                for evt in evts_p[:self.__daw_events.n_events]:
                    for ch in evt.Channel[:self.__info.channels]:
                        try:
                            lib.free_dpp_waveforms(self.handle, ch.contents.Waveforms)
                        except Error as ex:
                            if ex.code is not Error.Code.FUNCTION_NOT_ALLOWED or lib.ver_at_least((2, 19, 0)):
                                raise
            case FirmwareCode.V1724_DPP_DAW:
                raise RuntimeError('Firmware not supported by the C API')
            case _:
                raise RuntimeError('Not a DAW firmware')
        # Free events
        lib.free_dpp_events(self.handle, self.__daw_events.data)
        self.__daw_events = None

    def malloc_dpp_waveforms(self) -> int:
        """
        Binding of CAEN_DGTZ_MallocDPPWaveforms() for DPP only

        Note: for DAW use malloc_daw_events_and_waveforms().
        """
        if self.__firmware_type is not _FirmwareType.DPP:
            raise RuntimeError('Not a DPP firmware')
        if self.__dpp_waveforms is not None:
            raise RuntimeError('DPP waveforms already allocated')
        l_waveforms = ct.c_void_p()
        l_size = ct.c_uint32()
        lib.malloc_dpp_waveforms(self.handle, l_waveforms, l_size)
        self.__dpp_waveforms = l_waveforms
        return l_size.value

    def free_dpp_waveforms(self) -> None:
        """
        Binding of CAEN_DGTZ_FreeDPPWaveforms() for DPP only

        Note: for DAW use free_daw_events_and_waveforms() method.
        """
        if self.__firmware_type is not _FirmwareType.DPP:
            raise RuntimeError('Not a DPP firmware')
        if self.__dpp_waveforms is None:
            return
        lib.free_dpp_waveforms(self.handle, self.__dpp_waveforms)
        self.__dpp_waveforms = None

    def decode_dpp_waveforms(self, ch: int, evt_id: int) -> DPPPHAWaveforms | DPPPSDWaveforms | DPPCIWaveforms | DPPQDCWaveforms:
        """
        Binding of CAEN_DGTZ_DecodeDPPWaveforms() for DPP only

        Note: for DAW firmware use decode_daw_waveforms()

        The content is valid until the next call to one of:
        - decode_dpp_waveforms() (this method)
        - read_data()
        - free_dpp_waveforms()
        """
        if self.__firmware_type is not _FirmwareType.DPP:
            raise RuntimeError('Not a DPP firmware')
        if self.__dpp_events is None:
            raise RuntimeError('DPP events not allocated')
        if self.__dpp_waveforms is None:
            raise RuntimeError('DPP waveforms not allocated')
        evts_p_p = ct.cast(self.__dpp_events, self.__e.raw_p_p)
        lib.decode_dpp_waveforms(self.handle, ct.byref(evts_p_p[ch][evt_id]), self.__dpp_waveforms)
        wave_p = ct.cast(self.__dpp_waveforms, self.__w.raw_p)
        return self.__w.native(wave_p.contents)

    def decode_daw_waveforms(self, evt_id: int) -> None:
        """
        Binding of CAEN_DGTZ_DecodeDPPWaveforms() for DAW only

        Returns None, the waveforms are placed directly into the event structure,
        at the same index used to decode the event with get_daw_events().
        """
        if self.__firmware_type is not _FirmwareType.DAW:
            raise RuntimeError('Not a DAW firmware')
        if self.__daw_events is None:
            raise RuntimeError('DAW events not allocated')
        evts_p = ct.cast(self.__daw_events.data, self.__e.raw_p)
        lib.decode_dpp_waveforms(self.handle, ct.byref(evts_p[evt_id]), None)

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

    def set_dpp_parameters(self, channel_mask: int, params: DPPPHAParams | DPPPSDParams | DPPCIParams | DPPQDCParams | DPPX743Params) -> None:
        """
        Binding of CAEN_DGTZ_SetDPPParameters()
        """
        l_params = params.to_raw()
        lib.set_dpp_parameters(self.handle, channel_mask, ct.byref(l_params))

    def set_dpp_acquisition_mode(self, mode: DPPAcqMode, param: DPPSaveParam) -> None:
        """
        Binding of CAEN_DGTZ_SetDPPAcquisitionMode()
        """
        lib.set_dpp_acquisition_mode(self.handle, mode, param)

    def get_dpp_acquisition_mode(self) -> tuple[DPPAcqMode, DPPSaveParam]:
        """
        Binding of CAEN_DGTZ_GetDPPAcquisitionMode()
        """
        l_mode = ct.c_int()
        l_param = ct.c_int()
        lib.get_dpp_acquisition_mode(self.handle, l_mode, l_param)
        return DPPAcqMode(l_mode.value), DPPSaveParam(l_param.value)

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

    def set_dpp_virtual_probe(self, trace: DPPTrace, probe: DPPProbe) -> None:
        """
        Binding of CAEN_DGTZ_SetDPP_VirtualProbe()
        """
        lib.set_dpp_virtual_probe(self.handle, trace, probe)

    def get_dpp_virtual_probe(self, trace: DPPTrace) -> DPPProbe:
        """
        Binding of CAEN_DGTZ_GetDPP_VirtualProbe()
        """
        l_value = ct.c_int()
        lib.get_dpp_virtual_probe(self.handle, trace, l_value)
        return DPPProbe(l_value.value)

    def get_dpp_supported_virtual_probes(self, trace: DPPTrace) -> tuple[DPPProbe, ...]:
        """
        Binding of CAEN_DGTZ_GetDPP_SupportedVirtualProbes()
        """
        max_probes = len(DPPProbe)  # Assuming trace supports at most all probes
        l_value = (ct.c_int * max_probes)()
        l_num_probes = ct.c_int()
        lib.get_dpp_supported_virtual_probes(self.handle, trace, l_value, l_num_probes)
        return tuple(map(DPPProbe, l_value[:l_num_probes.value]))

    def allocate_event(self) -> None:
        """
        Binding of CAEN_DGTZ_AllocateEvent()
        """
        if self.__firmware_type is not _FirmwareType.STANDARD:
            raise RuntimeError('Not a standard firmware')
        if self.__scope_event is not None:
            raise RuntimeError('Event already allocated')
        l_event = ct.c_void_p()
        lib.allocate_event(self.handle, l_event)
        self.__scope_event = l_event

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

    def set_group_fast_trigger_dc_offset(self, group: int, dc_value: int) -> None:
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

    def load_drs4_correction_data(self, frequency: DRS4Frequency) -> None:
        """
        Binding of CAEN_DGTZ_LoadDRS4CorrectionData()
        """
        lib.load_drs4_correction_data(self.handle, frequency)

    def get_correction_tables(self, frequency: DRS4Frequency) -> DRS4Correction:
        """
        Binding of CAEN_DGTZ_GetCorrectionTables()
        """
        l_ctable = _types.DRS4CorrectionRaw()
        lib.get_correction_tables(self.handle, frequency, ct.byref(l_ctable))
        return DRS4Correction.from_raw(l_ctable)

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

    def decode_zle_waveforms(self, evt_id: int) -> None:
        """
        Binding of CAEN_DGTZ_DecodeZLEWaveforms()

        Returns None, the waveforms are placed directly into the event structure,
        at the same index used to decode the event with get_zle_events().
        """
        if self.__zle_events is None:
            raise RuntimeError('ZLE events not allocated')
        evts_p = ct.cast(self.__zle_events.data, self.__e.raw_p)
        match self.__info.firmware_code:
            case FirmwareCode.V1730_DPP_ZLE:
                # Last argument is ignored, placed directly into the event structure
                lib.decode_zle_waveforms(self.handle, ct.byref(evts_p[evt_id]), None)
            case FirmwareCode.V1751_DPP_ZLE:
                assert self.__zle_waveforms is not None
                lib.decode_zle_waveforms(self.handle, ct.byref(evts_p[evt_id]), ct.byref(self.__zle_waveforms[evt_id]))
            case _:
                raise RuntimeError('Not a ZLE firmware')

    def free_zle_events_and_waveforms(self) -> None:
        """
        Binding of CAEN_DGTZ_FreeZLEEvents() and CAEN_DGTZ_FreeZLEWaveforms()

        See malloc_zle_events_and_waveforms() for the rationale of this
        combined method.
        """
        if self.__firmware_type is not _FirmwareType.ZLE:
            raise RuntimeError('Not a ZLE firmware')
        if self.__zle_events is None:
            return
        # Free waveforms
        match self.__info.firmware_code:
            case FirmwareCode.V1730_DPP_ZLE:
                evts_p = ct.cast(self.__zle_events.data, self.__e.raw_p)
                for evt in evts_p[:self.__zle_events.n_events]:
                    for ch in evt.Channel[:self.__info.channels]:
                        lib.free_zle_waveforms(self.handle, ch.contents.Waveforms)
            case FirmwareCode.V1751_DPP_ZLE:
                assert self.__zle_waveforms is not None
                for value in self.__zle_waveforms:
                    lib.free_zle_waveforms(self.handle, ct.byref(value))
                self.__zle_waveforms = None
            case _:
                raise RuntimeError('Not a ZLE firmware')
        # Free events
        lib.free_zle_events(self.handle, self.__zle_events.data)
        self.__zle_events = None

    def malloc_zle_events_and_waveforms(self) -> None:
        """
        Binding of CAEN_DGTZ_MallocZLEEvents() and CAEN_DGTZ_MallocZLEWaveforms()

        The rationale for this combined method is that, for V1730, the waveforms
        are allocated inside each event/channel structure. We need to allocate
        the events first, then the waveforms inside each event/channel.

        Even if in V1751 the waveforms are allocated separately, we provide
        this combined method for symmetry and convenience, embedding the
        waveforms pointers inside the event class.
        """
        if self.__firmware_type is not _FirmwareType.ZLE:
            raise RuntimeError('Not a ZLE firmware')
        if self.__zle_events is not None:
            raise RuntimeError('ZLE events already allocated')
        n_events = self.get_max_num_events_blt()
        # Allocate events
        l_zle_events = ct.c_void_p()
        l_size = ct.c_uint32()  # Unused, pretty useless in the C API too
        lib.malloc_zle_events(self.handle, l_zle_events, l_size)
        # Allocate waveforms
        match self.__info.firmware_code:
            case FirmwareCode.V1730_DPP_ZLE:
                # Waveforms are allocated inside each event/channel structure
                evts_p = ct.cast(l_zle_events, self.__e.raw_p)
                for evt in evts_p[:n_events]:
                    for ch in evt.Channel[:self.__info.channels]:
                        l_value = ct.c_void_p()
                        lib.malloc_zle_waveforms(self.handle, l_value, l_size)
                        ch.contents.Waveforms = ct.cast(l_value, self.__w.raw_p)
            case FirmwareCode.V1751_DPP_ZLE:
                # We use an external array of waveforms, one per event,
                # to make the interface similar to the V1730 case.
                assert self.__zle_waveforms is None
                l_values = (self.__w.raw * n_events)()
                for value in l_values:
                    lib.malloc_zle_waveforms(self.handle, ct.byref(value), l_size)
                self.__zle_waveforms = l_values
            case _:
                raise RuntimeError('Not a ZLE firmware')
        self.__zle_events = _EventsBuffer(l_zle_events, n_events)

    def get_zle_events(self) -> list[ZLEEvent730] | list[ZLEEvent751]:
        """
        Binding of CAEN_DGTZ_GetZLEEvents()

        The content is valid until the next call to one of:
        - read_data()
        - free_zle_events_and_waveforms()
        - free_readout_buffer()
        """
        if self.__firmware_type is not _FirmwareType.ZLE:
            raise RuntimeError('Not a ZLE firmware')
        if self.__ro_buff is None:
            raise RuntimeError('Readout buffer not allocated')
        if self.__zle_events is None:
            raise RuntimeError('ZLE events not allocated')
        n_words = self.__ro_buff.occupancy.value // 4
        if n_words == 0:
            return []  # Workaround for empty buffer, causes a segfault in the C API
        l_n_events = ct.c_uint32()
        lib.get_zle_events(self.handle, self.__ro_buff.data, n_words, self.__zle_events.data, l_n_events)
        evts_p = ct.cast(self.__zle_events.data, self.__e.raw_p)
        match self.__info.firmware_code:
            case FirmwareCode.V1730_DPP_ZLE:
                return list(map(self.__e.native, evts_p[:l_n_events.value]))
            case FirmwareCode.V1751_DPP_ZLE:
                # Also adds the waveforms to the event structure, where
                # the user will find the waveforms after calling
                # decode_zle_waveforms().
                assert self.__zle_waveforms is not None
                # We only need to limit one of the two sequences, as in zip:
                # the resulting size is the minimum of the two.
                return list(map(self.__e.native, evts_p[:l_n_events.value], self.__zle_waveforms))
            case _:
                raise RuntimeError('Not a ZLE firmware')

    def set_zle_parameters(self, channel_mask: int, params: ZLEParams751) -> None:
        """
        Binding of CAEN_DGTZ_SetZLEParameters()
        """
        l_params = params.to_raw()
        lib.set_zle_parameters(self.handle, channel_mask, ct.byref(l_params))

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

    def read_eeprom(self, eeprom_index: int, add: int, num_bytes: int) -> bytes:
        """
        Binding of _CAEN_DGTZ_Read_EEPROM()
        """
        buf = (ct.c_ubyte * num_bytes)()
        lib.read_eeprom(self.handle, eeprom_index, add, num_bytes, buf)
        return ct.string_at(buf, num_bytes)

    def write_eeprom(self, eeprom_index: int, add: int, data: bytes) -> None:
        """
        Binding of _CAEN_DGTZ_Write_EEPROM()
        """
        l_num_bytes = len(data)
        buf = (ct.c_ubyte * l_num_bytes)(*data)
        lib.write_eeprom(self.handle, eeprom_index, add, l_num_bytes, buf)

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

    def set_sam_acquisition_mode(self, mode: AcquisitionMode) -> None:
        """
        Binding of CAEN_DGTZ_SetSAMAcquisitionMode()
        """
        lib.set_sam_acquisition_mode(self.handle, mode)

    def get_sam_acquisition_mode(self) -> AcquisitionMode:
        """
        Binding of CAEN_DGTZ_GetSAMAcquisitionMode()
        """
        l_value = ct.c_int()
        lib.get_sam_acquisition_mode(self.handle, l_value)
        return AcquisitionMode(l_value.value)

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

    def __hash__(self) -> int:
        return hash(self.handle)
