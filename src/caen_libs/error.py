"""
Base error class
"""

__author__ = 'Giovanni Cerretani'
__copyright__ = 'Copyright (C) 2024 CAEN SpA'
__license__ = 'LGPL-3.0-or-later'
# SPDX-License-Identifier: LGPL-3.0-or-later


class Error(RuntimeError):
    """
    Raised when a wrapped C API function returns negative values.
    """

    message: str  # Message description
    func: str  # Name of failed function

    def __init__(self, message: str, error_code: str, func: str) -> None:
        self.message = message
        self.func = func
        super().__init__(f'{self.func} failed: {self.message} ({error_code})')
