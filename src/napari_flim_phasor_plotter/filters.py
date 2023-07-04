from magicgui import magic_factory
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import napari.types

def make_time_mask(image, laser_frequency):
    '''
    Create a time mask from the image histogram maximum onwards

    Parameters
    ----------
    image: array
        The flim timelapse image
    laser_frequency: float
        Frequency of the pulsed laser (in MHz)
    Returns
    -------
    time_mask : boolean array
        Time mask
    '''
    import numpy as np
    from napari_flim_phasor_plotter._synthetic import create_time_array
    # create time array based on laser frequency
    time_array = create_time_array(
        laser_frequency, n_points=image.shape[0])  # ut axis
    time_step = time_array[1]
    # choose starting index based on maximum value of image histogram
    heights, bin_edges = np.histogram(
        # index where ut max
        np.ravel(np.argmax(image, axis=0) * time_step), bins=time_array
    )

    start_index = np.argmax(heights[1:]) + 1
    time_mask = time_array >= time_array[start_index]

    return time_mask


def make_space_mask_from_manual_threshold(image, threshold):
    '''
    Create a space mask from the summed intensity image over time, keeping
    pixels whose value is above threshold.

    Parameters
    ----------
    image: array
        The flim timelapse image
    threshold: float
        An integer threshold value.
    Returns
    -------
    space_mask : boolean array
        A boolean mask representing pixels to keep.
    '''
    import numpy as np
    intensity_image = np.sum(image, axis=0)
    space_mask = intensity_image >= threshold

    return space_mask


def apply_median_filter(image, n=1):
    import numpy as np
    from skimage.filters import median
    from skimage.morphology import cube
    assert len(image.shape) == 5, "Image must have 5 dimensions, even if unitary (ut, time, z, y, x)"
    footprint = cube(3)
    # TODO: make this work with dask, may need rechunking and using
    # https://image.dask.org/en/latest/dask_image.ndfilters.html#dask_image.ndfilters.median_filter
    image_filt = np.copy(image)
    for i in range(n):
        for ut in range(image.shape[0]):
            for t in range(image.shape[1]):
                image_filt[ut, t] = median(image_filt[ut, t], footprint)
    return image_filt

@magic_factory
def apply_binning(flim_image: "napari.types.ImageData", 
                       bin_size: int = 2, 
                       binning_3D: bool = True) -> "napari.types.ImageData":
    """
    Apply binning to TCSPC FLIM image.

    Parameters
    ----------
    flim_image: array
        The FLIM timelapse image
    bin_size : int, optional
        size of binning kernel, by default 2
    binning_3D : bool, optional
        if True, applies a 3D binning kernel, 
        if False, applies a 2D binning kernel to each slice, 
        by default True
    """
    import numpy as np
    from scipy.ndimage import convolve

    image_binned = np.zeros_like(flim_image)

    if binning_3D:
        kernel=np.full((bin_size, bin_size, bin_size), 1)

        for  utime, time in np.ndindex(flim_image.shape[0], flim_image.shape[1]):
            image_binned[utime, time, :, :, :] = convolve(flim_image[utime, time, :, :, :],kernel)
    else:
        kernel=np.full((bin_size, bin_size), 1)

        for  utime, time, z in np.ndindex(flim_image.shape[0], flim_image.shape[1], flim_image.shape[2]):
            image_binned[utime, time, z, :, :] = convolve(flim_image[utime, time, z, :, :],kernel)
    
    return(image_binned)
