

def format_metadata(flim_metadata, stack_shape=None, z_pixel_size = 0.5, pixel_size_unit = 'µm', time_resolution_per_slice = 0.663, time_unit = 's', channel_names = ['0', '1'], axes='CTZYX', timelapse=True):
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
    
    if stack_shape is None:
        raise ValueError('stack_shape must be provided if no XML file is provided')
    # If no XML file is provided, use the metadata from the Zarr file along with some manual inputs
    # The time resolution must be calculated depending on the number of z-slices
    time_resolution = time_resolution_per_slice * stack_shape[-3] 
    metadata_timelapse = dict()
    metadata_timelapse['axes'] = axes
    metadata_timelapse['PhysicalSizeX'] = flim_metadata[0]['x_pixel_size']
    metadata_timelapse['PhysicalSizeXUnit'] = pixel_size_unit
    metadata_timelapse['PhysicalSizeY'] = flim_metadata[0]['y_pixel_size']
    metadata_timelapse['PhysicalSizeYUnit'] = pixel_size_unit
    metadata_timelapse['PhysicalSizeZ'] = z_pixel_size
    metadata_timelapse['PhysicalSizeZUnit'] = pixel_size_unit
    if timelapse:
        metadata_timelapse['TimeIncrement'] = time_resolution
        metadata_timelapse['TimeIncrementUnit'] = time_unit
    if 'C' in axes:
        metadata_timelapse['Channel'] = dict()
        metadata_timelapse['Channel']['Name'] = channel_names
        

    metadata_single_timepoint = metadata_timelapse.copy()
    metadata_single_timepoint['TimeIncrement'] = flim_metadata[0]['tcspc_resolution'] * 1e12
    metadata_single_timepoint['TimeIncrementUnit'] = 'ps'

    return metadata_timelapse, metadata_single_timepoint