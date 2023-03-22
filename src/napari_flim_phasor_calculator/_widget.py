from typing import TYPE_CHECKING

from magicgui import magic_factory
from napari.layers import Image, Labels
from napari import Viewer
import numpy as np
import pandas as pd
import dask.array as da

from .phasor import get_phasor_components
from .filters import make_time_mask, make_space_mask_from_manual_threshold
from .filters import apply_median_filter
from ._plotting import PhasorPlotterWidget

if TYPE_CHECKING:
    import napari


def connect_events(widget):
    '''
    Connect widget events to make some visible/invisible depending on others
    '''
    def toggle_median_n_widget(event):
        widget.median_n.visible = event
    # Connect events
    widget.apply_median.changed.connect(toggle_median_n_widget)
    # Intial visibility states
    widget.median_n.visible = False
    widget.laser_frequency.label = 'Laser Frequency (MHz)'


@magic_factory(widget_init=connect_events,
               laser_frequency={'step': 0.001,
                                'tooltip': ('If loaded image has metadata, laser frequency will get automatically updated after run. '
                                            'Otherwise, manually insert laser frequency here.')})
def make_flim_phasor_plot(image_layer: Image,
                          laser_frequency: float = 40,
                          harmonic: int = 1,
                          threshold: int = 0,
                          apply_median: bool = False,
                          median_n: int = 1,
                          napari_viewer: Viewer = None) -> None:
    from skimage.segmentation import relabel_sequential
    image = image_layer.data
    if 'file_type' in image_layer.metadata:
        if (image_layer.metadata['file_type'] == 'ptu') and ('TTResult_SyncRate' in image_layer.metadata):
            laser_frequency = image_layer.metadata['TTResult_SyncRate'] * 1E-6  # MHz
        elif image_layer.metadata['file_type'] == 'sdt':
            laser_frequency = image_layer.metadata['measure_info']['StopInfo']['max_sync_rate'] * 10 ** -6  # in MHz

    time_mask = make_time_mask(image, laser_frequency)

    space_mask = make_space_mask_from_manual_threshold(image, threshold)

    image = image[time_mask]

    if apply_median:
        image = apply_median_filter(image, median_n)

    g, s, dc = get_phasor_components(image, harmonic=harmonic)

    label_image = np.arange(np.prod(dc.shape)).reshape(dc.shape) + 1
    label_image[~space_mask] = 0
    label_image = relabel_sequential(label_image)[0]

    g_flat_masked = np.ravel(g[space_mask])
    s_flat_masked = np.ravel(s[space_mask])
    if isinstance(g, da.Array):
        g_flat_masked.compute_chunk_sizes()
        s_flat_masked.compute_chunk_sizes()

    phasor_components = pd.DataFrame({
        'label': np.ravel(label_image[space_mask]),
        'G': g_flat_masked,
        'S': s_flat_masked})
    table = phasor_components
    # Build frame column
    frame = np.arange(dc.shape[0])
    frame = np.repeat(frame, np.prod(dc.shape[1:]))
    table['frame'] = frame[space_mask.ravel()]

    # The layer has to be created here so the plotter can be filled properly
    # below. Overwrite layer if it already exists.
    for layer in napari_viewer.layers:
        if (isinstance(layer, Labels)) & (layer.name == 'Label_' + image_layer.name):
            labels_layer = layer
            labels_layer.data = label_image
            labels_layer.features = table
            break
    else:
        labels_layer = napari_viewer.add_labels(label_image,
                                                name='Label_' + image_layer.name,
                                                features=table)

    # Check if plotter was alrerady added to dock_widgets
    # TO DO: avoid using private method access to napari_viewer.window._dock_widgets (will be deprecated)
    dock_widgets_names = [key for key, value in napari_viewer.window._dock_widgets.items()]
    if 'Plotter Widget' not in dock_widgets_names:
        plotter_widget = PhasorPlotterWidget(napari_viewer)
        napari_viewer.window.add_dock_widget(plotter_widget, name='Plotter Widget')
    else:
        widgets = napari_viewer.window._dock_widgets['Plotter Widget']
        plotter_widget = widgets.findChild(PhasorPlotterWidget)

    # UPDATE to line below once clusters_plotter updates with support to other layers
    # plotter_widget.layer_select.value = plotter_widget.layer_select.choices[-1]  # Set layer on top (labels)
    plotter_widget.labels_select.value = plotter_widget.labels_select.choices[-1]  # Set layer on top (labels)
    # Set G and S as features to plot (update_axes_list method clears Comboboxes)
    plotter_widget.plot_x_axis.setCurrentIndex(1)
    plotter_widget.plot_y_axis.setCurrentIndex(2)
    # Show parent (PlotterWidget) so that run function can run properly
    plotter_widget.parent().show()
    # Disconnect selector to reset collection of points in plotter
    # (it gets reconnected when 'run' method is run)
    plotter_widget.graphics_widget.selector.disconnect()
    plotter_widget.run(labels_layer.features,
                       plotter_widget.plot_x_axis.currentText(),
                       plotter_widget.plot_y_axis.currentText())

    # Update laser frequency spinbox
    # TO DO: access and update widget in a better way
    if 'Make FLIM Phasor Plot (napari-flim-phasor-calculator)' in dock_widgets_names:
        widgets = napari_viewer.window._dock_widgets['Make FLIM Phasor Plot (napari-flim-phasor-calculator)']
        laser_frequency_spinbox = widgets.children()[4].children()[2].children()[-1]
        # Set precision of spinbox based on number of decimals in laser_frequency
        laser_frequency_spinbox.setDecimals(str(laser_frequency)[::-1].find('.'))
        laser_frequency_spinbox.setValue(laser_frequency)

    return
