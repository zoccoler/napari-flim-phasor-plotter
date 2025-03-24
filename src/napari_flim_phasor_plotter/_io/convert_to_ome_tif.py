from magicgui import magic_factory
import pathlib
from napari.utils import notifications

from magicgui.tqdm import tqdm

@magic_factory(call_button='Convert', layout="vertical",
               folder_path={'widget_type': 'FileEdit',
                            'mode': 'd'},
                x_pixel_size={'widget_type': 'FloatSpinBox',
                            'label': 'X Pixel Size',
                            'step': 0.001, 'min': 0},
                y_pixel_size={'widget_type': 'FloatSpinBox',
                            'label': 'Y Pixel Size',
                            'step': 0.001, 'min': 0},
                z_pixel_size={'widget_type': 'FloatSpinBox',
                            'label': 'Z Pixel Size',
                            'step': 0.001, 'min': 0},
                pixel_size_unit={'widget_type': 'ComboBox',
                            'label': 'Pixel Size Unit',
                            'choices': ['pm', 'nm', 'um', 'mm', 'cm', 'm']},
                time_resolution_per_slice={'widget_type': 'FloatSpinBox',
                            'label': 'Time Resolution per Slice',
                            'tooltip': 'Time resolution per image or z-slice if 3D stack (not time for whole z-stack)',
                            'step': 0.001, 'min': 0},
                time_unit={'widget_type': 'ComboBox',
                            'label': 'Time Unit',
                            'choices': ['fs', 'ps', 'ns', 'us', 'ms', 's']},
                channel_names={'widget_type': 'LineEdit',
                            'label': 'Channel Names',
                            'tooltip': 'Comma separated channel names'},
                micro_time_resolution={'widget_type': 'FloatSpinBox',
                            'label': 'FLIM Time Resolution',
                            'tooltip': 'Time resolution for the TCSPC histogram',
                            'step': 0.001, 'min': 0},
                micro_time_unit={'widget_type': 'ComboBox',
                            'label': 'FLIM Time Unit',
                            'choices': ['fs', 'ps', 'ns', 'us', 'ms', 's']},                           
               cancel_button={'widget_type': 'PushButton',
                              'visible': False,
                              'text': 'Cancel', })
