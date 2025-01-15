"""
Utilities
"""

__author__ = 'Giovanni Cerretani'
__copyright__ = 'Copyright (C) 2024 CAEN SpA'
__license__ = 'LGPL-3.0-or-later'
# SPDX-License-Identifier: LGPL-3.0-or-later

import ctypes as ct
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Any, Optional, Union, overload

if sys.platform == 'win32':
    _LibNotFoundClass = FileNotFoundError
else:
    _LibNotFoundClass = OSError


class Lib:
    """
    This class loads the shared library and exposes its functions on its
    public attributes using ctypes.
    """

    def __init__(self, name: str) -> None:
        self.__name = name
        self.__load_lib()

    def __load_lib(self) -> None:
        loader: Union[ct.LibraryLoader[ct.WinDLL], ct.LibraryLoader[ct.CDLL]]
        loader_variadic: ct.LibraryLoader[ct.CDLL]

        # Platform dependent stuff
        if sys.platform == 'win32':
            # API functions are declared as __stdcall, but variadic
            # functions are __cdecl even if declared as __stdcall.
            # This difference applies only to 32 bit applications,
            # 64 bit applications have its own calling convention.
            loader = ct.windll
            loader_variadic = ct.cdll
            path = f'{self.name}.dll'
        else:
            loader = ct.cdll
            loader_variadic = ct.cdll
            path = f'lib{self.name}.so'

        self.__path = path

        # Load library
        try:
            self.__lib = loader.LoadLibrary(self.path)
            self.__lib_variadic = loader_variadic.LoadLibrary(self.path)
        except _LibNotFoundClass as ex:
            raise RuntimeError(
                f'Library {self.name} not found. This module requires '
                'the latest version of the library to be installed on '
                'your system. You may find the official installers at '
                'https://www.caen.it/. Please install it and retry.'
            ) from ex

    @property
    def name(self) -> str:
        """Name of the shared library"""
        return self.__name

    @property
    def path(self) -> Any:
        """Path of the shared library"""
        return self.__path

    @property
    def lib(self) -> Union[ct.WinDLL, ct.CDLL]:
        """ctypes object to shared library"""
        return self.__lib

    @property
    def lib_variadic(self) -> ct.CDLL:
        """ctypes object to shared library (for variadic functions)"""
        return self.__lib_variadic

    # Python utilities

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.path})'

    def __str__(self) -> str:
        return self.path


def version_to_tuple(version: str) -> tuple[int, ...]:
    """Version string in the form N.N.N to tuple (N, N, N)"""
    return tuple(map(int, version.split('.')))


# Slots brings some performance improvements and memory savings.
if sys.version_info >= (3, 10):
    dataclass_slots = {'slots': True}
else:
    dataclass_slots = {}


# Weakref support is required by the cache manager.
if sys.version_info >= (3, 11):
    dataclass_slots_weakref = dataclass_slots | {'weakref_slot': True}
else:
    dataclass_slots_weakref = {}


@dataclass(frozen=True, **dataclass_slots)
class Registers:
    """
    Class to simplify syntax for registers access with square brackets
    operators, slices and in-place operators.
    """

    getter: Callable[[int], int]
    setter: Callable[[int, int], None]
    multi_getter: Optional[Callable[[Sequence[int]], list[int]]] = field(default=None)
    multi_setter: Optional[Callable[[Sequence[int], Sequence[int]], None]] = field(default=None)

    def get(self, address: int) -> int:
        """Get value"""
        return self.getter(address)

    def set(self, address: int, value: int) -> None:
        """Set value"""
        return self.setter(address, value)

    def multi_get(self, addresses: Sequence[int]) -> list[int]:
        """Get multiple value"""
        if self.multi_getter is not None:
            return self.multi_getter(addresses)
        return [self.get(i) for i in addresses]

    def multi_set(self, addresses: Sequence[int], values: Sequence[int]) -> None:
        """Set multiple value"""
        if self.multi_setter is not None:
            return self.multi_setter(addresses, values)
        for a, v in zip(addresses, values):
            self.set(a, v)

    @staticmethod
    def __get_addresses(key: slice) -> Sequence[int]:
        if key.start is None or key.stop is None:
            raise ValueError('Both start and stop must be specified.')
        step = 1 if key.step is None else key.step
        return range(key.start, key.stop, step)

    @overload
    def __getitem__(self, address: int) -> int: ...
    @overload
    def __getitem__(self, address: slice) -> list[int]: ...

    def __getitem__(self, address):
        if isinstance(address, int):
            return self.get(address)
        if isinstance(address, slice):
            addresses = self.__get_addresses(address)
            return self.multi_get(addresses)
        raise TypeError('Invalid argument type.')

    @overload
    def __setitem__(self, address: int, value: int) -> None: ...
    @overload
    def __setitem__(self, address: slice, value: Sequence[int]) -> None: ...

    def __setitem__(self, address, value):
        if isinstance(address, int):
            return self.set(address, value)
        if isinstance(address, slice) and isinstance(value, Sequence):
            addresses = self.__get_addresses(address)
            if len(value) != len(addresses):
                raise ValueError('Invalid value size.')
            return self.multi_set(addresses, value)
        raise TypeError('Invalid argument type.')
