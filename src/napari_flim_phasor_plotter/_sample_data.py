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

    Returns
    -------
    list_of_tuples_of_images_and_metadata : List[LayerDataTuple]
        A list of tuples, each tuple containing an image and its metadata.
        The first tuple contains the raw FLIM image with dimensions (ch, ut, t, z, y, x) and metadata.
        The second tuple contains the intensity image with dimensions (ch, t, z, y, x) and metadata.
        Channel, time and z dimensions are all of length 1.
        If loaded into napari, channel dimension is used to split image into layers.
    """
    import numpy as np
    from napari_flim_phasor_plotter._reader import read_single_sdt_file

    file_path = DATA_ROOT / "seminal_receptacle_FLIM_single_image.sdt"
    image, metadata = read_single_sdt_file(file_path)
    image = np.expand_dims(image, axis=(2, 3))  # (ch, ut, t, z, y, x)
    return [(image, {'name': 'seminal receptacle raw FLIM image',
                     'metadata': metadata,
                     'channel_axis': 0,
                     'contrast_limits': (np.amin(image[:, image.shape[1] // 2, ...]),
                                         np.amax(image[:, image.shape[1] // 2, ...])),
                     }),
            (np.amax(image, axis=1), {'name': 'seminal receptacle intensity image',
                                      'metadata': metadata,
                                      }),
            ]


def load_hazelnut_image():
    """
    Load a hazelnut FLIM single image from a .ptu file.

    Returns
    -------
    list_of_tuples_of_images_and_metadata : List[LayerDataTuple]
        A list of tuples, each tuple containing an image and its metadata.
        The first tuple contains the raw FLIM image with dimensions (ch, ut, t, z, y, x) and metadata.
        The second tuple contains the intensity image with dimensions (ch, t, z, y, x) and metadata.
        Channel, time and z dimensions are all of length 1.
        If loaded into napari, channel dimension is used to split image into layers.
    """
    import numpy as np
    from napari_flim_phasor_plotter._reader import read_single_ptu_file

    file_path = DATA_ROOT / "hazelnut_FLIM_single_image.ptu"
    image, metadata = read_single_ptu_file(file_path)
    image, metadata = image[0], metadata[0]  # Use first channel, second detector is empty
    image = np.expand_dims(image, axis=(0, 2, 3))  # (ch, ut, t, z, y, x)
    return [(image, {'name': 'hazelnut raw FLIM image',
                     'metadata': metadata,
                     'channel_axis': 0,
                     'contrast_limits': (np.amin(image[:, image.shape[1] // 2, ...]),
                                         np.amax(image[:, image.shape[1] // 2, ...])),
                     }),
            (np.amax(image, axis=1), {'name': 'hazelnut intensity image',
                                      'metadata': metadata,
                                      }),
            ]
