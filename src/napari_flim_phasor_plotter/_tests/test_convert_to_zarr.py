from napari_flim_phasor_plotter._io import convert_to_zarr
from napari_flim_phasor_plotter._synthetic import make_synthetic_flim_data
from napari_flim_phasor_plotter._synthetic import create_time_array
import numpy as np
from pathlib import Path
from skimage import io
import zarr

def test_convert_to_zarr():
    laser_frequency = 40  # MHz
    amplitude = 1
    tau_list = list(np.linspace(start=0.1, stop=5, num=54))  # ns
    tau_list = [round(tau, 2) for tau in tau_list]
    number_of_photon_count_bins = 10

    local_folder_path = Path(__file__).parent / "test_data"
    local_folder_path.mkdir(exist_ok=True)
    
    time_array = create_time_array(laser_frequency, number_of_photon_count_bins)
    flim_data = make_synthetic_flim_data(time_array, amplitude, tau_list)
    flim_data = flim_data.reshape(number_of_photon_count_bins, 2, 3, 3, 3) # (h, t, z, y, x)
    # Save synthetic FLIM data as multiple tif files
    for i in range(flim_data.shape[1]):
        for j in range(flim_data.shape[2]):
            io.imsave(local_folder_path / f"test_t{i}_z{j}.tif", flim_data[:, i, j, :, :])

    widget = convert_to_zarr.convert_folder_to_zarr()
    # Set the folder path
    widget.folder_path.value = local_folder_path
    # Run the function by calling the widget
    widget()

    assert "test_data.zarr" in [str(file_path) for file_path in local_folder_path.iterdir()]
    zarr_array = zarr.open(local_folder_path / "test_data.zarr", mode='r')
    assert zarr_array.shape == (10, 2, 3, 3, 3)

    # Test the function
    # result = convert_to_zarr.test_convert_to_zarr(flim_data)
    # assert result is not None
    # assert result.shape == flim_data.shape
    # assert np.allclose(result, flim_data, rtol=0, atol=1e-5)