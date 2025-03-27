from typing import TYPE_CHECKING
from magicgui import magic_factory
from magicgui.widgets import Container, PushButton, ComboBox, SpinBox
from typing import List
from importlib.metadata import version

if TYPE_CHECKING:
    import napari
    import pandas

napari_version = tuple(map(int, list(version("napari").split(".")[:2])))


def connect_events(widget):
    """
    Connect widget events to make some visible/invisible depending on others
    """

    def toggle_median_n_widget(event):
        widget.median_n.visible = event

    # Connect events
    widget.apply_median.changed.connect(toggle_median_n_widget)
    # Intial visibility states
    widget.median_n.visible = False
    widget.laser_frequency.label = "Laser Frequency (MHz)"


@magic_factory(
    widget_init=connect_events,
    laser_frequency={
        "step": 0.001,
        "tooltip": (
            "If loaded image has metadata, laser frequency will get automatically updated after run. "
            "Otherwise, manually insert laser frequency here."
        ),
    },
)
def make_flim_phasor_plot(
    image_layer: "napari.layers.Image",
    laser_frequency: float = 40,
    harmonic: int = 1,
    threshold: int = 10,
    apply_median: bool = False,
    median_n: int = 1,
    napari_viewer: "napari.Viewer" = None,
) -> None:
    """Calculate phasor components from FLIM image and plot them.

    Parameters
    ----------
    image_layer : napari.layers.Image
        napari image layer with FLIM data with dimensions (ut, time, z, y, x). microtime must be the first dimention. time and z are optional.
    laser_frequency : float, optional
        laser frequency in MHz. If using '.ptu' or '.sdt' files, this field is filled afterwards from the file metadata. By default 40.
    harmonic : int, optional
        the harmonic to display in the phasor plot, by default 1
    threshold : int, optional
        pixels with summed intensity below this threshold will be discarded, by default 10
    apply_median : bool, optional
        apply median filter to image before phasor calculation, by default False (median_n is ignored)
    median_n : int, optional
        number of iterations of median filter, by default 1
    napari_viewer : napari.Viewer, optional
        napari viewer instance, by default None
    """
    import warnings
    import numpy as np
    import dask.array as da
    import pandas as pd
    from skimage.segmentation import relabel_sequential
    from napari.layers import Labels

    from napari_flim_phasor_plotter.phasor import get_phasor_components
    from napari_flim_phasor_plotter.filters import (
        make_time_mask,
        make_space_mask_from_manual_threshold,
    )
    from napari_flim_phasor_plotter.filters import apply_median_filter
    from napari_flim_phasor_plotter._plotting import PhasorPlotterWidget

    image = image_layer.data
    if "file_type" in image_layer.metadata:
        if (image_layer.metadata["file_type"] == "ptu") and (
            "TTResult_SyncRate" in image_layer.metadata
        ):
            # in MHz
            laser_frequency = image_layer.metadata["TTResult_SyncRate"] * 1e-6
        elif image_layer.metadata["file_type"] == "sdt":
            # in MHz
            laser_frequency = (
                image_layer.metadata["measure_info"]["StopInfo"][
                    "max_sync_rate"
                ][0]
                * 10**-6
            )

    time_mask = make_time_mask(image, laser_frequency)

    space_mask = make_space_mask_from_manual_threshold(image, threshold)

    image = image[time_mask]

    g, s, dc = get_phasor_components(image, harmonic=harmonic)

    if apply_median:
        g = apply_median_filter(g, median_n)
        s = apply_median_filter(s, median_n)

    label_image = np.arange(np.prod(dc.shape)).reshape(dc.shape) + 1
    label_image[~space_mask] = 0
    label_image = relabel_sequential(label_image)[0]

    g_flat_masked = np.ravel(g[space_mask])
    s_flat_masked = np.ravel(s[space_mask])
    t_coords, z_coords, y_coords, x_coords = np.where(space_mask)
    if isinstance(g, da.Array):
        g_flat_masked.compute_chunk_sizes()
        s_flat_masked.compute_chunk_sizes()
    if isinstance(space_mask, da.Array):
        t_coords.compute_chunk_sizes()
        z_coords.compute_chunk_sizes()
        y_coords.compute_chunk_sizes()
        x_coords.compute_chunk_sizes()

    phasor_components = pd.DataFrame(
        {
            "label": np.ravel(label_image[space_mask]),
            "G": g_flat_masked,
            "S": s_flat_masked,
            "pixel_x_coordinates": x_coords,
            "pixel_y_coordinates": y_coords,
            "pixel_z_coordinates": z_coords,
        }
    )
    table = phasor_components
    # Build frame column
    frame = np.arange(dc.shape[0])
    frame = np.repeat(frame, np.prod(dc.shape[1:]))
    table["frame"] = frame[space_mask.ravel()]

    # The layer has to be created here so the plotter can be filled properly
    # below. Overwrite layer if it already exists.
    for layer in napari_viewer.layers:
        if (isinstance(layer, Labels)) & (
            layer.name == "Labelled_pixels_from_" + image_layer.name
        ):
            labels_layer = layer
            labels_layer.data = label_image
            labels_layer.features = table
            break
    else:
        labels_layer = napari_viewer.add_labels(
            label_image,
            name="Labelled_pixels_from_" + image_layer.name,
            features=table,
            scale=image_layer.scale[1:],
            visible=True,
            opacity=0.2,
        )

    # Check if plotter was alrerady added to dock_widgets
    # TODO: avoid using private method access to napari_viewer.window._dock_widgets (will be deprecated)
    with warnings.catch_warnings():
        warnings.simplefilter(action="ignore", category=FutureWarning)
        dock_widgets_names = [
            key for key, value in napari_viewer.window._dock_widgets.items()
        ]
        if (
            "Phasor Plotter Widget (napari-flim-phasor-plotter)"
            not in dock_widgets_names
        ):
            plotter_widget = PhasorPlotterWidget(napari_viewer)
            napari_viewer.window.add_dock_widget(
                plotter_widget,
                name="Phasor Plotter Widget (napari-flim-phasor-plotter)",
            )
        else:
            widgets = napari_viewer.window._dock_widgets[
                "Phasor Plotter Widget (napari-flim-phasor-plotter)"
            ]
            plotter_widget = widgets.findChild(PhasorPlotterWidget)

        # Get labels layer with labelled pixels (labels)
        for choice in plotter_widget.layer_select.choices:
            if choice.name == "Labelled_pixels_from_" + image_layer.name:
                plotter_widget.layer_select.value = choice
                break
        # Set G and S as features to plot (update_axes_list method clears Comboboxes)
        plotter_widget.plot_x_axis.setCurrentIndex(1)
        plotter_widget.plot_y_axis.setCurrentIndex(2)
        plotter_widget.plotting_type.setCurrentIndex(1)
        plotter_widget.log_scale.setChecked(True)
        plotter_widget.frequency = laser_frequency
        plotter_widget.harmonic = harmonic

        # Show parent (PlotterWidget) so that run function can run properly
        plotter_widget.parent().show()
        # Disconnect selector to reset collection of points in plotter
        # (it gets reconnected when 'run' method is run)
        plotter_widget.graphics_widget.selector.disconnect()
        plotter_widget.run(
            features=labels_layer.features,
            plot_x_axis_name=plotter_widget.plot_x_axis.currentText(),
            plot_y_axis_name=plotter_widget.plot_y_axis.currentText(),
            plot_cluster_name=plotter_widget.plot_cluster_id.currentText(),
            redraw_cluster_image=False,
            ensure_full_semi_circle_displayed=True,
        )

        # Update laser frequency spinbox
        # TO DO: access and update widget in a better way
        if (
            "Calculate Phasors (napari-flim-phasor-plotter)"
            in dock_widgets_names
        ):
            widgets = napari_viewer.window._dock_widgets[
                "Calculate Phasors (napari-flim-phasor-plotter)"
            ]
            laser_frequency_spinbox = (
                widgets.children()[4].children()[2].children()[-1]
            )
            # Set precision of spinbox based on number of decimals in laser_frequency
            laser_frequency_spinbox.setDecimals(
                str(laser_frequency)[::-1].find(".")
            )
            laser_frequency_spinbox.setValue(laser_frequency)

    return plotter_widget, labels_layer


