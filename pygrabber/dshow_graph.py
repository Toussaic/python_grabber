# -*- coding: utf-8 -*-

"""Python grabber.

Authors:
  Andrea Schiavinato <andrea.schiavinato84@gmail.com>

Copyright (C) 2019 Andrea Schiavinato

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

from typing import List, Tuple, Callable
import numpy as np
from pathlib import Path
from enum import Enum

# from ctypes import *
from ctypes import (wstring_at, cast, POINTER, pointer, windll, byref,
                    create_unicode_buffer)

# from ctypes.wintypes import *
from ctypes.wintypes import DWORD

# from comtypes import *
from comtypes import COMError, GUID, COMObject

import comtypes.client as comclient
from comtypes.persist import IPropertyBag

# from pygrabber.dshow_core import *
from pygrabber.dshow_core import (
    IAMStreamConfig, IVideoWindow, VIDEOINFOHEADER, ISpecifyPropertyPages,
    ISampleGrabber, qedit, quartz, ICreateDevEnum, ICaptureGraphBuilder2,
    PIN_OUT)

# from pygrabber.windows_media import *
from pygrabber.windows_media import IWMProfileManager2, WMCreateProfileManager

# from pygrabber.dshow_ids import *
from pygrabber.dshow_ids import (subtypes, clsids, MediaTypes, MediaSubtypes,
                                 DeviceCategories, PinCategory)

# from pygrabber.win_api_extra import *
from pygrabber.win_api_extra import (OleCreatePropertyFrame, LPUNKNOWN,
                                     WS_CHILD, WS_CLIPSIBLINGS)


class StateGraph(Enum):
    """Enum of FilterGraph states."""

    Stopped = 0
    Paused = 1
    Running = 2


class RecordingFormat(Enum):
    """Enum of recording format allowed."""

    AVI = 0
    ASF = 1


class FilterType(Enum):
    """Enum of available filter types."""

    video_input = 0
    audio_input = 1
    video_compressor = 2
    audio_compressor = 3
    sample_grabber = 4
    render = 5
    file_sink = 6
    muxer = 7
    smart_tee = 8


class Filter:
    """Wrapper around a Direct Show filter."""

    def __init__(self,
                 instance: "FilterGraph",
                 name,
                 capture_builder):
        """Initialize the filter.

        Args:
            instance (FilterGraph): instance of FilterGraph which created this
                filter.
        """
        self._instance = instance
        self._capture_builder = capture_builder
        self._name = name
        self._out_pins = []
        self._in_pins = []
        self.reload_pins()

    def get_out(self):
        """Get the first out pin."""
        return self._out_pins[0]

    def get_in(self, index: int = 0):
        """Get the input pin at given index.

        Args:
            index (int) : Index of the desired pin.

        Returns:
            pin : The desired pin.
        """
        return self._in_pins[index]

    def find_pin(self, direction, category=None, type=None, unconnected=True):
        """Get a specific pin.

        Args:
            direction ()
        """
        try:
            return self._capture_builder.FindPin(self._instance, direction,
                                                 category, type,
                                                 unconnected, 0)
        except COMError:
            return None  # assuming preview pin not found

    def reload_pins(self):
        """Build the list of pins."""
        # 0 = in, 1 = out
        self._out_pins = []
        self._in_pins = []
        enum = self._instance.EnumPins()
        pin, count = enum.Next(1)
        while count > 0:
            if pin.QueryDirection() == 0:
                self._in_pins.append(pin)
            else:
                self._out_pins.append(pin)
            pin, count = enum.Next(1)

    def set_properties(self):
        """Display the properties of the instance."""
        show_properties(self._instance)

    def get_name(self) -> str:
        """Get the name of the owning intance of FilterGraph.

        Returns:
            str: The name of the filter
        """
        filter_info = self._instance.QueryFilterInfo()
        return wstring_at(filter_info.achName)

    def print_info(self):
        """Display info of all the pins."""
        print(f"Pins of: {self.get_name()}")
        enum = self._instance.EnumPins()
        pin, count = enum.Next(1)
        while count > 0:
            info = pin.QueryPinInfo()
            direction, name = (info.dir, wstring_at(info.achName))
            print(f"PIN {'in' if direction == 0 else 'out'} - {name}")
            pin, count = enum.Next(1)


class VideoInput(Filter):
    """Specific class for Video Filter."""

    def __init__(self, args: Tuple[str, int], capture_builder):
        """Initialize the filter.

        Args:
            args (TYPE): DESCRIPTION.
            capture_builder (TYPE): DESCRIPTION.
        """
        Filter.__init__(self, args[0], args[1], capture_builder)

    def get_current_format(self):
        """Get the current format.

        Returns:
            (int, int): Tuple of width and height of the image.
        """
        stream_config = self.get_out().QueryInterface(IAMStreamConfig)
        media_type = stream_config.GetFormat()
        p_video_info_header = cast(media_type.contents.pbFormat,
                                   POINTER(VIDEOINFOHEADER))
        bmp_header = p_video_info_header.contents.bmi_header
        return bmp_header.biWidth, bmp_header.biHeight

    def get_formats(self):
        """Get the available formats for the device.

        Returns:
            List of dictionnaries: Each dictionnary contains the
                properties of the format. The keys are :
                * index
                * media_type_str
                * width
                * height
                * min_framerate
                * max_framerate
        """
        # https://docs.microsoft.com/en-us/windows/win32/directshow/configure-the-video-output-format
        stream_config = self.get_out().QueryInterface(IAMStreamConfig)
        media_types_count, _ = stream_config.GetNumberOfCapabilities()
        result = []
        for i in range(0, media_types_count):
            media_type, capability = stream_config.GetStreamCaps(i)
            p_video_info_header = cast(media_type.contents.pbFormat,
                                       POINTER(VIDEOINFOHEADER))
            bmp_header = p_video_info_header.contents.bmi_header
            result.append({
                'index': i,
                'media_type_str': subtypes[str(media_type.contents.subtype)],
                'width': bmp_header.biWidth,
                'height': bmp_header.biHeight,
                'min_framerate': 10000000 / capability.MinFrameInterval,
                'max_framerate': 10000000 / capability.MaxFrameInterval
            })
            # print(f"{capability.MinOutputSize.cx}"
            #       f"x{capability.MinOutputSize.cx}"
            #       f" - {capability.MaxOutputSize.cx}"
            #       f"x{capability.MaxOutputSize.cx}")
        return result

    def set_format(self, format_index: int):
        """Set the format of the image captured.

        Args:
            format_index (int): Index of the format to use.
        """
        stream_config = self.get_out().QueryInterface(IAMStreamConfig)
        media_type, _ = stream_config.GetStreamCaps(format_index)
        stream_config.SetFormat(media_type)

    def show_format_dialog(self):
        """Display a dialog with the available formats."""
        show_properties(self.get_out())


class AudioInput(Filter):
    """Subclass filter for audio input."""

    def __init__(self, args, capture_builder):
        """Initialize the audio filter.

        Args:
            args (TYPE): DESCRIPTION.
            capture_builder (TYPE): DESCRIPTION.
        """
        Filter.__init__(self, args[0], args[1], capture_builder)


class VideoCompressor(Filter):
    """Subclass filter for video compressor."""

    def __init__(self, args, capture_builder):
        """Initialize the video compressor.

        Args:
            args (TYPE): DESCRIPTION.
            capture_builder (TYPE): DESCRIPTION.
        """
        Filter.__init__(self, args[0], args[1], capture_builder)


class AudioCompressor(Filter):
    """Subclass filter for audio compressor."""

    def __init__(self, args, capture_builder):
        """Initialize the audio compressor.

        Args:
            args (TYPE): DESCRIPTION.
            capture_builder (TYPE): DESCRIPTION.
        """
        Filter.__init__(self, args[0], args[1], capture_builder)


class Render(Filter):
    """Subclass filter for renderer."""

    def __init__(self, instance, capture_builder):
        """Initialize the render.

        Args:
            instance (FilterGraph): DESCRIPTION.
            capture_builder (TYPE): DESCRIPTION.
        """
        Filter.__init__(self, instance, "Render", capture_builder)
        try:
            self._video_window = self.instance.QueryInterface(IVideoWindow)
        except COMError:
            # probably interface IVideoWindow not supported because
            # using NullRender
            self._video_window = None

    def configure_video_window(self, handle):
        """Configure the window holding the video.

        Args:
            handle (TYPE): DESCRIPTION.
        """
        # must be called after the graph is connected
        self._video_window.put_Owner(handle)
        self._video_window.put_WindowStyle(WS_CHILD | WS_CLIPSIBLINGS)

    def set_window_position(self, x, y, width, height):
        """Set the position of the window holding the video.

        Args:
            x (TYPE): DESCRIPTION.
            y (TYPE): DESCRIPTION.
            width (TYPE): DESCRIPTION.
            height (TYPE): DESCRIPTION.

        Returns:
            None.

        """
        self._video_window.SetWindowPosition(x, y, width, height)


class SampleGrabber(Filter):
    """Subclass filter for sample grabber."""

    def __init__(self, capture_builder):
        """Initialize the sample grabber.

        Args:
            capture_builder (TYPE): DESCRIPTION.
        """
        Filter.__init__(self,
                        comclient.CreateObject(
                            GUID(clsids.CLSID_SampleGrabber),
                            interface=qedit.IBaseFilter),
                        "Sample Grabber",
                        capture_builder)
        self._sample_grabber = self._instance.QueryInterface(ISampleGrabber)
        self._callback = None

    @property
    def callback(self):
        """Get the callback function."""
        return self._callback

    def set_callback(self, callback: Callable, which_method_to_callback):
        """Set the callback used when the image is grabbed.

        Args:
            callback (Callable): DESCRIPTION.
            which_method_to_callback (TYPE): DESCRIPTION.
        """
        self._callback = callback
        self._sample_grabber.SetCallback(callback, which_method_to_callback)

    def set_media_type(self, media_type: MediaTypes,
                       media_subtype: MediaSubtypes):
        """Set the type of media.

        Args:
            media_type (MediaTypes): A member of dshow_ids.MediaTypes.
            media_subtype (MediaSubtypes): A member of dshow_ids.MediaSubtypes.
        """
        sg_type = qedit._AMMediaType()
        sg_type.majortype = GUID(media_type)
        sg_type.subtype = GUID(media_subtype)
        self._sample_grabber.SetMediaType(sg_type)

    def get_resolution(self) -> Tuple[int, int]:
        """Get the current resolution of the grabber.

        Returns:
            (int, int): The width and height of the image.
        """
        media_type = self._sample_grabber.GetConnectedMediaType()
        p_video_info_header = cast(media_type.pbFormat,
                                   POINTER(VIDEOINFOHEADER))
        bmp_header = p_video_info_header.contents.bmi_header
        return bmp_header.biWidth, bmp_header.biHeight

    def initialize_after_connection(self):
        """Define the resolution for the callback function."""
        self._callback.image_resolution = self.get_resolution()


class SmartTee(Filter):
    """Subclass filter for smart tee."""

    def __init__(self, capture_builder):
        """Initialize the smart tee.

        Args:
            capture_builder (TYPE): DESCRIPTION.
        """
        Filter.__init__(self,
                        comclient.CreateObject(GUID(clsids.CLSID_SmartTee),
                                               interface=qedit.IBaseFilter),
                        "Smart Tee",
                        capture_builder)


class Muxer(Filter):
    """Subclass filter for muxer."""

    def __init__(self, args, capture_builder):
        """Initialize the muxer.

        Args:
            capture_builder (TYPE): DESCRIPTION.
        """
        Filter.__init__(self, args, "Muxer", capture_builder)


class SystemDeviceEnum:
    """Enumerator for system devices."""

    def __init__(self):
        """Create a wrapper to enumerate available filters."""
        self._system_device_enum = comclient.CreateObject(
            clsids.CLSID_SystemDeviceEnum, interface=ICreateDevEnum)

    def get_available_filters(self, category_clsid: clsids) -> List:
        """Get a list of available filters.

        Args:
            category_clsid (clsids): A member of 'dshow_ids.clsids'.

        Returns:
            List of Filters: DESCRIPTION.
        """
        filter_enumerator = self._system_device_enum.CreateClassEnumerator(
            GUID(category_clsid), dwFlags=0)

        moniker, count = filter_enumerator.Next(1)

        result = []
        while count > 0:
            result.append(get_moniker_name(moniker))
            moniker, count = filter_enumerator.Next(1)
        return result

    def get_filter_by_index(self, category_clsid, index):
        """Get the associate filter by its type and index.

        Args:
            category_clsid (TYPE): DESCRIPTION.
            index (TYPE): DESCRIPTION.

        Returns:
            TYPE: DESCRIPTION.
        """
        filter_enumerator = self._system_device_enum.CreateClassEnumerator(
            GUID(category_clsid), dwFlags=0)
        moniker, count = filter_enumerator.Next(1)
        i = 0
        while i != index and count > 0:
            moniker, count = filter_enumerator.Next(1)
            i = i + 1

        base_filter = moniker.BindToObject(0, 0, qedit.IBaseFilter._iid_)

        return (base_filter.QueryInterface(qedit.IBaseFilter),
                get_moniker_name(moniker))


class FilterFactory:
    """Class building the different kinds of filters."""

    def __init__(self, system_device_enum, capture_builder):
        """Initialize the Factory.

        Args:
            sytem_device_enum (TYPE): DESCRIPTION.
            capture_builder (TYPE): DESCRIPTION.
        """
        self._system_device_enum = system_device_enum
        self._capture_builder = capture_builder

    def build_filter(self, filter_type: int, id):
        """Build a filter of the given.

        Args:
            filter_type (int): A member of FilterType.
            id (TYPE): DESCRIPTION.

        Raises:
            ValueError: DESCRIPTION.

        Returns:
            TYPE: DESCRIPTION.
        """
        if filter_type == FilterType.video_input:
            filterinfo = self._system_device_enum.get_filter_by_index(
                DeviceCategories.VideoInputDevice, id),
            return VideoInput(filterinfo, self._capture_builder)

        elif filter_type == FilterType.audio_input:
            return AudioInput(
                self._system_device_enum.get_filter_by_index(
                    DeviceCategories.AudioInputDevice, id),
                self._capture_builder)

        elif filter_type == FilterType.video_compressor:
            return VideoCompressor(
                self._system_device_enum.get_filter_by_index(
                    DeviceCategories.VideoCompressor, id),
                self._capture_builder)

        elif filter_type == FilterType.audio_compressor:
            return AudioCompressor(
                self._system_device_enum.get_filter_by_index(
                    DeviceCategories.AudioCompressor, id),
                self._capture_builder)

        elif filter_type == FilterType.render:
            return Render(
                comclient.CreateObject(GUID(id),
                                       interface=qedit.IBaseFilter),
                self._capture_builder)
        elif filter_type == FilterType.sample_grabber:
            return SampleGrabber(self._capture_builder)
        elif filter_type == FilterType.muxer:
            return Muxer(id, self._capture_builder)
        elif filter_type == FilterType.smart_tee:
            return SmartTee(self._capture_builder)
        else:
            raise ValueError('Cannot create filter', filter_type, id)


class MediaType:
    """Defines a media type."""

    def __init__(self, majortype_guid: MediaTypes,
                 subtype_guid: MediaSubtypes):
        """Initialize the type of the media with a given type and subtype.

        Args:
            majortype_guid (MediaTypes): A member of MediaTypes.
            subtype_guid (MediaSubtypes): A member of MediaSubtypes.
        """
        self._instance = qedit._AMMediaType()
        self._instance.majortype = GUID(majortype_guid)
        self._instance.subtype = GUID(subtype_guid)


class WmProfileManager:
    """Class for a profile manager."""

    def __init__(self):
        """Initialize the profile manager."""
        self._profile_manager = POINTER(IWMProfileManager2)()
        WMCreateProfileManager(byref(self._profile_manager))
        self._profile_manager.SetSystemProfileVersion(0x00080000)
        self._profiles, self._profiles_names = self._load_profiles()

    @property
    def profiles_names(self):
        """Get the profile's names."""
        return self._profiles_names
    # No setter for this attribute

    def _load_profiles(self):
        nr_profiles = self._profile_manager.GetSystemProfileCount()
        profiles = [self._profile_manager.LoadSystemProfile(i)
                    for i in range(nr_profiles)]

        profiles_names = []
        buf = create_unicode_buffer(200)
        for profile in profiles:
            i = DWORD(200)
            profile.GetName(buf, pointer(i))
            profiles_names.append(buf.value)
        return profiles, profiles_names


