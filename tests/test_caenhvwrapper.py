""""Test the caenhvwrapper module."""

import unittest
from unittest.mock import ANY, DEFAULT, patch

import caen_libs.caenhvwrapper as hv


class TestHVDevice(unittest.TestCase):
    """Test the HVDevice class."""

    def setUp(self):
        patcher = patch('caen_libs.caenhvwrapper.lib', autospec=True)
        self.addCleanup(patcher.stop)
        self.mock_lib = patcher.start()
        def side_effect(*args):
            args[5].value = 0xdeadbeaf
            return DEFAULT
        self.mock_lib.init_system.side_effect = side_effect
        self.device = hv.Device.open(hv.SystemType.SY4527, hv.LinkType.TCPIP, '192.168.0.1', 'user', 'password')
        self.addCleanup(self.device.close)

    def test_error_handling(self):
        """Test error handling."""
        self.mock_lib.init_system.side_effect = hv.Error('Test error', -1, 'InitSystem')
        with self.assertRaises(hv.Error):
            hv.Device.open(hv.SystemType.SY4527, hv.LinkType.TCPIP, '192.168.0.1', 'user', 'password')

    def test_deinit_system(self):
        """Test deinit_system"""
        self.device.close()
        self.mock_lib.deinit_system.assert_called_once_with(self.device.handle)

    def test_get_crate_map(self):
        """Test get_crate_map"""
        crate_map = self.device.get_crate_map()
        self.assertEqual(len(crate_map), 0)
        self.mock_lib.get_crate_map.assert_called_once_with(self.device.handle, ANY, ANY, ANY, ANY, ANY, ANY, ANY)

    def test_get_sys_prop_list(self):
        """Test get_sys_prop_list"""
        prop_list = self.device.get_sys_prop_list()
        self.assertEqual(len(prop_list), 0)
        self.mock_lib.get_sys_prop_list.assert_called_once_with(self.device.handle, ANY, ANY)

    def test_get_sys_prop_info(self):
        """Test get_sys_prop_info"""
        prop_info = self.device.get_sys_prop_info('TestProp')
        self.assertEqual(prop_info, hv.SysProp('TestProp', 0, 0))
        self.mock_lib.get_sys_prop_info.assert_called_once_with(self.device.handle, b'TestProp', ANY, ANY)

    def test_get_sys_prop(self):
        """Test get_sys_prop"""
        def side_effect(*args):
            args[3].value = hv.SysPropType.STR.value
            return DEFAULT
        self.mock_lib.get_sys_prop_info.side_effect = side_effect
        value = self.device.get_sys_prop('TestProp')
        self.assertEqual(value, '')
        self.mock_lib.get_sys_prop.assert_called_once_with(self.device.handle, b'TestProp', ANY)

    def test_set_sys_prop(self):
        """Test set_sys_prop"""
        self.device.set_sys_prop('TestProp', 'NewValue')
        self.mock_lib.set_sys_prop.assert_called_once_with(self.device.handle, b'TestProp', ANY)

    def test_get_bd_param(self):
        """Test get_bd_param"""
        def side_effect(*args):
            args[4]._obj.value = 0
            return DEFAULT
        self.mock_lib.get_bd_param_prop.side_effect = side_effect
        slot_list = [0, 1]
        values = self.device.get_bd_param(slot_list, 'TestParam')
        self.assertEqual(values, [0, 0])
        self.mock_lib.get_bd_param.assert_called_once_with(self.device.handle, 2, ANY, b'TestParam', ANY)

    def test_set_bd_param(self):
        """Test set_bd_param"""
        def side_effect(*args):
            args[4]._obj.value = 0
            return DEFAULT
        self.mock_lib.get_bd_param_prop.side_effect = side_effect
        slot_list = [0, 1]
        self.device.set_bd_param(slot_list, 'TestParam', 123)
        self.mock_lib.set_bd_param.assert_called_once_with(self.device.handle, 2, ANY, b'TestParam', ANY)

    def test_get_ch_param(self):
        """Test get_ch_param"""
        def side_effect(*args):
            args[5]._obj.value = 0
            return DEFAULT
        self.mock_lib.get_ch_param_prop.side_effect = side_effect
        channel_list = [0, 1]
        values = self.device.get_ch_param(0, channel_list, 'TestParam')
        self.assertEqual(values, [0, 0])
        self.mock_lib.get_ch_param.assert_called_once_with(self.device.handle, 0, b'TestParam', 2, ANY, ANY)

    def test_set_ch_param(self):
        """Test set_ch_param"""
        def side_effect(*args):
            args[5]._obj.value = 0
            return DEFAULT
        self.mock_lib.get_ch_param_prop.side_effect = side_effect
        channel_list = [0, 1]
        self.device.set_ch_param(0, channel_list, 'TestParam', 123)
        self.mock_lib.set_ch_param.assert_called_once_with(self.device.handle, 0, b'TestParam', 2, ANY, ANY)

    def test_get_exec_comm_list(self):
        """Test get_exec_comm_list"""
        exec_comm_list = self.device.get_exec_comm_list()
        self.assertEqual(len(exec_comm_list), 0)
        self.mock_lib.get_exec_comm_list.assert_called_once_with(self.device.handle, ANY, ANY)

    def test_exec_comm(self):
        """Test exec_comm"""
        self.device.exec_comm('TestComm')
        self.mock_lib.exec_comm.assert_called_once_with(self.device.handle, b'TestComm')

    def test_get_event_data(self):
        """Test get_event_data"""
        with self.assertRaises(RuntimeError):
            self.device.get_event_data()

if __name__ == '__main__':
    unittest.main()
