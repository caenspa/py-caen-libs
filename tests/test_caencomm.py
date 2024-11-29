"""Tests for the caencomm module."""

import unittest
from unittest.mock import DEFAULT, patch

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

    def test_device_close(self):
        """Test close_device"""
        self.device.close()
        self.mock_lib.close_device.assert_called_once_with(self.device.handle)

    def test_write32(self):
        """Test write32"""
        self.device.write32(0x1000, 0x1234)
        self.mock_lib.write32.assert_called_once_with(self.device.handle, 0x1000, 0x1234)

    def test_write16(self):
        """Test write16"""
        self.device.write16(0x1000, 0x1234)
        self.mock_lib.write16.assert_called_once_with(self.device.handle, 0x1000, 0x1234)

    def test_read32(self):
        """Test read32"""
        value = self.device.read32(0x1000)
        self.assertEqual(value, 0)
        self.mock_lib.read32.assert_called_once_with(self.device.handle, 0x1000, unittest.mock.ANY)

    def test_read16(self):
        """Test read16"""
        value = self.device.read16(0x1000)
        self.assertEqual(value, 0)
        self.mock_lib.read16.assert_called_once_with(self.device.handle, 0x1000, unittest.mock.ANY)

    def test_multi_write32(self):
        """Test multi_write32"""
        addrs = [0x1000, 0x2000]
        data = [0x1234, 0x5678]
        self.device.multi_write32(addrs, data)
        self.mock_lib.multi_write32.assert_called_once_with(self.device.handle, unittest.mock.ANY, 2, unittest.mock.ANY, unittest.mock.ANY)

    def test_multi_write16(self):
        """Test multi_write16"""
        addrs = [0x1000, 0x2000]
        data = [0x1234, 0x5678]
        self.device.multi_write16(addrs, data)
        self.mock_lib.multi_write16.assert_called_once_with(self.device.handle, unittest.mock.ANY, 2, unittest.mock.ANY, unittest.mock.ANY)

    def test_multi_read32(self):
        """Test multi_read32"""
        addrs = [0x1000, 0x2000]
        values = self.device.multi_read32(addrs)
        self.assertEqual(values, [0, 0])
        self.mock_lib.multi_read32.assert_called_once_with(self.device.handle, unittest.mock.ANY, 2, unittest.mock.ANY, unittest.mock.ANY)

    def test_multi_read16(self):
        """Test multi_read16"""
        addrs = [0x1000, 0x2000]
        values = self.device.multi_read16(addrs)
        self.assertEqual(values, [0, 0])
        self.mock_lib.multi_read16.assert_called_once_with(self.device.handle, unittest.mock.ANY, 2, unittest.mock.ANY, unittest.mock.ANY)

    def test_blt_read(self):
        """Test blt_read"""
        values = self.device.blt_read(0x1000, 256)
        self.assertEqual(values, [])
        self.mock_lib.blt_read.assert_called_once_with(self.device.handle, 0x1000, unittest.mock.ANY, 256, unittest.mock.ANY)

    def test_mblt_read(self):
        """Test mblt_read"""
        values = self.device.mblt_read(0x1000, 256)
        self.assertEqual(values, [])
        self.mock_lib.mblt_read.assert_called_once_with(self.device.handle, 0x1000, unittest.mock.ANY, 256, unittest.mock.ANY)

    def test_irq_disable(self):
        """Test irq_disable"""
        self.device.irq_disable(0x01)
        self.mock_lib.irq_disable.assert_called_once_with(self.device.handle, 0x01)

    def test_irq_enable(self):
        """Test irq_enable"""
        self.device.irq_enable(0x01)
        self.mock_lib.irq_enable.assert_called_once_with(self.device.handle, 0x01)

    def test_iack_cycle(self):
        """Test iack_cycle"""
        value = self.device.iack_cycle(comm.IRQLevels.L1)
        self.assertEqual(value, 0)
        self.mock_lib.iack_cycle.assert_called_once_with(self.device.handle, comm.IRQLevels.L1, unittest.mock.ANY)

    def test_irq_wait(self):
        """Test irq_wait"""
        self.device.irq_wait(1000)
        self.mock_lib.irq_wait.assert_called_once_with(self.device.handle, 1000)

    def test_info(self):
        """Test info"""
        value = self.device.info(comm.Info.PCI_BOARD_SN)
        self.assertEqual(value, '')
        self.mock_lib.info.assert_called_once_with(self.device.handle, comm.Info.PCI_BOARD_SN, unittest.mock.ANY)

    def test_vme_handle(self):
        """Test vme_handle"""
        value = self.device.vme_handle()
        self.assertEqual(value, 0)
        self.mock_lib.info.assert_called_once_with(self.device.handle, 5, unittest.mock.ANY)

if __name__ == '__main__':
    unittest.main()
