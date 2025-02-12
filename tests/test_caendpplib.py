"""Tests for the caendpp module."""

import unittest
from unittest.mock import ANY, DEFAULT, patch

import caen_libs.caendpplib as dpp


class TestDevice(unittest.TestCase):
    """Test the Device class."""

    def setUp(self):
        patcher = patch('caen_libs.caendpplib.lib', autospec=True)
        self.addCleanup(patcher.stop)
        self.mock_lib = patcher.start()
        def side_effect(*args):
            args[0].value = 0xdeadbeaf
            return DEFAULT
        self.mock_lib.init_library.side_effect = side_effect
        self.device = dpp.Device.open()
        self.addCleanup(self.device.close)

    def test_error_handling(self):
        """Test error handling."""
        self.mock_lib.init_library.side_effect = dpp.Error('Test error', -100, 'InitLibrary')
        with self.assertRaises(dpp.Error):
            dpp.Device.open()

    def test_device_close(self):
        """Test close_device"""
        self.device.close()
        self.mock_lib.end_library.assert_called_once_with(self.device.handle)

    def test_add_board(self):
        """Test add_board"""
        params = dpp.ConnectionParams(dpp.ConnectionType.USB, 0)
        def side_effect(*args):
            args[2].value = 0
            return DEFAULT
        self.mock_lib.add_board.side_effect = side_effect
        result = self.device.add_board(params)
        self.assertEqual(result, 0)
        self.mock_lib.add_board.assert_called_once_with(self.device.handle, ANY, ANY)

    def test_get_dpp_info(self):
        """Test get_dpp_info"""
        def side_effect(*args):
            args[2].DPPCodeMaj = dpp.DPPCode.CI_X720
            return DEFAULT
        self.mock_lib.get_dpp_info.side_effect = side_effect
        info = self.device.get_dpp_info(0)
        self.assertIsInstance(info, dpp.Info)
        self.mock_lib.get_dpp_info.assert_called_once_with(self.device.handle, 0, ANY)

    def test_start_board_parameters_guess(self):
        """Test start_board_parameters_guess"""
        params = dpp.DgtzParams()
        self.device.start_board_parameters_guess(0, 1, params)
        self.mock_lib.start_board_parameters_guess.assert_called_once_with(self.device.handle, 0, 1, ANY)

    def test_get_board_parameters_guess_status(self):
        """Test get_board_parameters_guess_status"""
        status = self.device.get_board_parameters_guess_status(0)
        self.assertIsInstance(status, dpp.GuessConfigStatus)
        self.mock_lib.get_board_parameters_guess_status.assert_called_once_with(self.device.handle, 0, ANY)

    def test_get_board_parameters_guess_result(self):
        """Test get_board_parameters_guess_result"""
        params, mask = self.device.get_board_parameters_guess_result(0)
        self.assertIsInstance(params, dpp.DgtzParams)
        self.assertIsInstance(mask, int)
        self.mock_lib.get_board_parameters_guess_result.assert_called_once_with(self.device.handle, 0, ANY, ANY)

    def test_stop_board_parameters_guess(self):
        """Test stop_board_parameters_guess"""
        self.device.stop_board_parameters_guess(0)
        self.mock_lib.stop_board_parameters_guess.assert_called_once_with(self.device.handle, 0)

    def test_set_board_configuration(self):
        """Test set_board_configuration"""
        params = dpp.DgtzParams()
        self.device.set_board_configuration(0, dpp.AcqMode.HISTOGRAM, params)
        self.mock_lib.set_board_configuration.assert_called_once_with(self.device.handle, 0, dpp.AcqMode.HISTOGRAM, ANY)

    def test_get_board_configuration(self):
        """Test get_board_configuration"""
        mode, params = self.device.get_board_configuration(0)
        self.assertIsInstance(mode, dpp.AcqMode)
        self.assertIsInstance(params, dpp.DgtzParams)
        self.mock_lib.get_board_configuration.assert_called_once_with(self.device.handle, 0, ANY, ANY)

    def test_acquisition_controls(self):
        """Test acquisition control methods"""
        self.device.start_acquisition(0)
        self.mock_lib.start_acquisition.assert_called_once_with(self.device.handle, 0)

        self.device.arm_acquisition(0)
        self.mock_lib.arm_acquisition.assert_called_once_with(self.device.handle, 0)

        self.device.stop_acquisition(0)
        self.mock_lib.stop_acquisition.assert_called_once_with(self.device.handle, 0)

    def test_histogram_operations(self):
        """Test histogram operations"""
        self.device.set_histogram_size(0, 1, 1024)
        self.mock_lib.set_histogram_size.assert_called_once_with(self.device.handle, 0, 1, 1024)

        self.device.get_histogram_size(0, 1)
        self.mock_lib.get_histogram_size.assert_called_once_with(self.device.handle, 0, 1, ANY)

        self.device.clear_histogram(0, 1)
        self.mock_lib.clear_histogram.assert_called_once_with(self.device.handle, 0, 1)

        self.device.reset_histogram(0, 1)
        self.mock_lib.reset_histogram.assert_called_once_with(self.device.handle, 0, 1)

    def test_list_events(self):
        """Test get_list_events"""
        events = self.device.get_list_events(0)
        self.assertIsInstance(events, tuple)
        self.mock_lib.get_list_events.assert_called_once_with(self.device.handle, 0, ANY, ANY)

    def test_waveform_operations(self):
        """Test waveform operations"""
        waveforms = self.device.allocate_waveform(0)
        self.assertIsInstance(waveforms, dpp.Waveforms)

        samples, tsample = self.device.get_waveform(0, True, waveforms)
        self.assertIsInstance(samples, int)
        self.assertIsInstance(tsample, float)
        self.mock_lib.get_waveform.assert_called_once_with(self.device.handle, 0, ANY, ANY, ANY, ANY, ANY, ANY, ANY)

    def test_statistics(self):
        """Test get_acq_stats"""
        stats = self.device.get_acq_stats(0)
        self.assertIsInstance(stats, dpp.Statistics)
        self.mock_lib.get_acq_stats.assert_called_once_with(self.device.handle, 0, ANY)

    def test_parameter_info(self):
        """Test get_parameter_info"""
        info = self.device.get_parameter_info(0, dpp.ParamID.RECORD_LENGTH)
        self.assertIsInstance(info, dpp.ParamInfo)
        self.mock_lib.get_parameter_info.assert_called_once_with(self.device.handle, 0, dpp.ParamID.RECORD_LENGTH, ANY)

    def test_hv_operations(self):
        """Test HV operations"""
        config = dpp.HVChannelConfig(0.0, 0.0, 0.0, 0.0, 0.0, dpp.PWDownMode.RAMP)

        self.device.set_hv_channel_configuration(0, 0, config)
        self.mock_lib.set_hv_channel_configuration.assert_called_once_with(self.device.handle, 0, 0, ANY)

        self.device.get_hv_channel_configuration(0, 0)
        self.mock_lib.get_hv_channel_configuration.assert_called_once_with(self.device.handle, 0, 0, ANY)

        self.device.set_hv_channel_power_on(0, 0, True)
        self.mock_lib.set_hv_channel_power_on.assert_called_once_with(self.device.handle, 0, 0, True)

        self.device.get_hv_channel_power_on(0, 0)
        self.mock_lib.get_hv_channel_power_on.assert_called_once_with(self.device.handle, 0, 0, ANY)

    def test_device_info(self):
        """Test device info methods"""
        info = self.device.get_daq_info(0)
        self.assertIsInstance(info, dpp.DAQInfo)
        self.mock_lib.get_daq_info.assert_called_once_with(self.device.handle, 0, ANY)

        temp = self.device.get_channel_temperature(0)
        self.assertIsInstance(temp, float)
        self.mock_lib.get_channel_temperature.assert_called_once_with(self.device.handle, 0, ANY)

    def test_device_enumeration(self):
        """Test enumerate_devices"""
        devices = self.device.enumerate_devices()
        self.assertIsInstance(devices, dpp.EnumeratedDevices)
        self.mock_lib.enumerate_devices.assert_called_once_with(ANY)

    def test_logger_severity(self):
        """Test logger severity methods"""
        self.device.set_logger_severity_mask(dpp.LogMask.ALL)
        self.mock_lib.set_logger_severity_mask.assert_called_once_with(self.device.handle, dpp.LogMask.ALL)

        mask = self.device.get_logger_severity_mask()
        self.assertIsInstance(mask, dpp.LogMask)
        self.mock_lib.get_logger_severity_mask.assert_called_once_with(ANY)

if __name__ == '__main__':
    unittest.main()
