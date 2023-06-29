import numpy as np

ALLOWED_FILE_EXTENSION = [
    '.ptu',
    '.sdt',
    '.tif',
    '.zarr'
]


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


def read_single_ptu_file(path):
    """Read a single ptu file."""
    from napari_flim_phasor_plotter._io.readPTU_FLIM import PTUreader

    ptu_file = PTUreader(path, print_header_data=False)
    data, _ = ptu_file.get_flim_data_stack()
    # from (x, y, ch, ut) to (ch, ut, y, x)
    data = np.moveaxis(data, [0, 1], [-2, -1])
    # metadata per channel/detector
    metadata_per_channel = []
    metadata = ptu_file.head
    metadata['file_type'] = 'ptu'
    # Add same metadata to each channel
    for channel in range(data.shape[0]):
        metadata_per_channel.append(metadata)
    return data, metadata_per_channel


def read_single_sdt_file(path):
    """Read a single sdt file."""
    import sdtfile
    sdt_file = sdtfile.SdtFile(path)  # header to be implemented
    data_raw = np.asarray(sdt_file.data)  # option to choose channel to include
    # from (ch, y, x, ut) to (ch, ut, y, x)
    data = np.moveaxis(np.stack(data_raw), -1, 1)

    metadata_per_channel = []
    for measure_info_recarray in sdt_file.measure_info:
        metadata = {'measure_info': recarray_to_dict(measure_info_recarray),
                    'file_type': 'sdt'}
        metadata_per_channel.append(metadata)
    return data, metadata_per_channel


def read_single_tif_file(path, channel_axis=0, ut_axis=1):
    """Read a single tif file."""
    from skimage.io import imread
    data = imread(path)
    # if not there already, move ch and ut from their given positions to 0 and 1 axes
    data = np.moveaxis(data, [channel_axis, ut_axis], [0, 1])
    # TO DO: allow external reading of metadata
    metadata_per_channel = []
    metadata = {}
    metadata['file_type'] = 'tif'
    for channel in range(data.shape[0]):
        metadata_per_channel.append(metadata)
    return data, metadata_per_channel


# Dictionary relating file extension to compatible reading function
get_read_function_from_extension = {
    '.tif': read_single_tif_file,
    '.ptu': read_single_ptu_file,
    '.sdt': read_single_sdt_file
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
            if path.suffix != '':
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
            dictionary[name] = recarray[name].item()
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
    # handle both a string and a list of strings
    paths = [path] if isinstance(path, str) else path
    # Use Path from pathlib
    paths = [Path(path) for path in paths]

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
            imread = get_read_function_from_extension[file_extension]
            data, metadata_list = imread(file_path)  # (ch, ut, y, x)
            data = np.expand_dims(data, axis=(2, 3))  # (ch, ut, t, z, y, x)
        if data is None:
            return [(np.zeros((1, 1, 1, 1, 1, 1)), {'name': 'too big: convert to zarr first'}, 'image')]
        summed_intensity_image = np.sum(data, axis=1, keepdims=True)
        # arguments for TCSPC stack
        add_kwargs = {'channel_axis': 0, 'metadata': metadata_list}
        layer_type = "image"
        layer_data.append((data, add_kwargs, layer_type))
        # arguments for intensity image
        add_kwargs = {'channel_axis': 0, 'metadata': metadata_list,
                      'name': 'summed_intensity_image_' + Path(path).stem}
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
    if file_extension == '.zarr':
        file_paths = folder_path
        # TO DO: read zarr metadata
        data = zarr.open(file_paths, mode='r+')
        data = da.from_zarr(data)
        metadata_list = []
    else:
        # Get all file path with specified file extension
        file_paths = natsorted([file_path for file_path in folder_path.iterdir(
        ) if file_path.suffix == file_extension])
        # Estimate stack sizes
        # TO DO: estimate stack size from shape and dtype instead of file size (to handle compressed files)
        stack_size_in_MB = get_stack_estimated_size(file_paths, file_extension)
        if stack_size_in_MB < 2e3:  # 2GB
            # read full stack
            data, metadata_list = make_full_numpy_stack(
                file_paths, file_extension)
        else:
            notifications.show_error(
                'Stack is larger than 2GB, please convert to .zarr')
            print('Stack is larger than 2GB, please convert to .zarr')
            return None, None
    # TO DO: remove print
    print('stack = True\n', 'data type: ', file_extension,
          '\ndata_shape = ', data.shape, '\n')

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
    shapes_list = []
    for file_path in file_paths:
        if file_path.suffix == file_extension:
            imread = get_read_function_from_extension[file_extension]
            image_slice, _ = imread(file_path)
            shapes_list.append(image_slice.shape)  # (ch, ut, y, x)
    # Get slice max shape (ch, mt, y, x)
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
    # Read all images to get max slice shape
    image_slice_shape, image_dtype = get_max_slice_shape_and_dtype(
        file_paths, file_extension)
    imread = get_read_function_from_extension[file_extension]

    list_of_time_point_paths = get_structured_list_of_paths(
        file_paths, file_extension)
    z_list, t_list = [], []
    for list_of_zslice_paths in list_of_time_point_paths:
        for zslice_path in list_of_zslice_paths:
            data, metadata_per_channel = imread(zslice_path)
            z_slice = np.zeros(image_slice_shape, dtype=image_dtype)
            z_slice[:data.shape[0], :data.shape[1],
                    :data.shape[2], :data.shape[3]] = data
            z_list.append(z_slice)
        z_stack = np.stack(z_list)
        t_list.append(z_stack)
        z_list = []
    stack = np.stack(t_list)
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
    pattern_t = '_t(\\d+)'
    pattern_z = '_z(\\d+)'
    current_t, current_z = None, None
    file_name = file_path.stem
    matches_z = re.search(pattern_z, file_name)
    if matches_z is not None:
        current_z = int(matches_z.group(1))  # .zfill(2)
    matches_t = re.search(pattern_t, file_name)
    if matches_t is not None:
        current_t = int(matches_t.group(1))
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
    max_z = max([get_current_tz(file_path)
                for file_path in file_paths if file_path.suffix == file_extension])[1]
    if max_z is None:
        return 1
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
    max_time = max([get_current_tz(file_path)
                   for file_path in file_paths if file_path.suffix == file_extension])[0]
    if max_time is None:
        return 1
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
    previous_t = 1
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
