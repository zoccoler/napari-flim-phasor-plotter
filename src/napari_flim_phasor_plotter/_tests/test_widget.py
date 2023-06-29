from napari_flim_phasor_plotter._widget import make_flim_phasor_plot
from napari_flim_phasor_plotter._synthetic import make_synthetic_flim_data
from napari_flim_phasor_plotter._synthetic import create_time_array
import numpy as np
import pandas as pd
# make_napari_viewer is a pytest fixture that returns a napari viewer object
# capsys is a pytest fixture that captures stdout and stderr output streams


def test_make_flim_phasor_plot(make_napari_viewer, capsys):
    output_table = pd.DataFrame({
        'label': [1, 2, 3, 4, 5, 6, 7],
        'G': [0.984806, 0.941213, 0.799235, 0.388781, 0.137519, 0.025144, 0.010088],
        'S': [0.120760, 0.233658, 0.399003, 0.485904, 0.342826, 0.154997, 0.098370],
        'frame': [0, 1, 1, 1, 2, 2, 2]
    })

    viewer = make_napari_viewer()
    laser_frequency = 40  # MHz
    amplitude = 1
    tau_list = [0.1, 0.2, 0.5, 1, 2, 5, 10, 25, 40]  # ns
    number_of_time_points = 1000

    time_array = create_time_array(laser_frequency, number_of_time_points)
    flim_data = make_synthetic_flim_data(time_array, amplitude, tau_list)
    flim_data = flim_data.reshape(number_of_time_points, 3, 3)

    layer = viewer.add_image(flim_data, rgb=False)

    # this time, our widget will be a MagicFactory or FunctionGui instance
    my_widget = make_flim_phasor_plot()

    # if we "call" this object, it'll execute our function
    my_widget()

    labels_layer = viewer.layers[-1]

    assert len(viewer.layers) == 2
    assert list(labels_layer.features.columns) == ['label', 'G', 'S', 'frame']
    assert labels_layer.features.shape == (7, 4)
    assert np.allclose(labels_layer.features.values,
                       output_table.values, rtol=0, atol=1e-5)
