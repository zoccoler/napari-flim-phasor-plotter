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
    
    stack = False
    if not paths[0].is_file():
        stack = True
        
    layer_data = []
    for path in paths:
        print(path)
        # Assume stack if paths are folders 
        if not path.is_file():
            # Get list of file paths
            file_paths = [file_path for file_path in path.iterdir()]
            # Sort file_paths
            pattern_t = '_t(\d+)' # numbers following '_t'
            pattern_z = '_z(\d+)' # numbers following '_z'
            file_paths = sorted(file_paths, key=lambda x: (int(re.findall(pattern_t, x.stem)[0]) if re.findall(pattern_t, x.stem) else 0,
                                                    int(re.findall(pattern_z, x.stem)[0]) if re.findall(pattern_z, x.stem) else 0))
            # To do: handle Nones
            tz_max = max([get_current_tz(file_path) for file_path in file_paths])
            z_list, t_list = [], []
            previous_t = 1
            for file_path in file_paths:
                current_z, current_t = get_current_tz(file_path)
                # If time changed, append to t_list and clear z_list
                if current_t is not None:
                    if current_t > previous_t:
                        t_list.append(da.stack(z_list, axis=0))
                        z_list = []
                        previous_t = current_t
                if file_path.suffix == '.ptu':
                    data, summed_intensity_image, metadata_list = read_ptu_file(path)
                    if current_z is not None:
                        z_list.append(data)
            data = da.stack(t_list)   
        else:
             # get data from ptu files
            if file_path.suffix == '.ptu':
                data, summed_intensity_image, metadata_list = read_ptu_file(path)
            # get data from sdt files
            elif path.suffix == '.sdt':
                sdt_file = sdtfile.SdtFile(path)  # header to be implemented
                data_raw = np.asarray(sdt_file.data)  # option to choose channel to include
                data = np.moveaxis(np.stack(data_raw), -1, 1)
                summed_intensity_image = np.sum(data, axis=1) # sum over photon_time axis

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
    return current_z, current_t
