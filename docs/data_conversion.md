# Data Conversion

## Single File Conversion

### To `.ome.tif` (5D Output)

If you have a `.ptu` or `.sdt` file and want to convert it to an `.ome.tif` file with minimal metadata, you can do so via `Plugins > FLIM-phasor-plotter > Convert Single File to ome.tif` (or `Layers -> Data -> Convert -> Single File -> Convert Single File to ome.tif` if napari version >= `0.5.0`).

After providing the path to the file, the plugin will try to fill the minimal metadata fields from the original raw file. In case it cannot find the information of a mandatory field (like the FLIM time resolution), it will display the missing field(s) in red to be filled manually.

![](https://github.com/zoccoler/napari-flim-phasor-plotter/raw/main/images/convert_file_to_ome_tif.png)

After filling the necessary fields, click on `Convert` to start the conversion. It will create a new folder (`OME-TIFs`) in the same path as the original file with at least two files:
- one 5D (`ch, t, z, y, x`) `.ome.tif` file containing the intensity data (without the `photon_counts` axis)
- one or more (in case of a timelapsed acquisition) 5D (`ch, photon_counts, z, y, x`) `.ome.tif` files containing the FLIM data (with the `photon_counts` axis), one file per timepoint.

The output files will always be 5D to be readily suitable for uploading to an OMERO server. If a dimension is missing, it will be added with a size of 1.

## Multiple Files Conversion (Stack)

### To `.ome.tif` (5D Output)

If you have a collection of `.ptu` or `.sdt` files and want to convert them to `.ome.tif` files with minimal metadata, you can do so via `Plugins > FLIM-phasor-plotter > Convert Folder (Stack) to ome.tif` (or `Layers -> Data -> Convert -> Folder (Stack) -> Convert Folder (Stack) to ome.tif` if napari version >= `0.5.0`).

After providing the path to the folder, the plugin will try to fill the minimal metadata fields with the information present in the original files. In case it cannot find the information of a necessary field (like the Z Pixel Size), it will display the missing field(s) in red to be filled manually.

![](https://github.com/zoccoler/napari-flim-phasor-plotter/raw/main/images/convert_folder_to_ome_tif.png)

After filling the necessary fields, click on `Convert` to start the conversion. It will create a new folder (`OME-TIFs`) in the same path as the original files with at least two files:
- one 5D (`ch, t, z, y, x`) `.ome.tif` file containing the intensity data (without the `photon_counts` axis)
- one or more (in case of a timelapsed acquisition) 5D (`ch, photon_counts, z, y, x`) `.ome.tif` files containing the FLIM data (with the `photon_counts` axis), one file per timepoint.

The output files will always be 5D to be readily suitable for uploading to an OMERO server. If a dimension is missing, it will be added with a size of 1.

### To `.zarr` (6D Output)

If a collection of raw (uncompressed) images are larger than 4GB, we recommend converting them to `.zarr`. This can be done via `Plugins > FLIM-phasor-plotter > Convert Folder (Stack) to zarr`(or `Layers -> Data -> Convert -> Folder (Stack) -> Convert Folder (Stack) to zarr` if napari version >= `0.5.0`).

_Warning: In the current version, lazy loading with `.zarr` is available, but processing may still load all data into memory, so keep track of your memory usage._

![](https://github.com/zoccoler/napari-flim-phasor-plotter/raw/main/images/convert_to_zarr.png)

Click on `Convert` to start the conversion. It will create a new "folder" (`.zarr`) in the same path as the original files. The `.zarr` file does **not** store any metadata, so keep the original files for reference.