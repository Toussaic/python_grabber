#
# python_grabber
#
# Authors:
#  Andrea Schiavinato <andrea.schiavinato84@gmail.com>
#
# Copyright (C) 2019 Andrea Schiavinato
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

from ctypes.wintypes import (SHORT, INT, ULONG, ULARGE_INTEGER,
                             LARGE_INTEGER, LPOLESTR)
from comtypes import IID, GUID
from ctypes import POINTER

"""
REFERENCE_TIME = c_longlong  # from ctypes
LONG_PTR = c_ulong  # from ctypes
OLE_HANDLE = c_int  # from ctypes
LPCOLESTR = c_wchar_p  # from ctypes
# from https://github.com/enthought/comtypes/blob/master/comtypes/errorinfo.py
REFIID = POINTER(GUID)  # POINTER from _ctypes, GUID from comtypes.GUID
REFGUID = POINTER(GUID)  # POINTER from _ctypes, GUID from comtypes.GUID
WORD = SHORT  # SHORT from wintypes = ctypes.c_short
DWORDLONG = c_ulonglong  # from ctypes
"""

REFERENCE_TIME = LARGE_INTEGER
LONG_PTR = ULONG
OLE_HANDLE = INT
# LPCOLESTR = c_wchar_p  # Redefinition of wintypes.LPCOLESTR
# from https://github.com/enthought/comtypes/blob/master/comtypes/errorinfo.py
REFIID = POINTER(IID)
REFGUID = POINTER(GUID)
# FIXME : Inconsistency between 'wintypes' definition of WORD = USHORT
WORD = SHORT
DWORDLONG = ULARGE_INTEGER