@magic_factory
def apply_binning_widget(
    image_layer: "napari.layers.Image",
    bin_size: int = 2,
    binning_3D: bool = True,
) -> "napari.layers.Image":
    """Apply binning to image layer.

    Parameters
    ----------
    image_layer : napari.layers.Image
        napari image layer with FLIM data with dimensions (ut, time, z, y, x).
        microtime must be the first dimention. time and z are optional.
    bin_size : int, optional
        bin kernel size, by default 2
    binning_3D : bool, optional
        if True, bin in 3D, otherwise bin each slice in 2D, by default True

    Returns
    -------
    image_layer_binned : napari.layers.Image
        binned layer
    """
    import numpy as np
    from napari.layers import Image
    from napari_flim_phasor_plotter.filters import apply_binning

    # Warning! This loads the image as a numpy array
    # TODO: add support for dask arrays
    image = np.asarray(image_layer.data)
    image_binned = apply_binning(image, bin_size, binning_3D)
    # Add dimensions if needed, to make it 5D (ut, time, z, y, x)
    while len(image_binned.shape) < 5:
        image_binned = np.expand_dims(image_binned, axis=0)
    return Image(
        image_binned,
        scale=image_layer.scale,
        name=image_layer.name + f" binned {bin_size}",
    )


def manual_label_extract(
    cluster_labels_layer: "napari.layers.Labels", label_number: int = 1
) -> "napari.layers.Labels":
    """Extracts single label from labels layer

    Parameters
    ----------
    cluster_labels_layer : napari.layers.Labels
        layer with labelled regions based on clusters
    label_number : int, optional
        chosen label number to be extracted, by default 1

    Returns
    -------
    napari.layers.Labels
        layer with single label
    """
    import numpy as np
    from napari.layers import Labels
    from napari.utils import DirectLabelColormap

    unitary_dims = [
        i
        for i, size in enumerate(np.asarray(cluster_labels_layer.data).shape)
        if size == 1
    ]
    labels_data = np.squeeze(np.asarray(cluster_labels_layer.data).copy())
    labels_data[labels_data != label_number] = 0
    if napari_version >= (0, 5):
        colormap = cluster_labels_layer.colormap
    else:
        label_color = cluster_labels_layer.color
        colormap = DirectLabelColormap(color_dict=label_color)
    new_scale = np.array(
        [
            scale
            for i, scale in enumerate(cluster_labels_layer.scale)
            if i not in unitary_dims
        ]
    )
    return Labels(
        labels_data,
        colormap=colormap,
        name=f"Cluster Label #{label_number}",
        scale=new_scale,
    )


