import numba as nb
import numpy as np


def get_phasor_components(flim_data, harmonic=1):
    """Calculate phasor components G and S from the Fourier transform.

    Parameters
    ----------
    flim_data : np.ndarray or da.Array
        FLIM data with dimensions (ut, time, z, y, x). microtime must be the first dimention. time and z are optional.
    harmonic : int, optional
        Harmonic to calculate, by default 1

    Returns
    -------
    Tuple[np.ndarray, np.ndarray, np.ndarray]
        G, S, and DC components.

    This function was adapted and modified based on PhasorPy v1.0.2
    (https://pypi.org/project/PhasorPy)

    MIT License

    Copyright (c) 2022 Bruno Schuty

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.
    """
    import dask.array as da

    if isinstance(flim_data, da.Array):
        fft_slice_function = fft_slice_4d_dask
    else:
        fft_slice_function = fft_slice_4d

    dc, _ = fft_slice_function(flim_data, 0)
    # change the zeros to the img average
    dc = np.where(dc.real != 0, dc.real, np.mean(dc.real))

    g, s = fft_slice_function(flim_data, harmonic)
    g /= dc
    s /= -dc

    return g, s, dc


@nb.njit
def jit_fft(a, axis=-1):
    """Numba fft version with rocket-fft"""
    return np.fft.fft(a, axis=axis)


def fft_slice_4d(arr, slice_num):
    """Slice of FFT over first axis of a numpy array"""
    fft_arr = jit_fft(arr, axis=0)
    # Return the specified slice of the FFT array
    return fft_arr[slice_num, ...].real, fft_arr[slice_num, ...].imag


def fft_slice_4d_dask(arr, slice_num):
    """Slice of FFT over first axis of a dask array"""
    import dask.array as da

    # Dask fft along first axis
    fft_arr = da.fft.fft(arr, axis=0)
    # Return the specified slice of the FFT array
    return fft_arr[slice_num, ...].real, fft_arr[slice_num, ...].imag
