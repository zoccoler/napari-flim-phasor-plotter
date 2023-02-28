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
    print(paths)
    
    stack = False
    if not paths[0].is_file():
        stack = True
        
    layer_data = []
    for path in paths:
        print(path)
        # Assume stack if paths are folders 
        if not path.is_file():
            # get data from ptu files and metadata
            if len([p for p in path.glob('*.ptu')]) > 0: 
                data, summed_intensity_image, metadata_list = read_ptu_stack(path)
            
        else:
            file_path = path
             # get data from ptu files and metadata
            if file_path.suffix == '.ptu':
                data, summed_intensity_image, metadata_list = read_ptu_file(file_path)
            # get data from sdt files
            elif file_path.suffix == '.sdt':
                sdt_file = sdtfile.SdtFile(file_path)  # header to be implemented
                data_raw = np.asarray(sdt_file.data)  # option to choose channel to include
                data = np.moveaxis(np.stack(data_raw), -1, 1)
                summed_intensity_image = np.sum(data, axis=1) # sum over photon_time axis
                # Build metadata
                metadata_list = []
                for measure_info_recarray in sdt_file.measure_info:
                    metadata = {'measure_info': recarray_to_dict(measure_info_recarray),
                                'file_type': 'sdt'}
                    metadata_list.append(metadata)
        # arguments for TCSPC stack
        add_kwargs = {'channel_axis': 0, 'metadata': metadata_list}
        layer_type = "image"
        layer_data.append((data, add_kwargs, layer_type))
        # arguments for intensity image
        add_kwargs = {'channel_axis': 0, 'metadata': metadata_list, 'name': 'summed_intensity_image_' + Path(path).stem}
        layer_data.append((summed_intensity_image, add_kwargs, layer_type))
    return layer_data

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
    max_time = get_max_time(file_paths)
    max_z = get_max_zslices(file_paths)
    time_stack_size = 0
    for file_path in file_paths:
        if file_path.suffix == '.ptu':
            file_size = file_path.stat().st_size / 1e6 # in MB
            time_stack_size += file_size
    z_stack_estimated_size = time_stack_size / max_time
    
    return z_stack_estimated_size, time_stack_size