class FilterGraph:
    """Main class holding the different filters for the device."""

    def __init__(self):
        """Initialize the Filter."""
        self._filter_graph = comclient.CreateObject(
            clsids.CLSID_FilterGraph,
            interface=qedit.IFilterGraph)

        self._graph_builder = \
            self._filter_graph.QueryInterface(qedit.IGraphBuilder)

        self._media_control = \
            self._filter_graph.QueryInterface(quartz.IMediaControl)

        self._media_event = self._filter_graph.QueryInterface(
            quartz.IMediaEvent)

        self._capture_builder = \
            comclient.CreateObject(clsids.CLSID_CaptureGraphBuilder2,
                                   interface=ICaptureGraphBuilder2)

        self._capture_builder.SetFiltergraph(self._filter_graph)

        self._system_device_enum = SystemDeviceEnum()

        self._filter_factory = \
            FilterFactory(self._system_device_enum, self._capture_builder)

        self._wm_profile_manager = WmProfileManager()

        self._filters = {}
        self._recording_format = None
        self._is_recording = False

    def _add_filter(self, filter_type: FilterType, filter_id: int):
        """Add a filter to the instance given the type and the id.

        Args:
            filter_type (FilterType): A member of FilterType.
            filter_id (int): DESCRIPTION.
        """
        assert not(filter_type in self._filters)
        filter = self._filter_factory.build_filter(filter_type, filter_id)
        self._filters[filter_type] = filter
        self._filter_graph.AddFilter(filter.instance, filter.Name)

    def add_video_input_device(self, index: int = 0):
        """Add the video input device at given index.

        Args:
            index (int, optionnal): The index of the device to add to the
                grabber. Defaults to 0.
        """
        self._add_filter(FilterType.video_input, index)

    def add_audio_input_device(self, index: int = 0):
        """Add the audio input device at given index.

        Args:
            index (int, optionnal): The index of the device to add to the
                grabber. Defaults to 0.
        """
        self._add_filter(FilterType.audio_input, index)

    def add_video_compressor(self, index: int = 0):
        """Add the video compressor at given index.

        Args:
            index (int, optionnal): The index of the device to add to the
                grabber. Defaults to 0.
        """
        self._add_filter(FilterType.video_compressor, index)

    def add_audio_compressor(self, index: int = 0):
        """Add the video input device at given index.

        Args:
            index (int, optionnal): The index of the device to add to the
                grabber. Defaults to 0.
        """
        self._add_filter(FilterType.audio_compressor, index)

    def add_sample_grabber(self, callback: Callable[[np.array], np.array]):
        """Add the video input device at given index.

        Args:
            index (Callable): A function to be called when an image is grabbed.
        """
        self._add_filter(FilterType.sample_grabber, None)
        sample_grabber = self._filters[FilterType.sample_grabber]
        sample_grabber_cb = SampleGrabberCallback(callback)
        sample_grabber.set_callback(sample_grabber_cb, 1)
        sample_grabber.set_media_type(MediaTypes.Video, MediaSubtypes.RGB24)

    def add_null_render(self):
        """Add a null renderer to the grabber."""
        self._add_filter(FilterType.render, clsids.CLSID_NullRender)

    def add_default_render(self):
        """Add a default renderer to the grabber."""
        self._add_filter(FilterType.render, clsids.CLSID_VideoRendererDefault)

    def add_video_mixing_render(self):
        """Add a default video mixing renderer to the grabber."""
        self._add_filter(FilterType.render, clsids.CLSID_VideoMixingRenderer)

    def add_file_writer_and_muxer(self, filename: Path):
        """Add a file writer to save the image as a video into.

        Args:
            filename (Path): The path of the file to write to.
        """
        extension = Path(filename).suffix.upper()

        mediasubtype = (MediaSubtypes.ASF if extension == ".WMV"
                        else MediaSubtypes.AVI)

        self._recording_format = (RecordingFormat.ASF if extension == ".WMV"
                                  else RecordingFormat.AVI)

        mux, filesink = self._capture_builder.SetOutputFileName(
            GUID(mediasubtype), filename)

        self._filters[FilterType.muxer] = \
            self._filter_factory.build_filter(FilterType.muxer, mux)

    def configure_asf_compressor(self):
        """Define the asf compressor for the grabber."""
        pass
        # asf_config = self.mux.QueryInterface(IConfigAsfWriter)
        # print(asf_config.GetCurrentProfileGuid())
        # profile = asf_config.GetCurrentProfile()

    def prepare_preview_graph(self):
        """Pipe of the video input and the renderer."""
        assert FilterType.video_input in self._filters
        assert FilterType.render in self._filters

        vinput = self._filters[FilterType.video_input]
        renderer = self._filters[FilterType.render]

        # If no sample grabber is defined in the filters
        if FilterType.sample_grabber not in self._filters:
            # Pipe the video input to the renderer
            self._graph_builder.Connect(vinput.get_out(), renderer.get_in())

        else:
            sgrabber = self._filters[FilterType.sample_grabber]

            # Pipe the video input to he sample grabber
            self._graph_builder.Connect(vinput.get_out(), sgrabber.get_in())

            # Pipe the sample grabber to the renderer
            self._graph_builder.Connect(sgrabber.get_out(), renderer.get_in())

            sgrabber.initialize_after_connection()
        self.is_recording = False

    def _get_capture_and_preview_pins(self):
        """Get the pins for capture and preview.

        Returns:
            preview_pin (TYPE): DESCRIPTION.
            capture_pin (TYPE): DESCRIPTION.
        """
        vinput = self._filters[FilterType.video_input]

        preview_pin = vinput.find_pin(PIN_OUT,
                                      category=GUID(PinCategory.Preview))
        capture_pin = vinput.find_pin(PIN_OUT,
                                      category=GUID(PinCategory.Capture))

        if (preview_pin is None) or (capture_pin is None):
            self._add_filter(FilterType.smart_tee, None)

            smart_tee = self._filters[FilterType.smart_tee]

            # Pipe the capture pin or the preview pin with the smart tee
            self._graph_builder.Connect(
                capture_pin if capture_pin else preview_pin,
                smart_tee.get_in())

            # assuming the 1st output pin of the smart tee filter is always the
            # capture one
            capture_pin, preview_pin = smart_tee.out_pins

        return preview_pin, capture_pin

    def prepare_recording_graph(self):
        """Pipe the video input with the muxer and the renderer."""
        # HINT : In theory we could use self._capture_builder.RenderStream,
        # but it is not working when including the video compressor :-(
        assert FilterType.video_input in self._filters
        assert FilterType.render in self._filters
        assert FilterType.muxer in self._filters

        preview_pin, capture_pin = self._get_capture_and_preview_pins()
        mux = self._filters[FilterType.muxer]
        ainput = self._filters[FilterType.audio_input]
        render = self._filters[FilterType.render]

        if self._recording_format == RecordingFormat.ASF:
            # Pipe the video input to the muxer input 1
            self._graph_builder.Connect(capture_pin, mux.get_in(1))

            # Pipe the audio input to the muxer input 0
            self._graph_builder.Connect(ainput.get_out(), mux.get_in(0))

            # Pipe the smart tee with the renderer
            self._graph_builder.Connect(preview_pin, render.get_in())

        else:
            vcompr = self._filters[FilterType.video_compressor]

            # Pipe the video input to the video compressor
            self._graph_builder.Connect(capture_pin, vcompr.get_in())

            # Pipe the video compressor to the muxer
            self._graph_builder.Connect(vcompr.get_out(), mux.get_in())

            # Pipe the smart tee to the renderer
            self._graph_builder.Connect(preview_pin, render.get_in())

            if FilterType.audio_input in self._filters:
                self._graph_builder.Connect(
                    self._filters[FilterType.audio_input].get_out(),
                    self._filters[FilterType.audio_compressor].get_in())
                self._filters[FilterType.muxer].reload_pins()
                # when you connect an input pin of the muxer, an additional
                # input pin is added
                self._graph_builder.Connect(
                    self._filters[FilterType.audio_compressor].get_out(),
                    self._filters[FilterType.muxer].get_in(1))

        self.is_recording = True

    def configure_render(self, handle):
        """Link the rendere to a video window.

        Args:
            handle (TYPE): DESCRIPTION.
        """
        self._filters[FilterType.render].configure_video_window(handle)

    def update_window(self, width: int, height: int):
        """Define the dimension of the video window.

        Args:
            width (int): DESCRIPTION.
            height (int): DESCRIPTION.
        """
        if FilterType.render in self._filters:
            vinput = self._filters[FilterType.video_input]
            img_w, img_h = vinput.get_current_format()

            scale_w = width / img_w
            scale_h = height / img_h
            scale = min(scale_w, scale_h, 1)

            render = self._filters[FilterType.render]
            render.set_window_position(0, 0,
                                       int(img_w * scale), int(img_h * scale))

    def run(self):
        """Launch the media."""
        self._media_control.Run()

    def stop(self):
        """Stop the media."""
        if self._media_control is not None:
            # calling stop without calling prepare
            self._media_control.Stop()
        # if self.video_window is not None:
            # self.video_window.put_Visible(False)
            # self.video_window.put_Owner(0)

    def pause(self):
        """Pause the media."""
        self._media_control.Pause()

    def get_state(self):
        """Get the state of the graph.

        Returns:
            StateGraph: The state of the graph.
        """
        # 0xFFFFFFFF = infinite timeout
        return StateGraph(self._media_control.GetState(0xFFFFFFFF))

    def get_input_devices(self) -> List:
        """Get the video input devices.

        Returns:
            List of Filters: DESCRIPTION.
        """
        return self._system_device_enum.get_available_filters(
            DeviceCategories.VideoInputDevice)

    def get_audio_devices(self):
        """Get the audio input devices.

        Returns:
            List of Filters: DESCRIPTION.
        """
        return self._system_device_enum.get_available_filters(
            DeviceCategories.AudioInputDevice)

    def get_video_compressors(self):
        """Get the video compressors devices.

        Returns:
            List of Filters: DESCRIPTION.
        """
        return self._system_device_enum.get_available_filters(
            DeviceCategories.VideoCompressor)

    def get_audio_compressors(self):
        """Get the audio compressors devices.

        Returns:
            List of Filters: DESCRIPTION.
        """
        return self._system_device_enum.get_available_filters(
            DeviceCategories.AudioCompressor)

    def get_asf_profiles(self):
        """Get the asf profiles.

        Returns:
            List of Filters: DESCRIPTION.
        """
        return self._wm_profile_manager.profiles_names

    def grab_frame(self) -> bool:
        """Call the grab callback function.

        Returns:
            bool: True if a sample grabber is defined.
        """
        if FilterType.sample_grabber in self._filters:
            self._filters[FilterType.sample_grabber].callback.grab_frame()
            return True
        else:
            return False

    def get_input_device(self) -> int:
        """Get the index of the current video input device.

        Returns:
            int: DESCRIPTION.
        """
        return self._filters[FilterType.video_input]

    def remove_filters(self):
        """Remove the existing filters."""
        enum_filters = self._filter_graph.EnumFilters()
        filt, count = enum_filters.Next(1)

        while count > 0:
            self._filter_graph.RemoveFilter(filt)
            enum_filters.Reset()
            filt, count = enum_filters.Next(1)
        self._filters = {}

    def remove_all_filters_but_video_source(self):
        """Remove the existing filters except the video input."""
        video_input = self._filters[FilterType.video_input]
        enum_filters = self._filter_graph.EnumFilters()

        filters_to_delete = []
        filt, count = enum_filters.Next(1)

        while count > 0:
            if filt != video_input.instance:
                filters_to_delete.append(filt)
            filt, count = enum_filters.Next(1)

        for filt in filters_to_delete:
            self._filter_graph.RemoveFilter(filt)

        self._filters = {FilterType.video_input: video_input}

    def print_debug_info(self):
        """Print some debug info of the filter graph."""
        helper = FilterGraphDebugHelper(self._filter_graph)
        helper.print_graph_info()


