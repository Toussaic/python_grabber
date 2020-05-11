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

from typing import TypeVar, List, Tuple, AnyStr

from pathlib import Path
import tkinter as tk
from tkinter import ttk

ListOfStr = TypeVar('ListOfStr', List[AnyStr], Tuple[AnyStr])


class ConfigureRecording:
    """An holder for all information about the file to save the video to."""

    def __init__(self,
                 parent: tk.Widget,
                 audio_devices: ListOfStr,
                 video_compressors: ListOfStr,
                 audio_compressors: ListOfStr,
                 asf_profiles: ListOfStr):
        """Create an holder for all information about the file to save to.

        Args:
            parent (tk.Widget): The parent widget.
            audio_devices (ListOfStr): List of available audio devices.
            video_compressors (ListOfStr): List of available video compressors.
            audio_compressors (ListOfStr): List of available audio compressors.
            asf_profiles (ListOfStr): List of available asf profiles.
        """
        # Definitions for the filename
        self._filename = tk.StringVar()
        self._filetype = tk.StringVar()
        self._filetype.set(".avi")

        # Index of selected devices in the combobox
        self._audio_device_index = None
        self._video_compressor_index = None
        self._audio_compressor_index = None
        self._asf_profile = None
        self._result = None

        self.top = tk.Toplevel(parent)
        self.top.attributes("-toolwindow", 1)
        self.top.attributes("-topmost", 1)
        self.top.geometry("500x290")
        self.top.resizable(False, False)

        self.lbl_title = tk.Label(self.top, text='Choose recording options:')
        self.lbl_title.pack(side=tk.TOP, padx=5, pady=5)

        content = tk.Frame(self.top)
        content.pack(side=tk.TOP)

        lbl_message = tk.Label(self.top,
                               text='* Valid only for AVI, '
                                    '** valid only for WMV')
        lbl_message.pack(side=tk.TOP, padx=5, pady=5)

        commands = tk.Frame(self.top)
        commands.pack(side=tk.BOTTOM)
        commands.columnconfigure(0, weight=1)
        commands.columnconfigure(1, weight=1)

        tblen1 = 43
        tblen2 = 50

        lbl1 = tk.Label(content, text='File name:')
        lbl1.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)

        input_file = tk.Entry(master=content,
                              width=tblen1,
                              takefocus=0,
                              textvariable=self._filename)
        input_file.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)

        btn_browse = tk.Button(master=content,
                               text="Browse",
                               command=self.ask_file_name)
        btn_browse.grid(row=0, column=2, padx=5, pady=5)

        lbl2 = tk.Label(content, text='File type:')
        lbl2.grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)

        frame_ftype = tk.Frame(content)
        frame_ftype.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)

        tk.Radiobutton(frame_ftype,
                       text="AVI",
                       variable=self._filetype,
                       value=".avi",
                       command=self._fix_extension).pack(side=tk.LEFT)
        tk.Radiobutton(frame_ftype,
                       text="WMV",
                       variable=self._filetype,
                       value=".wmv",
                       command=self._fix_extension).pack(side=tk.LEFT)

        # Creation of the different combobox and their labels
        lbl3 = tk.Label(content, text='Audio device:')
        lbl3.grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)

        self._input_audio_device = ttk.Combobox(master=content,
                                                width=tblen2,
                                                values=audio_devices,
                                                state='readonly')
        self._input_audio_device.grid(row=2, column=1,
                                      padx=5, pady=5,
                                      sticky=tk.W,
                                      columnspan=2)

        lbl4 = tk.Label(content, text='Video compressor (*):')
        lbl4.grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)

        self._input_video_compressor = ttk.Combobox(master=content,
                                                    width=tblen2,
                                                    values=video_compressors,
                                                    state='readonly')
        self._input_video_compressor.grid(row=3, column=1,
                                          padx=5, pady=5,
                                          sticky=tk.W,
                                          columnspan=2)

        lbl5 = tk.Label(content, text='Audio compressor (*):')
        lbl5.grid(row=4, column=0, padx=5, pady=5, sticky=tk.W)

        self._input_audio_compressor = ttk.Combobox(master=content,
                                                    width=tblen2,
                                                    values=audio_compressors,
                                                    state='readonly')
        self._input_audio_compressor.grid(row=4, column=1,
                                          padx=5, pady=5,
                                          sticky=tk.W,
                                          columnspan=2)

        lbl6 = tk.Label(content, text='Windows Media profile (**):')
        lbl6.grid(row=5, column=0, padx=5, pady=5, sticky=tk.W)

        self._input_asf_profile = ttk.Combobox(master=content,
                                               width=tblen2,
                                               values=asf_profiles,
                                               state='readonly')
        self._input_asf_profile.grid(row=5, column=1,
                                     padx=5, pady=5,
                                     sticky=tk.W,
                                     columnspan=2)

        submitButton = tk.Button(commands,
                                 text='Ok',
                                 width=10,
                                 command=self.send)
        submitButton.grid(row=0, column=0, padx=5, pady=5)

        cancelButton = tk.Button(commands,
                                 text='Cancel',
                                 width=10,
                                 command=self.cancel)
        cancelButton.grid(row=0, column=1, padx=5, pady=5)

    @property
    def result(self):
        """Get the result of the dialog."""
        return self._result
    # No setter for the property

    def ask_file_name(self):
        """Open the dialog for asking the filename."""
        # self.top.withdraw()
        self.top.attributes("-topmost", 0)
        filename = Path(tk.filedialog.asksaveasfilename(
            initialdir=".",
            title="Select file",
            filetypes=[('AVI', ".avi"), ('WMV', ".wmv")]))

        # self.top.deiconify()
        self.top.attributes("-topmost", 1)

        if filename:
            filename, file_extension = str(filename), filename.suffix

            if file_extension in (".avi", ".wmv"):
                self._filetype.set(file_extension)

            print(filename, file_extension)

            self._filename.set(filename + file_extension)
            self._fix_extension()

    def _fix_extension(self):
        """Change the extension of the path."""
        path = Path(self._filename.get())
        path = path.with_suffix(self._filetype.get())
        self._filename.set(str(path))

    def send(self):
        """Save the different indexes and close the dialog."""
        self._audio_device_index = (
            self._input_audio_device.current()
            if self._input_audio_device.current() >= 0
            else None)

        self._video_compressor_index = (
            self._input_video_compressor.current()
            if self._input_video_compressor.current() >= 0
            else None)

        self._audio_compressor_index = (
            self._input_audio_compressor.current()
            if self._input_audio_compressor.current() >= 0
            else None)

        self._asf_profile = self._input_asf_profile.current()

        self.top.destroy()
        self._result = True

    def cancel(self):
        """Close and cancel the dialog."""
        self.top.destroy()
        self._result = False

    def get_audio_device_index(self) -> int:
        """Get the current audio device index.

        Returns:
            int: Index of the audio device.
        """
        return self._audio_device_index

    def get_video_compressor_index(self) -> int:
        """Get the current video compressor index.

        Returns:
            int: Index of the video compressor.
        """
        return self._video_compressor_index

    def get_audio_compressor_index(self) -> int:
        """Get the current audio compressor index.

        Returns:
            int : Index of the audio compressor.
        """
        return self._audio_compressor_index

    def get_filename(self) -> str:
        """Get the name of the file.

        Returns:
            str: The name of the file.
        """
        return self._filename.get()

    def get_asf_profile(self) -> int:
        """Get the index of the current asf profile.

        Returns:
            int: Index of the asf profile.
        """
        return self._asf_profile