def get_n_largest_cluster_labels(
    features_table: "pandas.DataFrame",
    n: int = 1,
    clustering_id: str = "MANUAL_CLUSTER_ID",
) -> List[int]:
    """Get the labels of the n largest clusters in a features table

    Parameters
    ----------
    features_table : pd.DataFrame
        table of features
    n : int, optional
        number of clusters to return, by default 1
    clustering_id : str, optional
        cluster id column name, by default 'MANUAL_CLUSTER_ID'

    Returns
    -------
    List[int]
        list of cluster labels
    """
    import numpy as np

    unique_cluster_ids, counts = np.unique(
        features_table[clustering_id], return_counts=True
    )
    sorted_cluster_ids = (
        unique_cluster_ids[np.argsort(counts)[::-1]] + 1
    )  # noise clusters become 0 and unselected become 1 (matching labels layer)
    sorted_cluster_ids = sorted_cluster_ids[
        sorted_cluster_ids > 0
    ]  # remove noise cluster (0)
    if "MANUAL" in clustering_id:
        sorted_cluster_ids = sorted_cluster_ids[
            sorted_cluster_ids != 1
        ]  # remove unselected clusters when selection is manual

    return sorted_cluster_ids[:n].tolist()


def split_n_largest_cluster_labels(
    labels_layer: "napari.layers.Labels",
    clusters_labels_layer: "napari.layers.Labels",
    clustering_id: str,
    n: int = 1,
) -> List["napari.layers.Labels"]:
    """Split the n largest clusters from a labels layer inot new layers

    Parameters
    ----------
    labels_layer : napari.layers.Labels
        labels layer with features table
    clusters_labels_layer : napari.layers.Labels
        labels layer with clusters
    clustering_id : str
        cluster id column name
    n : int, optional
        number of clusters to extract, by default 1

    Returns
    -------
    List[napari.layers.Labels]
        list of labels layers
    """
    features_table = labels_layer.features
    cluster_labels = get_n_largest_cluster_labels(
        features_table, n, clustering_id
    )
    cluster_individual_labels_layer_list = []
    for label in cluster_labels:
        cluster_individual_labels_layer_list.append(
            manual_label_extract(clusters_labels_layer, label)
        )

    return cluster_individual_labels_layer_list


