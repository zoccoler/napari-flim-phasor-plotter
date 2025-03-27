from napari_flim_phasor_plotter._io import convert_to_ome_tif
from napari_flim_phasor_plotter._synthetic import make_synthetic_flim_data
from napari_flim_phasor_plotter._synthetic import create_time_array
import numpy as np
from pathlib import Path
from skimage import io
import tifffile


def test_convert_folder_to_ome_tif():
    """Test the convert_folder_to_ome_tif function."""
    # Create synthetic FLIM data
    number_of_photon_count_bins = 10
    ch = 2
    t = 2
    z = 5
    y = 5
    x = 5
    expected_summed_intensity_shape = (ch, t, z, y, x)  # (ch, t, z, y, x)
    expected_single_timepoint_shape = (
        ch,
        number_of_photon_count_bins,
        z,
        y,
        x,
    )  # (ch, ut, z, y, x)

    laser_frequency = 40  # MHz
    amplitude = 1  # a.u.
    tau_list = list(np.linspace(start=0.1, stop=5, num=t * z * y * x))  # ns
    tau_list = [round(tau, 2) for tau in tau_list]

    x_pixel_size = 0.1
    y_pixel_size = 0.1
    z_pixel_size = 0.2
    pixel_size_unit = "um"
    time_resolution_per_slice = 0.1
    time_unit = "s"
    channel_names = "Channel 1, Channel 2"
    micro_time_resolution = 0.1
    micro_time_unit = "ns"

    local_folder_path = Path(__file__).parent / "tif_files"
    local_folder_path.mkdir(exist_ok=True)

    time_array = create_time_array(
        laser_frequency, number_of_photon_count_bins
    )
    flim_data = make_synthetic_flim_data(time_array, amplitude, tau_list)
    flim_data = flim_data.reshape(
        number_of_photon_count_bins, t, z, y, x
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

    widget = convert_to_ome_tif.convert_folder_to_ome_tif()
    # Set the folder path
    widget.folder_path.value = local_folder_path
    widget.x_pixel_size.value = x_pixel_size
    widget.y_pixel_size.value = y_pixel_size
    widget.z_pixel_size.value = z_pixel_size
    widget.pixel_size_unit.value = pixel_size_unit
    widget.time_resolution_per_slice.value = time_resolution_per_slice
    widget.time_unit.value = time_unit
    widget.channel_names.value = channel_names
    widget.micro_time_resolution.value = micro_time_resolution
    widget.micro_time_unit.value = micro_time_unit
    # Run the function by calling the widget
    widget()

    output_folder_path = local_folder_path / "OME-TIFs"

    # check if multiple ome-tifs were created (same number as timepoints)
    assert (
        len(
            [
                file_path
                for file_path in output_folder_path.iterdir()
                if ".ome" in file_path.suffixes
                and ".tif" in file_path.suffixes
            ]
        )
        == flim_data.shape[2] + 1
    )
    # check if the ome-tif files have the correct shape
    for i, file_path in enumerate(output_folder_path.iterdir()):
        if ".ome" in file_path.suffixes and ".tif" in file_path.suffixes:
            if "_FLIM" in file_path.name:
                with tifffile.TiffFile(file_path) as tif:
                    assert (
                        tif.asarray(squeeze=False).shape[:-1]
                        == expected_single_timepoint_shape
                    )
            else:
                with tifffile.TiffFile(file_path) as tif:
                    # It seems squeeze=False keeps unitary dimensions, but adds an 'S' dimension in the end for OME-TIFFs
                    assert (
                        tif.asarray(squeeze=False).shape[:-1]
                        == expected_summed_intensity_shape
                    )


def test_convert_file_to_ome_tif():
    """Test the convert_file_to_ome_tif function."""
    # Create synthetic FLIM data
    number_of_photon_count_bins = 10
    ch = 2
    t = 1
    z = 1
    y = 5
    x = 5
    expected_single_timepoint_shape = (
        ch,
        number_of_photon_count_bins,
        z,
        y,
        x,
    )  # (ch, ut, z, y, x)

    laser_frequency = 40  # MHz
    amplitude = 1  # a.u.
    tau_list = list(np.linspace(start=0.1, stop=5, num=t * z * y * x))  # ns
    tau_list = [round(tau, 2) for tau in tau_list]

    x_pixel_size = 0.1
    y_pixel_size = 0.1
    pixel_size_unit = "um"
    channel_names = ""
    micro_time_resolution = 0.1
    micro_time_unit = "ns"

    local_folder_path = Path(__file__).parent / "tif_file"
    local_folder_path.mkdir(exist_ok=True)

    time_array = create_time_array(
        laser_frequency, number_of_photon_count_bins
    )
    flim_data = make_synthetic_flim_data(time_array, amplitude, tau_list)
    flim_data = flim_data.reshape(
        number_of_photon_count_bins, y, x
    )  # (ut, y, x)
    flim_data = np.stack(
        [flim_data, flim_data], axis=0
    )  # add another channel (ch, ut, y, x)
    # Save synthetic FLIM data as multiple tif files
    io.imsave(local_folder_path / f"test.tif", flim_data)  # (ch, ut, y, x)

    widget = convert_to_ome_tif.convert_file_to_ome_tif()
    # Set the folder path
    widget.file_path.value = local_folder_path / "test.tif"
    widget.x_pixel_size.value = x_pixel_size
    widget.y_pixel_size.value = y_pixel_size
    widget.pixel_size_unit.value = pixel_size_unit
    widget.channel_names.value = channel_names
    widget.micro_time_resolution.value = micro_time_resolution
    widget.micro_time_unit.value = micro_time_unit
    # Run the function by calling the widget
    widget()

    output_folder_path = local_folder_path / "OME-TIFs"

    # check if multiple ome-tifs were created (same number as timepoints)
    assert (
        len(
            [
                file_path
                for file_path in output_folder_path.iterdir()
                if ".ome" in file_path.suffixes
                and ".tif" in file_path.suffixes
            ]
        )
        == 1
    )
    # check if the ome-tif files have the correct shape
    for i, file_path in enumerate(output_folder_path.iterdir()):
        if ".ome" in file_path.suffixes and ".tif" in file_path.suffixes:
            with tifffile.TiffFile(file_path) as tif:
                assert (
                    tif.asarray(squeeze=False).shape[:-1]
                    == expected_single_timepoint_shape
                )
