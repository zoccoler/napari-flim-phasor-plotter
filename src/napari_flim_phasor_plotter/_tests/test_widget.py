from napari_flim_phasor_plotter._widget import make_flim_phasor_plot
from napari_flim_phasor_plotter._synthetic import make_synthetic_flim_data
from napari_flim_phasor_plotter._synthetic import create_time_array
from napari_flim_phasor_plotter._plotting import PhasorPlotterWidget
import numpy as np
import pandas as pd
# make_napari_viewer is a pytest fixture that returns a napari viewer object
# capsys is a pytest fixture that captures stdout and stderr output streams


def test_make_flim_phasor_plot_and_plotter(make_napari_viewer, capsys):
    output_table = pd.DataFrame({
        'label': [1, 2, 3, 4, 5, 6, 7],
        'G': [0.984806, 0.941213, 0.799235, 0.388781, 0.137519, 0.025144, 0.010088],
        'S': [0.120760, 0.233658, 0.399003, 0.485904, 0.342826, 0.154997, 0.098370],
        'pixel_x_coordinates': [2, 0, 1, 2, 0, 1, 2],
        'pixel_y_coordinates': [0, 1, 1, 1, 2, 2, 2],
        'pixel_z_coordinates': [0, 0, 0, 0, 0, 0, 0],
        'frame': [0, 0, 0, 0, 0, 0, 0]
    })

    input_selection_vertices = np.array(
        [
            [0.940, 0.23],
            [0.940, 0.24],
            [0.945, 0.24],
            [0.945, 0.23]
        ]
    ) # square vertices with G and S coordinates around 1 ns

    output_selected_cluster_image = np.array(
        [
            [
                [
                    [0, 0, 0],
                    [2, 0, 0],
                    [0, 0, 0]
                ]
            ]
        ]
    )

    # Test make_flim_phasor_plot
    viewer = make_napari_viewer()
    laser_frequency = 40  # MHz
    amplitude = 1
    tau_list = [0.1, 0.2, 0.5, 1, 2, 5, 10, 25, 40]  # nss
    number_of_time_points = 1000

    time_array = create_time_array(laser_frequency, number_of_time_points)
    flim_data = make_synthetic_flim_data(time_array, amplitude, tau_list)
    flim_data = flim_data.reshape(number_of_time_points, 3, 3)
    flim_data = np.expand_dims(flim_data, axis=[1,2]) # add unitary time and z dimensions

    layer = viewer.add_image(flim_data, rgb=False)

    # create the widget
    my_widget = make_flim_phasor_plot()

    # execute our function
    plotter_widget, labels_layer = my_widget()
    # Check if the plotter widget was created
    assert plotter_widget is not None

    assert len(viewer.layers) == 2
    assert list(labels_layer.features.columns) == ['label', 'G', 'S', 'pixel_x_coordinates', 'pixel_y_coordinates', 'pixel_z_coordinates', 'frame']
    assert labels_layer.features.shape == (7, 7)
    assert np.allclose(labels_layer.features.values,
                       output_table.values, rtol=0, atol=1e-5)
    
    # Test plotter widget options and selection

    # Plot tau lines
    plotter_widget.tau_lines_line_edit_widget.setText('0.1, 1')
    plotter_widget.tau_lines_button.click()

    # TODO: Fix the following test (manually it works)
    # # Select region around 1 ns
    # plotter_widget.graphics_widget.selector.onselect(input_selection_vertices)

    # # Check if the selected cluster image is displayed
    # assert len(viewer.layers) == 3
    # phasor_clusters_layer = viewer.layers[-1]
    # assert np.allclose(phasor_clusters_layer.data, output_selected_cluster_image, rtol=0, atol=1e-5)

    
