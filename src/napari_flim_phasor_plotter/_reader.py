import numpy as np

ALLOWED_FILE_EXTENSION = [".ptu", ".sdt", ".tif", ".zarr"]


def napari_get_reader(path):
    """A basic implementation of a Reader contribution.

    Parameters
    ----------
    path : str or list of str
        Path to file, or list of paths.

    Returns
    -------
    function or None
        If the path is a recognized format, return a function that accepts the
        same path or list of paths, and returns a list of layer data tuples.
    """
    file_extension = get_most_frequent_file_extension(path)
    # If we recognize the format, we return the actual reader function
    if file_extension in ALLOWED_FILE_EXTENSION:
        return flim_file_reader
    # otherwise we return None.
    return None


def read_single_ptu_file_2d_timelapse(path, *args, **kwargs):
    """Read a 2D timelapse PTU file.

    Parameters
    ----------
    path : str
        Path to the PTU file.

    Returns
    -------
    data : np.ndarray
        The data array with dimensions (ch, ut, t, z, y, x), where z has length 1 (following napari convention).
    metadata_per_channel : list
        List of metadata dictionaries for each channel.
    """
    from ptufile import PtuFile
    import numpy as np

    ptu = PtuFile(path)
    ptu_dims = list(ptu.dims)
    data = ptu[:]

    # Re-order dimensions to standard order
    standard_dims_order = ["C", "H", "T", "Y", "X"]  # (ch, ut, t, y, x)
    argsorted = [ptu_dims.index(dim) for dim in standard_dims_order]
    data = np.moveaxis(data, argsorted, range(len(argsorted)))
    # Add unitary dimension for z
    data = np.expand_dims(data, axis=3)  # (ch, ut, t, z, y, x)

    # Get metadata
    # metadata per channel/detector
    metadata_per_channel = []
    metadata = ptu.tags
    metadata["file_type"] = "ptu"
    metadata["frequency"] = ptu.frequency
    metadata["tcspc_resolution"] = ptu.tcspc_resolution
    metadata["x_pixel_size"] = ptu.coords["X"][1]
    metadata["y_pixel_size"] = ptu.coords["Y"][1]
    metadata["frame_time"] = ptu.frame_time
    # Add same metadata to each channel
    for channel in range(data.shape[0]):
        metadata_per_channel.append(metadata)
    return data, metadata_per_channel


def read_single_ptu_file(path, *args, **kwargs):
    """Read a single ptu file.

    Only accepts single frame PTU files. If PTU file is a time-lapse, split into single frame PTU files first, otherwise just first frame gets read.

    Parameters
    ----------
    path : str
        Path to the PTU file.

    Returns
    -------
    data : np.ndarray
        The data array with dimensions (ch, ut, y, x).
    metadata_per_channel : list
        List of metadata dictionaries for each channel.
    """
    from ptufile import PtuFile
    import numpy as np
    from warnings import warn

    ptu = PtuFile(path)
    ptu_dims = list(ptu.dims)
    if "T" in ptu_dims:
        t_pos = ptu_dims.index("T")
        n_frames = ptu.shape[t_pos]
        if n_frames > 1:
            warn(
                "Multiple 'time points' found in single ptu file. Assuming repeated laser scans. Returning first frame.\nUse read_single_ptu_file_2d_timelapse() for true timelapse PTU files."
            )
        # read single frame from axis where time is present
        # average over time axis
        # data = np.mean(ptu[:], axis=t_pos)
        data = np.take(ptu[:], 0, axis=t_pos)
        ptu_dims.pop(t_pos)
    else:
        data = ptu[:]

    # Re-order dimensions to standard order
    standard_dims_order = ["C", "H", "Y", "X"]  # (ch, ut, y, x)
    argsorted = [ptu_dims.index(dim) for dim in standard_dims_order]
    data = np.moveaxis(data, argsorted, range(len(argsorted)))

    # Get metadata
    # metadata per channel/detector
    metadata_per_channel = []
    metadata = ptu.tags
    metadata["file_type"] = "ptu"
    metadata["frequency"] = ptu.frequency
    metadata["tcspc_resolution"] = ptu.tcspc_resolution
    metadata["x_pixel_size"] = ptu.coords["X"][1]
    metadata["y_pixel_size"] = ptu.coords["Y"][1]
    # Add same metadata to each channel
    for channel in range(data.shape[0]):
        metadata_per_channel.append(metadata)
    return data, metadata_per_channel


