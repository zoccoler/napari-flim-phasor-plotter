"""
This module is an example of a barebones QWidget plugin for napari

It implements the Widget specification.
see: https://napari.org/stable/plugins/guides.html?#widgets

Replace code below according to your needs.
"""
from typing import TYPE_CHECKING

from magicgui import magic_factory
from qtpy.QtWidgets import QHBoxLayout, QPushButton, QWidget
from napari.types import ImageData, LayerDataTuple
import numpy as np
import pandas as pd

if TYPE_CHECKING:
    import napari

# Uses the `autogenerate: true` flag in the plugin manifest
# to indicate it should be wrapped as a magicgui to autogenerate
# a widget.

def get_phasor_components(flim_data, harmonic=1):
    '''
    Calculate phasor components G and S from the fourier transform
    '''
    import numpy as np
    flim_data_fft = np.fft.fft(flim_data, axis=0)
    dc = flim_data_fft[0].real
    # change the zeros to the img average
    # dc = np.where(dc != 0, dc, int(np.mean(dc)))
    dc = np.where(dc != 0, dc, 1)
    g = flim_data_fft[harmonic].real
    g = g / dc
    s = abs(flim_data_fft[harmonic].imag)
    s /= dc
    return g, s, dc

def create_time_array(frequency, n_points=100):
    '''
    Create time array from laser frequency
    
    Parameters
    ----------
    frequency: float
        Frquency of the pulsed laser (in MHz)
    n_points: int, optional
        The number of samples collected between each aser shooting
    Returns
    -------
    time_array : array
        Time array (in nanoseconds)
    '''
    import numpy as np
    time_window = 1 / (frequency * 10**6)
    time_window_ns = time_window * 10**9 # in nanoseconds
    time_step = time_window_ns / n_points # ns
    array = np.arange(0, n_points)
    time_array = array * time_step
    return time_array


def make_flim_label_layer(image : ImageData, laser_frequency : float, harmonic : int = 1, threshold : int = 0, apply_median : bool = False, viewer=None) -> LayerDataTuple:
    
    # create time array based on laser frequency
    time_array = create_time_array(laser_frequency, n_points = image.shape[0])
    time_step = time_array[1]
    # choose starting index based on maximum value of image histogram
    heights, bin_edges = np.histogram(np.ravel(np.argmax(image, axis=0) * time_step), bins=time_array)
    start_index = np.argmax(heights[1:]) + 1
    
    time_mask = time_array >= time_array[start_index]
    
    g, s, dc = get_phasor_components(image[time_mask], harmonic = harmonic)

    label_image = np.arange(dc.shape[0]*dc.shape[1]).reshape(dc.shape) + 1

    phasor_components = {'label': np.ravel(label_image), 'G': np.ravel(g), 'S': np.ravel(s)}
    table = pd.DataFrame(phasor_components)
    
    
    return (label_image, {'features' : table}, 'labels')

def example_function_widget(img_layer: "napari.layers.Image"):
    print(f"you have selected {img_layer}")
