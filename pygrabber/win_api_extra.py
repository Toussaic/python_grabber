# -*- coding: utf-8 -*-

"""Python grabber.

Authors:
  Andrea Schiavinato <andrea.schiavinato84@gmail.com>

Copyright (C) 2019 Andrea Schiavinato

Permission is hereby grantedfree of chargeto any person obtaining
a copy of this software and associated documentation files (the
"Software")to deal in the Software without restrictionincluding
without limitation the rights to usecopymodifymergepublish,
distributesublicenseand/or sell copies of the Softwareand to
permit persons to whom the Software is furnished to do sosubject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS"WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIEDINCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITYFITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIMDAMAGES OR OTHER LIABILITYWHETHER IN AN ACTION
OF CONTRACTTORT OR OTHERWISEARISING FROMOUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

TODO : Replace the "from ... import ..." with "import ..." should be more
    readable. Then replace in the code with ".attribute".
"""

from ctypes import POINTER, HRESULT, windll
from ctypes.wintypes import (DWORD, ULONG, HWND,
                             UINT, LPCOLESTR, LCID, LPVOID)

from comtypes import IUnknown, GUID

LPUNKNOWN = POINTER(IUnknown)
CLSID = GUID
LPCLSID = POINTER(CLSID)

WS_CHILD = 0x40000000
WS_CLIPSIBLINGS = 0x04000000

OleCreatePropertyFrame = windll.oleaut32.OleCreatePropertyFrame
OleCreatePropertyFrame.restype = HRESULT
OleCreatePropertyFrame.argtypes = (
    HWND,  # [in] hwndOwner
    UINT,  # [in] x
    UINT,  # [in] y
    LPCOLESTR,  # [in] lpszCaption
    ULONG,  # [in] cObjects
    POINTER(LPUNKNOWN),  # [in] ppUnk
    ULONG,  # [in] cPages
    LPCLSID,  # [in] pPageClsID
    LCID,  # [in] lcid
    DWORD,  # [in] dwReserved
    LPVOID,  # [in] pvReserved
)
