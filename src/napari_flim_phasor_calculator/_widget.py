"""
This module is an example of a barebones QWidget plugin for napari

It implements the Widget specification.
see: https://napari.org/stable/plugins/guides.html?#widgets

Replace code below according to your needs.
"""
from typing import TYPE_CHECKING

from magicgui import magic_factory
from napari.types import LayerDataTuple
from napari.layers import Image
from napari import Viewer
import numpy as np
import pandas as pd
# import napari_clusters_plotter


from phasor import get_phasor_components
from filters import make_time_mask, make_space_mask_from_manual_threshold
from filters import apply_median_filter
from _plotting import PhasorPlotterWidget

if TYPE_CHECKING:
    import napari



def connect_events(widget):
    def toggle_median_n_widget(event):
        widget.median_n.visible = event
    # Connect events
    widget.apply_median.changed.connect(toggle_median_n_widget)
    # Intial visibility states
    widget.median_n.visible = False

@magic_factory(widget_init=connect_events)
def make_flim_label_layer(image_layer : Image,
                          harmonic : int = 1,
                          threshold : int = 0,
                          apply_median : bool = False,
                          median_n : int = 1,
                          napari_viewer : Viewer = None) -> LayerDataTuple:
    from skimage.segmentation import relabel_sequential
    image = image_layer.data
    laser_frequency = image_layer.metadata['TTResult_SyncRate'] *1E-6 #MHz
    
    time_mask = make_time_mask(image, laser_frequency)
    
    space_mask = make_space_mask_from_manual_threshold(image, threshold)
    
    image = image[time_mask]
    
    if apply_median:
        image = apply_median_filter(image, median_n)
    
    g, s, dc = get_phasor_components(image, harmonic = harmonic)

    label_image = np.arange(dc.shape[0]*dc.shape[1]).reshape(dc.shape) + 1
    label_image[~space_mask] = 0
    label_image = relabel_sequential(label_image)[0]

    phasor_components = {'label': np.ravel(label_image[space_mask]), 
                         'G': np.ravel(g[space_mask]),
                         'S': np.ravel(s[space_mask])}
    table = pd.DataFrame(phasor_components)
    
    # Check if plotter was alrerady added to dock_widgets
    dock_widgets_names = [key for key, valye in napari_viewer.window._dock_widgets.items()]
    if 'Plotter Widget' not in dock_widgets_names:
        plotter_widget = PhasorPlotterWidget(napari_viewer)
        napari_viewer.window.add_dock_widget(plotter_widget, name = 'Plotter Widget')
        # If we were to use the original plotter, we could add it as below
        # _, plotter_widget = napari_viewer.window.add_plugin_dock_widget(
        #     'napari-clusters-plotter',
        #     widget_name='Plotter Widget')
        plotter_widget.plot_x_axis.setCurrentText('G')
        plotter_widget.plot_y_axis.setCurrentText('S')
        plotter_widget.update_axes_list() 
    return (label_image, {'name' : 'Label_' + image_layer.name,
                          'features' : table}, 'labels')