def read_single_sdt_file(path, *args, **kwargs):
    """Read a single sdt file."""
    import sdtfile
    from warnings import warn

    sdt_file = sdtfile.SdtFile(path)  # header to be implemented
    shapes = [array.shape for array in sdt_file.data]
    if all(shape == shapes[0] for shape in shapes):
        data_raw = np.asarray(
            sdt_file.data
        )  # get all arrays if they have the same shape
    else:
        data_raw = np.asarray(
            [sdt_file.data[0]]
        )  # get only the first array if they have different shapes
        warn(
            "Different shapes found in sdt file. Only the first array will be read."
        )
    # from (ch, y, x, ut) to (ch, ut, y, x)
    data = np.moveaxis(np.stack(data_raw), -1, 1)

    metadata_per_channel = []
    for i, measure_info_recarray in enumerate(sdt_file.measure_info):
        metadata = {
            "measure_info": recarray_to_dict(measure_info_recarray),
            "file_type": "sdt",
        }
        metadata["tcspc_resolution"] = (
            sdt_file.times[i][1] - sdt_file.times[i][0]
        )
        metadata_per_channel.append(metadata)
    return data, metadata_per_channel


def read_single_tif_file(
    path, channel_axis=0, ut_axis=1, timelapse=False, viewer_exists=False
):
    """
    Read a single tif file.

    - If a 2D single channel FLIM data, assumes dimensions (ut, y, x).
    - If a 3D single channel FLIM data, assumes dimensions (ut, z, y, x).
    - If a timelapse 2D single channel FLIM data, assumes dimensions (ut, t, y, x).
    - If a timelapse 3D single channel FLIM data, assumes dimensions (ut, t, z, y, x).
    - If channel_axis is not None, assumes array is multichannel.

    Parameters
    ----------
    path : str
        Path to file.
    channel_axis : int, optional
        Channel axis. The default is 0. If None, assumes array is single channel.
    ut_axis : int, optional
        Microtime axis. The default is 1.
    timelapse : bool, optional
        If True, assume there must be a time dimension. The default is False.
    viewer_exists : bool, optional
        If True, show error message in napari. The default is False.

    Returns
    -------
    data, metadata_per_channel : Tuple(array, List(dict))
        Array containing the FLIM images and a metadata list (one metadata per channel).
        Array is either 4D (ch, ut, y, x) or 6D (ch, ut, t, z, y, x).
    """
    from skimage.io import imread
    from napari.utils.notifications import show_error, show_warning

    data = imread(path)
    # Handle different input data dimensions
    if data.ndim == 2:
        if viewer_exists:
            show_error(
                f"Image is not raw FLIM data. Image dimensions should be >= 3, but current dimensions: {data.ndim}"
            )
            return None, None
        raise TypeError(
            f"Image is not raw FLIM data. Image dimensions should be >= 3, but current dimensions: {data.ndim}"
        )

    if channel_axis is None:
        # Handle different input data dimensions
        if data.ndim == 4 and timelapse:  # Assume (ut, t, y, x)
            # Yields: (ut, t, z, y, x)
            data = np.expand_dims(data, axis=-3)
        elif data.ndim == 4:  # Assume (ut, z, y, x)
            # Yields: (ut, t, z, y, x)
            data = np.expand_dims(data, axis=-4)
        # Add unidimensional channel axis (WARNING: this already moves the ut axis) TODO: fix this
        data = np.expand_dims(data, 0)
    # if multichannel
    else:
        # Move channel axis to first position and split channels
        data = np.moveaxis(data, channel_axis, 0)
        split_arrays = np.split(data, data.shape[0], axis=0)
        split_arrays_with_new_axis = []
        for split_array in split_arrays:
            single_channel_data = split_array[0]
            if np.any(single_channel_data):  # Do not add empty channels
                # Handle different input data dimensions
                if (
                    single_channel_data.ndim == 4 and timelapse
                ):  # Assume (ut, t, y, x)
                    # Yields: (ut, t, z, y, x)
                    single_channel_data = np.expand_dims(
                        single_channel_data, axis=-3
                    )
                elif single_channel_data.ndim == 4:  # Assume (ut, z, y, x)
                    # Yields: (ut, t, z, y, x)
                    single_channel_data = np.expand_dims(
                        single_channel_data, axis=-4
                    )
                split_arrays_with_new_axis.append(single_channel_data)
        # Rebuild data with fixed dimensions and channel axis as first axis
        data = np.stack(split_arrays_with_new_axis, axis=0)

    # move ut from its given position to axis 1, to yield either (ch, ut, y, x) or (ch, ut, t, z, y, x)
    data = np.moveaxis(data, source=ut_axis, destination=1)
    # TO DO: allow external reading of metadata
    metadata_per_channel = []
    metadata = {}
    metadata["file_type"] = "tif"
    for channel in range(data.shape[0]):
        metadata_per_channel.append(metadata)
    return data, metadata_per_channel


