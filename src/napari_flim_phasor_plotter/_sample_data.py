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
        The first tuple contains the raw FLIM image with dimensions (ut, t, z, y, x) and metadata.
        The second tuple contains the intensity image with dimensions (t, z, y, x) and metadata.
        Time and z dimensions are all of length 1.
    """
    import numpy as np
    from napari_flim_phasor_plotter._reader import read_single_sdt_file

    file_path = DATA_ROOT / "seminal_receptacle_FLIM_single_image.sdt"
    image, metadata = read_single_sdt_file(file_path)
    image, metadata = (
        image[0],
        metadata[0],
    )  # Use first channel, there is no second channel in this image
    image = np.expand_dims(image, axis=(1, 2))  # (ut, t, z, y, x)
    return [
        (
            image,
            {
                "name": "seminal receptacle raw FLIM image",
                "metadata": metadata,
                "contrast_limits": (
                    np.amin(image[image.shape[0] // 2, ...]),
                    np.amax(image[image.shape[0] // 2, ...]),
                ),
            },
        ),
        (
            np.amax(image, axis=0),
            {
                "name": "seminal receptacle intensity image",
                "metadata": metadata,
            },
        ),
    ]


def load_hazelnut_image():
    """
    Load a hazelnut FLIM single image from a .ptu file.

    Returns
    -------
    list_of_tuples_of_images_and_metadata : List[LayerDataTuple]
        A list of tuples, each tuple containing an image and its metadata.
        The first tuple contains the raw FLIM image with dimensions (ut, t, z, y, x) and metadata.
        The second tuple contains the intensity image with dimensions (t, z, y, x) and metadata.
        Time and z dimensions are all of length 1.
    """
    import numpy as np
    from napari_flim_phasor_plotter._reader import read_single_ptu_file

    file_path = DATA_ROOT / "hazelnut_FLIM_single_image.ptu"
    image, metadata = read_single_ptu_file(file_path)
    image, metadata = (
        image[0],
        metadata[0],
    )  # Use first channel, second detector is empty
    image = np.expand_dims(image, axis=(1, 2))  # (ut, t, z, y, x)
    return [
        (
            image,
            {
                "name": "hazelnut raw FLIM image",
                "metadata": metadata,
                "contrast_limits": (
                    np.amin(image[image.shape[0] // 2, ...]),
                    np.amax(image[image.shape[0] // 2, ...]),
                ),
                "scale": [metadata["ImgHdr_PixResol"]] * 2,
            },
        ),
        (
            np.amax(image, axis=0),
            {
                "name": "hazelnut intensity image",
                "metadata": metadata,
                "scale": [metadata["ImgHdr_PixResol"]] * 2,
            },
        ),
    ]


def load_hazelnut_z_stack():
    """
    Load a hazelnut FLIM z-stack image from a folder with individual .ptu files as slices from the stack.

    Returns
    -------
    list_of_tuples_of_images_and_metadata : List[LayerDataTuple]
        A list of tuples, each tuple containing an image and its metadata.
        The first tuple contains the raw FLIM image with dimensions (ut, t, z, y, x) and metadata.
        The second tuple contains the intensity image with dimensions (t, z, y, x) and metadata.
        Time dimension has length 1.
    """
    import numpy as np
    import zipfile
    import requests
    import shutil
    from pathlib import Path
    from tqdm import tqdm
    from napari_flim_phasor_plotter._reader import read_stack

    extracted_folder_path = Path(DATA_ROOT / "unzipped_hazelnut_FLIM_z_stack")
    # If extracted folder does not exist or is empty, download and extract the zip file
    if not extracted_folder_path.exists() or (
        extracted_folder_path.exists()
        and not any(extracted_folder_path.iterdir())
    ):

        zip_url = "https://github.com/zoccoler/hazelnut_FLIM_z_stack_data/raw/main/hazelnut_FLIM_z_stack.zip"
        zip_file_path = Path(DATA_ROOT / "hazelnut_FLIM_z_stack.zip")
        # Download the zip file
        response = requests.get(zip_url)

        # Total size in bytes.
        total_size = int(response.headers.get("content-length", 0))
        print(f"Total download size: {total_size/1e6} MBytes")
        print(f"Downloading to {zip_file_path}")
        block_size = 1024
        progress_bar = tqdm(
            total=total_size,
            unit="iB",
            unit_scale=True,
            desc="Downloading zip file",
        )
        with open(zip_file_path, "wb") as zip_file:
            for block in response.iter_content(block_size):
                progress_bar.update(len(block))
                zip_file.write(block)
        progress_bar.close()
        if total_size != 0 and progress_bar.n != total_size:
            print("ERROR: Something went wrong with the download")

        # Create the target directory
        extracted_folder_path.mkdir(parents=True, exist_ok=True)
        # Extract the zip file
        with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
            zip_ref.extractall(extracted_folder_path)

        # Delete the zip file after extraction
        Path(zip_file_path).unlink()
    folder_path = extracted_folder_path / "hazelnut_FLIM_z_stack"

    image, metadata = read_stack(folder_path)
    image, metadata = (
        image[0],
        metadata[0],
    )  # Use first channel, second detector is empty
    return [
        (
            image,
            {
                "name": "hazelnut raw FLIM z-stack",
                "metadata": metadata,
                "contrast_limits": (
                    np.amin(image[image.shape[0] // 2, ...]),
                    np.amax(image[image.shape[0] // 2, ...]),
                ),
                "scale": [2] + [metadata["ImgHdr_PixResol"]] * 2,
            },
        ),
        (
            np.amax(image, axis=0),
            {
                "name": "hazelnut intensity z-stack",
                "metadata": metadata,
                "scale": [2] + [metadata["ImgHdr_PixResol"]] * 2,
            },
        ),
    ]


def load_lifetime_cat_synthtetic_single_image():
    import yaml
    import numpy as np
    from napari_flim_phasor_plotter._reader import read_single_tif_file

    file_path = DATA_ROOT / "lifetime_cat.tif"
    image, metadata = read_single_tif_file(file_path, channel_axis=None)
    image = image[
        0
    ]  # Use first channel, there is no second channel in this image
    # Read metadata from associated yaml file
    with open(DATA_ROOT / "lifetime_cat_metadata.yml", "r") as stream:
        metadata = yaml.safe_load(stream)
    return [
        (
            image,
            {
                "name": "raw lifetime cat synthetic image",
                "metadata": metadata,
                "contrast_limits": (
                    np.amin(image[image.shape[0] // 2, ...]),
                    np.amax(image[image.shape[0] // 2, ...]),
                ),
            },
        ),
        (
            np.amax(image, axis=0),
            {
                "name": "intensity lifetime cat synthetic image",
                "metadata": metadata,
            },
        ),
    ]
