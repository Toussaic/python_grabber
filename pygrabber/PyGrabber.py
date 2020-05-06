# -*- coding: utf-8 -*-

"""Python grabber.

Authors:
  Andrea Schiavinato <andrea.schiavinato84@gmail.com>

Copyright (C) 2020 Andrea Schiavinato

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

__version__ = 0.5
__author__ = "Andrea Schiavinato"
__all__ = ["PyGrabber"]

from pathlib import Path
from typing import List, Callable, Union

from pygrabber.dshow_graph import FilterGraph, StateGraph


class PyGrabber:
    """Main class for creating a media grabber."""

    def __init__(self, callback: Callable):
        """Initialize the grabber.

        Create an empty grabber with no device attached.

        Args:
            callback (Callable): Function called when an image is grabbed.
        """
        self._graph = FilterGraph()
        self._callback = callback
        self._preview_graph_prepared = False
        self._recording_prepared = False

    def get_video_devices(self) -> List[str]:
        """Return a list of available input video devices."""
        return self._graph.get_input_devices()

    def get_audio_devices(self) -> List[str]:
        """Return a list of available input audio devices."""
        return self._graph.get_audio_devices()

    def get_video_compressors(self) -> List[str]:
        """Return a list of available video compressors."""
        return self._graph.get_video_compressors()

    def get_audio_compressors(self) -> List[str]:
        """Return a list of available audio compressors."""
        return self._graph.get_audio_compressors()

    def get_asf_profiles(self) -> List[str]:
        """Return a list of available asf profiles."""
        return self._graph.get_asf_profiles()

    def set_device(self, input_device_index: int):
        """Define the video input device to use.

        Args:
            input_device_index (int): Index of the device to use.
        """
        self._graph.add_video_input_device(input_device_index)

    def start_preview(self, handle=None):
        """Configure the grabber with defaults filters.

        Args:
            handle (TYPE): DESCRIPTION.
        """
        if not self._preview_graph_prepared:
            if self._recording_prepared:
                self._.remove_all_filters_but_video_source()
                self._recording_prepared = False

            self._graph.add_sample_grabber(self.callback)

            if handle:
                self._graph.add_default_render()
            else:
                self._graph.add_null_render()

            self._graph.prepare_preview_graph()
            if handle:
                self._graph.configure_render(handle)
            self._preview_graph_prepared = True
        self._graph.run()

    def start_recording(self,
                        filename: Path,
                        audio_device_index: int = None,
                        video_compressor_index: int = None,
                        audio_compressor_index: int = None,
                        handle: int = None):
        """Prepare the graph filter to enable recording.

        Args:
            filename (Path-like): DESCRIPTION.
            audio_device_index (int, optional): Index of the audio device to
                use. Defaults to None.
            video_compressor_index (int, optional): Index of the video
                compressor to use. Defaults to None.
            audio_compressor_index (int, optional): Index of the audio
                compressor to use. Defaults to None.
            handle (int, optional): Handle of video renderer to use. Defaults
                to None.

        Returns:
            None.

        """
        self._graph.stop()
        self._preview_graph_prepared = False
        self._graph.remove_all_filters_but_video_source()
        self._graph.add_default_render()

        if video_compressor_index:
            self._graph.add_video_compressor(video_compressor_index)

        if audio_device_index:
            self._graph.add_audio_input_device(audio_device_index)
            if audio_compressor_index:
                self._graph.add_audio_compressor(audio_compressor_index)

        self._graph.add_file_writer_and_muxer(filename)
        self._graph.prepare_recording_graph()
        self._graph.configure_render(handle)
        self._recording_prepared = True
        self._graph.run()

    def stop(self):
        """Stop the recording."""
        self._graph.stop()

    def update_window(self, width: int, height: int):
        """Update the size of the window.

        Args:
            width (int): Width of the video renderer.
            height (int): Height of the video renderer.
        """
        self._graph.update_window(width, height)

    def set_device_properties(self):
        """Set default properties of the video input device."""
        self._graph.get_input_device().set_properties()

    def display_format_dialog(self):
        """Open a dialog with the available formats of the video input."""
        self._graph.get_input_device().show_format_dialog()

    def grab_frame(self):
        """Grab an image from the video input."""
        self._graph.grab_frame()

    def get_status(self) -> Union[str, None]:
        """Get the status of the grabber.

        The grabber could be running, stopped or paused.

        Returns:
            Union[str, NoneType]: DESCRIPTION.
        """
        graph_state = self._graph.get_state()
        device_name = self._graph.get_input_device().Name
        resolution = self._graph.get_input_device().get_current_format()
        if graph_state == StateGraph.Stopped:
            return "Stopped"
        elif graph_state == StateGraph.Running:
            return (f"{'Recording' if self.graph.is_recording else 'Playing'} "
                    f"{device_name} [{resolution[0]}x{resolution[1]}]")
        elif graph_state == StateGraph.Paused:
            return f"Connected to {device_name} - paused"
        return None