def convert_folder_to_ome_tif(folder_path: pathlib.Path, 
                                x_pixel_size: float = 0,
                                y_pixel_size: float = 0,
                                z_pixel_size: float = 0,
                                pixel_size_unit: str = 'um',
                                time_resolution_per_slice: float = 0,
                                time_unit: str = 's',
                                channel_names: str = '',
                                micro_time_resolution: float = 0,
                                micro_time_unit: str = 'ps',
                              cancel_button: bool = False):
    """ Convert a folder of FLIM images representing an image stack to a OME-TIFF file per timepoint (if timelapse) plus a OME-TIFF file with summed intensity (no FLIM).

    The folder must contain only FLIM images of the same type (e.g. all .ptu files or all .sdt files).
    The file names must be in the format: "name_t000_z000", or "name_z000", or name_"t000", where "t000" is the time point and "z000" is the z slice.
    The z slice and time point must be the last two numbers in the file
    name. The z slice and time point must be separated by an underscore.

    Parameters
    ----------
    folder_path : str
        Path to the folder containing the FLIM images.
    x_pixel_size : float, optional
        Pixel size along the x-axis, by default 0.
    y_pixel_size : float, optional
        Pixel size along the y-axis, by default 0.
    z_pixel_size : float, optional
        Pixel size along the z-axis, by default 0.
    pixel_size_unit : str, optional
        Unit of the pixel size, by default 'um'.
    time_resolution_per_slice : float, optional
        Time resolution per slice, by default 0.
    time_unit : str, optional
        Unit of the time resolution, by default 's'.
    channel_names : str, optional
        Names of the channels, separated by comma, by default ''.
    micro_time_resolution : float, optional
        Time resolution for the TCSPC histogram, by default 0.
    micro_time_unit : str, optional
        Unit of the time resolution for the TCSPC histogram, by default 'ps'.
    
    Returns
    -------
    None
    """
    import numpy as np
    from natsort import natsorted
    from napari_flim_phasor_plotter._reader import get_read_function_from_extension, get_most_frequent_file_extension
    from napari_flim_phasor_plotter._reader import get_max_slice_shape_and_dtype, get_structured_list_of_paths
    from napari_flim_phasor_plotter._reader import get_max_zslices, get_max_time_points, ALLOWED_FILE_EXTENSION
    from napari_flim_phasor_plotter._io.utilities import format_metadata
    import tifffile

    folder_path = pathlib.Path(folder_path)
    file_extension = get_most_frequent_file_extension(folder_path)
    if file_extension not in ALLOWED_FILE_EXTENSION:
        if file_extension == '':
            message = 'Please select a folder containing FLIM images.'
            print(message)
        else:
            message = 'Plugin does not support ' + \
                file_extension + ' . Supported file extensions are: '
            message += ', '.join(ALLOWED_FILE_EXTENSION[:-1])
            print(message)

    if pixel_size_unit == 'um':
        pixel_size_unit = 'µm'
    if micro_time_unit == 'us':
        micro_time_unit = 'µs'
    if time_unit == 'us':
        time_unit = 'µs'

    if channel_names == '':
        channel_names = []
    else:
        # Split channel names by comma and stores them in a list
        channel_names = channel_names.split(',')

    # Get appropriate read function from file extension
    imread = get_read_function_from_extension[file_extension]
    print('Stack')

    # Get all file path with specified file extension
    file_paths = natsorted([file_path for file_path in folder_path.iterdir(
    ) if file_path.suffix == file_extension])
    # Get maximum shape and dtype from file names (file names must be in the format: "name_t000_z000")
    image_slice_shape, image_dtype = get_max_slice_shape_and_dtype(
        file_paths, file_extension)
    # If single channel, add a new axis
    if len(image_slice_shape) == 3:
        image_slice_shape = (1, *image_slice_shape)
    # Get maximum time and z from file names
    max_z = get_max_zslices(file_paths, file_extension)
    max_time_point = get_max_time_points(file_paths, file_extension)
    # Build stack shape with the fllowing convention: (channel, time, z, y, x)
    stack_shape = (
        image_slice_shape[0], max_time_point+1, max_z+1, *image_slice_shape[-2:])
    # Create an empty numpy array with the maximum shape and dtype
    numpy_array_summed_intensity = np.zeros(stack_shape, dtype=image_dtype)
    # Get a nested list of time point containing a list of z slices
    list_of_time_point_paths = get_structured_list_of_paths(
        file_paths, file_extension)

    output_path = folder_path / 'OME-TIFs'
    output_path.mkdir(exist_ok=True)
    timelapse = False
    if len(list_of_time_point_paths) > 1:
        timelapse = True

    for z_paths, t in zip(tqdm(list_of_time_point_paths, label='time_points'), range(len(list_of_time_point_paths))):
        stack_shape = (*image_slice_shape[:-2], max_z+1, *image_slice_shape[-2:]) # (channel, ut, z, y, x)
        numpy_array = np.zeros(stack_shape, dtype=image_dtype)
        for path, j in zip(tqdm(z_paths, label='z-slices'), range(len(z_paths))):
            data, flim_metadata = imread(path) # Read single file
            if j==0:
                # Test if format_metadata works with provided inputs
                metadata_timelapse, metadata_single_timepoint = format_metadata(
                    flim_metadata=flim_metadata,
                    stack_shape=numpy_array.shape,
                    x_pixel_size=x_pixel_size,
                    y_pixel_size=y_pixel_size,
                    z_pixel_size=z_pixel_size,
                    pixel_size_unit=pixel_size_unit,
                    time_resolution_per_slice=time_resolution_per_slice,
                    time_unit=time_unit,
                    channel_names=channel_names,
                    micro_time_resolution=micro_time_resolution,
                    micro_time_unit=micro_time_unit,
                    timelapse=timelapse,)
                if metadata_timelapse is None:
                    return
            # Populate numpy array with data
            if len(data.shape) == 3:
                # Consider slice is single channel
                numpy_array[0, :data.shape[0],
                        j, :data.shape[1], :data.shape[2]] = data
            else:
                numpy_array[:data.shape[0], :data.shape[1],
                        j, :data.shape[2], :data.shape[3]] = data
        print(f"Processing timepoint: {t}")
        numpy_array_summed_intensity[:, t, :, :, :] = np.sum(numpy_array, axis=1, dtype=image_dtype) # channel, z, y, x
        # Extract metadata
        metadata_timelapse, metadata_single_timepoint = format_metadata(
            flim_metadata=flim_metadata,
            stack_shape=numpy_array.shape,
            x_pixel_size=x_pixel_size,
            y_pixel_size=y_pixel_size,
            z_pixel_size=z_pixel_size,
            pixel_size_unit=pixel_size_unit,
            time_resolution_per_slice=time_resolution_per_slice,
            time_unit=time_unit,
            channel_names=channel_names,
            micro_time_resolution=micro_time_resolution,
            micro_time_unit=micro_time_unit,
            timelapse=timelapse,)
        print(f"Saving OME-TIF...")

        if timelapse:
            t_string = str(t).zfill(len(str(len(list_of_time_point_paths))))
            output_file_name =  folder_path.stem + f'_t{t_string}.ome.tif'
        else:
            output_file_name = folder_path.stem + '.ome.tif'
        with tifffile.TiffWriter(output_path / output_file_name, ome=True) as tif:
            tif.write(numpy_array, metadata=metadata_single_timepoint, compression='zlib')
    output_file_name = folder_path.stem + '_summed_intensity.ome.tif'
    with tifffile.TiffWriter(output_path / output_file_name, ome=True) as tif:
        tif.write(numpy_array_summed_intensity[:], metadata=metadata_timelapse, compression='zlib')
    print('Done')
    notifications.show_info(f'Conversion to OME-TIFF completed.\nOME-TIFFs saved in\n{output_path}')

