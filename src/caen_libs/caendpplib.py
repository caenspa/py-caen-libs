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
from enum import IntEnum, unique
import os
from pathlib import Path
import sys
from typing import TypeVar

import numpy as np

from caen_libs import error, _utils
import caen_libs._caendpplibtypes as _types

# Add some types to the module namespace
from caen_libs._caendpplibtypes import (  # pylint: disable=W0611
    AcqMode,
    AcqStatus,
    BoardFamilyCode,
    BoardFormFactor,
    BoardModel,
    CoincLogic,
    CoincOp,
    CoincParams,
    COMStatus,
    ConnectionParams,
    ConnectionType,
    DAQInfo,
    DAQInfoRaw,
    DgtzParams,
    DigitalProbe1,
    DigitalProbe2,
    DPPCode,
    DumpMask,
    EnumeratedDevices,
    EnumerationSingleDevice,
    ExtLogic,
    ExtraParameters,
    GainStabilizationStatus,
    GateParams,
    GPIO,
    GPIOConfig,
    GPIOLogic,
    GPIOMode,
    GuessConfigStatus,
    Histogram,
    HVChannelConfig,
    HVChannelExternals,
    HVChannelInfo,
    HVChannelMonitoring,
    HVFamilyCode,
    HVRange,
    HVRangeInfo,
    INCoupling,
    Info,
    InfoType,
    InputImpedance,
    InputRange,
    IOLevel,
    ListEvent,
    ListParams,
    ListSaveMode,
    LogMask,
    MonOutParams,
    MultiHistoCondition,
    OutSignal,
    ParamID,
    ParamInfo,
    PHAMonOutProbe,
    PHAParams,
    ProbeTrigger,
    PulsePolarity,
    PWDownMode,
    ResetDetectionMode,
    RunSpecs,
    RunState,
    SpectrumControl,
    SpectrumMode,
    Statistics,
    StopCriteria,
    TempCorrParams,
    TriggerControl,
    TRReset,
    Units,
    VirtualProbe1,
    VirtualProbe2,
    WaveformParams,
    Waveforms,
)

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


# Utility definitions
_c_int_p = ct.POINTER(ct.c_int)
_c_int16_p = ct.POINTER(ct.c_int16)
_c_int32_p = ct.POINTER(ct.c_int32)
_c_uint8_p = ct.POINTER(ct.c_uint8)
_c_uint16_p = ct.POINTER(ct.c_uint16)
_c_uint32_p = ct.POINTER(ct.c_uint32)
_c_uint64_p = ct.POINTER(ct.c_uint64)
_c_double_p = ct.POINTER(ct.c_double)
_info_p = ct.POINTER(_types.InfoRaw)
_dgtz_params_p = ct.POINTER(_types.DgtzParamsRaw)
_list_event_p = ct.POINTER(_types.ListEventRaw)
_statistics_p = ct.POINTER(_types.StatisticsRaw)
_param_info_p = ct.POINTER(_types.ParamInfoRaw)
_daq_info_p = ct.POINTER(_types.DAQInfoRaw)
_hv_channel_config_p = ct.POINTER(_types.HVChannelConfigRaw)
_enumerated_devices_p = ct.POINTER(_types.EnumeratedDevicesRaw)


def _default_log_file_path() -> Path:
    """Generate file log path"""
    # Platform dependent stuff
    if sys.platform == 'win32':
        app_data = os.getenv('LOCALAPPDATA')
        assert app_data is not None
        user_path = Path(app_data) / 'CAEN'
    else:
        user_path = Path.home() / '.CAEN'
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
        self.add_board = self.__get('AddBoard', ct.c_int32, _types.ConnectionParamsRaw, _c_int32_p)
        self.get_dpp_info = self.__get('GetDPPInfo', ct.c_int32, ct.c_int32, _info_p)
        self.start_board_parameters_guess = self.__get('StartBoardParametersGuess', ct.c_int32, ct.c_int32, ct.c_uint32, _dgtz_params_p)
        self.get_board_parameters_guess_status = self.__get('GetBoardParametersGuessStatus', ct.c_int32, ct.c_int32, _c_int_p)
        self.get_board_parameters_guess_result = self.__get('GetBoardParametersGuessResult', ct.c_int32, ct.c_int32, _dgtz_params_p, _c_uint32_p)
        self.stop_board_parameters_guess = self.__get('StopBoardParametersGuess', ct.c_int32, ct.c_int32)
        self.set_board_configuration = self.__get('SetBoardConfiguration', ct.c_int32, ct.c_int32, ct.c_int, _types.DgtzParamsRaw)
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
        self.set_hv_channel_configuration = self.__get('SetHVChannelConfiguration', ct.c_int32, ct.c_int32, ct.c_int, _types.HVChannelConfigRaw)
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


@dataclass(slots=True)
class Device:
    """
    Class representing a device.
    """

    # Public members
    handle: int
    log_severity_mask: LogMask | None = None

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
        l_i = _types.InfoRaw()
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
        l_params = _types.DgtzParamsRaw()
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
        l_params = _types.DgtzParamsRaw()
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
        l_events = (_types.ListEventRaw * 8192)()
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
        l_stats = _types.StatisticsRaw()
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
        l_info = _types.ParamInfoRaw()
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
        l_info = _types.DAQInfoRaw()
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
        l_config = _types.HVChannelConfigRaw()
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
        l_devices = _types.EnumeratedDevicesRaw()
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

    def __hash__(self) -> int:
        return hash(self.handle)
