"""
This module is an example of a barebones numpy reader plugin for napari.

It implements the Reader specification, but your plugin may choose to
implement multiple readers or even other plugin contributions. see:
https://napari.org/stable/plugins/guides.html?#readers
"""
import numpy as np
from napari_flim_phasor_calculator._io.readPTU_FLIM import PTUreader
import sdtfile
from pathlib import Path
import os
import re
import dask.array as da
import dask
from natsort import natsorted
from napari.utils import notifications

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
    if isinstance(path, list):
        # reader plugins may be handed single path, or a list of paths.
        # if it is a list, it is assumed to be an image stack...
        # so we are only going to look at the first file.
        path = path[0]
    # If directory, get one file to probe file type
    if os.path.isdir(path):
        path = os.listdir(path)[0]

    # If we recognize the format, we return the actual reader function
    if isinstance(path, str) and (path.lower().endswith('.ptu') or (path.lower().endswith('.sdt'))):
        return flim_file_reader
    # otherwise we return None.
    return None

def recarray_to_dict(recarray):
    # convert recarray to dict
    dictionary = {}
    for name in recarray.dtype.names:
        if type(recarray[name]) == np.recarray:
            dictionary[name] = recarray_to_dict(recarray[name])
        else:
            dictionary[name] = recarray[name].item()
    return dictionary

def flim_file_reader(path):
    """Take a path or list of paths and return a list of LayerData tuples.

    Readers are expected to return data as a list of tuples, where each tuple
    is (data, [add_kwargs, [layer_type]]), "add_kwargs" and "layer_type" are
    both optional.

    Parameters
    ----------
    path : str or list of str
        Path to file, or list of paths.

    Returns
    -------
    layer_data : list of tuples
        A list of LayerData tuples where each tuple in the list contains
        (data, metadata, layer_type), where data is a numpy array, metadata is
        a dict of keyword arguments for the corresponding viewer.add_* method
        in napari, and layer_type is a lower-case string naming the type of
        layer. Both "meta", and "layer_type" are optional. napari will
        default to layer_type=="image" if not provided
    """
    # handle both a string and a list of strings
    paths = [path] if isinstance(path, str) else path
    # Use Path from pathlib
    paths = [Path(path) for path in paths]
        
    layer_data = []
    for path in paths:
        # Assume stack if paths are folders 
        if not path.is_file():
            # get data from ptu files and metadata
            if len([p for p in path.glob('*.ptu')]) > 0: 
                data, summed_intensity_image, metadata_list = read_ptu_stack(path)
            else:
                notifications.show_warning('No .ptu file in folder.')
        # If paths are files, read individual separated files
        else:
            file_path = path
             # get data from ptu files and metadata
            if file_path.suffix == '.ptu':
                data, summed_intensity_image, metadata_list = read_single_ptu_file(file_path)
            # get data from sdt files
            elif file_path.suffix == '.sdt':
                sdt_file = sdtfile.SdtFile(file_path)  # header to be implemented
                data_raw = np.asarray(sdt_file.data)  # option to choose channel to include
                data = np.moveaxis(np.stack(data_raw), [-1, 0], [0, 1]) # from (ch, y, x, mt) to ( mt, ch, y, x)
                summed_intensity_image = np.sum(data, axis=0, keepdims=True) # sum over photon_time axis
                # Build metadata
                metadata_list = []
                for measure_info_recarray in sdt_file.measure_info:
                    metadata = {'measure_info': recarray_to_dict(measure_info_recarray),
                                'file_type': 'sdt'}
                    metadata_list.append(metadata)
        # arguments for TCSPC stack
        add_kwargs = {'channel_axis': 1, 'metadata': metadata_list}
        layer_type = "image"
        layer_data.append((data, add_kwargs, layer_type))
        # arguments for intensity image
        add_kwargs = {'channel_axis': 1, 'metadata': metadata_list, 'name': 'summed_intensity_image_' + Path(path).stem}
        layer_data.append((summed_intensity_image, add_kwargs, layer_type))
    return layer_data