def get_resolutions_from_single_file(file_path, file_extension):
    """Get the pixel size along the x and y axes and the time resolution for the TCSPC histogram from a single file.

    Parameters
    ----------
    file_path : str
        Path to the file.

    Returns
    -------
    x_pixel_size : float
        Pixel size along the x-axis.
    y_pixel_size : float
        Pixel size along the y-axis.
    tcspc_resolution : float
        Time resolution for the TCSPC histogram.
    """
    x_pixel_size = 0
    y_pixel_size = 0
    tcspc_resolution = 0
    number_channels = 0
    # Get appropriate read function from file extension
    if file_extension == ".ptu":
        from ptufile import PtuFile

        ptu = PtuFile(file_path)
        x_pixel_size = ptu.coords["X"][1]
        y_pixel_size = ptu.coords["Y"][1]
        tcspc_resolution = ptu.tcspc_resolution
        number_channels = ptu.number_channels
    elif file_extension == ".sdt":
        from sdtfile import SdtFile

        sdt = SdtFile(file_path)
        tcspc_resolution = sdt.times[0][1] - sdt.times[0][0]
        number_channels = len(sdt.measure_info)
    return x_pixel_size, y_pixel_size, tcspc_resolution, number_channels


# Dictionary relating file extension to compatible reading function
get_read_function_from_extension = {
    ".tif": read_single_tif_file,
    ".ptu": read_single_ptu_file,
    ".sdt": read_single_sdt_file,
}


def get_most_frequent_file_extension(path):
    """Get most frequent file extension in path.

    Parameters
    ----------
    path : str or list of str
        Path to file, or list of paths.

    Returns
    -------
    most_frequent_file_type : str
        Most frequent file extension in path.
    """
    from pathlib import Path

    # Check if path is a list of paths
    if isinstance(path, list):
        # reader plugins may be handed single path, or a list of paths.
        # if it is a list, it is assumed to be an image stack...
        # so we are going to look at the most common file extension/suffix.
        suffixes = [Path(p).suffix for p in path]
    # Path is a single string
    else:
        path = Path(path)
        # If directory
        if path.is_dir():
            # Check if directory has suffix (meaning it can be .zarr)
            if path.suffix != "":
                # Get path suffix
                suffixes = [path.suffix]
            # Get suffixes from files inside
            else:
                suffixes = [p.suffix for p in path.iterdir()]
        # Get file suffix
        elif path.is_file():
            suffixes = [path.suffix]
    # Get most frequent file entension in path
    most_frequent_file_type = max(set(suffixes), key=suffixes.count)
    return most_frequent_file_type


def recarray_to_dict(recarray):
    # convert recarray to dict
    dictionary = {}
    for name in recarray.dtype.names:
        if isinstance(recarray[name], np.recarray):
            dictionary[name] = recarray_to_dict(recarray[name])
        else:
            dictionary[name] = recarray[name].tolist()
    return dictionary


