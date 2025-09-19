
"""Tests for the caendigitizer module."""

import unittest
from unittest.mock import patch, ANY, DEFAULT

import caen_libs.caendigitizer as dgtz

class TestDevice(unittest.TestCase):

    def setUp(self):
        patcher = patch('caen_libs.caendigitizer.lib', autospec=True)
        self.addCleanup(patcher.stop)
        self.mock_lib = patcher.start()
        def side_effect(*args):
            args[4].value = 0xdeadbeaf
            return DEFAULT
        self.mock_lib.open_digitizer2.side_effect = side_effect
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

    def test_write_register(self):
        self.device.write_register(0x1000, 0x1234)
        self.mock_lib.write_register.assert_called_once_with(self.device.handle, 0x1000, 0x1234)


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
        self.device.read_data(1)
        self.mock_lib.read_data.assert_called_once_with(self.device.handle, 1, ANY, ANY)

    def test_get_num_events(self):
        self.device.get_num_events()
        self.mock_lib.get_num_events.assert_called_once_with(self.device.handle, ANY, ANY, ANY)

    def test_get_event_info(self):
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


if __name__ == '__main__':
    unittest.main()
