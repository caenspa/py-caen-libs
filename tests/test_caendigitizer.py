"""Tests for the caen_libs.caendigitizer module."""

import unittest
from unittest.mock import ANY, DEFAULT, MagicMock, patch

import ctypes as ct

import caen_libs.caendigitizer as dgtz


class _TestDevice(unittest.TestCase):

    mock_lib: MagicMock
    device: dgtz.Device

    def baseSetUp(self, fw_type: dgtz._types.FirmwareCode) -> None:
        """Common setup for tests."""
        patcher = patch('caen_libs.caendigitizer.lib', autospec=True)
        self.addCleanup(patcher.stop)
        self.mock_lib = patcher.start()
        def side_effect(*args):
            args[4].value = 0xdeadbeaf
            return DEFAULT
        self.mock_lib.open_digitizer2.side_effect = side_effect
        # open also invokes get_info to infer firmware type:
        # mock it here to assume a standard firmware.
        def info_side_effect(*args):
            amc_version = f'{fw_type}.0'.encode('ascii')
            args[1].AMC_FirmwareRel = amc_version
            args[1].Channels = 16
            return DEFAULT
        self.mock_lib.get_info.side_effect = info_side_effect
        self.device = dgtz.Device.open(dgtz.ConnectionType.USB, 0, 0, 0)
        self.addCleanup(self.device.close)

    def test_error_handling(self):
        """Test error handling."""
        self.mock_lib.open_digitizer2.side_effect = dgtz.Error('Test error', -1, 'OpenDevice2')
        with self.assertRaises(dgtz.Error):
            dgtz.Device.open(dgtz.ConnectionType.USB, 0, 0, 0)

    def test_close(self):
        """Test close"""
        self.device.close()
        self.mock_lib.close_digitizer.assert_called_once_with(self.device.handle)

    def test_get_info(self):
        """Test get_info"""
        self.device.get_info()
        self.mock_lib.get_info.assert_called()

    def test_reset(self):
        """Test reset"""
        self.device.reset()
        self.mock_lib.reset.assert_called_once_with(self.device.handle)

    def test_clear_data(self):
        """Test clear_data"""
        self.device.clear_data()
        self.mock_lib.clear_data.assert_called_once_with(self.device.handle)

    def test_send_sw_trigger(self):
        """Test send_sw_trigger"""
        self.device.send_sw_trigger()
        self.mock_lib.send_sw_trigger.assert_called_once_with(self.device.handle)

    def test_sw_start_acquisition(self):
        """Test sw_start_acquisition"""
        self.device.sw_start_acquisition()
        self.mock_lib.sw_start_acquisition.assert_called_once_with(self.device.handle)

    def test_sw_stop_acquisition(self):
        """Test sw_stop_acquisition"""
        self.device.sw_stop_acquisition()
        self.mock_lib.sw_stop_acquisition.assert_called_once_with(self.device.handle)

    def test_irq_wait(self):
        """Test irq_wait"""
        self.device.irq_wait(1000)
        self.mock_lib.irq_wait.assert_called_once_with(self.device.handle, 1000)

    def test_set_record_length(self):
        """Test set_record_length"""
        self.device.set_record_length(1024, 10)
        self.mock_lib.set_record_length.assert_called_once_with(self.device.handle, 1024, ANY)

    def test_get_record_length(self):
        """Test get_record_length"""
        self.device.get_record_length(10)
        self.mock_lib.get_record_length.assert_called_once_with(self.device.handle, ANY, ANY)

    def test_set_channel_enable_mask(self):
        """Test set_channel_enable_mask"""
        self.device.set_channel_enable_mask(0xF)
        self.mock_lib.set_channel_enable_mask.assert_called_once_with(self.device.handle, 0xF)

    def test_get_channel_enable_mask(self):
        """Test get_channel_enable_mask"""
        self.device.get_channel_enable_mask()
        self.mock_lib.get_channel_enable_mask.assert_called_once_with(self.device.handle, ANY)

    def test_set_group_enable_mask(self):
        """Test set_group_enable_mask"""
        self.device.set_group_enable_mask(0x3)
        self.mock_lib.set_group_enable_mask.assert_called_once_with(self.device.handle, 0x3)

    def test_get_group_enable_mask(self):
        """Test get_group_enable_mask"""
        self.device.get_group_enable_mask()
        self.mock_lib.get_group_enable_mask.assert_called_once_with(self.device.handle, ANY)

    def test_set_post_trigger_size(self):
        """Test set_post_trigger_size"""
        self.device.set_post_trigger_size(50)
        self.mock_lib.set_post_trigger_size.assert_called_once_with(self.device.handle, 50)

    def test_get_post_trigger_size(self):
        """Test get_post_trigger_size"""
        self.device.get_post_trigger_size()
        self.mock_lib.get_post_trigger_size.assert_called_once_with(self.device.handle, ANY)

    def test_set_channel_dc_offset(self):
        """Test set_channel_dc_offset"""
        self.device.set_channel_dc_offset(0, 100)
        self.mock_lib.set_channel_dc_offset.assert_called_once_with(self.device.handle, 0, 100)

    def test_get_channel_dc_offset(self):
        """Test get_channel_dc_offset"""
        self.device.get_channel_dc_offset(0)
        self.mock_lib.get_channel_dc_offset.assert_called_once_with(self.device.handle, 0, ANY)

    def test_set_acquisition_mode(self):
        """Test set_acquisition_mode"""
        self.device.set_acquisition_mode(dgtz.AcqMode.FIRST_TRG_CONTROLLED)
        self.mock_lib.set_acquisition_mode.assert_called_once_with(self.device.handle, dgtz.AcqMode.FIRST_TRG_CONTROLLED)

    def test_get_acquisition_mode(self):
        """Test get_acquisition_mode"""
        self.device.get_acquisition_mode()
        self.mock_lib.get_acquisition_mode.assert_called_once_with(self.device.handle, ANY)

    def test_write_register(self):
        """Test write_register"""
        self.device.write_register(0x1000, 0x1234)
        self.mock_lib.write_register.assert_called_once_with(self.device.handle, 0x1000, 0x1234)

    def test_read_register(self):
        """Test read_register"""
        self.device.read_register(0x1000)
        self.mock_lib.read_register.assert_called_once_with(self.device.handle, 0x1000, ANY)

    def test_registers(self):
        """Test registers"""
        address = 0x1000
        value = 0x1234
        self.device.registers[address] |= value
        self.mock_lib.read_register.assert_called_once_with(self.device.handle, address, ANY)
        self.mock_lib.write_register.assert_called_once_with(self.device.handle, address, value)

    def test_set_channel_trigger_threshold(self):
        """Test set_channel_trigger_threshold"""
        self.device.set_channel_trigger_threshold(0, 1.5)
        self.mock_lib.set_channel_trigger_threshold.assert_called_once()

    def test_get_channel_trigger_threshold(self):
        """Test get_channel_trigger_threshold"""
        self.device.get_channel_trigger_threshold(0)
        self.mock_lib.get_channel_trigger_threshold.assert_called_once()

    def test_set_max_num_events_blt(self):
        """Test set_max_num_events_blt"""
        self.device.set_max_num_events_blt(1)
        self.mock_lib.set_max_num_events_blt.assert_called_once_with(self.device.handle, 1)

    def test_get_max_num_events_blt(self):
        """Test get_max_num_events_blt"""
        self.device.get_max_num_events_blt()
        self.mock_lib.get_max_num_events_blt.assert_called_once_with(self.device.handle, ANY)

    def test_set_interrupt_config(self):
        """Test set_interrupt_config"""
        self.device.set_interrupt_config(dgtz.EnaDis.DISABLE, 2, 3, 4, dgtz.IRQMode.ROAK)
        self.mock_lib.set_interrupt_config.assert_called_once_with(self.device.handle, dgtz.EnaDis.DISABLE, 2, 3, 4, dgtz.IRQMode.ROAK)

    def test_get_interrupt_config(self):
        """Test get_interrupt_config"""
        self.device.get_interrupt_config()
        self.mock_lib.get_interrupt_config.assert_called_once_with(self.device.handle, ANY, ANY, ANY, ANY, ANY)

    def test_set_des_mode(self):
        """Test set_des_mode"""
        self.device.set_des_mode(1)
        self.mock_lib.set_des_mode.assert_called_once_with(self.device.handle, 1)

    def test_get_des_mode(self):
        """Test get_des_mode"""
        self.device.get_des_mode()
        self.mock_lib.get_des_mode.assert_called_once_with(self.device.handle, ANY)

    def test_set_sw_trigger_mode(self):
        """Test set_sw_trigger_mode"""
        self.device.set_sw_trigger_mode(dgtz.TriggerMode.ACQ_AND_EXTOUT)
        self.mock_lib.set_sw_trigger_mode.assert_called_once_with(self.device.handle, dgtz.TriggerMode.ACQ_AND_EXTOUT)

    def test_get_sw_trigger_mode(self):
        """Test get_sw_trigger_mode"""
        self.device.get_sw_trigger_mode()
        self.mock_lib.get_sw_trigger_mode.assert_called_once_with(self.device.handle, ANY)

    def test_set_ext_trigger_input_mode(self):
        """Test set_ext_trigger_input_mode"""
        self.device.set_ext_trigger_input_mode(dgtz.TriggerMode.ACQ_AND_EXTOUT)
        self.mock_lib.set_ext_trigger_input_mode.assert_called_once_with(self.device.handle, dgtz.TriggerMode.ACQ_AND_EXTOUT)

    def test_get_ext_trigger_input_mode(self):
        """Test get_ext_trigger_input_mode"""
        self.device.get_ext_trigger_input_mode()
        self.mock_lib.get_ext_trigger_input_mode.assert_called_once_with(self.device.handle, ANY)

    def test_set_channel_self_trigger(self):
        """Test set_channel_self_trigger"""
        self.device.set_channel_self_trigger(dgtz.TriggerMode.ACQ_AND_EXTOUT, 2)
        self.mock_lib.set_channel_self_trigger.assert_called_once_with(self.device.handle, dgtz.TriggerMode.ACQ_AND_EXTOUT, 2)

    def test_get_channel_self_trigger(self):
        """Test get_channel_self_trigger"""
        self.device.get_channel_self_trigger(1)
        self.mock_lib.get_channel_self_trigger.assert_called_once_with(self.device.handle, 1, ANY)

    def test_set_group_self_trigger(self):
        """Test set_group_self_trigger"""
        self.device.set_group_self_trigger(1, 2)
        self.mock_lib.set_group_self_trigger.assert_called_once_with(self.device.handle, 1, 2)

    def test_get_group_self_trigger(self):
        """Test get_group_self_trigger"""
        self.device.get_group_self_trigger(1)
        self.mock_lib.get_group_self_trigger.assert_called_once_with(self.device.handle, 1, ANY)

    def test_set_dpp_pre_trigger_size(self):
        """Test set_dpp_pre_trigger_size"""
        self.device.set_dpp_pre_trigger_size(1, 2)
        self.mock_lib.set_dpp_pre_trigger_size.assert_called_once_with(self.device.handle, 1, 2)

    def test_get_dpp_pre_trigger_size(self):
        """Test get_dpp_pre_trigger_size"""
        self.device.get_dpp_pre_trigger_size(1)
        self.mock_lib.get_dpp_pre_trigger_size.assert_called_once_with(self.device.handle, 1, ANY)

    def test_set_group_dc_offset(self):
        """Test set_group_dc_offset"""
        self.device.set_group_dc_offset(1, 2)
        self.mock_lib.set_group_dc_offset.assert_called_once_with(self.device.handle, 1, 2)

    def test_get_group_dc_offset(self):
        """Test get_group_dc_offset"""
        self.device.get_group_dc_offset(1)
        self.mock_lib.get_group_dc_offset.assert_called_once_with(self.device.handle, 1, ANY)

    def test_set_channel_pulse_polarity(self):
        """Test set_channel_pulse_polarity"""
        self.device.set_channel_pulse_polarity(1, dgtz.PulsePolarity.NEGATIVE)
        self.mock_lib.set_channel_pulse_polarity.assert_called_once_with(self.device.handle, 1, dgtz.PulsePolarity.NEGATIVE)

    def test_get_channel_pulse_polarity(self):
        """Test get_channel_pulse_polarity"""
        self.device.get_channel_pulse_polarity(1)
        self.mock_lib.get_channel_pulse_polarity.assert_called_once_with(self.device.handle, 1, ANY)

    def test_set_group_trigger_threshold(self):
        """Test set_group_trigger_threshold"""
        self.device.set_group_trigger_threshold(1, 2)
        self.mock_lib.set_group_trigger_threshold.assert_called_once_with(self.device.handle, 1, 2)

    def test_get_group_trigger_threshold(self):
        """Test get_group_trigger_threshold"""
        self.device.get_group_trigger_threshold(1)
        self.mock_lib.get_group_trigger_threshold.assert_called_once_with(self.device.handle, 1, ANY)

    def test_set_zero_suppression_mode(self):
        """Test set_zero_suppression_mode"""
        self.device.set_zero_suppression_mode(dgtz.ZSMode.AMP)
        self.mock_lib.set_zero_suppression_mode.assert_called_once_with(self.device.handle, dgtz.ZSMode.AMP)

    def test_get_zero_suppression_mode(self):
        """Test get_zero_suppression_mode"""
        self.device.get_zero_suppression_mode()
        self.mock_lib.get_zero_suppression_mode.assert_called_once_with(self.device.handle, ANY)

    def test_set_channel_zs_params(self):
        """Test set_channel_zs_params"""
        self.device.set_channel_zs_params(1, dgtz.ThresholdWeight.COARSE, 3, 4)
        self.mock_lib.set_channel_zs_params.assert_called_once_with(self.device.handle, 1, dgtz.ThresholdWeight.COARSE, 3, 4)

    def test_get_channel_zs_params(self):
        """Test get_channel_zs_params"""
        self.device.get_channel_zs_params(1)
        self.mock_lib.get_channel_zs_params.assert_called_once_with(self.device.handle, 1, ANY, ANY, ANY)

    def test_set_run_synchronization_mode(self):
        """Test set_run_synchronization_mode"""
        self.device.set_run_synchronization_mode(dgtz.RunSyncMode.DISABLED)
        self.mock_lib.set_run_synchronization_mode.assert_called_once_with(self.device.handle, dgtz.RunSyncMode.DISABLED)

    def test_get_run_synchronization_mode(self):
        """Test get_run_synchronization_mode"""
        self.device.get_run_synchronization_mode()
        self.mock_lib.get_run_synchronization_mode.assert_called_once_with(self.device.handle, ANY)

    def test_set_analog_mon_output(self):
        """Test set_analog_mon_output"""
        self.device.set_analog_mon_output(dgtz.AnalogMonitorOutputMode.ANALOG_INSPECTION)
        self.mock_lib.set_analog_mon_output.assert_called_once_with(self.device.handle, dgtz.AnalogMonitorOutputMode.ANALOG_INSPECTION)

    def test_get_analog_mon_output(self):
        """Test get_analog_mon_output"""
        self.device.get_analog_mon_output()
        self.mock_lib.get_analog_mon_output.assert_called_once_with(self.device.handle, ANY)

    def test_set_analog_inspection_mon_params(self):
        """Test set_analog_inspection_mon_params"""
        self.device.set_analog_inspection_mon_params(1, 2, dgtz.AnalogMonitorMagnify.MAGNIFY_1X, dgtz.AnalogMonitorInspectorInverter.N_1X)
        self.mock_lib.set_analog_inspection_mon_params.assert_called_once_with(self.device.handle, 1, 2, dgtz.AnalogMonitorMagnify.MAGNIFY_1X, dgtz.AnalogMonitorInspectorInverter.N_1X)

    def test_get_analog_inspection_mon_params(self):
        """Test get_analog_inspection_mon_params"""
        self.device.get_analog_inspection_mon_params()
        self.mock_lib.get_analog_inspection_mon_params.assert_called_once_with(self.device.handle, ANY, ANY, ANY, ANY)

    def test_disable_event_aligned_readout(self):
        """Test disable_event_aligned_readout"""
        self.device.disable_event_aligned_readout()
        self.mock_lib.disable_event_aligned_readout.assert_called_once_with(self.device.handle)

    def test_set_event_packaging(self):
        """Test set_event_packaging"""
        self.device.set_event_packaging(dgtz.EnaDis.ENABLE)
        self.mock_lib.set_event_packaging.assert_called_once_with(self.device.handle, dgtz.EnaDis.ENABLE)

    def test_get_event_packaging(self):
        """Test get_event_packaging"""
        self.device.get_event_packaging()
        self.mock_lib.get_event_packaging.assert_called_once_with(self.device.handle, ANY)

    def test_set_max_num_aggregates_blt(self):
        """Test set_max_num_aggregates_blt"""
        self.device.set_max_num_aggregates_blt(1)
        self.mock_lib.set_max_num_aggregates_blt.assert_called_once_with(self.device.handle, 1)

    def test_get_max_num_aggregates_blt(self):
        """Test get_max_num_aggregates_blt"""
        self.device.get_max_num_aggregates_blt()
        self.mock_lib.get_max_num_aggregates_blt.assert_called_once_with(self.device.handle, ANY)

    def test_set_num_events_per_aggregate(self):
        """Test set_num_events_per_aggregate"""
        self.device.set_num_events_per_aggregate(1, 2)
        self.mock_lib.set_num_events_per_aggregate.assert_called_once_with(self.device.handle, 1, 2)

    def test_get_num_events_per_aggregate(self):
        """Test get_num_events_per_aggregate"""
        self.device.get_num_events_per_aggregate(2)
        self.mock_lib.get_num_events_per_aggregate.assert_called_once_with(self.device.handle, ANY, 2)

    def test_dpp_event_aggregation(self):
        """Test set_dpp_event_aggregation"""
        self.device.set_dpp_event_aggregation(1, 1)
        self.mock_lib.set_dpp_event_aggregation.assert_called_once_with(self.device.handle, 1, 1)

    def test_set_dpp_acquisition_mode(self):
        """Test set_dpp_acquisition_mode"""
        self.device.set_dpp_acquisition_mode(dgtz.DPPAcqMode.LIST, dgtz.DPPSaveParam.CHARGE_AND_TIME)
        self.mock_lib.set_dpp_acquisition_mode.assert_called_once_with(self.device.handle, dgtz.DPPAcqMode.LIST, dgtz.DPPSaveParam.CHARGE_AND_TIME)

    def test_get_dpp_acquisition_mode(self):
        """Test get_dpp_acquisition_mode"""
        self.device.get_dpp_acquisition_mode()
        self.mock_lib.get_dpp_acquisition_mode.assert_called_once_with(self.device.handle, ANY, ANY)

    def test_set_dpp_trigger_mode(self):
        """Test set_dpp_trigger_mode"""
        self.device.set_dpp_trigger_mode(dgtz.DPPTriggerMode.NORMAL)
        self.mock_lib.set_dpp_trigger_mode.assert_called_once_with(self.device.handle, dgtz.DPPTriggerMode.NORMAL)

    def test_get_dpp_trigger_mode(self):
        """Test get_dpp_trigger_mode"""
        self.device.get_dpp_trigger_mode()
        self.mock_lib.get_dpp_trigger_mode.assert_called_once_with(self.device.handle, ANY)

    def test_set_dpp_virtual_probe(self):
        """Test set_dpp_virtual_probe"""
        self.device.set_dpp_virtual_probe(dgtz.DPPTrace.ANALOG_1, dgtz.DPPProbe.VIRTUAL_BASELINE)
        self.mock_lib.set_dpp_virtual_probe.assert_called_once_with(self.device.handle, dgtz.DPPTrace.ANALOG_1, dgtz.DPPProbe.VIRTUAL_BASELINE)

    def test_get_dpp_virtual_probe(self):
        """Test get_dpp_virtual_probe"""
        self.device.get_dpp_virtual_probe(dgtz.DPPTrace.ANALOG_1)
        self.mock_lib.get_dpp_virtual_probe.assert_called_once_with(self.device.handle, dgtz.DPPTrace.ANALOG_1, ANY)

    def test_get_get_dpp_supported_virtual_probes(self):
        """Test get_dpp_supported_virtual_probes"""
        self.device.get_dpp_supported_virtual_probes(dgtz.DPPTrace.ANALOG_1)
        self.mock_lib.get_dpp_supported_virtual_probes.assert_called_once_with(self.device.handle, dgtz.DPPTrace.ANALOG_1, ANY, ANY)

    def test_set_io_level(self):
        """Test set_io_level"""
        self.device.set_io_level(dgtz.IOLevel.NIM)
        self.mock_lib.set_io_level.assert_called_once_with(self.device.handle, dgtz.IOLevel.NIM)

    def test_get_io_level(self):
        """Test get_io_level"""
        self.device.get_io_level()
        self.mock_lib.get_io_level.assert_called_once_with(self.device.handle, ANY)

    def test_set_trigger_polarity(self):
        """Test set_trigger_polarity"""
        self.device.set_trigger_polarity(1, dgtz.TriggerPolarity.ON_FALLING_EDGE)
        self.mock_lib.set_trigger_polarity.assert_called_once_with(self.device.handle, 1, dgtz.TriggerPolarity.ON_FALLING_EDGE)

    def test_get_trigger_polarity(self):
        """Test get_trigger_polarity"""
        self.device.get_trigger_polarity(1)
        self.mock_lib.get_trigger_polarity.assert_called_once_with(self.device.handle, 1, ANY)

    def test_rearm_interrupt(self):
        """Test rearm_interrupt"""
        self.device.rearm_interrupt()
        self.mock_lib.rearm_interrupt.assert_called_once_with(self.device.handle)

    def test_set_drs4_sampling_frequency(self):
        """Test set_drs4_sampling_frequency"""
        self.device.set_drs4_sampling_frequency(dgtz.DRS4Frequency.F_1GHz)
        self.mock_lib.set_drs4_sampling_frequency.assert_called_once_with(self.device.handle, dgtz.DRS4Frequency.F_1GHz)

    def test_get_drs4_sampling_frequency(self):
        """Test get_drs4_sampling_frequency"""
        self.device.get_drs4_sampling_frequency()
        self.mock_lib.get_drs4_sampling_frequency.assert_called_once_with(self.device.handle, ANY)

    def test_set_output_signal_mode(self):
        """Test set_output_signal_mode"""
        self.device.set_output_signal_mode(dgtz.OutputSignalMode.BUSY)
        self.mock_lib.set_output_signal_mode.assert_called_once_with(self.device.handle, dgtz.OutputSignalMode.BUSY)

    def test_get_output_signal_mode(self):
        """Test get_output_signal_mode"""
        self.device.get_output_signal_mode()
        self.mock_lib.get_output_signal_mode.assert_called_once_with(self.device.handle, ANY)

    def test_set_group_fast_trigger_threshold(self):
        """Test set_group_fast_trigger_threshold"""
        self.device.set_group_fast_trigger_threshold(1, 2)
        self.mock_lib.set_group_fast_trigger_threshold.assert_called_once_with(self.device.handle, 1, 2)

    def test_get_group_fast_trigger_threshold(self):
        """Test get_group_fast_trigger_threshold"""
        self.device.get_group_fast_trigger_threshold(1)
        self.mock_lib.get_group_fast_trigger_threshold.assert_called_once_with(self.device.handle, 1, ANY)

    def test_set_group_fast_trigger_dc_offset(self):
        """Test set_group_fast_trigger_dc_offset"""
        self.device.set_group_fast_trigger_dc_offset(1, 2)
        self.mock_lib.set_group_fast_trigger_dc_offset.assert_called_once_with(self.device.handle, 1, 2)

    def test_get_group_fast_trigger_dc_offset(self):
        """Test get_group_fast_trigger_dc_offset"""
        self.device.get_group_fast_trigger_dc_offset(1)
        self.mock_lib.get_group_fast_trigger_dc_offset.assert_called_once_with(self.device.handle, 1, ANY)

    def test_set_fast_trigger_digitizing(self):
        """Test set_fast_trigger_digitizing"""
        self.device.set_fast_trigger_digitizing(dgtz.EnaDis.DISABLE)
        self.mock_lib.set_fast_trigger_digitizing.assert_called_once_with(self.device.handle, dgtz.EnaDis.DISABLE)

    def test_get_fast_trigger_digitizing(self):
        """Test get_fast_trigger_digitizing"""
        self.device.get_fast_trigger_digitizing()
        self.mock_lib.get_fast_trigger_digitizing.assert_called_once_with(self.device.handle, ANY)

    def test_set_fast_trigger_mode(self):
        """Test set_fast_trigger_mode"""
        self.device.set_fast_trigger_mode(dgtz.TriggerMode.ACQ_AND_EXTOUT)
        self.mock_lib.set_fast_trigger_mode.assert_called_once_with(self.device.handle, dgtz.TriggerMode.ACQ_AND_EXTOUT)

    def test_get_fast_trigger_mode(self):
        """Test get_fast_trigger_mode"""
        self.device.get_fast_trigger_mode()
        self.mock_lib.get_fast_trigger_mode.assert_called_once_with(self.device.handle, ANY)

    def test_load_drs4_correction_data(self):
        """Test load_drs4_correction_data"""
        self.device.load_drs4_correction_data(dgtz.DRS4Frequency.F_1GHz)
        self.mock_lib.load_drs4_correction_data.assert_called_once_with(self.device.handle, dgtz.DRS4Frequency.F_1GHz)

    def test_get_correction_tables(self):
        """Test get_correction_tables"""
        self.device.get_correction_tables(dgtz.DRS4Frequency.F_1GHz)
        self.mock_lib.get_correction_tables.assert_called_once_with(self.device.handle, dgtz.DRS4Frequency.F_1GHz, ANY)

    def test_enable_drs4_correction(self):
        """Test enable_drs4_correction"""
        self.device.enable_drs4_correction()
        self.mock_lib.enable_drs4_correction.assert_called_once_with(self.device.handle)

    def test_disable_drs4_correction(self):
        """Test disable_drs4_correction"""
        self.device.disable_drs4_correction()
        self.mock_lib.disable_drs4_correction.assert_called_once_with(self.device.handle)

    def test_sam_correction_level(self):
        """Test set_sam_correction_level"""
        self.device.set_sam_correction_level(dgtz.SAMCorrectionLevel.ALL)
        self.mock_lib.set_sam_correction_level.assert_called_once_with(self.device.handle, dgtz.SAMCorrectionLevel.ALL)

    def test_get_sam_correction_level(self):
        """Test get_sam_correction_level"""
        self.device.get_sam_correction_level()
        self.mock_lib.get_sam_correction_level.assert_called_once_with(self.device.handle, ANY)

    def test_enable_sam_pulse_gen(self):
        """Test enable_sam_pulse_gen"""
        self.device.enable_sam_pulse_gen(1, 2, dgtz.SAMPulseSourceType.CONT)
        self.mock_lib.enable_sam_pulse_gen.assert_called_once_with(self.device.handle, 1, 2, dgtz.SAMPulseSourceType.CONT)

    def test_disable_sam_pulse_gen(self):
        """Test disable_sam_pulse_gen"""
        self.device.disable_sam_pulse_gen(1)
        self.mock_lib.disable_sam_pulse_gen.assert_called_once_with(self.device.handle, 1)

    def test_set_sam_post_trigger_size(self):
        """Test set_sam_post_trigger_size"""
        self.device.set_sam_post_trigger_size(100, 200)
        self.mock_lib.set_sam_post_trigger_size.assert_called_once_with(self.device.handle, 100, 200)

    def test_get_sam_post_trigger_size(self):
        """Test get_sam_post_trigger_size"""
        self.device.get_sam_post_trigger_size(0)
        self.mock_lib.get_sam_post_trigger_size.assert_called_once_with(self.device.handle, 0, ANY)

    def test_set_sam_sampling_frequency(self):
        """Test set_sam_sampling_frequency"""
        self.device.set_sam_sampling_frequency(dgtz.SAMFrequency.F_400MHz)
        self.mock_lib.set_sam_sampling_frequency.assert_called_once_with(self.device.handle, dgtz.SAMFrequency.F_400MHz)

    def test_get_sam_sampling_frequency(self):
        """Test get_sam_sampling_frequency"""
        self.device.get_sam_sampling_frequency()
        self.mock_lib.get_sam_sampling_frequency.assert_called_once_with(self.device.handle, ANY)

    def test_load_sam_correction_data(self):
        """Test load_sam_correction_data"""
        self.device.load_sam_correction_data()
        self.mock_lib.load_sam_correction_data.assert_called_once_with(self.device.handle)

    def test_read_eeprom(self):
        """Test read_eeprom"""
        self.device.read_eeprom(1, 2, 3)
        self.mock_lib.read_eeprom.assert_called_once_with(self.device.handle, 1, 2, 3, ANY)

    def test_write_eeprom(self):
        """Test write_eeprom"""
        self.device.write_eeprom(1, 2, b'')
        self.mock_lib.write_eeprom.assert_called_once_with(self.device.handle, 1, 2, ANY, ANY)

    def test_trigger_threshold(self):
        """Test trigger_threshold"""
        self.device.trigger_threshold(dgtz.EnaDis.ENABLE)
        self.mock_lib.trigger_threshold.assert_called_once_with(self.device.handle, dgtz.EnaDis.ENABLE)

    def test_send_sam_pulse(self):
        """Test send_sam_pulse"""
        self.device.send_sam_pulse()
        self.mock_lib.send_sam_pulse.assert_called_once_with(self.device.handle,)

    def test_set_sam_acquisition_mode(self):
        """Test set_sam_acquisition_mode"""
        self.device.set_sam_acquisition_mode(dgtz.AcquisitionMode.STANDARD)
        self.mock_lib.set_sam_acquisition_mode.assert_called_once_with(self.device.handle, dgtz.AcquisitionMode.STANDARD)

    def test_get_sam_acquisition_mode(self):
        """Test get_sam_acquisition_mode"""
        self.device.get_sam_acquisition_mode()
        self.mock_lib.get_sam_acquisition_mode.assert_called_once_with(self.device.handle, ANY)

    def test_set_trigger_logic(self):
        """Test set_trigger_logic"""
        self.device.set_trigger_logic(dgtz.TriggerLogic.OR, 1)
        self.mock_lib.set_trigger_logic.assert_called_once_with(self.device.handle, dgtz.TriggerLogic.OR, 1)

    def test_get_trigger_logic(self):
        """Test get_trigger_logic"""
        self.device.get_trigger_logic()
        self.mock_lib.get_trigger_logic.assert_called_once_with(self.device.handle, ANY, ANY)

    def test_set_channel_pair_trigger_logic(self):
        """Test set_channel_pair_trigger_logic"""
        self.device.set_channel_pair_trigger_logic(1, 2, dgtz.TriggerLogic.AND, 3)
        self.mock_lib.set_channel_pair_trigger_logic.assert_called_once_with(self.device.handle, 1, 2, dgtz.TriggerLogic.AND, 3)

    def test_get_channel_pair_trigger_logic(self):
        """Test get_channel_pair_trigger_logic"""
        self.device.get_channel_pair_trigger_logic(1, 2)
        self.mock_lib.get_channel_pair_trigger_logic.assert_called_once_with(self.device.handle, 1, 2, ANY, ANY)

    def test_set_decimation_factor(self):
        """Test set_decimation_factor"""
        self.device.set_decimation_factor(1)
        self.mock_lib.set_decimation_factor.assert_called_once_with(self.device.handle, 1)

    def test_get_decimation_factor(self):
        """Test get_decimation_factor"""
        self.device.get_decimation_factor()
        self.mock_lib.get_decimation_factor.assert_called_once_with(self.device.handle, ANY)

    def test_set_sam_trigger_count_veto_param(self):
        """Test set_sam_trigger_count_veto_param"""
        self.device.set_sam_trigger_count_veto_param(1, dgtz.EnaDis.ENABLE, 2)
        self.mock_lib.set_sam_trigger_count_veto_param.assert_called_once_with(self.device.handle, 1, dgtz.EnaDis.ENABLE, 2)

    def test_get_sam_trigger_count_veto_param(self):
        """Test get_sam_trigger_count_veto_param"""
        self.device.get_sam_trigger_count_veto_param(1)
        self.mock_lib.get_sam_trigger_count_veto_param.assert_called_once_with(self.device.handle, 1, ANY, ANY)

    def test_set_trigger_in_as_gate(self):
        """Test set_trigger_in_as_gate"""
        self.device.set_trigger_in_as_gate(dgtz.EnaDis.ENABLE)
        self.mock_lib.set_trigger_in_as_gate.assert_called_once_with(self.device.handle, dgtz.EnaDis.ENABLE)

    def test_calibrate(self):
        """Test calibrate"""
        self.device.calibrate()
        self.mock_lib.calibrate.assert_called_once_with(self.device.handle)

    def test_read_temperature(self):
        """Test read_temperature"""
        self.device.read_temperature(1)
        self.mock_lib.read_temperature.assert_called_once_with(self.device.handle, 1, ANY)

    def test_get_dpp_firmware_type(self):
        """Test get_dpp_firmware_type"""
        self.device.get_dpp_firmware_type()
        self.mock_lib.get_dpp_firmware_type.assert_called_once_with(self.device.handle, ANY)