def read_ptu_stack(path):
    # Get list of file paths
    file_paths = natsorted([file_path for file_path in path.iterdir()])
    # Get maximum time and z (returns None if not present)
    max_time, max_z = max([get_current_tz(file_path) for file_path in file_paths if file_path.suffix == '.ptu'])
    # Estimate stack sizes
    z_stack_estimated_size, time_stack_size = get_stack_estimated_sizes(file_paths)
    
    # TO DO: offer fast reading option by calculating max shape from metadata (array may become bigger)
    # Go through files to get max shape (number of photon bins may vary from image to image)
    shapes_list = []
    for file_path in file_paths:
        if file_path.suffix == '.ptu':
            ptu_file = PTUreader(file_path, print_header_data = False)
            shapes_list.append((np.unique(ptu_file.channel).size, # number of channels
                                np.unique(ptu_file.tcspc).size,   # number of photon bins
                                ptu_file.y_size,                  # y shape
                                ptu_file.x_size))                 # x shape
    # Get image slice shape (ch, mt, y, x)
    image_slice_shape = max(shapes_list)
    # Get data type from last ptu file read
    image_dtype = ptu_file.get_flim_data_stack()[0].dtype

    # Choose whether to read full stack or to make dask arrays
    # If full stack is small, read as numpy (using 1 for now for testing)
    if time_stack_size < 1:#8e3: #8GB
        # read full stack
        data = make_full_numpy_stack(file_paths, image_slice_shape, image_dtype)
    else:
        # If z_stack small, make a dask array where each chunk is a timepoint (single chunck for single timepoint)
        # NOT WORKING, rechunking too slow, test MINIMAL EXAMPLE IN JUPYTER NOTEBOOK
        if z_stack_estimated_size < 8e3: # 10GB
            # If z_stack_estimated_size is not big:
            image_stack_shape = list(image_slice_shape)
            image_stack_shape.insert(0, max_z)
            image_stack_shape = tuple(image_stack_shape)
            data = make_dask_timelapse_of_3D_stacks(file_paths, image_stack_shape, image_dtype)
        # If zstack is too large, then make a dask array where each chunk is a z-slice (not practicak with napari, becomes too slow)
        else:
            data = make_dask_timelapse_of_dask_2D_slices(file_paths, image_slice_shape, image_dtype)
    # maks summed intensity from second dimension (axis=1) (microtime)
    summed_intensity_image = da.sum(data, axis=1)
  
    # The code below works!! But napari becomes super slow when moving the sliders...
    # # Make a dask stack
    # z_list, t_list, z_summed_intensity_list, t_summed_intensity_list = [], [], [], []
    # previous_t = 1
    # for file_path in file_paths:
    #     if file_path.suffix == '.ptu':
    #         current_t, current_z = get_current_tz(file_path)
    #         #If time changed, append to t_list and clear z_list
    #         if current_t is not None:
    #             if current_t > previous_t:
    #                 t_list.append(da.stack(z_list, axis=0))
    #                 # t_summed_intensity_list.append(da.stack(z_summed_intensity_list, axis=0))
    #                 z_list = []
    #                 z_summed_intensity_list = []
    #                 previous_t = current_t
    #         # TO DO: delayed reading with dask
    #         # TO DO: reading function should return single image, not tuple
    #         data = da.from_delayed(read_ptu_data_2D_delayed(file_path), shape=image_shape, dtype=image_dtype)
    #         summed_intensity_image = da.from_delayed(read_ptu_summed_intensity_image_delayed(file_path), 
    #                                                  shape=tuple([x for i,x in enumerate(image_shape) if i!=1]),
    #                                                  dtype=image_dtype)
    #         # summed_intensity_image
    #         # metadata_list
    #         if current_z is not None:
    #             print(file_path.stem)
    #             print(data.shape)
    #             # TO DO: Add as delayed?
    #             # image = np.zeros(image_shape, dtype=np.uint16)
    #             # # Try some broadcast function instead
    #             # image[:data.shape[0], :data.shape[1], :data.shape[2], :data.shape[3]] = data
    #             z_list.append(data)
    #             z_summed_intensity_list.append(summed_intensity_image)
    # # Append last time point
    # t_list.append(da.stack(z_list, axis=0))
    # t_summed_intensity_list.append(da.stack(z_summed_intensity_list, axis=0))
    # data = da.stack(t_list)
    # summed_intensity_image = da.stack(t_summed_intensity_list)
    # data =  da.moveaxis(data, [-4, -3], [0, 1])
    # summed_intensity_image = da.moveaxis(summed_intensity_image, -3, 0)

    metadata_list = []
    return data, summed_intensity_image, metadata_list

@dask.delayed
def read_ptu_data_2D_delayed(path):
    return read_ptu_data_2D(path)

def read_ptu_data_2D(path):
    ptu_file = PTUreader(path, print_header_data = False)
    image, _ = ptu_file.get_flim_data_stack()
    # move x,y to the end
    image = np.moveaxis(image, [0, 1], [-2, -1])
    return image

@dask.delayed
def read_ptu_data_3D_delayed(file_paths, image_slice_shape):
    return read_ptu_3D_data(file_paths, image_slice_shape)

def read_ptu_3D_data(file_paths, image_slice_shape):
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
                print(file_path.stem)
                print(data.shape)
                z_slice = np.zeros(image_slice_shape, dtype=image_dtype)
                z_slice[:data.shape[0], :data.shape[1], :data.shape[2], :data.shape[3]] = data
                z_list.append(z_slice)
    # If no timepoints, make zstack
    if current_t is None:
        z_stack = np.stack(z_list)
        t_list.append(z_stack)
    # Append last time point
    t_list.append(z_stack)
    stack = np.stack(t_list)
    stack =  np.moveaxis(data, [-4, -3], [0, 1])
    return stack
    
