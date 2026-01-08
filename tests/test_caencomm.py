"""Tests for the caen_libs.caencomm module."""

import struct
import unittest
from unittest.mock import ANY, DEFAULT, patch

import caen_libs.caencomm as comm


class TestDevice(unittest.TestCase):
    """Test the Device class."""

    def setUp(self):
        patcher = patch('caen_libs.caencomm.lib', autospec=True)
        self.addCleanup(patcher.stop)
        self.mock_lib = patcher.start()
        def side_effect(*args):
            args[4].value = 0xdeadbeaf
            return DEFAULT
        self.mock_lib.open_device2.side_effect = side_effect
        self.device = comm.Device.open(comm.ConnectionType.USB, 0, 0, 0)
        self.addCleanup(self.device.close)

    def test_error_handling(self):
        """Test error handling."""
        self.mock_lib.open_device2.side_effect = comm.Error('Test error', -1, 'OpenDevice2')
        with self.assertRaises(comm.Error):
            comm.Device.open(comm.ConnectionType.USB, 0, 0, 0)

    def test_close(self):
        """Test close"""
        self.device.close()
        self.mock_lib.close_device.assert_called_once_with(self.device.handle)

    def test_write32(self):
        """Test write32"""
        address = 0x1000
        value = 0x1234
        self.device.write32(address, value)
        self.mock_lib.write32.assert_called_once_with(self.device.handle, address, value)

    def test_write16(self):
        """Test write16"""
        address = 0x1000
        value = 0x1234
        self.device.write16(address, value)
        self.mock_lib.write16.assert_called_once_with(self.device.handle, address, value)

    def test_read32(self):
        """Test read32"""
        address = 0x1000
        value = 0x1234
        def side_effect(*args):
            args[2].value = value
            return DEFAULT
        self.mock_lib.read32.side_effect = side_effect
        result = self.device.read32(address)
        self.assertEqual(result, value)
        self.mock_lib.read32.assert_called_once_with(self.device.handle, address, ANY)

    def test_read16(self):
        """Test read16"""
        address = 0x1000
        value = 0x1234
        def side_effect(*args):
            args[2].value = value
            return DEFAULT
        self.mock_lib.read16.side_effect = side_effect
        result = self.device.read16(address)
        self.assertEqual(result, value)
        self.mock_lib.read16.assert_called_once_with(self.device.handle, address, ANY)

    def test_reg(self):
        """Test reg16 and reg32"""
        address = 0x1000
        value = 0x1234
        data = [0x1234, 0x5678, 0x9abc, 0xdef0]
        self.device.reg16[address] |= value
        self.mock_lib.read16.assert_called_once_with(self.device.handle, address, ANY)
        self.mock_lib.write16.assert_called_once_with(self.device.handle, address, value)
        self.device.reg32[address] |= value
        self.mock_lib.read32.assert_called_once_with(self.device.handle, address, ANY)
        self.mock_lib.write32.assert_called_once_with(self.device.handle, address, value)
        self.device.reg16[0:4] = data
        self.mock_lib.multi_write16.assert_called_once_with(self.device.handle, ANY, len(data), ANY, ANY)
        self.device.reg32[0:4] = data
        self.mock_lib.multi_write32.assert_called_once_with(self.device.handle, ANY, len(data), ANY, ANY)

    def test_multi_write32(self):
        """Test multi_write32"""
        addrs = [0x1000, 0x2000]
        data = [0x1234, 0x5678]
        self.device.multi_write32(addrs, data)
        self.mock_lib.multi_write32.assert_called_once_with(self.device.handle, ANY, len(addrs), ANY, ANY)

    def test_multi_write16(self):
        """Test multi_write16"""
        addrs = [0x1000, 0x2000]
        data = [0x1234, 0x5678]
        self.device.multi_write16(addrs, data)
        self.mock_lib.multi_write16.assert_called_once_with(self.device.handle, ANY, len(addrs), ANY, ANY)

    def test_multi_read32(self):
        """Test multi_read32"""
        addrs = [0x1000, 0x2000]
        data = [0x1234, 0x5678]
        def side_effect(*args):
            args[3][:] = data
            return DEFAULT
        self.mock_lib.multi_read32.side_effect = side_effect
        result = self.device.multi_read32(addrs)
        self.assertEqual(result, data)
        self.mock_lib.multi_read32.assert_called_once_with(self.device.handle, ANY, len(addrs), ANY, ANY)

    def test_multi_read16(self):
        """Test multi_read16"""
        addrs = [0x1000, 0x2000]
        data = [0x1234, 0x5678]
        def side_effect(*args):
            args[3][:] = data
            return DEFAULT
        self.mock_lib.multi_read16.side_effect = side_effect
        result = self.device.multi_read16(addrs)
        self.assertEqual(result, data)
        self.mock_lib.multi_read16.assert_called_once_with(self.device.handle, ANY, len(addrs), ANY, ANY)

    def test_blt_read(self):
        """Test blt_read"""
        address = 0x1000
        blt_size = 256
        data = [i for i in range(blt_size)]
        def side_effect(*args):
            args[2][:] = data
            args[4].value = len(data)
            return DEFAULT
        self.mock_lib.blt_read.side_effect = side_effect
        result = self.device.blt_read(address, blt_size)
        self.assertIsInstance(result, comm.ReadResult)
        # Recompact the bytes into groups of 4 (uint32 native endianness)
        actual_data = list(struct.unpack('I' * (len(result.data) // 4), result.data))
        self.assertEqual(actual_data, data)
        self.assertFalse(result.terminated)
        self.mock_lib.blt_read.assert_called_once_with(self.device.handle, address, ANY, blt_size, ANY)

    def test_mblt_read(self):
        """Test mblt_read"""
        address = 0x1000
        blt_size = 256
        data = [i for i in range(blt_size)]
        def side_effect(*args):
            args[2][:] = data
            args[4].value = len(data)
            return DEFAULT
        self.mock_lib.mblt_read.side_effect = side_effect
        result = self.device.mblt_read(address, blt_size)
        self.assertIsInstance(result, comm.ReadResult)
        # Recompact the bytes into groups of 4 (uint32 native endianness)
        actual_data = list(struct.unpack('I' * (len(result.data) // 4), result.data))
        self.assertEqual(actual_data, data)
        self.assertFalse(result.terminated)
        self.mock_lib.mblt_read.assert_called_once_with(self.device.handle, address, ANY, blt_size, ANY)

    def test_irq_disable(self):
        """Test irq_disable"""
        value = 0x01
        self.device.irq_disable(value)
        self.mock_lib.irq_disable.assert_called_once_with(self.device.handle, value)

    def test_irq_enable(self):
        """Test irq_enable"""
        value = 0x01
        self.device.irq_enable(value)
        self.mock_lib.irq_enable.assert_called_once_with(self.device.handle, value)

    def test_iack_cycle(self):
        """Test iack_cycle"""
        for i in set(comm.IRQLevels):
            result = self.device.iack_cycle(i)
            self.assertEqual(result, 0)
            self.mock_lib.iack_cycle.assert_called_with(self.device.handle, i, ANY)
            self.mock_lib.iack_cycle.reset_mock()

    def test_irq_wait(self):
        """Test irq_wait"""
        timeout = 1000
        self.device.irq_wait(timeout)
        self.mock_lib.irq_wait.assert_called_once_with(self.device.handle, timeout)

    def test_info(self):
        """Test info"""
        for i in set(comm.Info):
            result = self.device.info(i)
            self.assertEqual(result, '')
            self.mock_lib.info.assert_called_with(self.device.handle, i, ANY)
            self.mock_lib.info.reset_mock()

    def test_vme_handle(self):
        """Test vme_handle"""
        result = self.device.vme_handle()
        self.assertEqual(result, 0)
        self.mock_lib.info.assert_called_once_with(self.device.handle, 5, ANY)

if __name__ == '__main__':
    unittest.main()