class TestDeviceStandard(_TestDevice):
    """
    Test the Device class. Specific for Standard Firmware.
    """

    def setUp(self):
        self.baseSetUp(dgtz._types.FirmwareCode.STANDARD_FW)  # pylint: disable=W0212

    def test_standard_firmware_daq(self):
        """
        Test Standard Firmware DAQ:
        - malloc_readout_buffer
        - allocate_event
        - read_data
        - get_num_events
        - get_event_info
        - decode_event
        - free_event
        - free_readout_buffer
        """
        event_buffer = ct.create_string_buffer(1024)
        def side_effect(*args):
            args[1].value = ct.addressof(event_buffer)
            return DEFAULT
        self.mock_lib.allocate_event.side_effect = side_effect
        self.device.malloc_readout_buffer()
        self.device.allocate_event()
        self.device.read_data(dgtz.ReadMode.SLAVE_TERMINATED_READOUT_MBLT)
        self.device.get_num_events()
        _, buffer = self.device.get_event_info(1)
        self.device.decode_event(buffer)
        self.device.free_event()
        self.device.free_readout_buffer()
        self.mock_lib.malloc_readout_buffer.assert_called_once_with(self.device.handle, ANY, ANY)
        self.mock_lib.allocate_event.assert_called_once_with(self.device.handle, ANY)
        self.mock_lib.read_data.assert_called_once_with(self.device.handle, dgtz.ReadMode.SLAVE_TERMINATED_READOUT_MBLT, ANY, ANY)
        self.mock_lib.get_num_events.assert_called_once_with(self.device.handle, ANY, ANY, ANY)
        self.mock_lib.get_event_info.assert_called_once_with(self.device.handle, ANY, ANY, ANY, ANY, ANY)
        self.mock_lib.decode_event.assert_called_once_with(self.device.handle, ANY, ANY)
        self.mock_lib.free_event.assert_called_once_with(self.device.handle, ANY)
        self.mock_lib.free_readout_buffer.assert_called_once_with(ANY)


