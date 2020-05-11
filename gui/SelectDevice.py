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
"""

from typing import List, AnyStr
import tkinter as tk


class SelectDevice:
    """Dialog for selecting the devices."""

    def __init__(self, parent: tk.Widget, devices: List[AnyStr]):
        """Initialize the dialog.

        Args:
            parent (tk.Widget): The parent widget.
            devices (List of str) : The list of video devices.
        """
        self._device_id = None

        self._top = tk.Toplevel(parent)
        self._top.attributes("-toolwindow", 1)
        self._top.attributes("-topmost", 1)
        self._top.geometry("250x200")
        self._top.resizable(False, False)
        self._top.columnconfigure(0, weight=1)
        self._top.rowconfigure(1, weight=1)

        myLabel = tk.Label(self._top, text='Select a video device:')
        myLabel.grid(padx=5, pady=5)

        self._listbox = tk.Listbox(self._top, selectmode=tk.SINGLE)
        self._listbox.grid(sticky=tk.W + tk.E + tk.N + tk.S, padx=5, pady=5)
        for item in devices:
            self._listbox.insert(tk.END, item)

        mySubmitButton = tk.Button(self._top,
                                   text='Ok',
                                   width=10,
                                   command=self.send)
        mySubmitButton.grid(padx=5, pady=5)

        self._top.bind('<Return>', lambda event: self.send())

    @property
    def top(self):
        """Get the top level of the dialog."""
        return self._top
    # No setter for this attribute

    @property
    def device_id(self):
        """Get the selected device id."""
        return self._device_id
    # No setter for this attribute

    def send(self):
        """Close the dialog ang set the selected device."""
        self._device_id = self._listbox.curselection()[0]
        self._top.destroy()