def make_dask_timelapse_of_3D_stacks(file_paths, image_stack_shape, image_dtype):
    # Make a dask stack
    t_list = []
    z_path_list = []
    previous_t = 1
    for file_path in file_paths:
        if file_path.suffix == '.ptu':
            current_t, current_z = get_current_tz(file_path)
            #If time changed, append to t_list and clear z_list
            if current_t is not None:
                if current_t > previous_t:
                    z_stack = da.from_delayed(read_ptu_data_3D_delayed(z_path_list, image_slice_shape = image_stack_shape[1:]),
                                              shape=image_stack_shape, dtype=image_dtype)
                    t_list.append(z_stack)
                    z_path_list = []
                    previous_t = current_t
                else:
                    z_path_list.append(file_path)
    # If no timepoints, make zstack
    if current_t is None:
        z_path_list = file_paths
        z_stack = da.from_delayed(read_ptu_data_3D_delayed(z_path_list, image_slice_shape = image_stack_shape[1:]),
                                              shape=image_stack_shape, dtype=image_dtype)
    # Append last time point
    t_list.append(z_stack)
    dask_timelapse_of_3D_stacks = da.stack(t_list)
    chunk = (len(t_list), image_stack_shape[0], image_stack_shape[1], 1, 1, 1) # t, z, ch, mt, y, x
    dask_timelapse_of_3D_stacks = dask_timelapse_of_3D_stacks.rechunk(chunk) # too slow, never finishes....
    # move channel and microtime to the beginning (putting t behind them): (ch, mt, t, z, y, x)
    dask_timelapse_of_3D_stacks =  da.moveaxis(dask_timelapse_of_3D_stacks, [-5, -4], [0, 1])
    return dask_timelapse_of_3D_stacks

def make_dask_timelapse_of_dask_2D_slices(file_paths, image_slice_shape, image_dtype):
    # Make a dask stack
    z_list, t_list = [], []
    previous_t = 1
    for file_path in file_paths:
        if file_path.suffix == '.ptu':
            current_t, current_z = get_current_tz(file_path)
            #If time changed, append to t_list and clear z_list
            if current_t is not None:
                if current_t > previous_t:
                    t_list.append(da.stack(z_list, axis=0))
                    z_list = []
                    previous_t = current_t
            z_slice = da.from_delayed(read_ptu_data_2D_delayed(file_path), shape=image_slice_shape, dtype=image_dtype)
            if current_z is not None:
                print(file_path.stem)
                print(z_slice.shape)
                z_list.append(z_slice)
    # Append last time point
    t_list.append(da.stack(z_list, axis=0))
    dask_timelapse_of_dask_2D_slices = da.stack(t_list)
    dask_timelapse_of_dask_2D_slices =  da.moveaxis(dask_timelapse_of_dask_2D_slices, [-4, -3], [0, 1])
    return dask_timelapse_of_dask_2D_slices





# To HANDLE LATER
@dask.delayed
def read_ptu_summed_intensity_image_delayed(path):
    return read_ptu_summed_intensity_image(path)

def read_ptu_summed_intensity_image(path):
    data = read_ptu_data_2D(path)
    summed_intensity_image = np.sum(data, axis=1) # sum over photon_time axis
    return summed_intensity_image

def read_ptu_metadata(path):
    ptu_file = PTUreader(path, print_header_data = False)
    metadata = ptu_file.head
    metadata['file_type'] = 'ptu'
    return metadata

# Read single ptu file
def read_ptu_file(path):
    # create list of metadata for each channel
    metadata_list = []
    ptu_file = PTUreader(path, print_header_data = False)
    
    data, _ = ptu_file.get_flim_data_stack()
    # Move xy dimensions to the end
    # TO DO: handle 3D images
    data = np.moveaxis(data, [0, 1], [-2, -1])
    summed_intensity_image = np.sum(data, axis=1) # sum over photon_time axis
    metadata = ptu_file.head
    metadata['file_type'] = 'ptu'
    # Add same metadata to each channel
    # TO DO: get laser frequency for multiple channels, similar to 
    # how it was done for sdt below. Currently duplicating metadata.
    for channel in range(data.shape[0]):
        metadata_list.append(metadata)
    return data, summed_intensity_image, metadata_list

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