class Split_N_Largest_Cluster_Labels(Container):
    """Widget to split the n largest clusters from a labels layer"""

    from napari import layers as napari_layers

    input_layer_types = (napari_layers.Labels,)

    def __init__(self, viewer: "napari.viewer.Viewer"):
        from napari import layers as napari_layers

        self._viewer = viewer

        # Create widgets
        self._labels_layer_combobox = ComboBox(
            choices=self._get_layers,
            label="Labels Layer with Table:",
            tooltip="Labels layer generated by Calculate Phasors widget",
        )
        self._viewer.layers.events.inserted.connect(
            self._labels_layer_combobox.reset_choices
        )
        self._viewer.layers.events.removed.connect(
            self._labels_layer_combobox.reset_choices
        )

        self._clusters_labels_layer_combobox = ComboBox(
            choices=self._get_layers,
            label="Labels Layer with Clusters Labels:",
            tooltip="Labels layer generated by Manual clustering or applying a clustering algorithm",
        )
        self._viewer.layers.events.inserted.connect(
            self._clusters_labels_layer_combobox.reset_choices
        )
        self._viewer.layers.events.removed.connect(
            self._clusters_labels_layer_combobox.reset_choices
        )

        self._n_spinbox = SpinBox(
            min=1,
            step=1,
            label="Number of clusters to extract:",
            tooltip="From largest to smallest",
        )

        self._clustering_id_combobox = ComboBox(
            choices=self._get_valid_clusters_column_names,
            label="Clustering ID:",
            tooltip="Column name of the clustering id in the features table",
        )
        self._labels_layer_combobox.changed.connect(
            self._clustering_id_combobox.reset_choices
        )
        # Connect all labels layer data change events to reset clustering id choices
        # to ensure cluster id is up-to-date
        for layer in self._viewer.layers:
            if isinstance(layer, napari_layers.Labels):
                layer.events.data.connect(
                    self._clustering_id_combobox.reset_choices
                )

        # Create cut button
        self._run_btn = PushButton(label="Run")
        self._run_btn.clicked.connect(self._on_run_clicked)

        # Assemble widgets into container
        super().__init__(
            widgets=[
                self._labels_layer_combobox,
                self._clusters_labels_layer_combobox,
                self._n_spinbox,
                self._clustering_id_combobox,
                self._run_btn,
            ]
        )

    def _get_layers(self, widget):
        """Get layers of a certain type

        Returns
        -------
        List[napari.layers.Layer]
            list of layers
        """
        return [
            layer
            for layer in self._viewer.layers
            if isinstance(layer, self.input_layer_types)
        ]

    def _get_valid_clusters_column_names(self, widget):
        """Get valid column names for clustering id

        Returns
        -------
        List[str]
            list of column names
        """
        if self._labels_layer_combobox.value is None:
            return []
        features_table = self._labels_layer_combobox.value.features
        return [
            column_name
            for column_name in features_table.columns
            if "_CLUSTER_ID" in column_name
        ]

    def _on_run_clicked(self):
        """Run the widget

        Creates new labels layers for each of the n largest clusters
        if entries are valid
        """
        cluster_individual_labels_layer_list = split_n_largest_cluster_labels(
            labels_layer=self._labels_layer_combobox.value,
            clusters_labels_layer=self._clusters_labels_layer_combobox.value,
            clustering_id=self._clustering_id_combobox.value,
            n=self._n_spinbox.value,
        )
        # Add new layers to viewer
        for layer in cluster_individual_labels_layer_list:
            self._viewer.add_layer(layer)


def smooth_cluster_mask(
    cluster_mask_layer: "napari.layers.Labels",
    fill_area_px: int = 64,
    smooth_radius: int = 3,
) -> "napari.layers.Labels":
    """Smooths a mask from a labels layer with morphological operations

    Parameters
    ----------
    cluster_mask_layer : napari.layers.Labels
        labels layer with cluster mask
    fill_area_px : int, optional
        threshold for area to fill, by default 64
    smooth_radius : int, optional
        radius of morphological operations (isotropic closing and opening), by default 3

    Returns
    -------
    napari.layers.Labels
        layer with smoothed labels
    """
    from skimage import morphology
    import numpy as np
    from napari.layers import Labels
    from napari.utils import DirectLabelColormap

    unitary_dims = [
        i
        for i, size in enumerate(np.asarray(cluster_mask_layer.data).shape)
        if size == 1
    ]
    labels_data = np.squeeze(np.asarray(cluster_mask_layer.data))
    # Fill holes based on area threshold
    labels_data = morphology.area_closing(labels_data, fill_area_px)
    # Connect nearby labels
    labels_data = morphology.isotropic_closing(labels_data, smooth_radius)
    # Remove small objects
    labels_data = morphology.isotropic_opening(labels_data, smooth_radius)
    # Restore label number
    labels_data = (
        labels_data.astype(cluster_mask_layer.data.dtype)
        * cluster_mask_layer.data.max()
    )
    if napari_version >= (0, 5):
        colormap = cluster_mask_layer.colormap
    else:
        label_color = cluster_mask_layer.color
        colormap = DirectLabelColormap(color_dict=label_color)
    new_scale = np.array(
        [
            scale
            for i, scale in enumerate(cluster_mask_layer.scale)
            if i not in unitary_dims
        ]
    )
    return Labels(
        labels_data,
        colormap=colormap,
        scale=new_scale,
        name=cluster_mask_layer.name + " smoothed",
    )
