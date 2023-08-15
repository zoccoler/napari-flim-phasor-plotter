from __future__ import annotations
from pathlib import Path

DATA_ROOT = Path(__file__).parent / "data"


def load_seminal_receptacle_image():
    """
    Load a seminal receptacle FLIM single image from a .sdt file.

    This image was published in:
    Wetzker, Cornelia. (2019).
    Example sdt raw FLIM images of NAD(P)H autofluorescence in Drosophila melanogaster tissues [Data set].
    https://doi.org/10.1038/s41598-019-56067-w
    """
    import numpy as np
    from napari_flim_phasor_plotter._reader import read_single_sdt_file

    file_path = DATA_ROOT / "seminal_receptacle_FLIM_single_image.sdt"
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
