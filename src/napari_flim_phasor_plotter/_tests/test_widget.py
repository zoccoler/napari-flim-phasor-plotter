from napari_flim_phasor_plotter._widget import make_flim_phasor_plot
from napari_flim_phasor_plotter._synthetic import make_synthetic_flim_data
from napari_flim_phasor_plotter._synthetic import create_time_array
import numpy as np
import pandas as pd

# make_napari_viewer is a pytest fixture that returns a napari viewer object
# capsys is a pytest fixture that captures stdout and stderr output streams

# Global inputs
laser_frequency = 40  # MHz
amplitude = 1
tau_list = [0.1, 0.2, 0.5, 1, 2, 5, 10, 25, 40]  # ns
# Obs: after running calculate phasors with default thresholding (10), 0.1 and 0.2 associated pixels are excluded/masked out because they end up with low photon budget (summed intensity < 10) given the low amplitude and fast decay

table = pd.DataFrame(
    {
        "label": [1, 2, 3, 4, 5, 6, 7],
        "G": [
            0.984806,
            0.941213,
            0.799235,
            0.388781,
            0.137519,
            0.025144,
            0.010088,
        ],
        "S": [
            0.120760,
            0.233658,
            0.399003,
            0.485904,
            0.342826,
            0.154997,
            0.098370,
        ],
        "pixel_x_coordinates": [2, 0, 1, 2, 0, 1, 2],
        "pixel_y_coordinates": [0, 1, 1, 1, 2, 2, 2],
        "pixel_z_coordinates": [0, 0, 0, 0, 0, 0, 0],
        "frame": [0, 0, 0, 0, 0, 0, 0],
    }
)

labelled_pixels_masked = np.array(
    [
        [
            [
                [
                    0,
                    0,
                    1,
                ],  # 0 represents masked pixels after default thresholding (10)
                [2, 3, 4],
                [5, 6, 7],
            ]
        ]
    ]
)

phasor_clusters_labels = np.array(
    [
        [
            [
                [0, 0, 2],  # 0 represents noise or masked pixels
                [1, 1, 2],  # 1 represents not selected pixels
                [
                    3,
                    3,
                    3,
                ],  # 2 and 3 represent the first 2 selected clusters labels (in table they are 1 and 2)
            ]
        ]
    ]
)
# Manual clusters column contains phasor cluster labels, where labelled pixels are present, minus 1 because 0 is reserved for noise clusters and 1 for not selected pixels
manual_clusters_column = pd.Series(
    phasor_clusters_labels[labelled_pixels_masked > 0] - 1,
    name="MANUAL_CLUSTER_ID",
    index=table.index,
)
table_with_clusters = pd.concat([table, manual_clusters_column], axis=1)


def test_make_flim_phasor_plot_and_plotter(make_napari_viewer, capsys):
    # Inputs for manual selection
    input_selection_vertices = np.array(
        [
            [0.940, 0.23],
            [0.940, 0.24],
            [0.945, 0.24],
            [0.945, 0.23],
        ]
    )  # square vertices with G and S coordinates around 1 ns
    # Expected output array after manual selection
    output_selected_cluster_labels = np.array(
        [
            [
                [
                    [0, 0, 0],
                    [2, 0, 0],
                    [0, 0, 0],
                ]
            ]
        ]
    )

    # Test make_flim_phasor_plot
    viewer = make_napari_viewer()

    number_of_time_points = 1000

    time_array = create_time_array(laser_frequency, number_of_time_points)
    flim_data = make_synthetic_flim_data(time_array, amplitude, tau_list)
    flim_data = flim_data.reshape(number_of_time_points, 3, 3)
    flim_data = np.expand_dims(
        flim_data, axis=[1, 2]
    )  # add unitary time and z dimensions

    layer = viewer.add_image(flim_data, rgb=False)

    # create the widget
    my_widget = make_flim_phasor_plot()

    # execute function
    plotter_widget, labels_layer = my_widget()
    # Check if the plotter widget was created
    assert plotter_widget is not None
    # Check if outputs match expected values
    assert len(viewer.layers) == 2
    assert list(labels_layer.features.columns) == list(table.columns)
    assert labels_layer.features.shape == (7, 7)
    assert labels_layer.name.startswith("Labelled_pixels_from_")
    assert np.allclose(
        labels_layer.features.values, table.values, rtol=0, atol=1e-5
    )

    # Test plotter widget options and selection

    # Plot tau lines
    plotter_widget.tau_lines_line_edit_widget.setText("0.1, 1")
    plotter_widget.tau_lines_button.click()

    # # Select region around 1 ns
    plotter_widget.graphics_widget.selector.onselect(input_selection_vertices)

    # # Check if the selected cluster image is displayed
    assert len(viewer.layers) == 3
    phasor_clusters_layer = viewer.layers[-1]
    assert phasor_clusters_layer.name.startswith("Phasor_clusters_from_")
    assert np.allclose(
        phasor_clusters_layer.data,
        output_selected_cluster_labels,
        rtol=0,
        atol=1e-5,
    )