@magic_factory(call_button='Convert', layout="vertical",
            file_path={'widget_type': 'FileEdit',
                        'mode': 'r'},
            x_pixel_size={'widget_type': 'FloatSpinBox',
                        'label': 'X Pixel Size',
                        'step': 0.001, 'min': 0},
            y_pixel_size={'widget_type': 'FloatSpinBox',
                        'label': 'Y Pixel Size',
                        'step': 0.001, 'min': 0},
            pixel_size_unit={'widget_type': 'ComboBox',
                        'label': 'Pixel Size Unit',
                        'choices': ['pm', 'nm', 'um', 'mm', 'cm', 'm']},
            time_resolution_per_slice={'widget_type': 'FloatSpinBox',
                        'label': 'Time Resolution per Slice',
                        'tooltip': 'Time resolution per image or z-slice if 3D stack (not time for whole z-stack)',
                        'step': 0.001, 'min': 0},
            time_unit={'widget_type': 'ComboBox',
                        'label': 'Time Unit',
                        'choices': ['fs', 'ps', 'ns', 'us', 'ms', 's']},
            channel_names={'widget_type': 'LineEdit',
                        'label': 'Channel Names',
                        'tooltip': 'Comma separated channel names'},
            micro_time_resolution={'widget_type': 'FloatSpinBox',
                        'label': 'FLIM Time Resolution',
                        'tooltip': 'Time resolution for the TCSPC histogram',
                        'step': 0.001, 'min': 0},
            micro_time_unit={'widget_type': 'ComboBox',
                        'label': 'FLIM Time Unit',
                        'choices': ['fs', 'ps', 'ns', 'us', 'ms', 's']},                           
            cancel_button={'widget_type': 'PushButton',
                            'visible': False,
                            'text': 'Cancel', })
