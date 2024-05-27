__author__ = 'Giovanni Cerretani'
__copyright__ = 'Copyright (C) 2024 CAEN SpA'
__license__ = 'LGPL-3.0-or-later'  # SPDX-License-Identifier

import ctypes as ct
import sys
from typing import Any


class Lib:
    """
    This class loads the shared library and
    exposes its functions on its public attributes
    using ctypes.
    """

    def __init__(self, name: str) -> None:
        self.__name = name
        self.__load_lib()

    def __load_lib(self) -> None:
        loader: ct.LibraryLoader
        loader_variadic: ct.LibraryLoader

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

        ## Library path on the filesystem
        self.__path = path

        # Load library
        try:
            self.__lib = loader.LoadLibrary(path)
            self.__lib_variadic = loader_variadic.LoadLibrary(self.path)
        except FileNotFoundError as ex:
            raise RuntimeError(
                f'Library {self.name} not found. '
                'This module requires the latest version of '
                'the library to be installed on your system. '
                'You may find the official installers at '
                'https://www.caen.it/. '
                'Please install it and retry.'
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
    def lib(self) -> Any:
        """ctypes object to shared library"""
        return self.__lib

    @property
    def lib_variadic(self) -> Any:
        """ctypes object to shared library (for variadic functions)"""
        return self.__lib_variadic
