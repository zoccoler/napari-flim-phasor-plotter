from napari_flim_phasor_plotter._io import convert_to_zarr
from napari_flim_phasor_plotter._synthetic import make_synthetic_flim_data
from napari_flim_phasor_plotter._synthetic import create_time_array
import numpy as np
from pathlib import Path
from skimage import io
import zarr


def test_convert_to_zarr():
    """Test the convert_folder_to_zarr function."""
    # Create synthetic FLIM data
    expected_shape = (2, 10, 2, 3, 3, 3)  # (ch, ut, t, z, y, x)

    laser_frequency = 40  # MHz
    amplitude = 1  # a.u.
    tau_list = list(np.linspace(start=0.1, stop=5, num=54))  # ns
    tau_list = [round(tau, 2) for tau in tau_list]
    number_of_photon_count_bins = 10

    local_folder_path = Path(__file__).parent / "zarr_file"
    local_folder_path.mkdir(exist_ok=True)

    time_array = create_time_array(
        laser_frequency, number_of_photon_count_bins
    )
    flim_data = make_synthetic_flim_data(time_array, amplitude, tau_list)
    flim_data = flim_data.reshape(
        number_of_photon_count_bins, 2, 3, 3, 3
    )  # (ut, t, z, y, x)
    flim_data = np.stack(
        [flim_data, flim_data], axis=0
    )  # add another channel (ch, ut, t, z, y, x)
    # Save synthetic FLIM data as multiple tif files
    for i in range(flim_data.shape[2]):  # iterate over time points
        for j in range(flim_data.shape[3]):  # iterate over z planes
            # file name convention starts at 1, e.g., "name_t001_z001"
            io.imsave(
                local_folder_path / f"test_t{i+1}_z{j+1}.tif",
                flim_data[:, :, i, j, :, :],
            )  # (ch, ut, y, x)

    widget = convert_to_zarr.convert_folder_to_zarr()
    # Set the folder path
    widget.folder_path.value = local_folder_path
    # Run the function by calling the widget
    widget()

    # Check if the zarr file was created
    assert local_folder_path / "zarr_file.zarr" in [
        file_path for file_path in local_folder_path.iterdir()
    ]
    # Check if the zarr file has the correct shape and values
    file = zarr.open(str(local_folder_path / "zarr_file.zarr"), mode="r")
    assert file.shape == expected_shape
    assert np.allclose(file[:], flim_data, rtol=0, atol=1e-5)
    # Check if the zarr file has the correct metadata
    metadata = file.attrs.asdict()
    for channel_key, metadata_value in metadata.items():
        assert "file_type" in metadata_value