# Read single ptu file
def read_single_ptu_file(path):
    # create list of metadata for each channel
    metadata_list = []
    ptu_file = PTUreader(path, print_header_data = False)
    
    data, _ = ptu_file.get_flim_data_stack()
    # Move xy dimensions to the end
    data = np.moveaxis(data, [0, 1], [-2, -1])
    data = np.moveaxis(data, 0, 1) # from (ch, mt, y, x) to (mt, ch, y, x)
    summed_intensity_image = np.sum(data, axis=0, keepdims=True) # sum over photon_time axis

    metadata = ptu_file.head
    metadata['file_type'] = 'ptu'
    # Add same metadata to each channel
    # TO DO: get laser frequency for multiple channels, similar to 
    # how it was done for sdt (not sure if possible, laser info in metadata looks the same). 
    # Currently duplicating metadata.
    for channel in range(data.shape[1]):
        metadata_list.append(metadata)
    return data, summed_intensity_image, metadata_list

def read_ptu_data_2D(path):
    ptu_file = PTUreader(path, print_header_data = False)
    image, _ = ptu_file.get_flim_data_stack()
    # move x,y to the end
    image = np.moveaxis(image, [0, 1], [-2, -1])
    return image

def read_ptu_3D_data(file_paths, image_slice_shape):
    file_paths = natsorted(file_paths)
    z_list = []
    for file_path in file_paths:
        if file_path.suffix == '.ptu':
            current_t, current_z = get_current_tz(file_path)
            data = read_ptu_data_2D(file_path)
            if current_z is not None:
                image = np.zeros(image_slice_shape, dtype=np.uint16)
                image[:data.shape[0], :data.shape[1], :data.shape[2], :data.shape[3]] = data
                z_list.append(image)
    image_3D = np.stack(z_list)
    # move channel and microtime to the beginning (putting z behind them): (ch, mt, z, y, x)
    image_3D = np.moveaxis(image_3D, [-4, -3], [0, 1])
    return image_3D

@dask.delayed(pure=True)
def read_ptu_data_3D_delayed(file_paths, image_slice_shape):
    return read_ptu_3D_data(file_paths, image_slice_shape)

def get_current_tz(file_path):
    pattern_t = '_t(\d+)'
    pattern_z = '_z(\d+)'
    current_t, current_z = None, None
    file_name = file_path.stem
    matches_z = re.search(pattern_z, file_name)
    if matches_z is not None:
        current_z = int(matches_z.group(1)) #.zfill(2)
    matches_t = re.search(pattern_t, file_name)
    if matches_t is not None:
        current_t = int(matches_t.group(1))
    return current_t, current_z

def get_max_zslices(file_paths):
    max_z = max([get_current_tz(file_path) for file_path in file_paths if file_path.suffix == '.ptu'])[1]
    if max_z is None:
        return 1
    return max_z

def get_max_time(file_paths):
    max_time = max([get_current_tz(file_path) for file_path in file_paths if file_path.suffix == '.ptu'])[0]
    if max_time is None:
        return 1
    return max_time

def get_stack_estimated_sizes(file_paths):
    max_t = get_max_time(file_paths)
    max_z = get_max_zslices(file_paths)
    time_stack_size = 0
    for file_path in file_paths:
        if file_path.suffix == '.ptu':
            file_size = file_path.stat().st_size / 1e6 # in MB
            time_stack_size += file_size
    z_stack_estimated_size = time_stack_size / max_t
    
    return z_stack_estimated_size, time_stack_size

def get_structured_list_of_paths(file_paths):
    t_path_list = []
    z_path_list = []
    file_paths = natsorted(file_paths)
    previous_t = 1
    for file_path in file_paths:
        if file_path.suffix == '.ptu':
            current_t, current_z = get_current_tz(file_path)
            if current_t is not None:
                if current_t > previous_t:
                    t_path_list.append(z_path_list)
                    z_path_list = []
                    previous_t = current_t
                z_path_list.append(file_path)
    # If no timepoints, z+path_list is file_paths
    if current_t is None:
        z_path_list = file_paths
    # Append last timepoint
    t_path_list.append(z_path_list)
    return t_path_list

def make_full_numpy_stack(file_paths, image_slice_shape, image_dtype):
     # Make a dask stack
    z_list, t_list = [], []
    previous_t = 1
    for file_path in file_paths:
        if file_path.suffix == '.ptu':
            current_t, current_z = get_current_tz(file_path)
            #If time changed, append to t_list and clear z_list
            if current_t is not None:
                if current_t > previous_t:
                    z_stack = np.stack(z_list)
                    t_list.append(z_stack)
                    z_list = []
                    previous_t = current_t
            data = read_ptu_data_2D(file_path)
            # summed_intensity_image
            # metadata_list
            if current_z is not None:
                z_slice = np.zeros(image_slice_shape, dtype=image_dtype)
                z_slice[:data.shape[0], :data.shape[1], :data.shape[2], :data.shape[3]] = data
                z_list.append(z_slice)
    # If no timepoints, make zstack
    if current_t is None:
        z_stack = np.stack(z_list)
    # Append last time point
    t_list.append(z_stack)
    stack = np.stack(t_list)
    stack =  np.moveaxis(stack, [-4, -3], [1, 2]) # from (t,z,ch,mt, y, x) to (t, ch, mt, z, y, x)
    return stack