class FilterGraphDebugHelper:
    """Convenient class for printing some debug info."""

    def __init__(self, filter_graph: FilterGraph):
        """Set the instance of the filter graph.

        Args:
            filter_graph (FilterGraph): The instance of the filter graph.
        """
        self._filter_graph = filter_graph

    def print_graph_info(self):
        """Pretty print some information on the filter graph."""
        enum_filters = self._filter_graph.EnumFilters()
        filt, count = enum_filters.Next(1)

        while count > 0:
            filterName = self.get_filter_name(filt)
            print(f"FILTER {filterName} [{filt}]")

            enum_pins = filt.EnumPins()
            pin, count = enum_pins.Next(1)
            while count > 0:
                pin_name, direction, connected_pin, owner = \
                    self.get_pin_info(pin)
                if connected_pin is not None:
                    connected_pin_name, _, _, connected_filter = \
                        self.get_pin_info(connected_pin)
                    connected_filter_name = \
                        self.get_filter_name(connected_filter)

                print(f" - PIN {pin_name} {'in' if direction == 0 else 'out'}"
                      f" - Connected to: {connected_filter_name} [{pin}]")

                pin, count = enum_pins.Next(1)
            filt, count = enum_filters.Next(1)

    def get_filter_name(self, filter) -> str:
        """Get the name of the filter.

        Args:
            filter (TYPE): DESCRIPTION.

        Returns:
            str: DESCRIPTION.
        """
        filter_info = filter.QueryFilterInfo()
        return wstring_at(filter_info.achName)

    def get_pin_info(self, pin):
        """Get information on a given pin.

        Args:
            pin (TYPE): DESCRIPTION.

        Returns:
            name (TYPE): DESCRIPTION.
            TYPE: DESCRIPTION.
            connected_pin (TYPE): DESCRIPTION.
            owner_filter (TYPE): DESCRIPTION.
        """
        info = pin.QueryPinInfo()
        name = wstring_at(info.achName)
        owner_filter = info.pFilter

        try:
            connected_pin = pin.ConnectedTo()
        except COMError:
            connected_pin = None
        return name, info.dir, connected_pin, owner_filter