class TestDeviceDPP(_TestDevice):
    """
    Test the Device class. Specific for DPP Firmware.
    """

    def setUp(self):
        self.baseSetUp(dgtz._types.FirmwareCode.V1720_DPP_PSD)  # pylint: disable=W0212

    def test_dpp_daq(self):
        """
        Test DPP Firmware DAQ:
        - malloc_readout_buffer
        - malloc_dpp_events
        - malloc_dpp_waveforms
        - read_data
        - get_dpp_events
        - decode_dpp_waveforms
        - free_dpp_waveforms
        - free_dpp_events
        - free_readout_buffer
        """
        events_buffer = ct.create_string_buffer(1024)
        def evt_side_effect(*args):
            for i in range(self.device.get_info().channels):
                args[1][i] = ct.addressof(events_buffer)
            return DEFAULT
        self.mock_lib.malloc_dpp_events.side_effect = evt_side_effect
        def wave_side_effect(*args):
            args[1].value = ct.addressof(events_buffer)
            return DEFAULT
        self.mock_lib.malloc_dpp_waveforms.side_effect = wave_side_effect
        self.device.malloc_readout_buffer()
        self.device.malloc_dpp_events()
        self.device.malloc_dpp_waveforms()
        self.device.read_data(dgtz.ReadMode.SLAVE_TERMINATED_READOUT_MBLT)
        self.device.get_dpp_events()
        self.device.decode_dpp_waveforms(0, 0)
        self.device.free_dpp_waveforms()
        self.device.free_dpp_events()
        self.device.free_readout_buffer()
        self.mock_lib.malloc_readout_buffer.assert_called_once_with(self.device.handle, ANY, ANY)
        self.mock_lib.malloc_dpp_events.assert_called_once_with(self.device.handle, ANY, ANY)
        self.mock_lib.malloc_dpp_waveforms.assert_called_once_with(self.device.handle, ANY, ANY)
        self.mock_lib.read_data.assert_called_once_with(self.device.handle, dgtz.ReadMode.SLAVE_TERMINATED_READOUT_MBLT, ANY, ANY)
        self.mock_lib.get_dpp_events.assert_called_once_with(self.device.handle, ANY, ANY, ANY, ANY)
        self.mock_lib.decode_dpp_waveforms.assert_called_once_with(self.device.handle, ANY, ANY)
        self.mock_lib.free_dpp_waveforms.assert_called_once_with(self.device.handle, ANY)
        self.mock_lib.free_dpp_events.assert_called_once_with(self.device.handle, ANY)
        self.mock_lib.free_readout_buffer.assert_called_once_with(ANY)

    def test_set_dpp_parameters(self):
        """Test set_dpp_parameters"""
        self.device.set_dpp_parameters(0xff, dgtz.DPPPSDParams())
        self.mock_lib.set_dpp_parameters.assert_called_once_with(self.device.handle, 0xff, ANY)


