import ctypes as ct
import unittest
from unittest.mock import DEFAULT, patch

import caen_libs.caenvme as vme

class TestDevice(unittest.TestCase):

    def setUp(self):
        patcher = patch('caen_libs.caenvme.lib', autospec=True)
        self.addCleanup(patcher.stop)
        self.mock_lib = patcher.start()
        self.device = vme.Device.open(vme.BoardType.V2718, 0)
        self.addCleanup(self.device.close)

    def test_error_handling(self):
        self.mock_lib.init2.side_effect = vme.Error("Test error", -1, "Init2")
        with self.assertRaises(vme.Error):
            vme.Device.open(vme.BoardType.V2718, 0)

    def test_device_reset(self):
        self.device.device_reset()
        self.mock_lib.device_reset.assert_called_once_with(0)

    def test_board_fw_release(self):
        self.mock_lib.board_fw_release.return_value = 0
        fw_release = self.device.board_fw_release()
        self.assertEqual(fw_release, '')
        self.mock_lib.board_fw_release.assert_called_once_with(0, unittest.mock.ANY)

    def test_driver_release(self):
        self.mock_lib.driver_release.return_value = 0
        driver_release = self.device.driver_release()
        self.assertEqual(driver_release, '')
        self.mock_lib.driver_release.assert_called_once_with(0, unittest.mock.ANY)

    def test_read_register(self):
        self.mock_lib.read_register.return_value = 0
        value = self.device.read_register(0x1000)
        self.assertEqual(value, 0)
        self.mock_lib.read_register.assert_called_once_with(0, 0x1000, unittest.mock.ANY)

    def test_write_register(self):
        self.device.write_register(0x1000, 0x1234)
        self.mock_lib.write_register.assert_called_once_with(0, 0x1000, 0x1234)

    def test_read_cycle(self):
        self.mock_lib.read_cycle.return_value = 0
        value = self.device.read_cycle(0x1000, vme.AddressModifiers.A32_U_DATA, vme.DataWidth.D32)
        self.assertEqual(value, 0)
        self.mock_lib.read_cycle.assert_called_once_with(0, 0x1000, unittest.mock.ANY, vme.AddressModifiers.A32_U_DATA, vme.DataWidth.D32)

    def test_write_cycle(self):
        self.device.write_cycle(0x1000, 0x1234, vme.AddressModifiers.A32_U_DATA, vme.DataWidth.D32)
        self.mock_lib.write_cycle.assert_called_once_with(0, 0x1000, unittest.mock.ANY, vme.AddressModifiers.A32_U_DATA, vme.DataWidth.D32)

    def test_multi_read(self):
        self.mock_lib.multi_read.return_value = 0
        addrs = [0x1000, 0x2000]
        ams = [vme.AddressModifiers.A32_U_DATA, vme.AddressModifiers.A32_U_DATA]
        dws = [vme.DataWidth.D32, vme.DataWidth.D32]
        values = self.device.multi_read(addrs, ams, dws)
        self.assertEqual(values, [0, 0])
        self.mock_lib.multi_read.assert_called_once_with(0, unittest.mock.ANY, unittest.mock.ANY, 2, unittest.mock.ANY, unittest.mock.ANY, unittest.mock.ANY)

    def test_multi_write(self):
        addrs = [0x1000, 0x2000]
        data = [0x1234, 0x5678]
        ams = [vme.AddressModifiers.A32_U_DATA, vme.AddressModifiers.A32_U_DATA]
        dws = [vme.DataWidth.D32, vme.DataWidth.D32]
        self.device.multi_write(addrs, data, ams, dws)
        self.mock_lib.multi_write.assert_called_once_with(0, unittest.mock.ANY, unittest.mock.ANY, 2, unittest.mock.ANY, unittest.mock.ANY, unittest.mock.ANY)

    def test_irq_enable(self):
        self.device.irq_enable(vme.IRQLevels.L1)
        self.mock_lib.irq_enable.assert_called_once_with(0, vme.IRQLevels.L1)

    def test_irq_disable(self):
        self.device.irq_disable(vme.IRQLevels.L1)
        self.mock_lib.irq_disable.assert_called_once_with(0, vme.IRQLevels.L1)

    def test_irq_wait(self):
        self.device.irq_wait(vme.IRQLevels.L1, 1000)
        self.mock_lib.irq_wait.assert_called_once_with(0, vme.IRQLevels.L1, 1000)

    def test_blt_read_cycle(self):
        self.mock_lib.blt_read_cycle.return_value = 0
        values = self.device.blt_read_cycle(0x1000, 256, vme.AddressModifiers.A32_U_DATA, vme.DataWidth.D32)
        self.assertEqual(values, [])
        self.mock_lib.blt_read_cycle.assert_called_once_with(0, 0x1000, unittest.mock.ANY, 256, vme.AddressModifiers.A32_U_DATA, vme.DataWidth.D32, unittest.mock.ANY)

    def test_fifo_blt_read_cycle(self):
        self.mock_lib.fifo_blt_read_cycle.return_value = 0
        values = self.device.fifo_blt_read_cycle(0x1000, 256, vme.AddressModifiers.A32_U_DATA, vme.DataWidth.D32)
        self.assertEqual(values, [])
        self.mock_lib.fifo_blt_read_cycle.assert_called_once_with(0, 0x1000, unittest.mock.ANY, 256, vme.AddressModifiers.A32_U_DATA, vme.DataWidth.D32, unittest.mock.ANY)

    def test_mblt_read_cycle(self):
        self.mock_lib.mblt_read_cycle.return_value = 0
        values = self.device.mblt_read_cycle(0x1000, 256, vme.AddressModifiers.A32_U_DATA)
        self.assertEqual(values, b'')
        self.mock_lib.mblt_read_cycle.assert_called_once_with(0, 0x1000, unittest.mock.ANY, 256, vme.AddressModifiers.A32_U_DATA, unittest.mock.ANY)

    def test_fifo_mblt_read_cycle(self):
        def side_effect(*args):
            args[2][0:4] = b'\x12\x34\x56\x78'
            args[5].value = 2
            return DEFAULT
        self.mock_lib.fifo_mblt_read_cycle.return_value = 0
        self.mock_lib.fifo_mblt_read_cycle.side_effect = side_effect
        values = self.device.fifo_mblt_read_cycle(0x1000, 256, vme.AddressModifiers.A32_U_DATA)
        self.assertEqual(values, b'\x12\x34')
        self.mock_lib.fifo_mblt_read_cycle.assert_called_once_with(0, 0x1000, unittest.mock.ANY, 256, vme.AddressModifiers.A32_U_DATA, unittest.mock.ANY)

    def test_blt_write_cycle(self):
        def side_effect(*args):
            args[6].value = 10
            return DEFAULT
        self.mock_lib.blt_write_cycle.return_value = 0
        self.mock_lib.blt_write_cycle.side_effect = side_effect
        count = self.device.blt_write_cycle(0x1000, [0x1234, 0x5678], vme.AddressModifiers.A32_U_DATA, vme.DataWidth.D32)
        self.assertEqual(count, 10)
        self.mock_lib.blt_write_cycle.assert_called_once_with(0, 0x1000, unittest.mock.ANY, 8, vme.AddressModifiers.A32_U_DATA, vme.DataWidth.D32, unittest.mock.ANY)

    def test_fifo_blt_write_cycle(self):
        self.mock_lib.fifo_blt_write_cycle.return_value = 0
        count = self.device.fifo_blt_write_cycle(0x1000, [0x1234, 0x5678], vme.AddressModifiers.A32_U_DATA, vme.DataWidth.D32)
        self.assertEqual(count, 0)
        self.mock_lib.fifo_blt_write_cycle.assert_called_once_with(0, 0x1000, unittest.mock.ANY, 8, vme.AddressModifiers.A32_U_DATA, vme.DataWidth.D32, unittest.mock.ANY)

    def test_mblt_write_cycle(self):
        self.mock_lib.mblt_write_cycle.return_value = 0
        count = self.device.mblt_write_cycle(0x1000, b'\x12\x34\x56\x78', vme.AddressModifiers.A32_U_DATA)
        self.assertEqual(count, 0)
        self.mock_lib.mblt_write_cycle.assert_called_once_with(0, 0x1000, unittest.mock.ANY, 4, vme.AddressModifiers.A32_U_DATA, unittest.mock.ANY)

    def test_fifo_mblt_write_cycle(self):
        self.mock_lib.fifo_mblt_write_cycle.return_value = 0
        count = self.device.fifo_mblt_write_cycle(0x1000, b'\x12\x34\x56\x78', vme.AddressModifiers.A32_U_DATA)
        self.assertEqual(count, 0)
        self.mock_lib.fifo_mblt_write_cycle.assert_called_once_with(0, 0x1000, unittest.mock.ANY, 4, vme.AddressModifiers.A32_U_DATA, unittest.mock.ANY)

    def test_ado_cycle(self):
        self.device.ado_cycle(0x1000, vme.AddressModifiers.A32_U_DATA)
        self.mock_lib.ado_cycle.assert_called_once_with(0, 0x1000, vme.AddressModifiers.A32_U_DATA)

    def test_adoh_cycle(self):
        self.device.adoh_cycle(0x1000, vme.AddressModifiers.A32_U_DATA)
        self.mock_lib.adoh_cycle.assert_called_once_with(0, 0x1000, vme.AddressModifiers.A32_U_DATA)

    def test_iack_cycle(self):
        self.mock_lib.iack_cycle.return_value = 0
        value = self.device.iack_cycle(vme.IRQLevels.L1, vme.DataWidth.D32)
        self.assertEqual(value, 0)
        self.mock_lib.iack_cycle.assert_called_once_with(0, vme.IRQLevels.L1, unittest.mock.ANY, vme.DataWidth.D32)

    def test_irq_check(self):
        self.mock_lib.irq_check.return_value = 0
        value = self.device.irq_check()
        self.assertEqual(value, 0)
        self.mock_lib.irq_check.assert_called_once_with(0, unittest.mock.ANY)

    def test_set_pulser_conf(self):
        self.device.set_pulser_conf(vme.PulserSelect.A, 1000, 500, vme.TimeUnits.T25_NS, 10, vme.IOSources.MANUAL_SW, vme.IOSources.INPUT_SRC_0)
        self.mock_lib.set_pulser_conf.assert_called_once_with(0, vme.PulserSelect.A, 1000, 500, vme.TimeUnits.T25_NS, 10, vme.IOSources.MANUAL_SW, vme.IOSources.INPUT_SRC_0)

    def test_set_scaler_conf(self):
        self.device.set_scaler_conf(1000, 1, vme.IOSources.INPUT_SRC_0, vme.IOSources.INPUT_SRC_1, vme.IOSources.MANUAL_SW)
        self.mock_lib.set_scaler_conf.assert_called_once_with(0, 1000, 1, vme.IOSources.INPUT_SRC_0, vme.IOSources.INPUT_SRC_1, vme.IOSources.MANUAL_SW)

    def test_set_output_conf(self):
        self.device.set_output_conf(vme.OutputSelect.O0, vme.IOPolarity.DIRECT, vme.LEDPolarity.ACTIVE_HIGH, vme.IOSources.MANUAL_SW)
        self.mock_lib.set_output_conf.assert_called_once_with(0, vme.OutputSelect.O0, vme.IOPolarity.DIRECT, vme.LEDPolarity.ACTIVE_HIGH, vme.IOSources.MANUAL_SW)

    def test_set_input_conf(self):
        self.device.set_input_conf(vme.InputSelect.I0, vme.IOPolarity.DIRECT, vme.LEDPolarity.ACTIVE_HIGH)
        self.mock_lib.set_input_conf.assert_called_once_with(0, vme.InputSelect.I0, vme.IOPolarity.DIRECT, vme.LEDPolarity.ACTIVE_HIGH)

    def test_get_pulser_conf(self):
        conf = self.device.get_pulser_conf(vme.PulserSelect.A)
        self.assertEqual(conf, (0, 0, 0, 0, 0, 0))
        self.mock_lib.get_pulser_conf.assert_called_once_with(0, vme.PulserSelect.A, unittest.mock.ANY, unittest.mock.ANY, unittest.mock.ANY, unittest.mock.ANY, unittest.mock.ANY, unittest.mock.ANY)

    def test_get_scaler_conf(self):
        conf = self.device.get_scaler_conf()
        self.assertEqual(conf, (0, 0, 0, 0, 0))
        self.mock_lib.get_scaler_conf.assert_called_once_with(0, unittest.mock.ANY, unittest.mock.ANY, unittest.mock.ANY, unittest.mock.ANY, unittest.mock.ANY)

    def test_get_output_conf(self):
        conf = self.device.get_output_conf(vme.OutputSelect.O0)
        self.assertEqual(conf, (0, 0, 0))
        self.mock_lib.get_output_conf.assert_called_once_with(0, vme.OutputSelect.O0, unittest.mock.ANY, unittest.mock.ANY, unittest.mock.ANY)

    def test_get_input_conf(self):
        conf = self.device.get_input_conf(vme.InputSelect.I0)
        self.assertEqual(conf, (0, 0))
        self.mock_lib.get_input_conf.assert_called_once_with(0, vme.InputSelect.I0, unittest.mock.ANY, unittest.mock.ANY)

    def test_set_arbiter_type(self):
        self.device.set_arbiter_type(vme.ArbiterTypes.PRIORIZED)
        self.mock_lib.set_arbiter_type.assert_called_once_with(0, vme.ArbiterTypes.PRIORIZED)

    def test_set_requester_type(self):
        self.device.set_requester_type(vme.RequesterTypes.FAIR)
        self.mock_lib.set_requester_type.assert_called_once_with(0, vme.RequesterTypes.FAIR)

    def test_set_release_type(self):
        self.device.set_release_type(vme.ReleaseTypes.RWD)
        self.mock_lib.set_release_type.assert_called_once_with(0, vme.ReleaseTypes.RWD)

    def test_set_bus_req_level(self):
        self.device.set_bus_req_level(vme.BusReqLevels.BR0)
        self.mock_lib.set_bus_req_level.assert_called_once_with(0, vme.BusReqLevels.BR0)

    def test_set_timeout(self):
        self.device.set_timeout(vme.VMETimeouts.T50_US)
        self.mock_lib.set_timeout.assert_called_once_with(0, vme.VMETimeouts.T50_US)

    def test_set_location_monitor(self):
        self.device.set_location_monitor(0x1000, vme.AddressModifiers.A32_U_DATA, 1, 1, 1)
        self.mock_lib.set_location_monitor.assert_called_once_with(0, 0x1000, vme.AddressModifiers.A32_U_DATA, 1, 1, 1)

    def test_set_fifo_mode(self):
        self.device.set_fifo_mode(1)
        self.mock_lib.set_fifo_mode.assert_called_once_with(0, 1)

    def test_get_arbiter_type(self):
        self.mock_lib.get_arbiter_type.return_value = 0
        value = self.device.get_arbiter_type()
        self.assertEqual(value, 0)
        self.mock_lib.get_arbiter_type.assert_called_once_with(0, unittest.mock.ANY)

    def test_get_requester_type(self):
        self.mock_lib.get_requester_type.return_value = 0
        value = self.device.get_requester_type()
        self.assertEqual(value, 0)
        self.mock_lib.get_requester_type.assert_called_once_with(0, unittest.mock.ANY)

    def test_get_release_type(self):
        self.mock_lib.get_release_type.return_value = 0
        value = self.device.get_release_type(vme.ReleaseTypes.RWD)
        self.assertEqual(value, 0)
        self.mock_lib.get_release_type.assert_called_once_with(0, vme.ReleaseTypes.RWD)

    def test_get_bus_req_level(self):
        self.mock_lib.get_bus_req_level.return_value = 0
        value = self.device.get_bus_req_level()
        self.assertEqual(value, 0)
        self.mock_lib.get_bus_req_level.assert_called_once_with(0, unittest.mock.ANY)

    def test_get_timeout(self):
        self.mock_lib.get_timeout.return_value = 0
        value = self.device.get_timeout()
        self.assertEqual(value, 0)
        self.mock_lib.get_timeout.assert_called_once_with(0, unittest.mock.ANY)

    def test_get_fifo_mode(self):
        self.mock_lib.get_fifo_mode.return_value = 0
        value = self.device.get_fifo_mode()
        self.assertEqual(value, 0)
        self.mock_lib.get_fifo_mode.assert_called_once_with(0, unittest.mock.ANY)

    def test_system_reset(self):
        self.device.system_reset()
        self.mock_lib.system_reset.assert_called_once_with(0)

    def test_reset_scaler_count(self):
        self.device.reset_scaler_count()
        self.mock_lib.reset_scaler_count.assert_called_once_with(0)

    def test_enable_scaler_gate(self):
        self.device.enable_scaler_gate()
        self.mock_lib.enable_scaler_gate.assert_called_once_with(0)

    def test_disable_scaler_gate(self):
        self.device.disable_scaler_gate()
        self.mock_lib.disable_scaler_gate.assert_called_once_with(0)

    def test_start_pulser(self):
        self.device.start_pulser(vme.PulserSelect.A)
        self.mock_lib.start_pulser.assert_called_once_with(0, vme.PulserSelect.A)

    def test_stop_pulser(self):
        self.device.stop_pulser(vme.PulserSelect.A)
        self.mock_lib.stop_pulser.assert_called_once_with(0, vme.PulserSelect.A)

    def test_read_flash_page(self):
        self.mock_lib.read_flash_page.return_value = 0
        values = self.device.read_flash_page(0)
        self.assertEqual(values, b'\x00' * 264)
        self.mock_lib.read_flash_page.assert_called_once_with(0, unittest.mock.ANY, 0)

    def test_erase_flash_page(self):
        self.device.erase_flash_page(0)
        self.mock_lib.erase_flash_page.assert_called_once_with(0, 0)

    def test_set_scaler_input_source(self):
        self.device.set_scaler_input_source(vme.ScalerSource.IN0)
        self.mock_lib.set_scaler_input_source.assert_called_once_with(0, vme.ScalerSource.IN0)

    def test_get_scaler_input_source(self):
        def side_effect(*args):
            args[1].value = vme.ScalerSource.IN0.value
            return DEFAULT
        self.mock_lib.get_scaler_input_source.side_effect = side_effect
        self.mock_lib.get_scaler_input_source.return_value = 0
        value = self.device.get_scaler_input_source()
        self.assertEqual(value, vme.ScalerSource.IN0.value)
        self.mock_lib.get_scaler_input_source.assert_called_once_with(0, unittest.mock.ANY)

    def test_set_scaler_gate_source(self):
        self.device.set_scaler_gate_source(vme.ScalerSource.IN0)
        self.mock_lib.set_scaler_gate_source.assert_called_once_with(0, vme.ScalerSource.IN0)

    def test_get_scaler_gate_source(self):
        def side_effect(*args):
            args[1].value = vme.ScalerSource.IN0.value
            return DEFAULT
        self.mock_lib.get_scaler_gate_source.side_effect = side_effect
        self.mock_lib.get_scaler_gate_source.return_value = 0
        value = self.device.get_scaler_gate_source()
        self.assertEqual(value, vme.ScalerSource.IN0.value)
        self.mock_lib.get_scaler_gate_source.assert_called_once_with(0, unittest.mock.ANY)

    def test_set_scaler_mode(self):
        self.device.set_scaler_mode(vme.ScalerMode.GATE_MODE)
        self.mock_lib.set_scaler_mode.assert_called_once_with(0, vme.ScalerMode.GATE_MODE)

    def test_get_scaler_mode(self):
        self.mock_lib.get_scaler_mode.return_value = 0
        value = self.device.get_scaler_mode()
        self.assertEqual(value, 0)
        self.mock_lib.get_scaler_mode.assert_called_once_with(0, unittest.mock.ANY)

    def test_set_scaler_clear_source(self):
        self.device.set_scaler_clear_source(vme.ScalerSource.IN0)
        self.mock_lib.set_scaler_clear_source.assert_called_once_with(0, vme.ScalerSource.IN0)

    def test_set_scaler_start_source(self):
        self.device.set_scaler_start_source(vme.ScalerSource.IN0)
        self.mock_lib.set_scaler_start_source.assert_called_once_with(0, vme.ScalerSource.IN0)

    def test_get_scaler_start_source(self):
        def side_effect(*args):
            args[1].value = vme.ScalerSource.IN0.value
            return DEFAULT
        self.mock_lib.get_scaler_start_source.side_effect = side_effect
        self.mock_lib.get_scaler_start_source.return_value = 0
        value = self.device.get_scaler_start_source()
        self.assertEqual(value, vme.ScalerSource.IN0.value)
        self.mock_lib.get_scaler_start_source.assert_called_once_with(0, unittest.mock.ANY)

    def test_set_scaler_continuous_run(self):
        self.device.set_scaler_continuous_run(vme.ContinuosRun.ON)
        self.mock_lib.set_scaler_continuous_run.assert_called_once_with(0, vme.ContinuosRun.ON)

    def test_get_scaler_continuous_run(self):
        self.mock_lib.get_scaler_continuous_run.return_value = 0
        value = self.device.get_scaler_continuous_run()
        self.assertEqual(value, 0)
        self.mock_lib.get_scaler_continuous_run.assert_called_once_with(0, unittest.mock.ANY)

    def test_set_scaler_max_hits(self):
        self.device.set_scaler_max_hits(1000)
        self.mock_lib.set_scaler_max_hits.assert_called_once_with(0, 1000)

    def test_get_scaler_max_hits(self):
        self.mock_lib.get_scaler_max_hits.return_value = 0
        value = self.device.get_scaler_max_hits()
        self.assertEqual(value, 0)
        self.mock_lib.get_scaler_max_hits.assert_called_once_with(0, unittest.mock.ANY)

    def test_set_scaler_dwell_time(self):
        self.device.set_scaler_dwell_time(1000)
        self.mock_lib.set_scaler_dwell_time.assert_called_once_with(0, 1000)

    def test_get_scaler_dwell_time(self):
        self.mock_lib.get_scaler_dwell_time.return_value = 0
        value = self.device.get_scaler_dwell_time()
        self.assertEqual(value, 0)
        self.mock_lib.get_scaler_dwell_time.assert_called_once_with(0, unittest.mock.ANY)

    def test_set_scaler_sw_start(self):
        self.device.set_scaler_sw_start()
        self.mock_lib.set_scaler_sw_start.assert_called_once_with(0)

    def test_set_scaler_sw_stop(self):
        self.device.set_scaler_sw_stop()
        self.mock_lib.set_scaler_sw_stop.assert_called_once_with(0)

    def test_set_scaler_sw_reset(self):
        self.device.set_scaler_sw_reset()
        self.mock_lib.set_scaler_sw_reset.assert_called_once_with(0)

    def test_set_scaler_sw_open_gate(self):
        self.device.set_scaler_sw_open_gate()
        self.mock_lib.set_scaler_sw_open_gate.assert_called_once_with(0)

    def test_set_scaler_sw_close_gate(self):
        self.device.set_scaler_sw_close_gate()
        self.mock_lib.set_scaler_sw_close_gate.assert_called_once_with(0)

    def test_blt_read_async(self):
        self.mock_lib.blt_read_async.return_value = 0
        self.device.blt_read_async(0x1000, 256, vme.AddressModifiers.A32_U_DATA, vme.DataWidth.D32)
        self.mock_lib.blt_read_async.assert_called_once_with(0, 0x1000, unittest.mock.ANY, 256, vme.AddressModifiers.A32_U_DATA, vme.DataWidth.D32)

    def test_blt_read_wait(self):
        self.mock_lib.blt_read_wait.return_value = 0
        value = self.device.blt_read_wait()
        self.assertEqual(value, 0)
        self.mock_lib.blt_read_wait.assert_called_once_with(0, unittest.mock.ANY)

if __name__ == '__main__':
    unittest.main()