"""
String utilities
"""

__author__ = 'Giovanni Cerretani'
__copyright__ = 'Copyright (C) 2024 CAEN SpA'
__license__ = 'LGPL-3.0-or-later'
# SPDX-License-Identifier: LGPL-3.0-or-later

import ctypes as ct
from typing import Iterator, Union


def from_char(data: Union[ct.c_char, ct.Array], n_strings: int) -> Iterator[str]:
    """
    Split a buffer into a list of N string.
    Strings are separated by the null terminator:
        e.g. S1\0 STR2\0 (n_strings == 2)
    String sizes are not bounded.
    For ct.c_char and arrays of it.

    Note: ct.Array is not subscriptable on Python 3.8, could be ct.Array[ct.c_char]
    """
    data_addr = ct.addressof(data)
    for _ in range(n_strings):
        value = ct.string_at(data_addr)
        data_addr += len(value) + 1
        yield value.decode()


def from_char_p(data: ct._Pointer, n_strings: int) -> Iterator[str]:
    """
    Same of from_char.
    For pointers to ct.c_char, to avoid dereferences in case of zero size.
    """
    if n_strings != 0:
        yield from from_char(data.contents, n_strings)


def from_char_array(data: Union[ct.c_char, ct.Array], string_size: int) -> Iterator[str]:
    """
    Split a buffer of fixed size string.
    Size is deduced by the first zero size string found:
        e.g. S1\0\0\0 STR2\0 \0 (string_size == 5)
    Each string cannot be longer than string_size - 1.
    For ct.c_char and arrays of it.
    """
    data_addr = ct.addressof(data)
    while True:
        value = ct.string_at(data_addr)
        if len(value) == 0:
            return
        assert len(value) < string_size
        data_addr += string_size
        yield value.decode()


def from_n_char_array(data: Union[ct.c_char, ct.Array], string_size: int, n_strings: int) -> Iterator[str]:
    """
    Split a buffer of fixed size string.
    Size is passed as parameter:
        e.g. S1\0\0\0 STR2\0 (string_size == 5, n_strings == 2)
    Each string cannot be longer than string_size - 1.
    For ct.c_char and arrays of it.
    """
    data_addr = ct.addressof(data)
    for _ in range(n_strings):
        value = ct.string_at(data_addr)
        assert len(value) < string_size
        data_addr += string_size
        yield value.decode()


def str_from_n_char_array_p(data: ct._Pointer, string_size: int, n_strings: int) -> Iterator[str]:
    """
    Same of _str_from_n_char_array.
    For pointers to ct.c_char, to avoid dereferences in case of zero size.
    """
    if n_strings != 0:
        yield from from_n_char_array(data.contents, string_size, n_strings)
