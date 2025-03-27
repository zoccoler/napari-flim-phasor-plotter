def monoexp(x, A, tau):
    import numpy as np

    return A * np.exp(-(1 / tau) * x)


def create_time_array(frequency, n_points=100):
    """
    Create time array from laser frequency

    Parameters
    ----------
    frequency: float
        Frequency of the pulsed laser (in MHz)
    n_points: int, optional
        The number of samples collected between each aser shooting
    Returns
    -------
    time_array : array
        Time array (in nanoseconds)
    """
    import numpy as np

    time_window = 1 / (frequency * 10**6)
    time_window_ns = time_window * 10**9  # in nanoseconds
    time_step = time_window_ns / n_points  # ns
    array = np.arange(0, n_points)
    time_array = array * time_step
    return time_array


def make_synthetic_flim_data(time_array, amplitude_list, tau_list):
    """Create a synthetic FLIM image from amplitudes and tau (lifetime)

    Each different tau in the list adds a new pixel to the image.

    Parameters
    ----------
    time_array : numpy array
        Time array (in nanoseconds)
    amplitude_list : List of floats
        List of amplitudes
    tau_list : List of floats
        List of lifetimes

    Returns
    -------
    flim_data : numpy array
        Synthetic FLIM image
    """
    import numpy as np

    # Handle input types
    if not isinstance(tau_list, list):
        tau_list = [tau_list]
    if not isinstance(amplitude_list, list):
        amplitude_list = [amplitude_list]
    if len(amplitude_list) == 1 and len(amplitude_list) < len(tau_list):
        amplitude_list = [amplitude_list] * len(tau_list)
    # Generates synthetic image
    flim_data_list = []
    for amp, tau in zip(amplitude_list, tau_list):
        intensity = monoexp(time_array, amp, tau)
        flim_data = np.repeat(intensity[:, np.newaxis], 1, axis=1).reshape(
            len(time_array), 1, 1
        )
        flim_data_list.append(flim_data)
    flim_data = np.concatenate(flim_data_list, axis=1)
    return flim_data
