from napari.utils import notifications
import warnings

def get_valid_file_extension(path):
    from napari_flim_phasor_plotter._reader import get_most_frequent_file_extension, ALLOWED_FILE_EXTENSION
    from pathlib import Path
    path = Path(path)
    file_extension = get_most_frequent_file_extension(path)
    if file_extension not in ALLOWED_FILE_EXTENSION:
        if file_extension == '':
            message = ('Please select a folder containing FLIM images.\n',
                       'Accepted file extensions are: ' + ', '.join(ALLOWED_FILE_EXTENSION[:-1]))
            notifications.show_error(message)
            return None
        else:
            message = 'Plugin does not support ' + \
                file_extension + ' .\nSupported file extensions are: '
            message += ', '.join(ALLOWED_FILE_EXTENSION[:-1])
            notifications.show_error(message)
            return None
    return file_extension

def format_metadata(flim_metadata, 
                    stack_shape, 
                    output_axes_order='CTZYX',
                    x_pixel_size = 0, 
                    y_pixel_size = 0, 
                    z_pixel_size = 0, 
                    pixel_size_unit = 'm', 
                    time_resolution_per_slice = 0, 
                    time_unit = 's', 
                    channel_names = [], 
                    micro_time_resolution = 0, 
                    micro_time_unit = 's', 
                    timelapse=True):
    """Format metadata for OME-TIFF based on the provided metadata and XML file.

    Parameters
    ----------
    flim_metadata : List[Dict]
        Metadata from the raw FLIM data file (usually .ptu or .sdt).
    stack_shape : Tuple[int], optional
        Shape of the stack, by default None. Required if no XML file is provided.
    z_pixel_size : float, optional
        Pixel size along the z-axis, by default 0.5. Required if no XML file is provided.
    pixel_size_unit : str, optional
        Unit of the pixel size, by default 'µm'. Required if no XML file is provided.
    time_resolution_per_slice : float, optional
        Time resolution per slice, by default 0.663. Required if no XML file is provided.
    time_unit : str, optional
        Unit of the time resolution, by default 's'. Required if no XML file is provided.
    channel_names : List[str], optional
        Names of the channels, by default ['0', '1']. Required if no XML file is provided.
    axes : str, optional
        Axes of the data, by default 'CTZYX'.
    timelapse : bool, optional
        Whether the data is a timelapse, by default True.

    Returns
    -------
    Tuple[Dict, Dict]
        Metadata for the whole timelapse without photon counts axis and metadata for single timepoint with photon counts axis.
    """
    z_stack = False
    multichannel = False
    if stack_shape is None:
        raise ValueError('stack_shape must be provided')
    if stack_shape[output_axes_order.index('Z')] > 1:
        z_stack = True
    if stack_shape[output_axes_order.index('C')] > 1:
        multichannel = True

    # Build metadata dictionary for timelapsed data
    metadata_timelapse = dict()
    metadata_timelapse['axes'] = output_axes_order
    # Feed user-provided XY pixel sizes if not present in the flim_metadata (metadata from the raw FLIM data file)
    if 'x_pixel_size' not in flim_metadata[0]:
        if x_pixel_size == 0:
            notifications.show_warning('x_pixel_size not found in file metadata,\nit must be provided manually')
            return None, None
        flim_metadata[0]['x_pixel_size'] = x_pixel_size
    else:
        # if provided, assume pixel size unit to be m and convert to provided pixel size unit to be consistent along x, y and z
        if pixel_size_unit == 'pm':
            flim_metadata[0]['x_pixel_size'] = flim_metadata[0]['x_pixel_size'] * 1e12
        elif pixel_size_unit == 'nm':
            flim_metadata[0]['x_pixel_size'] = flim_metadata[0]['x_pixel_size'] * 1e9
        elif pixel_size_unit == 'um':
            flim_metadata[0]['x_pixel_size'] = flim_metadata[0]['x_pixel_size'] * 1e6
        elif pixel_size_unit == 'mm':
            flim_metadata[0]['x_pixel_size'] = flim_metadata[0]['x_pixel_size'] * 1e3
        elif pixel_size_unit == 'cm':
            flim_metadata[0]['x_pixel_size'] = flim_metadata[0]['x_pixel_size'] * 1e2

    if 'y_pixel_size' not in flim_metadata[0]:
        if y_pixel_size == 0:
            notifications.show_warning('y_pixel_size not found in file metadata,\nit must be provided manually')
            return None, None
        flim_metadata[0]['y_pixel_size'] = y_pixel_size
    else:
        # if provided, assume pixel size unit to be m and convert to provided pixel size unit to be consistent along x, y and z
        if pixel_size_unit == 'pm':
            flim_metadata[0]['y_pixel_size'] = flim_metadata[0]['y_pixel_size'] * 1e12
        elif pixel_size_unit == 'nm':
            flim_metadata[0]['y_pixel_size'] = flim_metadata[0]['y_pixel_size'] * 1e9
        elif pixel_size_unit == 'um':
            flim_metadata[0]['y_pixel_size'] = flim_metadata[0]['y_pixel_size'] * 1e6
        elif pixel_size_unit == 'mm':
            flim_metadata[0]['y_pixel_size'] = flim_metadata[0]['y_pixel_size'] * 1e3
        elif pixel_size_unit == 'cm':
            flim_metadata[0]['y_pixel_size'] = flim_metadata[0]['y_pixel_size'] * 1e2
    
    # Fill in x and y pixel sizes metadata for ome-tiff
    metadata_timelapse['PhysicalSizeX'] = flim_metadata[0]['x_pixel_size']
    metadata_timelapse['PhysicalSizeXUnit'] = pixel_size_unit
    metadata_timelapse['PhysicalSizeY'] = flim_metadata[0]['y_pixel_size']
    metadata_timelapse['PhysicalSizeYUnit'] = pixel_size_unit
    # Fill in z pixel size metadata for ome-tiff
    if z_stack:
        if z_pixel_size == 0:
            notifications.show_warning('z_pixel_size must be provided manually')
            return None, None
        metadata_timelapse['PhysicalSizeZ'] = z_pixel_size
        metadata_timelapse['PhysicalSizeZUnit'] = pixel_size_unit
    else:
        # Always provide a z size, even if it is not a stack because output is always be 5D for OME-TIFF
        metadata_timelapse['PhysicalSizeZ'] = 1
        metadata_timelapse['PhysicalSizeZUnit'] = pixel_size_unit
    if timelapse: # If it is a true timelapse (not one having photon counts as the time axis)
        if time_resolution_per_slice == 0:
            notifications.show_warning('time_resolution_per_slice must be provided')
            return None, None
        if z_stack:
            # Time resolution is the time resolution per slice multiplied by the number of z-slices
            time_resolution = time_resolution_per_slice * stack_shape[output_axes_order.index('Z')]
        else:
            # Time resolution is the time resolution per slice (not a 3D stack)
            time_resolution = time_resolution_per_slice
        metadata_timelapse['TimeIncrement'] = time_resolution
        metadata_timelapse['TimeIncrementUnit'] = time_unit
    else:
        # Always provide a time increment, even if it is not a timelapse because output is always be 5D for OME-TIFF
        metadata_timelapse['TimeIncrement'] = 1
        metadata_timelapse['TimeIncrementUnit'] = 's'
    if multichannel:
        metadata_timelapse['Channel'] = dict()
        if channel_names == []:
            channel_names = [("Channel " + str(i)) for i in range(stack_shape[output_axes_order.index('C')])]
        else:
            if len(channel_names) != stack_shape[output_axes_order.index('C')]:
                notifications.show_warning(f'Number of channel names must match the number of channels in the data.\nNumber of channels in the data: {stack_shape[output_axes_order.index("C")]}')
                return None, None
        metadata_timelapse['Channel']['Name'] = channel_names

    # For the single timepoint metadata, replace the time axis with the photon counts axis
    metadata_single_timepoint = metadata_timelapse.copy() 
    if 'tcspc_resolution' in flim_metadata[0] and flim_metadata[0]['tcspc_resolution'] is not None:
        metadata_single_timepoint['TimeIncrement'] = flim_metadata[0]['tcspc_resolution']
        metadata_single_timepoint['TimeIncrementUnit'] = 's'
    else:
        if micro_time_resolution == 0:
            notifications.show_warning('micro_time_resolution must be provided')
            return None, None
        metadata_single_timepoint['TimeIncrement'] = micro_time_resolution
        metadata_single_timepoint['TimeIncrementUnit'] = micro_time_unit
    return metadata_timelapse, metadata_single_timepoint