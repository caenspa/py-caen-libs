import unittest
from unittest.mock import DEFAULT, patch

import caen_libs.caenhvwrapper as hv

class TestHVDevice(unittest.TestCase):

    def setUp(self):
        patcher = patch('caen_libs.caenhvwrapper.lib', autospec=True)
        self.addCleanup(patcher.stop)
        self.mock_lib = patcher.start()
        self.device = hv.Device.open(hv.SystemType.SY4527, hv.LinkType.TCPIP, '192.168.0.1', 'user', 'password')
        self.addCleanup(self.device.close)

    def test_error_handling(self):
        self.mock_lib.init_system.side_effect = hv.Error('Test error', -1, 'InitSystem')
        with self.assertRaises(hv.Error):
            hv.Device.open(hv.SystemType.SY4527, hv.LinkType.TCPIP, '192.168.0.1', 'user', 'password')

    def test_device_close(self):
        self.device.close()
        self.mock_lib.deinit_system.assert_called_once_with(self.device.handle)

    def test_get_sys_prop(self):
        def side_effect(*args):
            args[3].value = hv.SysPropType.STR.value
            return DEFAULT
        self.mock_lib.get_sys_prop_info.side_effect = side_effect
        self.mock_lib.get_sys_prop_info.return_value = 0
        self.mock_lib.get_sys_prop.return_value = 0
        value = self.device.get_sys_prop('TestProp')
        self.assertEqual(value, '')
        self.mock_lib.get_sys_prop.assert_called_once_with(self.device.handle, b'TestProp', unittest.mock.ANY)

    def test_set_sys_prop(self):
        self.device.set_sys_prop('TestProp', 'NewValue')
        self.mock_lib.set_sys_prop.assert_called_once_with(self.device.handle, b'TestProp', unittest.mock.ANY)

    def test_get_bd_param(self):
        def side_effect(*args):
            args[4]._obj.value = 0
            return DEFAULT
        self.mock_lib.get_bd_param_prop.side_effect = side_effect
        self.mock_lib.get_bd_param_prop.return_value = 0
        self.mock_lib.get_bd_param.return_value = 0
        slot_list = [0, 1]
        values = self.device.get_bd_param(slot_list, 'TestParam')
        self.assertEqual(values, [0, 0])
        self.mock_lib.get_bd_param.assert_called_once_with(self.device.handle, 2, unittest.mock.ANY, b'TestParam', unittest.mock.ANY)

    def test_set_bd_param(self):
        def side_effect(*args):
            args[4]._obj.value = 0
            return DEFAULT
        self.mock_lib.get_bd_param_prop.side_effect = side_effect
        self.mock_lib.get_bd_param_prop.return_value = 0
        self.mock_lib.get_bd_param.return_value = 0
        slot_list = [0, 1]
        self.device.set_bd_param(slot_list, 'TestParam', 123)
        self.mock_lib.set_bd_param.assert_called_once_with(self.device.handle, 2, unittest.mock.ANY, b'TestParam', unittest.mock.ANY)

    def test_get_ch_param(self):
        def side_effect(*args):
            args[5]._obj.value = 0
            return DEFAULT
        self.mock_lib.get_ch_param_prop.side_effect = side_effect
        self.mock_lib.get_ch_param_prop.return_value = 0
        self.mock_lib.get_ch_param.return_value = 0
        channel_list = [0, 1]
        values = self.device.get_ch_param(0, channel_list, 'TestParam')
        self.assertEqual(values, [0, 0])
        self.mock_lib.get_ch_param.assert_called_once_with(self.device.handle, 0, b'TestParam', 2, unittest.mock.ANY, unittest.mock.ANY)

    def test_set_ch_param(self):
        def side_effect(*args):
            args[5]._obj.value = 0
            return DEFAULT
        self.mock_lib.get_ch_param_prop.side_effect = side_effect
        self.mock_lib.get_ch_param_prop.return_value = 0
        self.mock_lib.get_ch_param.return_value = 0
        channel_list = [0, 1]
        self.device.set_ch_param(0, channel_list, 'TestParam', 123)
        self.mock_lib.set_ch_param.assert_called_once_with(self.device.handle, 0, b'TestParam', 2, unittest.mock.ANY, unittest.mock.ANY)

    def test_get_event_data(self):
        self.mock_lib.get_event_data.return_value = 0
        with self.assertRaises(RuntimeError):
            self.device.get_event_data()

if __name__ == '__main__':
    unittest.main()