class SampleGrabberCallback(COMObject):
    """A default callback for a sample grabber."""

    _com_interfaces_ = [qedit.ISampleGrabberCB]

    def __init__(self, callback):
        """Initialize the callback.

        Args:
            callback (Callable): DESCRIPTION.
        """
        self.callback = callback
        self.cnt = 0
        self.keep_photo = False
        self.image_resolution = None
        super(SampleGrabberCallback, self).__init__()

    def grab_frame(self):
        """Indicate that the image must be kept."""
        self.keep_photo = True

    def SampleCB(self, this, SampleTime, pSample):
        """Sample callback function.

        Args:
            this (TYPE): DESCRIPTION.
            SampleTime (TYPE): DESCRIPTION.
            pSample (TYPE): DESCRIPTION.

        Returns:
            int: DESCRIPTION.
        """
        return 0

    def BufferCB(self, this, SampleTime, pBuffer, BufferLen):
        """Buffer callback function called on grab.

        Args:
            this (TYPE): DESCRIPTION.
            SampleTime (TYPE): DESCRIPTION.
            pBuffer (TYPE): The image as a buffer.
            BufferLen (TYPE): DESCRIPTION.

        Returns:
            int: 0 if no image was grabbed, else None
        """
        if self.keep_photo:
            self.keep_photo = False

            # Convert the buffer to a numpy array
            img = np.ctypeslib.as_array(
                pBuffer,
                shape=(self.image_resolution[1],
                       self.image_resolution[0], 3))
            img = np.flip(np.copy(img), axis=0)
            self.callback(img)
        return 0

    # ALTERNATIVE
    # def BufferCB(self, this, SampleTime, pBuffer, BufferLen):
    #     if self.keep_photo:
    #         self.keep_photo = False
    #         bsize = self.image_resolution[1] *self.image_resolution[0] * 3
    #         img = pBuffer[:bsize]
    #         img = np.reshape(img, (self.image_resolution[1],
    #                                self.image_resolution[0], 3))
    #         img = np.flip(img, axis=0)
    #         self.callback(img)
    #     return 0


def get_moniker_name(moniker):
    """Get the name of the moniker.

    Args:
        moniker (TYPE): DESCRIPTION.

    Returns:
        TYPE: DESCRIPTION.
    """
    property_bag = moniker.BindToStorage(0, 0, IPropertyBag._iid_).\
        QueryInterface(IPropertyBag)
    return property_bag.Read("FriendlyName", pErrorLog=None)


def show_properties(object):
    """Display the properties of an object.

    Args:
        object (TYPE): The object to display the properties.
    """
    try:
        spec_pages = object.QueryInterface(ISpecifyPropertyPages)
        cauuid = spec_pages.GetPages()
        if cauuid.element_count > 0:
            whandle = windll.user32.GetTopWindow(None)
            OleCreatePropertyFrame(
                whandle,
                0, 0, None,
                1, byref(cast(object, LPUNKNOWN)),
                cauuid.element_count, cauuid.elements,
                0, 0, None)
            windll.ole32.CoTaskMemFree(cauuid.elements)
    except COMError:
        pass
