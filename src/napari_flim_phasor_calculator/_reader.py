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
    layer_data = []
    for path in paths:
        # create list of metadata for each channel
        metadata_list = []
        # get data from ptu files
        if path.lower().endswith('.ptu'):
            ptu_file = PTUreader(path, print_header_data = False)
            data, _ = ptu_file.get_flim_data_stack()
            # Move xy dimensions to the end
            # TO DO: handle 3D images
            data = np.moveaxis(data, [0, 1], [-2, -1])
            intensity_image = np.sum(data, axis=1) # sum over photon_time axis
            # optional kwargs for the corresponding viewer.add_* method
            # TO DO: get laser frequency for multiple channels, similar to 
            # how it was done for sdt below. Currently duplicating metadata.
            metadata = ptu_file.head
            metadata['file_type'] = 'ptu'
            # Add same metadata to each channel
            for channel in range(data.shape[0]):
                metadata_list.append(metadata)
        # get data from sdt files
        elif path.lower().endswith('.sdt'):
            sdt_file = sdtfile.SdtFile(path)  # header to be implemented
            data_raw = np.asarray(sdt_file.data)  # option to choose channel to include
            data = np.moveaxis(np.stack(data_raw), -1, 1)
            intensity_image = np.sum(data, axis=1) # sum over photon_time axis

            for measure_info_recarray in sdt_file.measure_info:
                metadata = {'measure_info': recarray_to_dict(measure_info_recarray),
                            'file_type': 'sdt'}
                metadata_list.append(metadata)
        # arguments for TCSPC stack
        add_kwargs = {'channel_axis': 0, 'metadata': metadata_list}
        layer_type = "image"
        layer_data.append((data, add_kwargs, layer_type))
        # arguments for intensity image
        add_kwargs = {'channel_axis': 0, 'metadata': metadata_list, 'name': 'intensity_image_' + Path(path).stem}
        layer_data.append((intensity_image, add_kwargs, layer_type))
    return layer_data