def flim_file_reader(path):
    """Take a path or list of paths to FLIM images and return a list of LayerData tuples.

    Parameters
    ----------
    path : str or list of str
        Path to file, folder or list of paths. If path to a folder, it assumes it is a stack with a
        standard file naming convention, like image_t000_z000.tif, image_t000_z001.tif, etc.

    Returns
    -------
    layer_data : list of tuples
        A list of LayerData tuples where each tuple in the list contains
        (data, metadata, layer_type), where data is a numpy or dask array, metadata is
        a dict of keyword arguments for the corresponding viewer.add_* method
        in napari along with other FLIM metadata, and layer_type is 'image'.
    """
    from pathlib import Path
    import tifffile
    from ptufile import PtuFile
    import numpy as np
    from napari.utils.notifications import show_warning

    # handle both a string and a list of strings
    paths = [path] if isinstance(path, str) else path
    # Use Path from pathlib
    paths = [Path(path) for path in paths]

    imread = None
    layer_data = []
    for path in paths:
        # Assume stack if paths are folders (which includes .zarr here)
        if path.is_dir():
            folder_path = path
            data, metadata_list = read_stack(folder_path)
        # If paths are files, read individual separated files
        else:
            file_path = path
            file_extension = file_path.suffix
            channel_axis = 0
            # If .tif, check shape before loading pixels
            if file_extension == ".tif" or file_extension == ".tiff":
                tif = tifffile.TiffFile(file_path)
                shaped_metadata = tif.shaped_metadata
                if shaped_metadata is not None and len(shaped_metadata) > 0:
                    # if len(shaped_metadata) > 0:
                    shape = tif.shaped_metadata[0]["shape"]
                else:
                    show_warning(
                        "Warning: Cannot determine shape from metadata. Loading full stack."
                    )
                    image = tifffile.imread(file_path)
                    shape = image.shape
                if len(shape) > 4:  # stack (z or timelapse)
                    if ".ome" in file_path.suffixes:
                        # If ome-tif, data should be 5D with channel being the first axis
                        data = np.expand_dims(
                            image, axis=2
                        )  # make it 6D, in accordance with plugin convention
                        channel_axis = 0
                    else:
                        channel_axis = None
                if len(shape) < 4:  # single 2D image (ut, y, x)
                    channel_axis = None
            # if .ptu, check if it is a 2D timelapse
            if file_extension == ".ptu":
                ptu = PtuFile(path)
                ptu_dims = list(ptu.dims)
                if "T" in ptu_dims:
                    t_pos = ptu_dims.index("T")
                    n_frames = ptu.shape[t_pos]
                    if n_frames > 1:
                        imread = read_single_ptu_file_2d_timelapse
            if imread is None:
                imread = get_read_function_from_extension[file_extension]
            # (ch, ut, y, x)  or (ch, ut, t, z, y, x) in case of single tif stack
            data, metadata_list = imread(
                file_path, channel_axis=channel_axis, viewer_exists=True
            )
            if data.ndim == 4:  # expand dims if not a stack already
                data = np.expand_dims(
                    data, axis=(2, 3)
                )  # (ch, ut, t, z, y, x)
        if data is None:
            return [
                (
                    np.zeros((1, 1, 1, 1, 1, 1)),
                    {
                        "name": "too big or not FLIM data: convert to zarr first"
                    },
                    "image",
                )
            ]
        # Exclude empty channels
        non_empty_channel_indices = [
            i for i in range(data.shape[0]) if np.any(data[i])
        ]
        data = data[non_empty_channel_indices]
        metadata_list = [
            metadata_list[i]
            for i in non_empty_channel_indices
            if len(metadata_list) > 0
        ]

        summed_intensity_image = np.sum(data, axis=1, keepdims=False)
        # arguments for TCSPC stack
        add_kwargs = {
            "channel_axis": 0,
            "metadata": metadata_list,
            "name": "FLIM_" + Path(path).stem,
        }
        layer_type = "image"
        layer_data.append((data, add_kwargs, layer_type))
        # arguments for intensity image
        add_kwargs = {
            "channel_axis": 0,
            "metadata": metadata_list,
            "name": Path(path).stem,
            "blending": "additive",
        }
        layer_data.append((summed_intensity_image, add_kwargs, layer_type))
    return layer_data


