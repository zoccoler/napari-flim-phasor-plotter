from napari.utils import notifications
import warnings


def get_valid_file_extension(path):
    """Check if the file extension is supported by the plugin."""
    from napari_flim_phasor_plotter._reader import (
        get_most_frequent_file_extension,
        ALLOWED_FILE_EXTENSION,
    )
    from pathlib import Path

    path = Path(path)
    file_extension = get_most_frequent_file_extension(path)
    if file_extension not in ALLOWED_FILE_EXTENSION:
        if file_extension == "":
            message = (
                "Please select a folder containing FLIM images.\n",
                "Accepted file extensions are: "
                + ", ".join(ALLOWED_FILE_EXTENSION[:-1]),
            )
            notifications.show_error(message)
            return None
        else:
            message = (
                "Plugin does not support "
                + file_extension
                + " .\nSupported file extensions are: "
            )
            message += ", ".join(ALLOWED_FILE_EXTENSION[:-1])
            notifications.show_error(message)
            return None
    return file_extension


def format_metadata(
    flim_metadata,
    stack_shape,
    output_axes_order="CTZYX",
    x_pixel_size=0,
    y_pixel_size=0,
    z_pixel_size=0,
    pixel_size_unit="m",
    time_resolution_per_slice=0,
    time_unit="s",
    channel_names=[],
    micro_time_resolution=0,
    micro_time_unit="s",
    timelapse=True,
):
    """Format metadata for OME-TIFF based on the provided metadata and XML file.

    Parameters
    ----------
    flim_metadata : List[Dict]
        Metadata from the raw FLIM data file (usually .ptu or .sdt).
    stack_shape : Tuple[int]
        Shape of the stack.
    output_axes_order : str, optional
        Order of the axes in the output data, by default 'CTZYX'.
    x_pixel_size : float, optional
        Pixel size along the x-axis, by default 0 which means missing information.
        The value will first be searched in the metadata.
        If x_pixel_size is found in the metadata, the unit is assumed to be 'm'.
        If x_pixel_size is not found in the metadata and this parameter equals to 0, a warning is shown and the function returns None.
        If x_pixel_size is not found in the metadata and this parameter is different from 0, the value will be taken from this parameter and the unit will be taken from the pixel_size_unit parameter.
    y_pixel_size : float, optional
        Pixel size along the y-axis, by default 0 which means missing information.
        The value will be taken from the metadata.
        If y_pixel_size is found in the metadata, the unit is assumed to be 'm'.
        If y_pixel_size is not found in the metadata and this parameter equals to 0, a warning is shown and the function returns None.
        If y_pixel_size is not found in the metadata and this parameter is different from 0, the value will be taken from this parameter and the unit will be taken from the pixel_size_unit parameter.
    z_pixel_size : float, optional
        Pixel size along the z-axis, by default 0 which means missing information.
        If the size of the z-axis is 1, the value will be set to 1.
        If the size of the z-axis is greater than 1 and this parameter equals to 0, a warning is shown and the function returns None.
        If the size of the z-axis is greater than 1 and this parameter is different from 0, the value will be taken from this parameter and the unit will be taken from the pixel_size_unit parameter.
    pixel_size_unit : str, optional
        Unit of the pixel size, by default 'm'.
        This parameter is overwritten if 'x_pixel_size' or 'y_pixel_size' are found in the metadata.
    time_resolution_per_slice : float, optional
        Time resolution per slice, by default 0 which means missing information.
        If the timelapse parameter is set to False, this parameter is ignored.
        If the timelapse parameter is set to True and this parameter equals to 0, a warning is shown and the function returns None.
        If the timelapse parameter is set to True and this parameter is different from 0, the value will be taken from this parameter and the unit will be taken from the time_unit parameter.
    time_unit : str, optional
        Unit of the time resolution, by default 's'.
        If timelapse is set to False, this parameter is ignored.
    channel_names : List[str], optional
        Names of the channels, by default [].
        If the number of channel names does not match the number of channels in the data, a warning is shown and the function returns None.
    micro_time_resolution : float, optional
        Time resolution for the photon counts axis, by default 0 which means missing information.
        If the 'tcspc_resolution' is found in the metadata, the unit is assumed to be 's'.
        If the 'tcspc_resolution' is not found in the metadata and this parameter equals to 0, a warning is shown and the function returns None.
        If the 'tcspc_resolution' is not found in the metadata and this parameter is different from 0, the value will be taken from this parameter and the unit will be taken from the micro_time_unit parameter.
    micro_time_unit : str, optional
        Unit of the time resolution for the photon counts axis, by default 's'.
        This parameter is overwritten if the 'tcspc_resolution' is found in the metadata.
    timelapse : bool, optional
        Whether the data is a timelapse, by default False.

    Returns
    -------
    Tuple[Dict, Dict]
        Metadata for the whole timelapse without photon counts axis and metadata for single timepoint with photon counts axis replacing the time dimension axis.
    """
    z_stack = False
    multichannel = False
    if stack_shape is None:
        raise ValueError("stack_shape must be provided")
    if stack_shape[output_axes_order.index("Z")] > 1:
        z_stack = True
    if stack_shape[output_axes_order.index("C")] > 1:
        multichannel = True

    # Build metadata dictionary for timelapsed data
    metadata_timelapse = dict()
    metadata_timelapse["axes"] = output_axes_order
    # Feed user-provided XY pixel sizes if not present in the flim_metadata (metadata from the raw FLIM data file)
    if "x_pixel_size" not in flim_metadata[0]:
        if x_pixel_size == 0:
            notifications.show_warning(
                "x_pixel_size not found in file metadata,\nit must be provided manually"
            )
            return None, None
        flim_metadata[0][
            "x_pixel_size"
        ] = x_pixel_size  # Assign manual pixel size to metadata
    else:
        # if provided, assume pixel size unit to be m and convert to provided pixel size unit to be consistent along x, y and z
        if pixel_size_unit == "pm":
            flim_metadata[0]["x_pixel_size"] = (
                flim_metadata[0]["x_pixel_size"] * 1e12
            )
        elif pixel_size_unit == "nm":
            flim_metadata[0]["x_pixel_size"] = (
                flim_metadata[0]["x_pixel_size"] * 1e9
            )
        elif pixel_size_unit == "µm":
            flim_metadata[0]["x_pixel_size"] = (
                flim_metadata[0]["x_pixel_size"] * 1e6
            )
        elif pixel_size_unit == "mm":
            flim_metadata[0]["x_pixel_size"] = (
                flim_metadata[0]["x_pixel_size"] * 1e3
            )
        elif pixel_size_unit == "cm":
            flim_metadata[0]["x_pixel_size"] = (
                flim_metadata[0]["x_pixel_size"] * 1e2
            )

    if "y_pixel_size" not in flim_metadata[0]:
        if y_pixel_size == 0:
            notifications.show_warning(
                "y_pixel_size not found in file metadata,\nit must be provided manually"
            )
            return None, None
        flim_metadata[0][
            "y_pixel_size"
        ] = y_pixel_size  # Assign manual pixel size to metadata
    else:
        # if provided, assume pixel size unit to be m and convert to provided pixel size unit to be consistent along x, y and z
        if pixel_size_unit == "pm":
            flim_metadata[0]["y_pixel_size"] = (
                flim_metadata[0]["y_pixel_size"] * 1e12
            )
        elif pixel_size_unit == "nm":
            flim_metadata[0]["y_pixel_size"] = (
                flim_metadata[0]["y_pixel_size"] * 1e9
            )
        elif pixel_size_unit == "µm":
            flim_metadata[0]["y_pixel_size"] = (
                flim_metadata[0]["y_pixel_size"] * 1e6
            )
        elif pixel_size_unit == "mm":
            flim_metadata[0]["y_pixel_size"] = (
                flim_metadata[0]["y_pixel_size"] * 1e3
            )
        elif pixel_size_unit == "cm":
            flim_metadata[0]["y_pixel_size"] = (
                flim_metadata[0]["y_pixel_size"] * 1e2
            )

    # Fill in x and y pixel sizes metadata for ome-tiff
    metadata_timelapse["PhysicalSizeX"] = flim_metadata[0]["x_pixel_size"]
    metadata_timelapse["PhysicalSizeXUnit"] = pixel_size_unit
    metadata_timelapse["PhysicalSizeY"] = flim_metadata[0]["y_pixel_size"]
    metadata_timelapse["PhysicalSizeYUnit"] = pixel_size_unit
    # Fill in z pixel size metadata for ome-tiff
    if z_stack:
        if z_pixel_size == 0:
            notifications.show_warning(
                "z_pixel_size must be provided manually"
            )
            return None, None
        metadata_timelapse["PhysicalSizeZ"] = (
            z_pixel_size  # Assign manual pixel size to metadata
        )
        metadata_timelapse["PhysicalSizeZUnit"] = pixel_size_unit
    else:
        # Always provide a z size, even if it is not a stack because output is always be 5D for OME-TIF
        metadata_timelapse["PhysicalSizeZ"] = 1
        metadata_timelapse["PhysicalSizeZUnit"] = pixel_size_unit
    if (
        timelapse
    ):  # If it is a true timelapse (not one having photon counts as the time axis)
        if time_resolution_per_slice == 0:
            notifications.show_warning(
                "time_resolution_per_slice must be provided"
            )
            return None, None
        if z_stack:
            # Time resolution is the time resolution per slice multiplied by the number of z-slices
            time_resolution = (
                time_resolution_per_slice
                * stack_shape[output_axes_order.index("Z")]
            )
        else:
            # Time resolution is the time resolution per slice (not a 3D stack)
            time_resolution = time_resolution_per_slice
        metadata_timelapse["TimeIncrement"] = time_resolution
        metadata_timelapse["TimeIncrementUnit"] = time_unit
    else:
        # Always provide a time increment, even if it is not a timelapse because output is always be 5D for OME-TIF
        metadata_timelapse["TimeIncrement"] = 1
        metadata_timelapse["TimeIncrementUnit"] = "s"
    if multichannel:
        metadata_timelapse["Channel"] = dict()
        if channel_names == []:
            channel_names = [
                ("Channel " + str(i))
                for i in range(stack_shape[output_axes_order.index("C")])
            ]
        else:
            if len(channel_names) != stack_shape[output_axes_order.index("C")]:
                notifications.show_warning(
                    f'Number of channel names must match the number of channels in the data.\nNumber of channels in the data: {stack_shape[output_axes_order.index("C")]}'
                )
                return None, None
        metadata_timelapse["Channel"]["Name"] = channel_names

    # For the single timepoint metadata, replace the time axis with the photon counts axis
    metadata_single_timepoint = metadata_timelapse.copy()
    if (
        "tcspc_resolution" in flim_metadata[0]
        and flim_metadata[0]["tcspc_resolution"] is not None
    ):
        metadata_single_timepoint["TimeIncrement"] = flim_metadata[0][
            "tcspc_resolution"
        ]
        metadata_single_timepoint["TimeIncrementUnit"] = "s"
    else:
        if micro_time_resolution == 0:
            notifications.show_warning(
                "micro_time_resolution must be provided"
            )
            return None, None
        metadata_single_timepoint["TimeIncrement"] = micro_time_resolution
        metadata_single_timepoint["TimeIncrementUnit"] = micro_time_unit
    return metadata_timelapse, metadata_single_timepoint
