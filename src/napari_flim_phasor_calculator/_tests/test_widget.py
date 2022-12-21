from napari_flim_phasor_calculator._widget import make_flim_phasor_plot
from napari_flim_phasor_calculator._synthetic import make_synthetic_flim_data
from napari_flim_phasor_calculator._synthetic import create_time_array

# make_napari_viewer is a pytest fixture that returns a napari viewer object
# capsys is a pytest fixture that captures stdout and stderr output streams
def test_make_flim_phasor_plot(make_napari_viewer, capsys):
    viewer = make_napari_viewer()
    laser_frequency = 40 # MHz
    amplitude = 1
    tau_list = [0.1, 0.2, 0.5, 1, 2, 5, 10, 25, 40] # ns
    number_of_time_points = 1000
    
    time_array = create_time_array(laser_frequency, number_of_time_points)
    flim_data = make_synthetic_flim_data(time_array, amplitude, tau_list)
    flim_data = flim_data.reshape(number_of_time_points, 3, 3)
    
    layer = viewer.add_image(flim_data, rgb = False)

    # this time, our widget will be a MagicFactory or FunctionGui instance
    my_widget = make_flim_phasor_plot()

    # if we "call" this object, it'll execute our function
    my_widget()
    
    labels_layer = viewer.layers[-1]
    
    assert len(viewer.layers) == 2
    assert labels_layer.features.shape == (9, 3)
