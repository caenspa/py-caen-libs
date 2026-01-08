"""Tests for the caen_libs.caenvme module."""

import unittest
from unittest.mock import ANY, DEFAULT, patch

import caen_libs.caenvme as vme


class TestDevice(unittest.TestCase):
    """Test the Device class."""

    def setUp(self):
        patcher = patch('caen_libs.caenvme.lib', autospec=True)
        self.addCleanup(patcher.stop)
        self.mock_lib = patcher.start()
        def side_effect(*args):
            args[3].value = 0xdeadbeaf
            return DEFAULT
        self.mock_lib.init2.side_effect = side_effect
        self.device = vme.Device.open(vme.BoardType.V2718, 0)
        self.addCleanup(self.device.close)

    def test_error_handling(self):
        """Test error handling."""
        self.mock_lib.init2.side_effect = vme.Error('Test error', -1, 'Init2')
        with self.assertRaises(vme.Error):
            vme.Device.open(vme.BoardType.V2718, 0)

    def test_device_reset(self):
        """Test device_reset"""
        self.device.device_reset()
        self.mock_lib.device_reset.assert_called_once_with(self.device.handle)

    def test_board_fw_release(self):
        """Test board_fw_release"""
        res = self.device.board_fw_release()
        self.assertEqual(res, '')
        self.mock_lib.board_fw_release.assert_called_once_with(self.device.handle, ANY)

    def test_driver_release(self):
        """Test driver_release"""
        res = self.device.driver_release()
        self.assertEqual(res, '')
        self.mock_lib.driver_release.assert_called_once_with(self.device.handle, ANY)

    def test_read_register(self):
        """Test read_register"""
        address = 0x1000
        def side_effect(*args):
            args[2].value = 0x1234
            return DEFAULT
        self.mock_lib.read_register.side_effect = side_effect
        res = self.device.read_register(address)
        self.assertEqual(res, 0x1234)
        self.mock_lib.read_register.assert_called_once_with(self.device.handle, address, ANY)

    def test_write_register(self):
        """Test write_register"""
        address = 0x1000
        value = 0x1234
        self.device.write_register(address, value)
        self.mock_lib.write_register.assert_called_once_with(self.device.handle, address, value)

    def test_read_cycle(self):
        """Test read_cycle"""
        address = 0x1000
        def side_effect(*args):
            args[2]._obj.value = 0x1234  # pylint: disable=W0212
            return DEFAULT
        self.mock_lib.read_cycle.side_effect = side_effect
        res = self.device.read_cycle(address, vme.AddressModifiers.A32_U_DATA, vme.DataWidth.D32)
        self.assertEqual(res, 0x1234)
        self.mock_lib.read_cycle.assert_called_once_with(self.device.handle, address, ANY, vme.AddressModifiers.A32_U_DATA, vme.DataWidth.D32)

    def test_write_cycle(self):
        """Test write_cycle"""
        address = 0x1000
        value = 0x1234
        self.device.write_cycle(address, value, vme.AddressModifiers.A32_U_DATA, vme.DataWidth.D32)
        self.mock_lib.write_cycle.assert_called_once_with(self.device.handle, address, ANY, vme.AddressModifiers.A32_U_DATA, vme.DataWidth.D32)

    def test_multi_read(self):
        """Test multi_read"""
        addrs = [0x1000, 0x2000]
        data = [0x1234, 0x5678]
        ams = [vme.AddressModifiers.A32_U_DATA, vme.AddressModifiers.A32_U_DATA]
        dws = [vme.DataWidth.D32, vme.DataWidth.D32]
        def side_effect(*args):
            args[2][:] = data
            return DEFAULT
        self.mock_lib.multi_read.side_effect = side_effect
        values = self.device.multi_read(addrs, ams, dws)
        self.assertEqual(values, data)
        self.mock_lib.multi_read.assert_called_once_with(self.device.handle, ANY, ANY, 2, ANY, ANY, ANY)

    def test_multi_write(self):
        """Test multi_write"""
        addrs = [0x1000, 0x2000]
        data = [0x1234, 0x5678]
        ams = [vme.AddressModifiers.A32_U_DATA, vme.AddressModifiers.A32_U_DATA]
        dws = [vme.DataWidth.D32, vme.DataWidth.D32]
        self.device.multi_write(addrs, data, ams, dws)
        self.mock_lib.multi_write.assert_called_once_with(self.device.handle, ANY, ANY, 2, ANY, ANY, ANY)

    def test_irq_enable(self):
        """Test irq_enable"""
        level = vme.IRQLevels.L1
        self.device.irq_enable(level)
        self.mock_lib.irq_enable.assert_called_once_with(self.device.handle, level)

    def test_irq_disable(self):
        """Test irq_disable"""
        level = vme.IRQLevels.L1
        self.device.irq_disable(level)
        self.mock_lib.irq_disable.assert_called_once_with(self.device.handle, level)

    def test_irq_wait(self):
        """Test irq_wait"""
        level = vme.IRQLevels.L1
        timeout = 1000
        self.device.irq_wait(level, timeout)
        self.mock_lib.irq_wait.assert_called_once_with(self.device.handle, level, timeout)

    def test_blt_read_cycle(self):
        """Test blt_read_cycle"""
        address = 0x1000
        size = 256
        address_modifier = vme.AddressModifiers.A32_U_DATA
        data_width = vme.DataWidth.D32
        data = list(i for i in range(size))
        def side_effect(*args):
            args[2][:] = data
            args[6].value = len(data)
            return DEFAULT
        self.mock_lib.blt_read_cycle.side_effect = side_effect
        result = self.device.blt_read_cycle(address, size, address_modifier, data_width)
        self.assertIsInstance(result, vme.ReadResult)
        self.assertEqual(list(result.data), data)
        self.assertFalse(result.bus_error)
        self.mock_lib.blt_read_cycle.assert_called_once_with(self.device.handle, address, ANY, size, address_modifier, data_width, ANY)

    def test_fifo_blt_read_cycle(self):
        """Test fifo_blt_read_cycle"""
        address = 0x1000
        size = 256
        address_modifier = vme.AddressModifiers.A32_U_DATA
        data_width = vme.DataWidth.D32
        data = list(i for i in range(size))
        def side_effect(*args):
            args[2][:] = data
            args[6].value = len(data)
            return DEFAULT
        self.mock_lib.fifo_blt_read_cycle.side_effect = side_effect
        result = self.device.fifo_blt_read_cycle(address, size, address_modifier, data_width)
        self.assertIsInstance(result, vme.ReadResult)
        self.assertEqual(list(result.data), data)
        self.assertFalse(result.bus_error)
        self.mock_lib.fifo_blt_read_cycle.assert_called_once_with(self.device.handle, address, ANY, size, address_modifier, data_width, ANY)

    def test_mblt_read_cycle(self):
        """Test mblt_read_cycle"""
        address = 0x1000
        size = 256
        address_modifier = vme.AddressModifiers.A32_U_DATA
        data = list(i for i in range(size))
        def side_effect(*args):
            args[2][:] = data
            args[5].value = len(data)
            return DEFAULT
        self.mock_lib.mblt_read_cycle.side_effect = side_effect
        result = self.device.mblt_read_cycle(address, size, address_modifier)
        self.assertIsInstance(result, vme.ReadResult)
        self.assertEqual(list(result.data), data)
        self.assertFalse(result.bus_error)
        self.mock_lib.mblt_read_cycle.assert_called_once_with(self.device.handle, address, ANY, size, address_modifier, ANY)

    def test_fifo_mblt_read_cycle(self):
        """Test fifo_mblt_read_cycle"""
        address = 0x1000
        size = 256
        address_modifier = vme.AddressModifiers.A32_U_DATA
        data = list(i for i in range(size))
        def side_effect(*args):
            args[2][:] = data
            args[5].value = len(data)
            return DEFAULT
        self.mock_lib.fifo_mblt_read_cycle.side_effect = side_effect
        result = self.device.fifo_mblt_read_cycle(address, size, address_modifier)
        self.assertIsInstance(result, vme.ReadResult)
        self.assertEqual(list(result.data), data)
        self.assertFalse(result.bus_error)
        self.mock_lib.fifo_mblt_read_cycle.assert_called_once_with(self.device.handle, address, ANY, size, address_modifier, ANY)

    def test_blt_write_cycle(self):
        """Test blt_write_cycle"""
        address = 0x1000
        data = b'\x00\x01\x02\x03\x04\x05\x06\x07'
        address_modifier = vme.AddressModifiers.A32_U_DATA
        data_width = vme.DataWidth.D32
        res = 10
        def side_effect(*args):
            args[6].value = res
            return DEFAULT
        self.mock_lib.blt_write_cycle.side_effect = side_effect
        count = self.device.blt_write_cycle(address, data, address_modifier, data_width)
        self.assertEqual(count, res)
        self.mock_lib.blt_write_cycle.assert_called_once_with(self.device.handle, address, ANY, len(data), address_modifier, data_width, ANY)

    def test_fifo_blt_write_cycle(self):
        """Test fifo_blt_write_cycle"""
        address = 0x1000
        data = b'\x12\x34\x56\x78'
        address_modifier = vme.AddressModifiers.A32_U_DATA
        data_width = vme.DataWidth.D32
        res = 10
        def side_effect(*args):
            args[6].value = res
            return DEFAULT
        self.mock_lib.fifo_blt_write_cycle.side_effect = side_effect
        count = self.device.fifo_blt_write_cycle(address, data, address_modifier, vme.DataWidth.D32)
        self.assertEqual(count, res)
        self.mock_lib.fifo_blt_write_cycle.assert_called_once_with(self.device.handle, address, ANY, len(data), address_modifier, data_width, ANY)

    def test_mblt_write_cycle(self):
        """Test mblt_write_cycle"""
        count = self.device.mblt_write_cycle(0x1000, b'\x12\x34\x56\x78', vme.AddressModifiers.A32_U_DATA)
        self.assertEqual(count, 0)
        self.mock_lib.mblt_write_cycle.assert_called_once_with(self.device.handle, 0x1000, ANY, 4, vme.AddressModifiers.A32_U_DATA, ANY)

    def test_fifo_mblt_write_cycle(self):
        """Test fifo_mblt_write_cycle"""
        count = self.device.fifo_mblt_write_cycle(0x1000, b'\x12\x34\x56\x78', vme.AddressModifiers.A32_U_DATA)
        self.assertEqual(count, 0)
        self.mock_lib.fifo_mblt_write_cycle.assert_called_once_with(self.device.handle, 0x1000, ANY, 4, vme.AddressModifiers.A32_U_DATA, ANY)

    def test_ado_cycle(self):
        """Test ado_cycle"""
        self.device.ado_cycle(0x1000, vme.AddressModifiers.A32_U_DATA)
        self.mock_lib.ado_cycle.assert_called_once_with(self.device.handle, 0x1000, vme.AddressModifiers.A32_U_DATA)

    def test_adoh_cycle(self):
        """Test adoh_cycle"""
        self.device.adoh_cycle(0x1000, vme.AddressModifiers.A32_U_DATA)
        self.mock_lib.adoh_cycle.assert_called_once_with(self.device.handle, 0x1000, vme.AddressModifiers.A32_U_DATA)

    def test_iack_cycle(self):
        """Test iack_cycle"""
        value = self.device.iack_cycle(vme.IRQLevels.L1, vme.DataWidth.D32)
        self.assertEqual(value, 0)
        self.mock_lib.iack_cycle.assert_called_once_with(self.device.handle, vme.IRQLevels.L1, ANY, vme.DataWidth.D32)

    def test_irq_check(self):
        """Test irq_check"""
        value = self.device.irq_check()
        self.assertEqual(value, 0)
        self.mock_lib.irq_check.assert_called_once_with(self.device.handle, ANY)

    def test_set_pulser_conf(self):
        """Test set_pulser_conf"""
        self.device.set_pulser_conf(vme.PulserSelect.A, 1000, 500, vme.TimeUnits.T25_NS, 10, vme.IOSources.MANUAL_SW, vme.IOSources.INPUT_SRC_0)
        self.mock_lib.set_pulser_conf.assert_called_once_with(self.device.handle, vme.PulserSelect.A, 1000, 500, vme.TimeUnits.T25_NS, 10, vme.IOSources.MANUAL_SW, vme.IOSources.INPUT_SRC_0)

    def test_set_scaler_conf(self):
        """Test set_scaler_conf"""
        self.device.set_scaler_conf(1000, 1, vme.IOSources.INPUT_SRC_0, vme.IOSources.INPUT_SRC_1, vme.IOSources.MANUAL_SW)
        self.mock_lib.set_scaler_conf.assert_called_once_with(self.device.handle, 1000, 1, vme.IOSources.INPUT_SRC_0, vme.IOSources.INPUT_SRC_1, vme.IOSources.MANUAL_SW)

    def test_set_output_conf(self):
        """Test set_output_conf"""
        self.device.set_output_conf(vme.OutputSelect.O0, vme.IOPolarity.DIRECT, vme.LEDPolarity.ACTIVE_HIGH, vme.IOSources.MANUAL_SW)
        self.mock_lib.set_output_conf.assert_called_once_with(self.device.handle, vme.OutputSelect.O0, vme.IOPolarity.DIRECT, vme.LEDPolarity.ACTIVE_HIGH, vme.IOSources.MANUAL_SW)

    def test_set_input_conf(self):
        """Test set_input_conf"""
        self.device.set_input_conf(vme.InputSelect.I0, vme.IOPolarity.DIRECT, vme.LEDPolarity.ACTIVE_HIGH)
        self.mock_lib.set_input_conf.assert_called_once_with(self.device.handle, vme.InputSelect.I0, vme.IOPolarity.DIRECT, vme.LEDPolarity.ACTIVE_HIGH)

    def test_get_pulser_conf(self):
        """Test get_pulser_conf"""
        conf = self.device.get_pulser_conf(vme.PulserSelect.A)
        self.assertEqual(conf, (0, 0, 0, 0, 0, 0))
        self.mock_lib.get_pulser_conf.assert_called_once_with(self.device.handle, vme.PulserSelect.A, ANY, ANY, ANY, ANY, ANY, ANY)

    def test_get_scaler_conf(self):
        """Test get_scaler_conf"""
        conf = self.device.get_scaler_conf()
        self.assertEqual(conf, (0, 0, 0, 0, 0))
        self.mock_lib.get_scaler_conf.assert_called_once_with(self.device.handle, ANY, ANY, ANY, ANY, ANY)

    def test_get_output_conf(self):
        """Test get_output_conf"""
        for i in set(vme.OutputSelect):
            conf = self.device.get_output_conf(i)
            self.assertEqual(conf, (0, 0, 0))
            self.mock_lib.get_output_conf.assert_called_with(self.device.handle, i, ANY, ANY, ANY)
            self.mock_lib.get_output_conf.reset_mock()

    def test_get_input_conf(self):
        """Test get_input_conf"""
        for i in set(vme.InputSelect):
            conf = self.device.get_input_conf(i)
            self.assertEqual(conf, (0, 0))
            self.mock_lib.get_input_conf.assert_called_with(self.device.handle, i, ANY, ANY)
            self.mock_lib.get_input_conf.reset_mock()

    def test_set_arbiter_type(self):
        """Test set_arbiter_type"""
        for i in set(vme.ArbiterTypes):
            self.device.set_arbiter_type(i)
            self.mock_lib.set_arbiter_type.assert_called_with(self.device.handle, i)
            self.mock_lib.set_arbiter_type.reset_mock()

    def test_set_requester_type(self):
        """Test set_requester_type"""
        for i in set(vme.RequesterTypes):
            self.device.set_requester_type(i)
            self.mock_lib.set_requester_type.assert_called_with(self.device.handle, i)
            self.mock_lib.set_requester_type.reset_mock()

    def test_set_release_type(self):
        """Test set_release_type"""
        for i in set(vme.ReleaseTypes):
            self.device.set_release_type(i)
            self.mock_lib.set_release_type.assert_called_with(self.device.handle, i)
            self.mock_lib.set_release_type.reset_mock()

    def test_set_bus_req_level(self):
        """Test set_bus_req_level"""
        for i in set(vme.BusReqLevels):
            self.device.set_bus_req_level(i)
            self.mock_lib.set_bus_req_level.assert_called_with(self.device.handle, i)
            self.mock_lib.set_bus_req_level.reset_mock()

    def test_set_timeout(self):
        """Test set_timeout"""
        for i in set(vme.VMETimeouts):
            self.device.set_timeout(i)
            self.mock_lib.set_timeout.assert_called_with(self.device.handle, i)
            self.mock_lib.set_timeout.reset_mock()

    def test_set_location_monitor(self):
        """Test set_location_monitor"""
        self.device.set_location_monitor(0x1000, vme.AddressModifiers.A32_U_DATA, 1, 1, 1)
        self.mock_lib.set_location_monitor.assert_called_once_with(self.device.handle, 0x1000, vme.AddressModifiers.A32_U_DATA, 1, 1, 1)

    def test_set_fifo_mode(self):
        """Test set_fifo_mode"""
        self.device.set_fifo_mode(1)
        self.mock_lib.set_fifo_mode.assert_called_once_with(self.device.handle, 1)

    def test_get_arbiter_type(self):
        """Test get_arbiter_type"""
        value = self.device.get_arbiter_type()
        self.assertEqual(value, 0)
        self.mock_lib.get_arbiter_type.assert_called_once_with(self.device.handle, ANY)

    def test_get_requester_type(self):
        """Test get_requester_type"""
        value = self.device.get_requester_type()
        self.assertEqual(value, 0)
        self.mock_lib.get_requester_type.assert_called_once_with(self.device.handle, ANY)

    def test_get_release_type(self):
        """Test get_release_type"""
        for i in set(vme.ReleaseTypes):
            value = self.device.get_release_type(i)
            self.assertEqual(value, 0)
            self.mock_lib.get_release_type.assert_called_with(self.device.handle, i)
            self.mock_lib.get_release_type.reset_mock()

    def test_get_bus_req_level(self):
        """Test get_bus_req_level"""
        value = self.device.get_bus_req_level()
        self.assertEqual(value, 0)
        self.mock_lib.get_bus_req_level.assert_called_once_with(self.device.handle, ANY)

    def test_get_timeout(self):
        """Test get_timeout"""
        value = self.device.get_timeout()
        self.assertEqual(value, 0)
        self.mock_lib.get_timeout.assert_called_once_with(self.device.handle, ANY)

    def test_get_fifo_mode(self):
        """Test get_fifo_mode"""
        value = self.device.get_fifo_mode()
        self.assertEqual(value, 0)
        self.mock_lib.get_fifo_mode.assert_called_once_with(self.device.handle, ANY)

    def test_system_reset(self):
        """Test system_reset"""
        self.device.system_reset()
        self.mock_lib.system_reset.assert_called_once_with(self.device.handle)

    def test_reset_scaler_count(self):
        """Test reset_scaler_count"""
        self.device.reset_scaler_count()
        self.mock_lib.reset_scaler_count.assert_called_once_with(self.device.handle)

    def test_enable_scaler_gate(self):
        """Test enable_scaler_gate"""
        self.device.enable_scaler_gate()
        self.mock_lib.enable_scaler_gate.assert_called_once_with(self.device.handle)

    def test_disable_scaler_gate(self):
        """Test disable_scaler_gate"""
        self.device.disable_scaler_gate()
        self.mock_lib.disable_scaler_gate.assert_called_once_with(self.device.handle)

    def test_start_pulser(self):
        """Test start_pulser"""
        for i in set(vme.PulserSelect):
            self.device.start_pulser(i)
            self.mock_lib.start_pulser.assert_called_with(self.device.handle, i)
            self.mock_lib.start_pulser.reset_mock()

    def test_stop_pulser(self):
        """Test stop_pulser"""
        for i in set(vme.PulserSelect):
            self.device.stop_pulser(i)
            self.mock_lib.stop_pulser.assert_called_with(self.device.handle, i)
            self.mock_lib.stop_pulser.reset_mock()

    def test_read_flash_page(self):
        """Test read_flash_page"""
        values = self.device.read_flash_page(0)
        self.assertEqual(values, b'\x00' * 264)
        self.mock_lib.read_flash_page.assert_called_once_with(self.device.handle, ANY, 0)

    def test_erase_flash_page(self):
        """Test erase_flash_page"""
        self.device.erase_flash_page(0)
        self.mock_lib.erase_flash_page.assert_called_once_with(self.device.handle, 0)

    def test_set_scaler_input_source(self):
        """Test set_scaler_input_source"""
        for i in set(vme.ScalerSource):
            self.device.set_scaler_input_source(i)
            self.mock_lib.set_scaler_input_source.assert_called_with(self.device.handle, i)
            self.mock_lib.set_scaler_input_source.reset_mock()

    def test_get_scaler_input_source(self):
        """Test get_scaler_input_source"""
        def side_effect(*args):
            args[1].value = vme.ScalerSource.IN0.value
            return DEFAULT
        self.mock_lib.get_scaler_input_source.side_effect = side_effect
        value = self.device.get_scaler_input_source()
        self.assertEqual(value, vme.ScalerSource.IN0.value)
        self.mock_lib.get_scaler_input_source.assert_called_once_with(self.device.handle, ANY)

    def test_set_scaler_gate_source(self):
        """Test set_scaler_gate_source"""
        for i in set(vme.ScalerSource):
            self.device.set_scaler_gate_source(i)
            self.mock_lib.set_scaler_gate_source.assert_called_with(self.device.handle, i)
            self.mock_lib.set_scaler_gate_source.reset_mock()

    def test_get_scaler_gate_source(self):
        """Test get_scaler_gate_source"""
        def side_effect(*args):
            args[1].value = vme.ScalerSource.IN0.value
            return DEFAULT
        self.mock_lib.get_scaler_gate_source.side_effect = side_effect
        value = self.device.get_scaler_gate_source()
        self.assertEqual(value, vme.ScalerSource.IN0.value)
        self.mock_lib.get_scaler_gate_source.assert_called_once_with(self.device.handle, ANY)

    def test_set_scaler_mode(self):
        """Test set_scaler_mode"""
        for i in set(vme.ScalerMode):
            self.device.set_scaler_mode(i)
            self.mock_lib.set_scaler_mode.assert_called_with(self.device.handle, i)
            self.mock_lib.set_scaler_mode.reset_mock()

    def test_get_scaler_mode(self):
        """Test get_scaler_mode"""
        value = self.device.get_scaler_mode()
        self.assertEqual(value, 0)
        self.mock_lib.get_scaler_mode.assert_called_once_with(self.device.handle, ANY)

    def test_set_scaler_clear_source(self):
        """Test set_scaler_clear_source"""
        for i in set(vme.ScalerSource):
            self.device.set_scaler_clear_source(i)
            self.mock_lib.set_scaler_clear_source.assert_called_with(self.device.handle, i)
            self.mock_lib.set_scaler_clear_source.reset_mock()

    def test_set_scaler_start_source(self):
        """Test set_scaler_start_source"""
        for i in set(vme.ScalerSource):
            self.device.set_scaler_start_source(i)
            self.mock_lib.set_scaler_start_source.assert_called_with(self.device.handle, i)
            self.mock_lib.set_scaler_start_source.reset_mock()

    def test_get_scaler_start_source(self):
        """Test get_scaler_start_source"""
        def side_effect(*args):
            args[1].value = vme.ScalerSource.IN0.value
            return DEFAULT
        self.mock_lib.get_scaler_start_source.side_effect = side_effect
        value = self.device.get_scaler_start_source()
        self.assertEqual(value, vme.ScalerSource.IN0.value)
        self.mock_lib.get_scaler_start_source.assert_called_once_with(self.device.handle, ANY)

    def test_set_scaler_continuous_run(self):
        """Test set_scaler_continuous_run"""
        for i in set(vme.ContinuosRun):
            self.device.set_scaler_continuous_run(i)
            self.mock_lib.set_scaler_continuous_run.assert_called_with(self.device.handle, i)
            self.mock_lib.set_scaler_continuous_run.reset_mock()

    def test_get_scaler_continuous_run(self):
        """Test get_scaler_continuous_run"""
        value = self.device.get_scaler_continuous_run()
        self.assertEqual(value, 0)
        self.mock_lib.get_scaler_continuous_run.assert_called_once_with(self.device.handle, ANY)

    def test_set_scaler_max_hits(self):
        """Test set_scaler_max_hits"""
        self.device.set_scaler_max_hits(1000)
        self.mock_lib.set_scaler_max_hits.assert_called_once_with(self.device.handle, 1000)

    def test_get_scaler_max_hits(self):
        """Test get_scaler_max_hits"""
        value = self.device.get_scaler_max_hits()
        self.assertEqual(value, 0)
        self.mock_lib.get_scaler_max_hits.assert_called_once_with(self.device.handle, ANY)

    def test_set_scaler_dwell_time(self):
        """Test set_scaler_dwell_time"""
        self.device.set_scaler_dwell_time(1000)
        self.mock_lib.set_scaler_dwell_time.assert_called_once_with(self.device.handle, 1000)

    def test_get_scaler_dwell_time(self):
        """Test get_scaler_dwell_time"""
        value = self.device.get_scaler_dwell_time()
        self.assertEqual(value, 0)
        self.mock_lib.get_scaler_dwell_time.assert_called_once_with(self.device.handle, ANY)

    def test_set_scaler_sw_start(self):
        """Test set_scaler_sw_start"""
        self.device.set_scaler_sw_start()
        self.mock_lib.set_scaler_sw_start.assert_called_once_with(self.device.handle)

    def test_set_scaler_sw_stop(self):
        """Test set_scaler_sw_stop"""
        self.device.set_scaler_sw_stop()
        self.mock_lib.set_scaler_sw_stop.assert_called_once_with(self.device.handle)

    def test_set_scaler_sw_reset(self):
        """Test set_scaler_sw_reset"""
        self.device.set_scaler_sw_reset()
        self.mock_lib.set_scaler_sw_reset.assert_called_once_with(self.device.handle)

    def test_set_scaler_sw_open_gate(self):
        """Test set_scaler_sw_open_gate"""
        self.device.set_scaler_sw_open_gate()
        self.mock_lib.set_scaler_sw_open_gate.assert_called_once_with(self.device.handle)

    def test_set_scaler_sw_close_gate(self):
        """Test set_scaler_sw_close_gate"""
        self.device.set_scaler_sw_close_gate()
        self.mock_lib.set_scaler_sw_close_gate.assert_called_once_with(self.device.handle)

    def test_blt_read_async(self):
        """Test blt_read_async"""
        self.device.blt_read_async(0x1000, 256, vme.AddressModifiers.A32_U_DATA, vme.DataWidth.D32)
        self.mock_lib.blt_read_async.assert_called_once_with(self.device.handle, 0x1000, ANY, 256, vme.AddressModifiers.A32_U_DATA, vme.DataWidth.D32)

    def test_blt_read_wait(self):
        """Test blt_read_wait"""
        value = self.device.blt_read_wait()
        self.assertEqual(value, 0)
        self.mock_lib.blt_read_wait.assert_called_once_with(self.device.handle, ANY)

if __name__ == '__main__':
    unittest.main()
