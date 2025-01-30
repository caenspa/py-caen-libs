"""Tests for the caencomm module."""

import unittest
from unittest.mock import DEFAULT, patch

import caen_libs._caendpplib as dpp


class TestDevice(unittest.TestCase):
    """Test the Device class."""

    def setUp(self):
        patcher = patch('caen_libs._caendpplib.lib', autospec=True)
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

if __name__ == '__main__':
    unittest.main()