class TestDeviceDAW(_TestDevice):
    """
    Test the Device class. Specific for DAW  Firmware.
    """

    def setUp(self):
        self.baseSetUp(dgtz._types.FirmwareCode.V1730_DPP_DAW)  # pylint: disable=W0212

    def test_daw_daq(self):
        """
        Test DAW Firmware DAQ:
        - malloc_readout_buffer
        - malloc_daw_events_and_waveforms
        - read_data
        - get_daw_events
        - decode_daw_waveforms
        - free_daw_events_and_waveforms
        - free_readout_buffer

        Waveform functions are not called because it is very complex to
        mock the waveform buffers within the events structure, allocated
        by malloc_dpp_events.
        """
        events_buffer = ct.create_string_buffer(1024)
        def read_side_effect(*args):
            args[2].value = ct.addressof(events_buffer)
            args[3].value = 1024
            return DEFAULT
        self.mock_lib.read_data.side_effect = read_side_effect
        def evt_side_effect(*args):
            args[1].value = ct.addressof(events_buffer)
            return DEFAULT
        self.mock_lib.malloc_dpp_events.side_effect = evt_side_effect
        self.device.malloc_readout_buffer()
        self.device.malloc_daw_events_and_waveforms()
        self.device.read_data(dgtz.ReadMode.SLAVE_TERMINATED_READOUT_MBLT)
        self.device.get_daw_events()
        self.device.decode_daw_waveforms(0)
        self.device.free_daw_events_and_waveforms()
        self.device.free_readout_buffer()
        self.mock_lib.malloc_readout_buffer.assert_called_once_with(self.device.handle, ANY, ANY)
        self.mock_lib.malloc_dpp_events.assert_called_once_with(self.device.handle, ANY, ANY)
        self.mock_lib.malloc_dpp_waveforms.assert_not_called()  # Not called because get_max_num_events_blt return 0
        self.mock_lib.read_data.assert_called_once_with(self.device.handle, dgtz.ReadMode.SLAVE_TERMINATED_READOUT_MBLT, ANY, ANY)
        self.mock_lib.get_dpp_events.assert_called_once_with(self.device.handle, ANY, ANY, ANY, ANY)
        self.mock_lib.decode_dpp_waveforms.assert_called_once_with(self.device.handle, ANY, ANY)
        self.mock_lib.free_dpp_waveforms.assert_not_called()  # Same of malloc_dpp_waveforms
        self.mock_lib.free_dpp_events.assert_called_once_with(self.device.handle, ANY)
        self.mock_lib.free_readout_buffer.assert_called_once_with(ANY)


