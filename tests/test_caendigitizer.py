
"""Tests for the caendigitizer module."""

import unittest
from unittest.mock import patch, ANY, DEFAULT

import ctypes as ct

import caen_libs.caendigitizer as dgtz
from caen_libs.caendigitizer import _types

class TestDevice(unittest.TestCase):

    def setUp(self):
        patcher = patch('caen_libs.caendigitizer.lib', autospec=True)
        self.addCleanup(patcher.stop)
        self.mock_lib = patcher.start()
        def side_effect(*args):
            args[4].value = 0xdeadbeaf
            return DEFAULT
        self.mock_lib.open_digitizer2.side_effect = side_effect
        def info_side_effect(*args):
            args[1].AMC_FirmwareRel = b'0.0'
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
        self.device.close()
        self.mock_lib.close_digitizer.assert_called_once_with(self.device.handle)

    def test_get_info(self):
        self.device.get_info()
        self.mock_lib.get_info.assert_called()

    def test_reset(self):
        self.device.reset()
        self.mock_lib.reset.assert_called_once_with(self.device.handle)

    def test_clear_data(self):
        self.device.clear_data()
        self.mock_lib.clear_data.assert_called_once_with(self.device.handle)

    def test_send_sw_trigger(self):
        self.device.send_sw_trigger()
        self.mock_lib.send_sw_trigger.assert_called_once_with(self.device.handle)

    def test_sw_start_acquisition(self):
        self.device.sw_start_acquisition()
        self.mock_lib.sw_start_acquisition.assert_called_once_with(self.device.handle)

    def test_sw_stop_acquisition(self):
        self.device.sw_stop_acquisition()
        self.mock_lib.sw_stop_acquisition.assert_called_once_with(self.device.handle)

    def test_irq_wait(self):
        self.device.irq_wait(1000)
        self.mock_lib.irq_wait.assert_called_once_with(self.device.handle, 1000)

    def test_set_record_length(self):
        self.device.set_record_length(1024, 10)
        self.mock_lib.set_record_length.assert_called_once_with(self.device.handle, 1024, ANY)

    def test_get_record_length(self):
        self.device.get_record_length(10)
        self.mock_lib.get_record_length.assert_called_once_with(self.device.handle, ANY, ANY)

    def test_set_channel_enable_mask(self):
        self.device.set_channel_enable_mask(0xF)
        self.mock_lib.set_channel_enable_mask.assert_called_once_with(self.device.handle, 0xF)

    def test_get_channel_enable_mask(self):
        self.device.get_channel_enable_mask()
        self.mock_lib.get_channel_enable_mask.assert_called_once_with(self.device.handle, ANY)

    def test_set_group_enable_mask(self):
        self.device.set_group_enable_mask(0x3)
        self.mock_lib.set_group_enable_mask.assert_called_once_with(self.device.handle, 0x3)

    def test_get_group_enable_mask(self):
        self.device.get_group_enable_mask()
        self.mock_lib.get_group_enable_mask.assert_called_once_with(self.device.handle, ANY)

    def test_set_post_trigger_size(self):
        self.device.set_post_trigger_size(50)
        self.mock_lib.set_post_trigger_size.assert_called_once_with(self.device.handle, 50)

    def test_get_post_trigger_size(self):
        self.device.get_post_trigger_size()
        self.mock_lib.get_post_trigger_size.assert_called_once_with(self.device.handle, ANY)

    def test_set_channel_dc_offset(self):
        self.device.set_channel_dc_offset(0, 100)
        self.mock_lib.set_channel_dc_offset.assert_called_once_with(self.device.handle, 0, 100)

    def test_get_channel_dc_offset(self):
        self.device.get_channel_dc_offset(0)
        self.mock_lib.get_channel_dc_offset.assert_called_once_with(self.device.handle, 0, ANY)

    def test_set_acquisition_mode(self):
        self.device.set_acquisition_mode(dgtz.AcqMode.FIRST_TRG_CONTROLLED)
        self.mock_lib.set_acquisition_mode.assert_called_once_with(self.device.handle, dgtz.AcqMode.FIRST_TRG_CONTROLLED)

    def test_get_acquisition_mode(self):
        self.device.get_acquisition_mode()
        self.mock_lib.get_acquisition_mode.assert_called_once_with(self.device.handle, ANY)

    def test_write_register(self):
        self.device.write_register(0x1000, 0x1234)
        self.mock_lib.write_register.assert_called_once_with(self.device.handle, 0x1000, 0x1234)

    def test_read_register(self):
        self.device.read_register(0x1000)
        self.mock_lib.read_register.assert_called_once_with(self.device.handle, 0x1000, ANY)

    def test_set_channel_trigger_threshold(self):
        self.device.set_channel_trigger_threshold(0, 1.5)
        self.mock_lib.set_channel_trigger_threshold.assert_called_once()

    def test_get_channel_trigger_threshold(self):
        self.device.get_channel_trigger_threshold(0)
        self.mock_lib.get_channel_trigger_threshold.assert_called_once()

    def test_set_max_num_events_blt(self):
        self.device.set_max_num_events_blt(1)
        self.mock_lib.set_max_num_events_blt.assert_called_once_with(self.device.handle, 1)

    def test_get_max_num_events_blt(self):
        self.device.get_max_num_events_blt()
        self.mock_lib.get_max_num_events_blt.assert_called_once_with(self.device.handle, ANY)

    def test_malloc_readout_buffer(self):
        self.device.malloc_readout_buffer()
        self.mock_lib.malloc_readout_buffer.assert_called_once_with(self.device.handle, ANY, ANY)

    def test_free_readout_buffer(self):
        self.device.free_readout_buffer()
        self.mock_lib.free_readout_buffer.assert_not_called()  # Requires malloc before

    def test_read_data(self):
        self.device.malloc_readout_buffer()
        self.device.read_data(1)
        self.mock_lib.read_data.assert_called_once_with(self.device.handle, 1, ANY, ANY)

    def test_get_num_events(self):
        self.device.malloc_readout_buffer()
        self.device.get_num_events()
        self.mock_lib.get_num_events.assert_called_once_with(self.device.handle, ANY, ANY, ANY)

    def test_get_event_info(self):
        self.device.malloc_readout_buffer()
        self.device.get_event_info(1)
        self.mock_lib.get_event_info.assert_called_once_with(self.device.handle, ANY, ANY, ANY, ANY, ANY)

    def test_set_interrupt_config(self):
        self.device.set_interrupt_config(1, 2, 3, 4, 5)
        self.mock_lib.set_interrupt_config.assert_called_once_with(self.device.handle, 1, 2, 3, 4, 5)

    def test_get_interrupt_config(self):
        self.device.get_interrupt_config()
        self.mock_lib.get_interrupt_config.assert_called_once_with(self.device.handle, ANY, ANY, ANY, ANY, ANY)

    def test_set_des_mode(self):
        self.device.set_des_mode(1)
        self.mock_lib.set_des_mode.assert_called_once_with(self.device.handle, 1)

    def test_get_des_mode(self):
        self.device.get_des_mode()
        self.mock_lib.get_des_mode.assert_called_once_with(self.device.handle, ANY)

    def test_set_sw_trigger_mode(self):
        self.device.set_sw_trigger_mode(1)
        self.mock_lib.set_sw_trigger_mode.assert_called_once_with(self.device.handle, 1)

    def test_get_sw_trigger_mode(self):
        self.device.get_sw_trigger_mode()
        self.mock_lib.get_sw_trigger_mode.assert_called_once_with(self.device.handle, ANY)

    def test_set_ext_trigger_input_mode(self):
        self.device.set_ext_trigger_input_mode(1)
        self.mock_lib.set_ext_trigger_input_mode.assert_called_once_with(self.device.handle, 1)

    def test_get_ext_trigger_input_mode(self):
        self.device.get_ext_trigger_input_mode()
        self.mock_lib.get_ext_trigger_input_mode.assert_called_once_with(self.device.handle, ANY)

    def test_set_channel_self_trigger(self):
        self.device.set_channel_self_trigger(1, 2)
        self.mock_lib.set_channel_self_trigger.assert_called_once_with(self.device.handle, 1, 2)

    def test_get_channel_self_trigger(self):
        self.device.get_channel_self_trigger(1)
        self.mock_lib.get_channel_self_trigger.assert_called_once_with(self.device.handle, 1, ANY)

    def test_set_group_self_trigger(self):
        self.device.set_group_self_trigger(1, 2)
        self.mock_lib.set_group_self_trigger.assert_called_once_with(self.device.handle, 1, 2)

    def test_get_group_self_trigger(self):
        self.device.get_group_self_trigger(1)
        self.mock_lib.get_group_self_trigger.assert_called_once_with(self.device.handle, 1, ANY)

    def test_set_dpp_pre_trigger_size(self):
        self.device.set_dpp_pre_trigger_size(1, 2)
        self.mock_lib.set_dpp_pre_trigger_size.assert_called_once_with(self.device.handle, 1, 2)

    def test_get_dpp_pre_trigger_size(self):
        self.device.get_dpp_pre_trigger_size(1)
        self.mock_lib.get_dpp_pre_trigger_size.assert_called_once_with(self.device.handle, 1, ANY)

    def test_set_group_dc_offset(self):
        self.device.set_group_dc_offset(1, 2)
        self.mock_lib.set_group_dc_offset.assert_called_once_with(self.device.handle, 1, 2)

    def test_get_group_dc_offset(self):
        self.device.get_group_dc_offset(1)
        self.mock_lib.get_group_dc_offset.assert_called_once_with(self.device.handle, 1, ANY)

    def test_set_channel_pulse_polarity(self):
        self.device.set_channel_pulse_polarity(1, 2)
        self.mock_lib.set_channel_pulse_polarity.assert_called_once_with(self.device.handle, 1, 2)

    def test_get_channel_pulse_polarity(self):
        self.device.get_channel_pulse_polarity(1)
        self.mock_lib.get_channel_pulse_polarity.assert_called_once_with(self.device.handle, 1, ANY)

    def test_set_group_trigger_threshold(self):
        self.device.set_group_trigger_threshold(1, 2)
        self.mock_lib.set_group_trigger_threshold.assert_called_once_with(self.device.handle, 1, 2)

    def test_get_group_trigger_threshold(self):
        self.device.get_group_trigger_threshold(1)
        self.mock_lib.get_group_trigger_threshold.assert_called_once_with(self.device.handle, 1, ANY)

    def test_set_zero_suppression_mode(self):
        self.device.set_zero_suppression_mode(1, 2)
        self.mock_lib.set_zero_suppression_mode.assert_called_once_with(self.device.handle, 1, 2)

    def test_get_zero_suppression_mode(self):
        self.device.get_zero_suppression_mode(1)
        self.mock_lib.get_zero_suppression_mode.assert_called_once_with(self.device.handle, 1, ANY)

    def test_set_channel_zs_params(self):
        self.device.set_channel_zs_params(1, 2, 3, 4)
        self.mock_lib.set_channel_zs_params.assert_called_once_with(self.device.handle, 1, 2, 3, 4)

    def test_get_channel_zs_params(self):
        self.device.get_channel_zs_params(1)
        self.mock_lib.get_channel_zs_params.assert_called_once_with(self.device.handle, 1, ANY, ANY, ANY)

    def test_set_run_synchronization_mode(self):
        self.device.set_run_synchronization_mode(1)
        self.mock_lib.set_run_synchronization_mode.assert_called_once_with(self.device.handle, 1)

    def test_get_run_synchronization_mode(self):
        self.device.get_run_synchronization_mode()
        self.mock_lib.get_run_synchronization_mode.assert_called_once_with(self.device.handle, ANY)

    def test_set_analog_mon_output(self):
        self.device.set_analog_mon_output(1, 2)
        self.mock_lib.set_analog_mon_output.assert_called_once_with(self.device.handle, 1, 2)

    def test_get_analog_mon_output(self):
        self.device.get_analog_mon_output(1)
        self.mock_lib.get_analog_mon_output.assert_called_once_with(self.device.handle, 1, ANY)

    def test_set_analog_inspection_mon_params(self):
        self.device.set_analog_inspection_mon_params(1, 2, 3, 4)
        self.mock_lib.set_analog_inspection_mon_params.assert_called_once_with(self.device.handle, 1, 2, 3, 4)

    def test_get_analog_inspection_mon_params(self):
        self.device.get_analog_inspection_mon_params(1, 2)
        self.mock_lib.get_analog_inspection_mon_params.assert_called_once_with(self.device.handle, 1, 2, ANY, ANY)

    def test_disable_event_aligned_readout(self):
        self.device.disable_event_aligned_readout()
        self.mock_lib.disable_event_aligned_readout.assert_called_once_with(self.device.handle)

    def test_set_event_packaging(self):
        self.device.set_event_packaging(1)
        self.mock_lib.set_event_packaging.assert_called_once_with(self.device.handle, 1)

    def test_get_event_packaging(self):
        self.device.get_event_packaging()
        self.mock_lib.get_event_packaging.assert_called_once_with(self.device.handle, ANY)

    def test_set_max_num_aggregates_blt(self):
        self.device.set_max_num_aggregates_blt(1)
        self.mock_lib.set_max_num_aggregates_blt.assert_called_once_with(self.device.handle, 1)

    def test_get_max_num_aggregates_blt(self):
        self.device.get_max_num_aggregates_blt()
        self.mock_lib.get_max_num_aggregates_blt.assert_called_once_with(self.device.handle, ANY)

    def test_allocate_event(self):
        self.device.allocate_event()
        self.device.free_event()
        self.mock_lib.allocate_event.assert_called_once_with(self.device.handle, ANY)
        self.mock_lib.free_event.assert_called_once_with(self.device.handle, ANY)

    def test_set_num_events_per_aggregate(self):
        self.device.set_num_events_per_aggregate(1, 2)
        self.mock_lib.set_num_events_per_aggregate.assert_called_once_with(self.device.handle, 1, 2)

    def test_get_num_events_per_aggregate(self):
        self.device.get_num_events_per_aggregate(2)
        self.mock_lib.get_num_events_per_aggregate.assert_called_once_with(self.device.handle, ANY, 2)

    def test_dpp_event_aggregation(self):
        self.device.set_dpp_event_aggregation(1, 1)
        self.mock_lib.set_dpp_event_aggregation.assert_called_once_with(self.device.handle, 1, 1)

    def test_set_dpp_acquisition_mode(self):
        self.device.set_dpp_acquisition_mode(dgtz.DPPAcqMode.LIST, dgtz.DPPSaveParam.CHARGE_AND_TIME)
        self.mock_lib.set_dpp_acquisition_mode.assert_called_once_with(self.device.handle, dgtz.DPPAcqMode.LIST, dgtz.DPPSaveParam.CHARGE_AND_TIME)

    def test_get_dpp_acquisition_mode(self):
        self.device.get_dpp_acquisition_mode()
        self.mock_lib.get_dpp_acquisition_mode.assert_called_once_with(self.device.handle, ANY, ANY)

    def test_set_dpp_trigger_mode(self):
        self.device.set_dpp_trigger_mode(dgtz.DPPTriggerMode.NORMAL)
        self.mock_lib.set_dpp_trigger_mode.assert_called_once_with(self.device.handle, dgtz.DPPTriggerMode.NORMAL)

    def test_get_dpp_trigger_mode(self):
        self.device.get_dpp_trigger_mode()
        self.mock_lib.get_dpp_trigger_mode.assert_called_once_with(self.device.handle, ANY)

    def test_set_dpp_virtual_probe(self):
        self.device.set_dpp_virtual_probe(dgtz.DPPTrace.ANALOG_1, dgtz.DPPProbe.VIRTUAL_BASELINE)
        self.mock_lib.set_dpp_virtual_probe.assert_called_once_with(self.device.handle, dgtz.DPPTrace.ANALOG_1, dgtz.DPPProbe.VIRTUAL_BASELINE)

    def test_get_dpp_virtual_probe(self):
        self.device.get_dpp_virtual_probe(dgtz.DPPTrace.ANALOG_1)
        self.mock_lib.get_dpp_virtual_probe.assert_called_once_with(self.device.handle, dgtz.DPPTrace.ANALOG_1, ANY)

    def test_get_get_dpp_supported_virtual_probes(self):
        self.device.get_dpp_supported_virtual_probes(dgtz.DPPTrace.ANALOG_1)
        self.mock_lib.get_dpp_supported_virtual_probes.assert_called_once_with(self.device.handle, dgtz.DPPTrace.ANALOG_1, ANY, ANY)

    def test_set_io_level(self):
        self.device.set_io_level(dgtz.IOLevel.NIM)
        self.mock_lib.set_io_level.assert_called_once_with(self.device.handle, dgtz.IOLevel.NIM)

    def test_get_io_level(self):
        self.device.get_io_level()
        self.mock_lib.get_io_level.assert_called_once_with(self.device.handle, ANY)

    def test_set_trigger_polarity(self):
        self.device.set_trigger_polarity(1, dgtz.TriggerPolarity.ON_FALLING_EDGE)
        self.mock_lib.set_trigger_polarity.assert_called_once_with(self.device.handle, 1, dgtz.TriggerPolarity.ON_FALLING_EDGE)

    def test_get_trigger_polarity(self):
        self.device.get_trigger_polarity(1)
        self.mock_lib.get_trigger_polarity.assert_called_once_with(self.device.handle, 1, ANY)

    def test_rearm_interrupt(self):
        self.device.rearm_interrupt()
        self.mock_lib.rearm_interrupt.assert_called_once_with(self.device.handle)

    def test_set_drs4_sampling_frequency(self):
        self.device.set_drs4_sampling_frequency(dgtz.DRS4Frequency.F_1GHz)
        self.mock_lib.set_drs4_sampling_frequency.assert_called_once_with(self.device.handle, dgtz.DRS4Frequency.F_1GHz)

    def test_get_drs4_sampling_frequency(self):
        self.device.get_drs4_sampling_frequency()
        self.mock_lib.get_drs4_sampling_frequency.assert_called_once_with(self.device.handle, ANY)

    def test_set_output_signal_mode(self):
        self.device.set_output_signal_mode(dgtz.OutputSignalMode.BUSY)
        self.mock_lib.set_output_signal_mode.assert_called_once_with(self.device.handle, dgtz.OutputSignalMode.BUSY)

    def test_get_output_signal_mode(self):
        self.device.get_output_signal_mode()
        self.mock_lib.get_output_signal_mode.assert_called_once_with(self.device.handle, ANY)

    def test_set_group_fast_trigger_threshold(self):
        self.device.set_group_fast_trigger_threshold(1, 2)
        self.mock_lib.set_group_fast_trigger_threshold.assert_called_once_with(self.device.handle, 1, 2)

    def test_get_group_fast_trigger_threshold(self):
        self.device.get_group_fast_trigger_threshold(1)
        self.mock_lib.get_group_fast_trigger_threshold.assert_called_once_with(self.device.handle, 1, ANY)

    def test_set_group_fast_trigger_dc_offset(self):
        self.device.set_group_fast_trigger_dc_offset(1, 2)
        self.mock_lib.set_group_fast_trigger_dc_offset.assert_called_once_with(self.device.handle, 1, 2)

    def test_get_group_fast_trigger_dc_offset(self):
        self.device.get_group_fast_trigger_dc_offset(1)
        self.mock_lib.get_group_fast_trigger_dc_offset.assert_called_once_with(self.device.handle, 1, ANY)

    def test_set_fast_trigger_digitizing(self):
        self.device.set_fast_trigger_digitizing(dgtz.EnaDis.DISABLE)
        self.mock_lib.set_fast_trigger_digitizing.assert_called_once_with(self.device.handle, dgtz.EnaDis.DISABLE)

    def test_get_fast_trigger_digitizing(self):
        self.device.get_fast_trigger_digitizing()
        self.mock_lib.get_fast_trigger_digitizing.assert_called_once_with(self.device.handle, ANY)

    def test_set_fast_trigger_mode(self):
        self.device.set_fast_trigger_mode(dgtz.TriggerMode.ACQ_AND_EXTOUT)
        self.mock_lib.set_fast_trigger_mode.assert_called_once_with(self.device.handle, dgtz.TriggerMode.ACQ_AND_EXTOUT)

    def test_get_fast_trigger_mode(self):
        self.device.get_fast_trigger_mode()
        self.mock_lib.get_fast_trigger_mode.assert_called_once_with(self.device.handle, ANY)

    def test_load_drs4_correction_data(self):
        self.device.load_drs4_correction_data()
        self.mock_lib.load_drs4_correction_data.assert_called_once_with(self.device.handle)

    def test_get_correction_tables(self):
        self.device.get_correction_tables(dgtz.DRS4Frequency.F_1GHz)
        self.mock_lib.get_correction_tables.assert_called_once_with(self.device.handle, dgtz.DRS4Frequency.F_1GHz, ANY)

    def test_enable_drs4_correction(self):
        self.device.enable_drs4_correction()
        self.mock_lib.enable_drs4_correction.assert_called_once_with(self.device.handle)

    def test_disable_drs4_correction(self):
        self.device.disable_drs4_correction()
        self.mock_lib.disable_drs4_correction.assert_called_once_with(self.device.handle)

    def test_sam_correction_level(self):
        self.device.set_sam_correction_level(dgtz.SAMCorrectionLevel.ALL)
        self.mock_lib.set_sam_correction_level.assert_called_once_with(self.device.handle, dgtz.SAMCorrectionLevel.ALL)

    def test_get_sam_correction_level(self):
        self.device.get_sam_correction_level()
        self.mock_lib.get_sam_correction_level.assert_called_once_with(self.device.handle, ANY)

    def test_enable_sam_pulse_gen(self):
        self.device.enable_sam_pulse_gen(1, 2, dgtz.SAMPulseSourceType.CONT)
        self.mock_lib.enable_sam_pulse_gen.assert_called_once_with(self.device.handle, 1, 2, dgtz.SAMPulseSourceType.CONT)

    def test_disable_sam_pulse_gen(self):
        self.device.disable_sam_pulse_gen(1)
        self.mock_lib.disable_sam_pulse_gen.assert_called_once_with(self.device.handle, 1)

    def test_set_sam_post_trigger_size(self):
        self.device.set_sam_post_trigger_size(100, 200)
        self.mock_lib.set_sam_post_trigger_size.assert_called_once_with(self.device.handle, 100, 200)

    def test_get_sam_post_trigger_size(self):
        self.device.get_sam_post_trigger_size(0)
        self.mock_lib.get_sam_post_trigger_size.assert_called_once_with(self.device.handle, 0, ANY)

    def test_set_sam_sampling_frequency(self):
        self.device.set_sam_sampling_frequency(dgtz.SAMFrequency.F_400MHz)
        self.mock_lib.set_sam_sampling_frequency.assert_called_once_with(self.device.handle, dgtz.SAMFrequency.F_400MHz)

    def test_get_sam_sampling_frequency(self):
        self.device.get_sam_sampling_frequency()
        self.mock_lib.get_sam_sampling_frequency.assert_called_once_with(self.device.handle, ANY)

    def test_load_sam_correction_data(self):
        self.device.load_sam_correction_data()
        self.mock_lib.load_sam_correction_data.assert_called_once_with(self.device.handle)

    def test_read_eeprom(self):
        self.device.read_eeprom(1, 2, 3)
        self.mock_lib.read_eeprom.assert_called_once_with(self.device.handle, 1, 2, 3, ANY)

    def test_write_eeprom(self):
        self.device.write_eeprom(1, 2, b'')
        self.mock_lib.write_eeprom.assert_called_once_with(self.device.handle, 1, 2, ANY, ANY)

    def test_trigger_threshold(self):
        self.device.trigger_threshold(dgtz.EnaDis.ENABLE)
        self.mock_lib.trigger_threshold.assert_called_once_with(self.device.handle, dgtz.EnaDis.ENABLE)

    def test_send_sam_pulse(self):
        self.device.send_sam_pulse()
        self.mock_lib.send_sam_pulse.assert_called_once_with(self.device.handle,)

    def test_set_sam_acquisition_mode(self):
        self.device.set_sam_acquisition_mode(dgtz.AcqMode.FIRST_TRG_CONTROLLED)
        self.mock_lib.set_sam_acquisition_mode.assert_called_once_with(self.device.handle, dgtz.AcqMode.FIRST_TRG_CONTROLLED)

    def test_get_sam_acquisition_mode(self):
        self.device.get_sam_acquisition_mode()
        self.mock_lib.get_sam_acquisition_mode.assert_called_once_with(self.device.handle, ANY)

    def test_set_trigger_logic(self):
        self.device.set_trigger_logic(dgtz.TriggerLogic.OR, 1)
        self.mock_lib.set_trigger_logic.assert_called_once_with(self.device.handle, dgtz.TriggerLogic.OR, 1)

    def test_get_trigger_logic(self):
        self.device.get_trigger_logic()
        self.mock_lib.get_trigger_logic.assert_called_once_with(self.device.handle, ANY, ANY)

    def test_set_channel_pair_trigger_logic(self):
        self.device.set_channel_pair_trigger_logic(1, 2, dgtz.TriggerLogic.AND, 3)
        self.mock_lib.set_channel_pair_trigger_logic.assert_called_once_with(self.device.handle, 1, 2, dgtz.TriggerLogic.AND, 3)

    def test_get_channel_pair_trigger_logic(self):
        self.device.get_channel_pair_trigger_logic(1, 2)
        self.mock_lib.get_channel_pair_trigger_logic.assert_called_once_with(self.device.handle, 1, 2, ANY, ANY)

    def test_set_decimation_factor(self):
        self.device.set_decimation_factor(1)
        self.mock_lib.set_decimation_factor.assert_called_once_with(self.device.handle, 1)

    def test_get_decimation_factor(self):
        self.device.get_decimation_factor()
        self.mock_lib.get_decimation_factor.assert_called_once_with(self.device.handle, ANY)

    def test_set_sam_trigger_count_veto_param(self):
        self.device.set_sam_trigger_count_veto_param(1, dgtz.EnaDis.ENABLE, 2)
        self.mock_lib.set_sam_trigger_count_veto_param.assert_called_once_with(self.device.handle, 1, dgtz.EnaDis.ENABLE, 2)

    def test_get_sam_trigger_count_veto_param(self):
        self.device.get_sam_trigger_count_veto_param(1)
        self.mock_lib.get_sam_trigger_count_veto_param.assert_called_once_with(self.device.handle, 1, ANY, ANY)

    def test_set_trigger_in_as_gate(self):
        self.device.set_trigger_in_as_gate(dgtz.EnaDis.ENABLE)
        self.mock_lib.set_trigger_in_as_gate.assert_called_once_with(self.device.handle, dgtz.EnaDis.ENABLE)

    def test_calibrate(self):
        self.device.calibrate()
        self.mock_lib.calibrate.assert_called_once_with(self.device.handle)

    def test_read_temperature(self):
        self.device.read_temperature(1)
        self.mock_lib.read_temperature.assert_called_once_with(self.device.handle, 1, ANY)

    def test_get_dpp_firmware_type(self):
        self.device.get_dpp_firmware_type()
        self.mock_lib.get_dpp_firmware_type.assert_called_once_with(self.device.handle, ANY)

if __name__ == '__main__':
    unittest.main()
