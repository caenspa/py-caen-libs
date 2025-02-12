"""
Utilities
"""

__author__ = 'Giovanni Cerretani'
__copyright__ = 'Copyright (C) 2024 CAEN SpA'
__license__ = 'LGPL-3.0-or-later'
# SPDX-License-Identifier: LGPL-3.0-or-later

import ctypes as ct
import os
import sys
from abc import ABC, abstractmethod
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Any, Optional, Union, overload

if sys.platform == 'win32':
    _LibNotFoundClass = FileNotFoundError
else:
    _LibNotFoundClass = OSError


class Lib(ABC):
    """
    This class loads the shared library and exposes its functions on its
    public attributes using ctypes.
    """

    def __init__(self, name: str, stdcall: bool = True, env: Optional[dict[str, str]] = None) -> None:
        self.__name = name
        self.__stdcall = stdcall  # Ignored on Linux
        self.__env = env
        self.__load_lib()

    def __load_lib(self) -> None:
        """
        Variadic functions are __cdecl even if declared as __stdcall.
        This difference applies only to 32 bit applications, 64 bit
        applications have its own calling convention.
        """
        self.__lib_variadic: ct.CDLL
        if sys.platform == 'win32':
            self.__lib: Union[ct.CDLL, ct.WinDLL]
        else:
            self.__lib: ct.CDLL

        # Set env
        if self.__env is not None:
            for key, value in self.__env.items():
                os.environ[key] = value

        # Load library
        try:
            if sys.platform == 'win32':
                self.__path = f'{self.name}.dll'
                if self.__stdcall:
                    self.__lib = ct.windll.LoadLibrary(self.__path)
                    self.__lib_variadic = ct.cdll.LoadLibrary(self.__path)
                else:
                    self.__lib = ct.cdll.LoadLibrary(self.__path)
                    self.__lib_variadic = self.__lib
            else:
                self.__path = f'lib{self.name}.so'
                self.__lib = ct.cdll.LoadLibrary(self.__path)
                self.__lib_variadic = self.__lib

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

    @abstractmethod
    def sw_release(self) -> str:
        """
        Get software release version as string with numeric format, like
        N.N.N, where N is a number.
        """

    def ver_at_least(self, target: tuple[int, ...]) -> bool:
        """Check if the library version is at least the target"""
        ver = self.sw_release()
        return version_to_tuple(ver) >= target

    def get(self, name: str, variadic: bool = False):
        """
        Get function by name.
        Use CDLL.__getitem__ rather than CDLL.__getattr__ to avoid
        caching, useless in our case.
        """
        if variadic:
            return self.__lib_variadic[name]
        return self.__lib[name]

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
        return self.__multi_get_fallback(addresses)

    def multi_set(self, addresses: Sequence[int], values: Sequence[int]) -> None:
        """Set multiple value"""
        if self.multi_setter is not None:
            return self.multi_setter(addresses, values)
        return self.__multi_set_fallback(addresses, values)

    def __multi_get_fallback(self, addresses: Sequence[int]) -> list[int]:
        return [self.get(a) for a in addresses]

    def __multi_set_fallback(self, addresses: Sequence[int], values: Sequence[int]) -> None:
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