def make_dask_stack(file_paths, image_slice_shape, image_dtype):
    # Get maximum time and z from file names
    max_z = get_max_zslices(file_paths)
    max_t = get_max_time(file_paths)

    # Get zstack max shape (ch, mt, z, y, x)
    image_stack_shape = (*image_slice_shape[:-2], max_z, *image_slice_shape[-2:])
    # Get list of file_paths arranged as a time path list of z slices lists
    t_path_list = get_structured_list_of_paths(file_paths)

    lazy_images = [read_ptu_data_3D_delayed(z_path_list, image_slice_shape=image_slice_shape) for z_path_list in t_path_list]

    arrays = [da.from_delayed(lazy_image,           # Construct a small Dask array
                            dtype=image_dtype,      # for every lazy value
                            shape=image_stack_shape)
            for lazy_image in lazy_images]

    stack = da.stack(arrays, axis=0)                # Stack all small Dask arrays into one
    # The line below seems to slow down interactivity in napari
    # stack = da.moveaxis(stack, 0, -4)               # from (t, ch, mt, z, y, x) to (ch, mt, t, z, y, x)
    # Get chunk size in MBytes
    chunk_size_MBytes = np.cumprod(stack.chunksize)[-1] * stack.itemsize / 1e6 #MB per chunk
    # Rechunk if z_stcak is too large (may slow down 3D display, but at least loads data)
    if chunk_size_MBytes > 1e3: # if larger than 1GB (1000MB)
        stack = stack.rechunk({-3: 'auto'}, block_size_limit=1e9) # rechunk z axis (-3). chunks must be smaller than 1e9 bytes (1GB)
    return stack

def read_ptu_stack(path):
    # Get list of file paths
    file_paths = natsorted([file_path for file_path in path.iterdir()])   
    
    # TO DO: offer fast reading option by calculating max shape from metadata (array may become bigger)
    # Go through files to get max shape (number of photon bins may vary from image to image)
    shapes_list = []
    for file_path in file_paths:
        if file_path.suffix == '.ptu':
            ptu_file = PTUreader(file_path, print_header_data = False)
            shapes_list.append((np.unique(ptu_file.channel).size, # number of channels (ch)
                                np.unique(ptu_file.tcspc).size,   # number of photon bins (microtime or mt)
                                ptu_file.y_size,                  # y shape
                                ptu_file.x_size))                 # x shape
    # Get slice max shape (ch, mt, y, x)
    slice_max_shape = max(shapes_list)
    # Get data type from last ptu file read
    image_dtype = ptu_file.get_flim_data_stack()[0].dtype
    # Estimate stack sizes
    z_stack_estimated_MBytes, time_stack_MBytes = get_stack_estimated_sizes(file_paths)

    # Choose whether to read full stack or to make dask arrays
    # If full stack is smaller then 4GB, read as numpy
    if time_stack_MBytes < 4e3: #4GB
        # read full stack
        data = make_full_numpy_stack(file_paths, image_slice_shape=slice_max_shape, image_dtype=image_dtype)
        # make summed intensity from second dimension (axis=2) (microtime)
        summed_intensity_image = np.sum(data, axis=2, keepdims=True)
    else:
        # If z_stack is bigger then 4GB, make a dask array where each chunk is a timepoint (single chunck for single timepoint)
        # But rechunk is zstack is too big
        data = make_dask_stack(file_paths, image_slice_shape=slice_max_shape, image_dtype=image_dtype)
        # make summed intensity from second dimension (axis=2) (microtime)
        summed_intensity_image = da.sum(data, axis=2, keepdims=True)
    metadata_list = []
    return data, summed_intensity_image, metadata_list



def read_ptu_metadata(path):
    ptu_file = PTUreader(path, print_header_data = False)
    metadata = ptu_file.head
    metadata['file_type'] = 'ptu'
    return metadata




