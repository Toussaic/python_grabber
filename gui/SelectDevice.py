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

from tkinter import *


class SelectDevice:
    def __init__(self, parent, devices):
        self.device_id = None

        top = self.top = Toplevel(parent)
        top.attributes("-toolwindow", 1)
        top.attributes("-topmost", 1)
        top.geometry("250x200")
        top.resizable(False, False)
        top.columnconfigure(0, weight=1)
        top.rowconfigure(1, weight=1)

        self.myLabel = Label(top, text='Select a video device:')
        self.myLabel.grid(padx=5, pady=5)

        self.listbox = Listbox(top, selectmode=SINGLE)
        self.listbox.grid(sticky=W + E + N + S, padx=5, pady=5)
        for item in devices:
            self.listbox.insert(END, item)

        self.mySubmitButton = Button(top, text='Ok', width=10, command=self.send)
        self.mySubmitButton.grid(padx=5, pady=5)

        top.bind('<Return>', lambda event: self.send())

    def send(self):
        self.device_id = self.listbox.curselection()[0]
        self.top.destroy()