def test_manual_label_extract():
    from napari_flim_phasor_plotter._widget import manual_label_extract
    from napari.layers import Labels

    # Inputs
    selected_label = 2
    # Expected output array
    output_selected_cluster_labels = np.array(
        [
            [0, 0, 2],
            [0, 0, 2],
            [0, 0, 0],
        ]
    )

    labels_layer = Labels(phasor_clusters_labels)
    selected_label_layer = manual_label_extract(labels_layer, selected_label)

    assert (
        selected_label_layer.data.shape == output_selected_cluster_labels.shape
    )  # squeeze dimensions to match other processing tools
    assert np.array_equal(
        selected_label_layer.data, output_selected_cluster_labels
    )


def test_get_n_largest_cluster_labels():
    from napari_flim_phasor_plotter._widget import get_n_largest_cluster_labels

    # Input
    number_of_clusters = 2
    # Expected outputs
    expected_list_of_cluster_labels = [
        3,
        2,
    ]  # lergest cluster is 3, second largest is 2 (1 represents not selected pixels)

    list_of_cluster_labels = get_n_largest_cluster_labels(
        table_with_clusters, number_of_clusters
    )

    assert len(list_of_cluster_labels) == number_of_clusters
    assert list(list_of_cluster_labels) == expected_list_of_cluster_labels


def test_Split_N_Largest_Cluster_Labels(make_napari_viewer):
    from napari_flim_phasor_plotter._widget import (
        Split_N_Largest_Cluster_Labels,
    )
    from napari.layers import Labels

    viewer = make_napari_viewer()
    # Inputs
    labelled_pixels_layer = Labels(
        labelled_pixels_masked, features=table_with_clusters
    )
    phasor_clusters_layer = Labels(phasor_clusters_labels)
    number_of_clusters = 2
    clustering_id = manual_clusters_column.name
    # Expected output arrays
    largest_cluster_labels = np.array(
        [
            [0, 0, 0],
            [0, 0, 0],
            [3, 3, 3],
        ]
    )
    second_largest_cluster_labels = np.array(
        [
            [0, 0, 2],
            [0, 0, 2],
            [0, 0, 0],
        ]
    )

    # Add layers to viewer
    viewer.add_layer(labelled_pixels_layer)
    viewer.add_layer(phasor_clusters_layer)
    n_layers_in_viewer = 2
    # Set widget options
    split_n_largest_widget = Split_N_Largest_Cluster_Labels(viewer)
    split_n_largest_widget._labels_layer_combobox.value = labelled_pixels_layer
    split_n_largest_widget._clusters_labels_layer_combobox.value = (
        phasor_clusters_layer
    )
    split_n_largest_widget._n_spinbox.value = number_of_clusters
    split_n_largest_widget._clustering_id_combobox.value = clustering_id
    # Run widget
    split_n_largest_widget._on_run_clicked()
    # Check new layers are created
    assert len(viewer.layers) == n_layers_in_viewer + number_of_clusters
    # Check that first layer created contains only largest cluster label
    assert np.array_equal(viewer.layers[-2].data, largest_cluster_labels)
    # Check that second layer created contain only second largest cluster label
    assert np.array_equal(
        viewer.layers[-1].data, second_largest_cluster_labels
    )
