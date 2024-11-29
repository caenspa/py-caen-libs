import unittest
from unittest.mock import Mock
from caen_libs._utils import Registers, version_to_tuple

class TestVersionToTuple(unittest.TestCase):
    def test_version_to_tuple(self):
        self.assertEqual(version_to_tuple("1.2.3"), (1, 2, 3))
        self.assertEqual(version_to_tuple("0.0.1"), (0, 0, 1))
        self.assertEqual(version_to_tuple("10.20.30"), (10, 20, 30))
        with self.assertRaises(ValueError):
            version_to_tuple("1.2.a")

class TestRegisters(unittest.TestCase):
    def setUp(self):
        self.getter = Mock(return_value=42)
        self.setter = Mock()
        self.multi_getter = Mock(return_value=[42, 43])
        self.multi_setter = Mock()
        self.registers = Registers(
            getter=self.getter,
            setter=self.setter,
            multi_getter=self.multi_getter,
            multi_setter=self.multi_setter
        )

    def test_get(self):
        self.assertEqual(self.registers.get(0), 42)
        self.getter.assert_called_once_with(0)

    def test_set(self):
        self.registers.set(0, 99)
        self.setter.assert_called_once_with(0, 99)

    def test_multi_get(self):
        self.assertEqual(self.registers.multi_get([0, 1]), [42, 43])
        self.multi_getter.assert_called_once_with([0, 1])

    def test_multi_set(self):
        self.registers.multi_set([0, 1], [99, 100])
        self.multi_setter.assert_called_once_with([0, 1], [99, 100])

    def test_getitem(self):
        self.assertEqual(self.registers[0], 42)
        self.getter.assert_called_once_with(0)

    def test_getitem_slice(self):
        self.assertEqual(self.registers[0:2], [42, 43])
        self.multi_getter.assert_called_once_with(range(0, 2))

    def test_setitem(self):
        self.registers[0] = 99
        self.setter.assert_called_once_with(0, 99)

    def test_setitem_slice(self):
        self.registers[0:2] = [99, 100]
        self.multi_setter.assert_called_once_with(range(0, 2), [99, 100])

if __name__ == '__main__':
    unittest.main()