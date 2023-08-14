"""
This module is an example of a barebones sample data provider for napari.

It implements the "sample data" specification.
see: https://napari.org/stable/plugins/guides.html?#sample-data

Replace code below according to your needs.
"""
from __future__ import annotations

import numpy


def make_sample_data():
    """Generates an image"""
    # Return list of tuples
    # [(data1, add_image_kwargs1), (data2, add_image_kwargs2)]
    # Check the documentation for more information about the
    # add_image_kwargs
    # https://napari.org/stable/api/napari.Viewer.html#napari.Viewer.add_image
    return [(numpy.random.rand(512, 512), {})]


def load_seminal_receptacle_image():
    """
    Load a seminal receptacle FLIM single image from a .sdt file.

    This image was published in:
    Wetzker, Cornelia. (2019).
    Example sdt raw FLIM images of NAD(P)H autofluorescence in Drosophila melanogaster tissues [Data set].
    https://doi.org/10.1038/s41598-019-56067-w
    """
    from pathlib import Path
    import numpy as np
    from napari_flim_phasor_plotter._reader import read_single_sdt_file

    file_path = Path(r"./src/napari_flim_phasor_plotter/data/seminal_receptacle_single_image.sdt")
    image, metadata = read_single_sdt_file(file_path)
    image = np.expand_dims(image, axis=(2, 3))  # (ch, ut, t, z, y, x)
    return [(image, {'name': 'seminal receptacle raw FLIM image',
                     'metadata': metadata,
                     'channel_axis': 0,
                     }),
            (np.amax(image, axis=1), {'name': 'seminal receptacle intensity image',
                                      'metadata': metadata,
                                      }),
            ]
