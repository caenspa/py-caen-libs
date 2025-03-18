"""
String utilities
"""

__author__ = 'Giovanni Cerretani'
__copyright__ = 'Copyright (C) 2024 CAEN SpA'
__license__ = 'LGPL-3.0-or-later'
# SPDX-License-Identifier: LGPL-3.0-or-later

import ctypes as ct
from collections.abc import Iterator
from typing import Union


def from_char(data: Union[ct.c_char, ct.Array[ct.c_char]], n_str: int) -> Iterator[str]:
    """
    Split a buffer into a list of N string.
    Strings are separated by the null terminator:
        e.g. S1\0 STR2\0 (n_str == 2)
    String sizes are not bounded.
    For ct.c_char and arrays of it.
    """
    data_addr = ct.addressof(data)
    for _ in range(n_str):
        value = ct.string_at(data_addr)
        data_addr += len(value) + 1
        yield value.decode('ascii')


def from_char_p(data: 'ct._Pointer[ct.c_char]', n_str: int) -> Iterator[str]:
    """
    Same of from_char.
    For pointers to ct.c_char, to avoid dereferences in case of zero size.
    """
    if n_str != 0:
        yield from from_char(data.contents, n_str)


def from_char_array(data: Union[ct.c_char, ct.Array[ct.c_char]], str_size: int) -> Iterator[str]:
    """
    Split a buffer of fixed size string.
    Size is deduced by the first zero size string found:
        e.g. S1\0\0\0 STR2\0 \0 (str_size == 5)
    Each string cannot be longer than str_size - 1.
    For ct.c_char and arrays of it.
    """
    data_addr = ct.addressof(data)
    while (value := ct.string_at(data_addr)) != b'':
        if len(value) >= str_size:
            raise ValueError('String longer than buffer size')
        data_addr += str_size
        yield value.decode('ascii')


def from_n_char_array(data: Union[ct.c_char, ct.Array[ct.c_char]], str_size: int, n_str: int) -> Iterator[str]:
    """
    Split a buffer of fixed size string.
    Size is passed as parameter:
        e.g. S1\0\0\0 STR2\0 (str_size == 5, n_str == 2)
    Each string cannot be longer than str_size - 1.
    For ct.c_char and arrays of it.
    """
    data_addr = ct.addressof(data)
    for _ in range(n_str):
        value = ct.string_at(data_addr)
        if len(value) >= str_size:
            raise ValueError('String longer than buffer size')
        data_addr += str_size
        yield value.decode('ascii')


def from_n_char_array_p(data: 'ct._Pointer[ct.c_char]', str_size: int, n_str: int) -> Iterator[str]:
    """
    Same of from_n_char_array.
    For pointers to ct.c_char, to avoid dereferences in case of zero size.
    """
    if n_str != 0:
        yield from from_n_char_array(data.contents, str_size, n_str)