def convert_file_to_ome_tif(file_path: pathlib.Path, 
                                x_pixel_size: float = 0,
                                y_pixel_size: float = 0,
                                pixel_size_unit: str = 'um',
                                channel_names: str = '',
                                micro_time_resolution: float = 0,
                                micro_time_unit: str = 'ps',
                              cancel_button: bool = False):
    """ Convert a file to a OME-TIFF file.

    The file must be a FLIM image of the same type (e.g. .ptu or .sdt).
    The plugin will generate a single OME-TIFF file, replacing the time axis ('T') with the photon counts axis.
    If the file contains multiple timepoints, the plugin will take the first timepoint.

    Parameters
    ----------
    file_path : str
        Path to the folder containing the FLIM images.
    x_pixel_size : float, optional
        Pixel size along the x-axis, by default 0.
    y_pixel_size : float, optional
        Pixel size along the y-axis, by default 0.
    pixel_size_unit : str, optional
        Unit of the pixel size, by default 'um'.
    channel_names : List[str], optional
        Names of the channels, by default [].
    micro_time_resolution : float, optional
        Time resolution for the TCSPC histogram, by default 0.
    micro_time_unit : str, optional
        Unit of the time resolution for the TCSPC histogram, by default 'ps'.
    
    Returns
    -------
    None
    """
    import numpy as np
    from natsort import natsorted
    from napari_flim_phasor_plotter._reader import get_read_function_from_extension, get_most_frequent_file_extension
    from napari_flim_phasor_plotter._reader import ALLOWED_FILE_EXTENSION
    from napari_flim_phasor_plotter._io.utilities import format_metadata
    import tifffile

    file_path = pathlib.Path(file_path)
    file_extension = get_most_frequent_file_extension(file_path)
    if file_extension not in ALLOWED_FILE_EXTENSION:
        if file_extension == '':
            message = 'Please select a folder containing FLIM images.'
            print(message)
        else:
            message = 'Plugin does not support ' + \
                file_extension + ' . Supported file extensions are: '
            message += ', '.join(ALLOWED_FILE_EXTENSION[:-1])
            print(message)

    if pixel_size_unit == 'um':
        pixel_size_unit = 'µm'
    if micro_time_unit == 'us':
        micro_time_unit = 'µs'

    if channel_names == '':
        channel_names = []
    else:
        # Split channel names by comma and stores them in a list
        channel_names = channel_names.split(',')
    # Get appropriate read function from file extension
    imread = get_read_function_from_extension[file_extension]
    print('Single file')
    data, flim_metadata = imread(file_path)
    # Add channel dimension in case it is missing
    if len(data.shape) == 3:
        data = data[np.newaxis, :]
    # Add unitary axis for z
    data = data[:, :, np.newaxis]
    metadata_timelapse, metadata_single_timepoint = format_metadata(
        flim_metadata=flim_metadata,
        stack_shape=data.shape,
        x_pixel_size=x_pixel_size,
        y_pixel_size=y_pixel_size,
        pixel_size_unit=pixel_size_unit,
        channel_names=channel_names,
        micro_time_resolution=micro_time_resolution,
        micro_time_unit=micro_time_unit,
        timelapse=False,)
    if metadata_timelapse is None:
        return
    print(f"Saving OME-TIF...")
    output_path = file_path.parent / 'OME-TIFs'
    output_path.mkdir(exist_ok=True)
    output_file_name = file_path.stem + '.ome.tif'
    with tifffile.TiffWriter(output_path / output_file_name, ome=True) as tif:
        tif.write(data, metadata=metadata_single_timepoint, compression='zlib')
    print('Done')
    notifications.show_info(f'Conversion to OME-TIFF completed.\nOME-TIFFs saved in\n{output_path}')