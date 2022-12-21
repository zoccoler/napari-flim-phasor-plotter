import numpy as np

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
    from napari_flim_phasor_calculator._synthetic import create_time_array
    # create time array based on laser frequency
    time_array = create_time_array(laser_frequency, n_points = image.shape[0])
    time_step = time_array[1]
    # choose starting index based on maximum value of image histogram
    heights, bin_edges = np.histogram(
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
    intensity_image = np.sum(image, axis=0)
    space_mask = intensity_image >= threshold

    return space_mask
    
def apply_median_filter(image, n = 1):
    from skimage.filters import median
    from skimage.morphology import cube
    footprint = cube(3)
    image_filt = np.copy(image)
    for i in range(n):
        image_filt = median(image_filt, footprint)
    return image_filt