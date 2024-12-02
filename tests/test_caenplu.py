import unittest
from unittest.mock import ANY, DEFAULT, patch

import caen_libs.caenplu as plu


class TestCaenPlu(unittest.TestCase):

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

    def test_device_close(self):
        """Test close_device"""
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
        serial_number = self.device.get_serial_number()
        self.assertEqual(serial_number, '')
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

if __name__ == '__main__':
    unittest.main()