def read_stack(folder_path):
    """Read a stack of FLIM images.

    Parameters
    ----------
    folder_path : str
        Path to folder containing FLIM images.

    Returns
    -------
    data, metadata_list : Tuple(array, List(dict))
        Array containing the FLIM images and a metadata list (one metadata per channel).
    """
    import zarr
    import dask.array as da
    from natsort import natsorted
    from napari.utils import notifications

    file_extension = get_most_frequent_file_extension(folder_path)
    if file_extension == ".zarr":
        file_paths = folder_path
        # TO DO: read zarr metadata
        file = zarr.open(file_paths, mode="r+")
        data = da.from_zarr(file)
        metadata_list = [
            metadata for key, metadata in file.attrs.asdict().items()
        ]
    else:
        # Get all file path with specified file extension
        file_paths = natsorted(
            [
                file_path
                for file_path in folder_path.iterdir()
                if file_path.suffix == file_extension
            ]
        )
        # Estimate stack sizes
        # TO DO: estimate stack size from shape and dtype instead of file size (to handle compressed files)
        stack_size_in_MB = get_stack_estimated_size(file_paths, file_extension)
        if stack_size_in_MB < 4e3:  # 4GB
            # read full stack
            data, metadata_list = make_full_numpy_stack(
                file_paths, file_extension
            )
        else:
            notifications.show_error(
                "Stack is larger than 4GB, please convert to .zarr"
            )
            print("Stack is larger than 4GB, please convert to .zarr")
            return None, None
    print(
        "stack = True",
        "\ndata type: ",
        file_extension,
        "\ndata_shape = ",
        data.shape,
        "\n",
    )

    return data, metadata_list


def get_max_slice_shape_and_dtype(file_paths, file_extension):
    """Get max slice shape and dtype.

    Go through files to get max shape (number of photon bins may vary from image to image)

    Parameters
    ----------
    file_paths : List of paths
        A list of Path objects from pathlib.
    file_extension : str
        A file extension, like '.tif' or '.ptu'.

    Returns
    -------
    max_shape, data_type : Tuple(Tuple(int), numpy.dtype)
        Max shape and data type.
    """
    # TO DO: offer fast reading option by calculating max shape from metadata (array may become bigger)
    from tqdm import tqdm

    progress_bar = tqdm(
        total=len(file_paths),
        desc="Calculating stack shape from individual files",
        unit="files",
    )
    shapes_list = []
    for file_path in file_paths:
        if file_path.suffix == file_extension:
            imread = get_read_function_from_extension[file_extension]
            image_slice, _ = imread(file_path)
            shapes_list.append(image_slice.shape)  # (ch, ut, y, x)
            progress_bar.update(1)
    progress_bar.close()
    # Get slice max shape (ch, ut, y, x)
    return max(shapes_list), image_slice.dtype


def make_full_numpy_stack(file_paths, file_extension):
    """Make full numpy stack from list of file paths.

    Parameters
    ----------
    file_paths : List of paths
        A list of Path objects from pathlib.
    file_extension : str
        A file extension, like '.tif' or '.ptu'.

    Returns
    -------
    numpy_stack, metadata_per_channel : Tuple(numpy array, List(dict))
        A numpy array of shape (ch, ut, t, z, y, x) and a metadata list (one metadata per channel).
    """
    from tqdm import tqdm

    # Read all images to get max slice shape
    image_slice_shape, image_dtype = get_max_slice_shape_and_dtype(
        file_paths, file_extension
    )
    imread = get_read_function_from_extension[file_extension]

    list_of_time_point_paths = get_structured_list_of_paths(
        file_paths, file_extension
    )
    progress_bar = tqdm(
        total=len(list_of_time_point_paths) * len(list_of_time_point_paths[0]),
        desc="Reading stack",
        unit="slices",
    )

    z_list, t_list = [], []
    for list_of_zslice_paths in list_of_time_point_paths:
        for zslice_path in list_of_zslice_paths:
            data, metadata_per_channel = imread(zslice_path)
            z_slice = np.zeros(image_slice_shape, dtype=image_dtype)
            z_slice[
                : data.shape[0],
                : data.shape[1],
                : data.shape[2],
                : data.shape[3],
            ] = data
            z_list.append(z_slice)
            progress_bar.update(1)
        z_stack = np.stack(z_list)
        t_list.append(z_stack)
        z_list = []
    stack = np.stack(t_list)
    progress_bar.close()
    # from (t, z, ch, ut, y, x) to (ch, ut, t, z, y, x)
    stack = np.moveaxis(stack, [-4, -3], [0, 1])
    return stack, metadata_per_channel