class TestDeviceZLE(_TestDevice):
    """
    Test the Device class. Specific for ZLE Firmware.
    """

    def setUp(self):
        self.baseSetUp(dgtz._types.FirmwareCode.V1730_DPP_ZLE)  # pylint: disable=W0212

    def test_zle_daq(self):
        """
        Test ZLE Firmware DAQ:
        - malloc_readout_buffer
        - malloc_zle_events_and_waveforms
        - read_data
        - get_zle_events
        - decode_zle_waveforms
        - free_zle_events_and_waveforms
        - free_readout_buffer

        Waveform functions are not called because it is very complex to
        mock the waveform buffers within the events structure, allocated
        by malloc_zle_events.
        """
        events_buffer = ct.create_string_buffer(1024)
        def read_side_effect(*args):
            args[2].value = ct.addressof(events_buffer)
            args[3].value = 1024
            return DEFAULT
        self.mock_lib.read_data.side_effect = read_side_effect
        def evt_side_effect(*args):
            args[1].value = ct.addressof(events_buffer)
            return DEFAULT
        self.mock_lib.malloc_zle_events.side_effect = evt_side_effect
        self.device.malloc_readout_buffer()
        self.device.malloc_zle_events_and_waveforms()
        self.device.read_data(dgtz.ReadMode.SLAVE_TERMINATED_READOUT_MBLT)
        self.device.get_zle_events()
        self.device.decode_zle_waveforms(0)
        self.device.free_zle_events_and_waveforms()
        self.device.free_readout_buffer()
        self.mock_lib.malloc_readout_buffer.assert_called_once_with(self.device.handle, ANY, ANY)
        self.mock_lib.malloc_zle_events.assert_called_once_with(self.device.handle, ANY, ANY)
        self.mock_lib.malloc_zle_waveforms.assert_not_called()  # Not called because get_max_num_events_blt return 0
        self.mock_lib.read_data.assert_called_once_with(self.device.handle, dgtz.ReadMode.SLAVE_TERMINATED_READOUT_MBLT, ANY, ANY)
        self.mock_lib.get_zle_events.assert_called_once_with(self.device.handle, ANY, ANY, ANY, ANY)
        self.mock_lib.decode_zle_waveforms.assert_called_once_with(self.device.handle, ANY, ANY)
        self.mock_lib.free_zle_waveforms.assert_not_called()  # Same of malloc_zle_waveforms
        self.mock_lib.free_zle_events.assert_called_once_with(self.device.handle, ANY)
        self.mock_lib.free_readout_buffer.assert_called_once_with(ANY)


TEST_CASES = (TestDeviceStandard, TestDeviceDPP, TestDeviceDAW, TestDeviceZLE)


def load_tests(loader: unittest.TestLoader, _standard_tests, _pattern):
    """
    Protocol for unittest test discovery:
    Manually create the test suite to avoid running _TestDevice
    """
    suite = unittest.TestSuite()
    for test_class in TEST_CASES:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    return suite


if __name__ == '__main__':
    unittest.main()
