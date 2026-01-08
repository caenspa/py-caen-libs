"""Tests for the caen_libs.caenplu module."""

import unittest
from unittest.mock import ANY, DEFAULT, patch

import caen_libs.caenplu as plu


class TestDevice(unittest.TestCase):
    """Test the Device class."""

    def setUp(self):
        patcher = patch('caen_libs.caenplu.lib', autospec=True)
        self.addCleanup(patcher.stop)
        self.mock_lib = patcher.start()
        def side_effect(*args):
            args[4].value = 0xdeadbeaf
            return DEFAULT
        self.mock_lib.open_device2.side_effect = side_effect
        self.device = plu.Device.open(plu.ConnectionModes.DIRECT_USB, 0, 0, 0)
        self.addCleanup(self.device.close)

    def test_error_handling(self):
        """Test error handling."""
        self.mock_lib.open_device2.side_effect = plu.Error('Test error', -1, 'OpenDevice2')
        with self.assertRaises(plu.Error):
            plu.Device.open(plu.ConnectionModes.DIRECT_USB, 0, 0, 0)

    def test_close(self):
        """Test close"""
        self.device.close()
        self.mock_lib.close_device.assert_called_once_with(self.device.handle)

    def test_write_read_register(self):
        """Test write_reg and read_reg"""
        address = 0x1000
        value = 0x1234
        self.device.write_reg(address, value)
        self.mock_lib.write_reg.assert_called_once_with(self.device.handle, address, value)
        self.device.read_reg(address)
        self.mock_lib.read_reg.assert_called_once_with(self.device.handle, address, ANY)

    def test_registers(self):
        """Test registers"""
        address = 0x1000
        value = 0x1234
        self.device.registers[address] |= value
        self.mock_lib.read_reg.assert_called_once_with(self.device.handle, address, ANY)
        self.mock_lib.write_reg.assert_called_once_with(self.device.handle, address, value)

    def test_enable_disable_flash_access(self):
        """Test enable_flash_access and disable_flash_access"""
        for i in set(plu.FPGA):
            self.device.enable_flash_access(i)
            self.mock_lib.enable_flash_access.assert_called_once_with(self.device.handle, i)
            self.mock_lib.enable_flash_access.reset_mock()
            self.device.disable_flash_access(i)
            self.mock_lib.disable_flash_access.assert_called_once_with(self.device.handle, i)
            self.mock_lib.disable_flash_access.reset_mock()

    def test_get_serial_number(self):
        """Test get_serial_number"""
        result = self.device.get_serial_number()
        self.assertEqual(result, '')
        self.mock_lib.get_serial_number.assert_called_once_with(self.device.handle, ANY, 32)

    def test_get_info(self):
        """Test get_info"""
        self.device.get_info()
        self.mock_lib.get_info.assert_called_once_with(self.device.handle, ANY)

    def test_write_flash_data(self):
        """Test write_flash_data"""
        data = b'\x01\x02\x03\x04'
        self.device.write_flash_data(plu.FPGA.MAIN, 0x1000, data)
        self.mock_lib.write_flash_data.assert_called_once_with(self.device.handle, plu.FPGA.MAIN, 0x1000, ANY, len(data) // 4)

    def test_read_flash_data(self):
        """Test read_flash_data"""
        self.device.read_flash_data(plu.FPGA.MAIN, 0x1000, 16)
        self.mock_lib.read_flash_data.assert_called_once_with(self.device.handle, plu.FPGA.MAIN, 0x1000, ANY, 16 // 4)

    def test_write_read_data32(self):
        """Test write_data32 and read_data32"""
        start_address = 0x1000
        data = [0x1234, 0x5678, 0x9abc, 0xdef0]
        self.device.write_data32(start_address, data)
        self.mock_lib.write_data32.assert_called_once_with(self.device.handle, start_address, len(data), ANY)
        def side_effect(*args):
            args[3][:] = data
            args[4].value = len(data)
            return DEFAULT
        self.mock_lib.read_data32.side_effect = side_effect
        result = self.device.read_data32(start_address, len(data))
        self.assertEqual(result, data)
        self.mock_lib.read_data32.assert_called_once_with(self.device.handle, start_address, len(data), ANY, ANY)

    def test_write_read_fifo32(self):
        """Test write_fifo32 and read_fifo32"""
        start_address = 0x1000
        data = [0x1234, 0x5678, 0x9abc, 0xdef0]
        self.device.write_fifo32(start_address, data)
        self.mock_lib.write_fifo32.assert_called_once_with(self.device.handle, start_address, len(data), ANY)
        def side_effect(*args):
            args[3][:] = data
            args[4].value = len(data)
            return DEFAULT
        self.mock_lib.read_fifo32.side_effect = side_effect
        result = self.device.read_fifo32(start_address, len(data))
        self.assertEqual(result, data)
        self.mock_lib.read_fifo32.assert_called_once_with(self.device.handle, start_address, len(data), ANY, ANY)

    def test_init_gate_and_delay_generators(self):
        """Test init_gate_and_delay_generators"""
        self.device.init_gate_and_delay_generators()
        self.mock_lib.init_gate_and_delay_generators.assert_called_once_with(self.device.handle)

    def test_set_gate_and_delay_generator(self):
        """Test set_gate_and_delay_generator"""
        channel = 1
        enable = 1
        gate = 100
        delay = 50
        scale_factor = 2
        self.device.set_gate_and_delay_generator(channel, enable, gate, delay, scale_factor)
        self.mock_lib.set_gate_and_delay_generator.assert_called_once_with(self.device.handle, channel, enable, gate, delay, scale_factor)

    def test_set_gate_and_delay_generators(self):
        """Test set_gate_and_delay_generators"""
        gate = 100
        delay = 50
        scale_factor = 2
        self.device.set_gate_and_delay_generators(gate, delay, scale_factor)
        self.mock_lib.set_gate_and_delay_generators.assert_called_once_with(self.device.handle, gate, delay, scale_factor)

    def test_get_gate_and_delay_generator(self):
        """Test get_gate_and_delay_generator"""
        channel = 1
        result = self.device.get_gate_and_delay_generator(channel)
        self.assertEqual(result, (0, 0, 0))
        self.mock_lib.get_gate_and_delay_generator.assert_called_once_with(self.device.handle, channel, ANY, ANY, ANY)

    def test_delete_flash_sector(self):
        """Test delete_flash_sector"""
        sector = 0x10
        self.device.delete_flash_sector(plu.FPGA.MAIN, sector)
        self.mock_lib.delete_flash_sector.assert_called_once_with(self.device.handle, plu.FPGA.MAIN, sector)

    def test_connection_status(self):
        """Test connection_status"""
        result = self.device.connection_status()
        self.assertEqual(result, 0)
        self.mock_lib.connection_status.assert_called_once_with(self.device.handle, ANY)

if __name__ == '__main__':
    unittest.main()