def get_current_tz(file_path):
    """Get current time point and z slice from file name.

    Parameters
    ----------
    file_path : Path
        A Path object from pathlib. It expects a file name with '_t' and '_z' patterns.

    Returns
    -------
    current_t, current_z : Tuple(int, int)
        Current time point and z slice.
    """
    import re

    pattern_t = "_t(\\d+)"
    pattern_z = "_z(\\d+)"
    current_t, current_z = None, None
    file_name = file_path.stem
    matches_z = re.search(pattern_z, file_name)
    if matches_z is not None:
        current_z = int(matches_z.group(1))
        current_z -= 1  # 0-based index while file names convention are 1-based
    matches_t = re.search(pattern_t, file_name)
    if matches_t is not None:
        current_t = int(matches_t.group(1))
        current_t -= 1  # 0-based index while file names convention are 1-based
    return current_t, current_z


def get_max_zslices(file_paths, file_extension):
    """Get max z slices.

    Parameters
    ----------
    file_paths : List of paths
        A list of Path objects from pathlib.
    file_extension : str
        A file extension, like '.tif' or '.ptu'.

    Returns
    -------
    max_z : int
        Max z slices.
    """
    z_numbers = [
        get_current_tz(file_path)[1]
        for file_path in file_paths
        if file_path.suffix == file_extension
    ]
    max_z = len(np.unique(np.array(z_numbers)))
    return max_z


def get_max_time_points(file_paths, file_extension):
    """Get max time points.

    Parameters
    ----------
    file_paths : List of paths
        A list of Path objects from pathlib.
    file_extension : str
        A file extension, like '.tif' or '.ptu'.

    Returns
    -------
    max_time : int
        Max time points.
    """
    t_numbers = [
        get_current_tz(file_path)[0]
        for file_path in file_paths
        if file_path.suffix == file_extension
    ]
    max_time = len(np.unique(np.array(t_numbers)))
    return max_time


def get_stack_estimated_size(file_paths, file_extension, from_file_size=False):
    """Get stack estimated size.

    Parameters
    ----------
    file_paths : List of paths
        A list of Path objects from pathlib.
    file_extension : str
        A file extension, like '.tif' or '.ptu'.
    from_file_size : bool, optional
        If True, the file size is used to estimate the stack size. If False, the stack size is estimated from the
        image size (slower, but more accurate for compressed files). The default is False.

    Returns
    -------
    stack_size : float
        Stack size in MB.
    """
    from tqdm import tqdm

    progress_bar = tqdm(
        total=len(file_paths),
        desc="Calculating decompressed stack size",
        unit="files",
    )
    stack_size = 0
    for file_path in file_paths:
        if file_path.suffix == file_extension:
            if from_file_size:
                file_size = file_path.stat().st_size / 1e6  # in MB
            else:
                imread = get_read_function_from_extension[file_extension]
                data, metadata_list = imread(file_path)  # (ch, ut, y, x)
                file_size = data.nbytes / 1e6  # in MB
            stack_size += file_size
            progress_bar.update(1)
    progress_bar.close()
    print(f"Estimated decompressed stack size: {stack_size} MB")
    return stack_size


def get_structured_list_of_paths(file_paths, file_extension):
    """Get structured list of paths.

    Parameters
    ----------
    file_paths : List of paths
        A list of Path objects from pathlib.
    file_extension : str
        A file extension, like '.tif' or '.ptu'.

    Returns
    -------
    t_path_list : List of lists of paths
        A list of lists of Path objects from pathlib. The first list is the time points, the second list is the z slices.
    """
    from natsort import natsorted

    t_path_list = []
    z_path_list = []
    file_paths = natsorted(file_paths)
    previous_t = 0
    for file_path in file_paths:
        if file_path.suffix == file_extension:
            current_t, current_z = get_current_tz(file_path)
            if current_t is not None:
                if current_t > previous_t:
                    t_path_list.append(z_path_list)
                    z_path_list = []
                    previous_t = current_t
                z_path_list.append(file_path)
    # If no timepoints, z_path_list is file_paths
    if current_t is None:
        z_path_list = file_paths
    # Append last timepoint
    t_path_list.append(z_path_list)
    return t_path_list
