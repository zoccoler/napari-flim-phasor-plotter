# Phasors API

```{eval-rst}
.. currentmodule:: napari_flim_phasor_plotter.phasors

.. py:function:: get_phasor_components(flim_data, harmonic=1)
    :noindex:

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
   

.. autofunction:: jit_fft

.. autofunction:: fft_slice_4d

.. autofunction:: fft_slice_4d_dask
```