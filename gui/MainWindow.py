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

from typing import Callable
from comtypes import COMError

import queue
import numpy as np

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import tkinter as tk

from gui.SelectDevice import SelectDevice
from gui.ConfigureRecording import ConfigureRecording

from pygrabber.PyGrabber import PyGrabber
import pygrabber.image_process as proc


class MainWindow:
    """Main window of the application."""

    def __init__(self, master: tk.Widget):
        """Create the main window.

        Args:
            master (tk.Widget): The parent widget.
        """
        self._create_gui(master)
        self.grabber = PyGrabber(self._on_image_received)
        self.queue = queue.Queue()
        self.image = None
        self.original_image = None
        self._select_device()

    def _create_gui(self, master: tk.Widget):
        """Build the interface.

        Args:
            master (tk.Widget): The parent widget.
        """
        self.master = master
        master.title("Python Photo App")
        self._create_menu(master)

        master.columnconfigure(0, weight=1, uniform="group1")
        master.columnconfigure(1, weight=1, uniform="group1")
        master.rowconfigure(0, weight=1)

        sticky_all = tk.W + tk.E + tk.N + tk.S

        self.video_area = tk.Frame(master, bg='black')
        self.video_area.grid(row=0, column=0,
                             sticky=sticky_all,
                             padx=5, pady=5)

        status_area = tk.Frame(master)
        status_area.grid(row=1, column=0,
                         sticky=sticky_all,
                         padx=5, pady=5)

        image_area = tk.Frame(master)
        image_area.grid(row=0, column=1,
                        sticky=sticky_all,
                        padx=5, pady=5)

        image_controls_area = tk.Frame(master)
        image_controls_area.grid(row=1, column=1, padx=5, pady=0)

        image_controls_area2 = tk.Frame(master)
        image_controls_area2.grid(row=2, column=1, padx=5, pady=0)

        # Grabbed image
        fig = Figure(figsize=(5, 4), dpi=100)
        self.plot = fig.add_subplot(111)
        self.plot.axis('off')

        self.canvas = FigureCanvasTkAgg(fig, master=image_area)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=1)

        # Status
        self.lbl_status1 = tk.Label(status_area,
                                    text="No device selected")
        self.lbl_status1.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)

        # Image control buttons
        grab_btn = tk.Button(
            image_controls_area,
            text="Grab",
            command=self._grab_frame)
        grab_btn.pack(padx=5, pady=20, side=tk.LEFT)

        image_filter_orig_btn = tk.Button(
            image_controls_area,
            text="Original",
            command=self._restore_original_image)
        image_filter_orig_btn.pack(padx=5, pady=2, side=tk.LEFT)

        image_filter_1_btn = tk.Button(
            image_controls_area,
            text="Sepia",
            command=self._image_filter(proc.sepia))
        image_filter_1_btn.pack(padx=5, pady=2, side=tk.LEFT)

        image_filter_2_btn = tk.Button(
            image_controls_area,
            text="Edge Preserving",
            command=self._image_filter(proc.edge_preserving))
        image_filter_2_btn.pack(padx=5, pady=2, side=tk.LEFT)

        image_filter_3_btn = tk.Button(
            image_controls_area2,
            text="Stylization",
            command=self._image_filter(proc.stylization))
        image_filter_3_btn.pack(padx=5, pady=2, side=tk.LEFT)

        image_filter_4_btn = tk.Button(
            image_controls_area2,
            text="Pencil Sketch",
            command=self._image_filter(proc.pencil_sketch))
        image_filter_4_btn.pack(padx=5, pady=2, side=tk.LEFT)

        save_btn = tk.Button(
            image_controls_area2,
            text="Save",
            command=self._save_image)
        save_btn.pack(padx=5, pady=2, side=tk.LEFT)

        self.video_area.bind("<Configure>", self._on_resize)

    def _create_menu(self, master: tk.Widget):
        """Create the menu.

        Args:
            master (tk.Widget): The parent widget.
        """
        menubar = tk.Menu(master)
        self.master.config(menu=menubar)

        camera_menu = tk.Menu(menubar)
        camera_menu.add_command(label="Open...",
                                command=self._change_camera)
        camera_menu.add_command(label="Set properties...",
                                command=self._camera_properties)
        camera_menu.add_command(label="Set format...",
                                command=self._set_format)
        camera_menu.add_command(label="Start preview",
                                command=self._start_preview)
        camera_menu.add_command(label="Stop",
                                command=self._stop)
        menubar.add_cascade(label="Camera", menu=camera_menu)

        image_menu = tk.Menu(menubar)
        image_menu.add_command(label="Grab image",
                               command=self._grab_frame)
        image_menu.add_command(label="Save...",
                               command=self._save_image)
        menubar.add_cascade(label="Image", menu=image_menu)

        recording_menu = tk.Menu(menubar)
        recording_menu.add_command(label="Start recording...",
                                   command=self._start_stop_recording)
        recording_menu.add_command(label="Stop recording",
                                   command=self._stop)
        menubar.add_cascade(label="Video Recording", menu=recording_menu)

    def _display_image(self):
        """Display the last grabbed image."""
        while self.queue.qsize():
            try:
                self.image = self.queue.get(0)
                self.original_image = self.image
                self.plot.imshow(np.flip(self.image, axis=2))
                self.canvas.draw()
            except queue.Empty:
                pass
        self.master.after(100, self._display_image)

    def _select_device(self):
        """Open the dialog for selecting the video device."""
        input_dialog = SelectDevice(self.master,
                                    self.grabber.get_video_devices())
        self.master.wait_window(input_dialog.top)

        # no device selected
        if input_dialog.device_id is None:
            exit()

        self.grabber.set_device(input_dialog.device_id)
        self.grabber.start_preview(self.video_area.winfo_id())
        self._display_status(self.grabber.get_status())
        self._on_resize(None)
        self._display_image()

    def _display_status(self, status):
        """Change the status label."""
        self.lbl_status1.config(text=status)

    def _change_camera(self):
        """Change the current camera used."""
        self.grabber.stop()
        del self.grabber
        self.grabber = PyGrabber(self._on_image_received)
        self._select_device()

    def _camera_properties(self):
        """Select the properties of the camera."""
        self.grabber.set_device_properties()

    def _set_format(self):
        """Open the dialog to change the format of the image."""
        self.grabber.display_format_dialog()

    def _on_resize(self, event):
        """Slot for the event of resising the window."""
        self.grabber.update_window(self.video_area.winfo_width(),
                                   self.video_area.winfo_height())

    def init_device(self):
        """Start the grabber."""
        self.grabber.start()

    def _grab_frame(self):
        """Grab a frame."""
        self.grabber.grab_frame()

    def _start_stop_recording(self):
        """Start or stop the recording."""
        # Get the different lists of devices
        audio_devices = self.grabber.get_audio_devices()
        video_compressors = self.grabber.get_video_compressors()
        audio_compressors = self.grabber.get_audio_compressors()
        asf_profiles = self.grabber.get_asf_profiles()

        input_dialog = ConfigureRecording(
            self.master,
            audio_devices, video_compressors, audio_compressors, asf_profiles)
        self.master.wait_window(input_dialog.top)

        if input_dialog.result:
            try:
                print(input_dialog.get_filename())

                self.grabber.start_recording(
                    input_dialog.get_audio_device_index(),
                    input_dialog.get_video_compressor_index(),
                    input_dialog.get_audio_compressor_index(),
                    input_dialog.get_filename(),
                    self.video_area.winfo_id())

                self.grabber.update_window(self.video_area.winfo_width(),
                                           self.video_area.winfo_height())
                self._display_status(self.grabber.get_status())
            except COMError:
                tk.messagebox.showinfo(
                    "Error",
                    "An error occurred during the recoding. Select a "
                    "different combination of compressors and try again.")
                self._display_status(self.grabber.get_status())

    def _on_image_received(self, image):
        """Slot for the event of receiving an image."""
        self.queue.put(image)

    def _start_preview(self):
        """Start the preview."""
        self.grabber.start_preview(self.video_area.winfo_id())
        self._display_status(self.grabber.get_status())
        self._on_resize(None)

    def _stop(self):
        """Stop the grabber."""
        self.grabber.stop()
        self._display_status(self.grabber.get_status())

    def _save_image(self):
        """Save the current image."""
        # Open a file dialog to choose the file to save to
        filename = tk.filedialog.asksaveasfilename(
            initialdir="/",
            title="Select file",
            filetypes=[('PNG', ".png"), ('JPG', ".jpg")])

        if filename:
            proc.save_image(filename, self.image)

    def _image_filter(self, process_function: Callable[[np.array], np.array]):
        """Define the image filter used.

        Args:
            process_function (Callable[[np.array], np.array]): A function
                called to process the image. The function must take an argument
                of type np.array and return another np.array.
        Returns:
            Callable: The function really called and calling the
                process_function.
        """
        def inner():
            if self.original_image is None:
                return
            self.image = process_function(self.original_image)
            self.plot.imshow(np.flip(self.image, axis=2))
            self.canvas.draw()
        return inner

    def _restore_original_image(self):
        """Restore the original image."""
        if self.original_image is None:
            return
        self.image = self.original_image
        self.plot.imshow(np.flip(self.image, axis=2))
        self.canvas.draw()
