# napari-flim-phasor-plotter

[![License BSD-3](https://img.shields.io/pypi/l/napari-flim-phasor-plotter.svg?color=green)](https://github.com/zoccoler/napari-flim-phasor-plotter/raw/main/LICENSE)
[![PyPI](https://img.shields.io/pypi/v/napari-flim-phasor-plotter.svg?color=green)](https://pypi.org/project/napari-flim-phasor-plotter)
[![Python Version](https://img.shields.io/pypi/pyversions/napari-flim-phasor-plotter.svg?color=green)](https://python.org)
[![tests](https://github.com/zoccoler/napari-flim-phasor-plotter/workflows/tests/badge.svg)](https://github.com/zoccoler/napari-flim-phasor-plotter/actions)
[![codecov](https://codecov.io/gh/zoccoler/napari-flim-phasor-plotter/branch/main/graph/badge.svg)](https://codecov.io/gh/zoccoler/napari-flim-phasor-plotter)
[![napari hub](https://img.shields.io/endpoint?url=https://api.napari-hub.org/shields/napari-flim-phasor-plotter)](https://napari-hub.org/plugins/napari-flim-phasor-plotter)
[![DOI](https://zenodo.org/badge/578127094.svg)](https://zenodo.org/doi/10.5281/zenodo.12620955)

Napari-flim-phasor-plotter is a [napari](https://napari.org/stable/) plugin to interactively load and show raw fluorescence lifetime imaging microscopy (FLIM) single images and series and generate phasor plots. These are Fourier transforms of the decay data being visualized using the [napari-clusters-plotter](https://github.com/BiAPoL/napari-clusters-plotter) plotter, adapted to suit the FLIM context. This allows qualitative and quantitative downstream analysis of FLIM images.  

----------------------------------

## Quick demo

![](https://github.com/zoccoler/napari-flim-phasor-plotter/raw/main/images/napari_FLIM_phasor_calculator_Demo.gif)

## Contents

- [Installation](#installation)
- [Usage](#usage)
  - [Loading Raw FLIM Data](#loading-raw-flim-data)
    1. [Input Data Types](#1-input-data-types)
    2. [Opening a Raw FLIM Image](#2-opening-a-raw-flim-image)
    3. [Loading Stacks](#3-loading-stacks)
    4. [Sample Data](#4-sample-data)
  - [Phasor Analysis](#phasor-analysis)
    1. [Generating Phasor Plots](#1-generating-phasor-plots)
    2. [Phasor Plot Navigation](#2-phasor-plot-navigation)
    3. [Phasor Plot Selection](#3-phasor-plot-selection)
    4. [Integrating Phasor Analysis into a Workflow](#4-integrating-phasor-analysis-into-a-workflow)
        - [Clustering](#clustering)
        - [Post-processing](#post-processing)
  - [Saving Results](#saving-results)
  - [Data Conversion](#data-conversion)
- [Limitations](#limitations)
- [Contributing](#contributing)
- [License](#license)
- [Issues](#issues)

## Installation

We recommend installing `napari-flim-phasor-plotter` with [mamba](https://mamba.readthedocs.io/en/latest/) after having [Miniforge](https://github.com/conda-forge/miniforge) installed in your computer. Follow these steps from a terminal.

Click [here](https://github.com/conda-forge/miniforge/releases) to choose the right download option for your OS after clicking on the latest release.

Create a conda environment:

    mamba create -n napari-flim-phasor-env python=3.10 napari pyqt git
    
Activate the environment:

    mamba activate napari-flim-phasor-env

Install `napari-flim-phasor-plotter` plugin with:

    pip install napari-flim-phasor-plotter
 
Alternatively, clone this repository and install the latest plugin development version with:

    pip install git+https://github.com/zoccoler/napari-flim-phasor-plotter.git

## Usage

### Loading Raw FLIM Data

#### 1. Input Data Types

This plugin can read the following FLIM **file types**:
  - `.ptu`
  - `.sdt`
  - `.tif` (including `ome.tif`)
  - `.zarr`

This plugin works with the following **data shapes**:
  - 2D FLIM images (actually 3D data where FLIM counts are in the first axis, i.e., `(photon_counts, y, x)`).
  - 3D FLIM images (actually 4D data where FLIM counts are in the first axis, i.e., `(photon_counts, z, y, x)`).
  - 3D timelapse FLIM images (actually 5D data where FLIM counts are in the first axis, i.e., `(photon_counts, t, z, y, x)`).
  - Multichannel `.tif` or `.zarr` data may need to be loaded separately.

If you read your files using this plugin as a reader, it returns and works with the data axes in the following order (data from multiple detectors are displayed as distinct napari layers):

(`photon_counts`, `time`, `z`, `y`, `x`)

Even if the data is 2D, the plugin will add a unitary `time` and a `z` axis.
It also provides the standard intensity image in another layer by summing the `photon_counts` dimension.

#### 2. Opening a Raw FLIM Image

Drag and drop a compatible file format (check supported file formats [here below](#input-data)) to open a FLIM image. It gets displayed in two layer: a 'raw FLIM image series' (a sequence of intensity images each corresponding to an individual time point of the FLIM 'micro-time'), and a timely summed up image (usually just known as the 'intensity' image). Scrolling through the FLIM time series provides a first glimpse of lifetimes across image regions.

#### 3. Loading Stacks

If you have multiple slices or time-points as separated files, you can choose a folder containing the files. In order for the plugin to properly build a stack, the file names must contain some indication about which slice or time-point they represent, i.e., **each file name should contain a `_t` and/or `_z` followed by a number**.

Here are a few example templates:
- timelapse:
  - `image_t001.ptu`
  - `image_t002.ptu`
- z-stack:
  - `image_z01.sdt`
  - `image_z02.sdt`
- 3D timelapse:
  - `image_t001_z001.tif`
  - `image_t001_z002.tif`
  - ...
  - `image_t002_z001.tif`

#### 4. Sample Data

The plugin comes with a few sample FLIM raw images:

- '2D' raw FLIM images:
  - Hazelnut (originally a `.ptu` file)
  - Seminal Receptacle (originally a `.sdt` file)
- '3D' raw FLIM image stack (Hazelnut 3D)
  - Hazelnut 3D (originally a series of `.ptu` files)
- '2D' synthetic FLIM image
  - Lifetime Cat

 To load it, go to `File > Open Sample -> FLIM phasor plotter`.

### Phasor Analysis

#### 1. Generating Phasor Plots

Call the plugin from the menu `Plugins > FLIM phasor plotter > Calculate Phasors` (or `Layers -> Data -> Phasors -> Calculate Phasors` if napari version >= `0.5.0`) to generate a phasor plot by pixel-wise Fourier transformation of the decay data. Hereby, select the FLIM image to be used (it should be the layer with the raw data), specify the laser pulse frequency (if information is present in the file metadata, this field will be updated after phasor calculation). Choose a harmonic for optimal visualization, define an intensity threshold (here in absoluete values) to exclude pixels of low photon counts, and optionally apply a number of iterations `n` of a 3x3 median filter. `Run` creates the phasor plot and an additional labels layer in the layer list.

#### 2. Phasor Plot Navigation

 Use the toolbar on top of the plot to navigate through the plot. For example, by activating the zoom tool button (magnifying glass icon), you can zoom in (with left click) or out (with right click), just *remember to disbale the zoom tool after using it by clicking on the icon once again*.

Change the colormap of the phasor plot from various `Colormaps` by clicking on the pulldown `Expand for advanced options`. There, you can also choose to display the color range in log scale by checking the `Log scale` checkbox. Optionally, add tau lines to the plot by specifying a range of lifetimes to be displayed (write them separated by commas) in the field `Tau lines` anc click on `Show/hide` to visualize them on top of the phasor plot.

#### 3. Phasor Plot Selection

 Manually encircle a region of interest in the phasor plot to highlight the corresponding pixels in the newly created image layer. Hold `SHIFT` to select and visualize several clusters with different colors, as a way to investigate image regions of similar FLIM patterns.

#### 4. Integrating Phasor Analysis into a Workflow

##### Clustering

This plugin integrates with [napari-clusters-plotter plugin](https://github.com/BiAPoL/napari-clusters-plotter). Thus, you can use the [clustering widget](https://github.com/BiAPoL/napari-clusters-plotter?tab=readme-ov-file#clustering) provided by the `napari-clusters-plotter` plugin to segment the phasor plot automatically and then visualize the segmentation results in the original FLIM image. Access it via `Tools -> Measurement post-processing -> Clustering (ncp)`. Below is a demonstration:

![clustering](https://github.com/zoccoler/napari-flim-phasor-plotter/raw/main/images/clustering.gif)

##### Post-processing

After cluster selection, it is common to have different labels (colors) for selected clusters. Within each label, it is also common to have disconnected regions and even isolated pixel in the segmentation. To address this, we offer a few basic post-processing functions. 

A common step is to select a single cluster of interest for further processing. By selecting the `Labels` layer (usually named `cluster_ids_in_space`) and checking the `show selected` checkbox, we can identify our cluster/label os interest by continuously increasing the label number until we find the desired cluster. After that, we can extract the chosen label as a mask via `Plugins -> FLIM phasor plotter -> Manual Label Extraction` (or `Layers -> Data -> Post-Processing -> Manual Label Extraction` if napari version >= `0.5.0`). This will create a new layer with the mask of the selected cluster.

To connect small isolated regions and remove small holes within the mask, we can use the `smooth_cluster_mask` function. This can be accessed via `Plugins -> FLIM phasor plotter -> Smooth Cluster Mask` (or `Layers -> Data -> Post-Processing -> Smooth Cluster Mask` if napari version >= `0.5.0`). This will remove holes with an area smaller than the specified `fill area px` in total number of pixels and connect regions within a given `smooth radius`. Don't forget to select the layer containing the mask before running the function, because this function expects a layer with a single label (like a binary mask).

Beyond this point, we can use other plugins, like the `napari-segment-blobs-and-things-with-membranes` and `napari-skimage-regionprops` plugins, to further process the mask. For example, we can perform instance segmentation on the mask via `Tools -> Segmentation / labeling -> Connectec component labeling (scikit-image, nsbatwm)`. We can also extract features from the objects via `Tools -> Measurement tables -> Objetct Features/Properties (scikit-image, nsr)`.

Below is a demonstration of the post-processing steps:

![post-processing](https://github.com/zoccoler/napari-flim-phasor-plotter/raw/main/images/post_processing.gif)

Also, this example workflow can be reproduced by running this jupyter notebook: [Example_workflow.ipynb](./src/napari_flim_phasor_plotter/notebooks/Example_workflow.ipynb).

### Saving Results

 Save your segmentation results by selecting (clicking on) the corresponding `Labels` layer (usually named `cluster_ids_in_space`) and then going to `File -> Save Selected Layer`. This can save the layer as a `.tif` file. To save a screenshot of the phasor plot, click on the `Save` button on the toolbar. To save the phasor plot as a `.csv` file, go to `Tools -> Measurement -> Show table (nsr)` and a new widget will show up. From the `labels layer` dropdown, choose the layer that contains the table, whose name starts with `Labelled_pixels_from_`... and then click on the `Run` button. This should bring the table with `G` and `S` values for each pixel. Click on the `Save as csv...` button to save the table as a `.csv` file.

![saving](https://github.com/zoccoler/napari-flim-phasor-plotter/raw/main/images/saving_results.gif)

### Data Conversion

#### Single File Conversion

##### To `.ome.tif` (5D Output)

If you have a `.ptu` or `.sdt` file and want to convert it to an `.ome.tif` file with minimal metadata, you can do so via `Plugins > FLIM-phasor-plotter > Convert Single File to ome.tif` (or `Layers -> Data -> Convert -> Single File -> Convert Single File to ome.tif` if napari version >= `0.5.0`).

After providing the path to the file, the plugin will try to fill the minimal metadata fields from the original raw file. In case it cannot find the information of a mandatory field (like the FLIM time resolution), it will display the missing field(s) in red to be filled manually.

![](https://github.com/zoccoler/napari-flim-phasor-plotter/raw/main/images/convert_file_to_ome_tif.png)

After filling the necessary fields, click on `Convert` to start the conversion. It will create a new folder (`OME-TIFs`) in the same path as the original file with at least two files:
- one 5D (`ch, t, z, y, x`) `.ome.tif` file containing the intensity data (without the `photon_counts` axis)
- one or more (in case of a timelapsed acquisition) 5D (`ch, photon_counts, z, y, x`) `.ome.tif` files containing the FLIM data (with the `photon_counts` axis), one file per timepoint.

The output files will always be 5D to be readily suitable for uploading to an OMERO server. If a dimension is missing, it will be added with a size of 1.

#### Multiple Files Conversion (Stack)

##### To `.ome.tif` (5D Output)

If you have a collection of `.ptu` or `.sdt` files and want to convert them to `.ome.tif` files with minimal metadata, you can do so via `Plugins > FLIM-phasor-plotter > Convert Folder (Stack) to ome.tif` (or `Layers -> Data -> Convert -> Folder (Stack) -> Convert Folder (Stack) to ome.tif` if napari version >= `0.5.0`).

After providing the path to the folder, the plugin will try to fill the minimal metadata fields with the information present in the original files. In case it cannot find the information of a necessary field (like the Z Pixel Size), it will display the missing field(s) in red to be filled manually.

![](https://github.com/zoccoler/napari-flim-phasor-plotter/raw/main/images/convert_folder_to_ome_tif.png)

After filling the necessary fields, click on `Convert` to start the conversion. It will create a new folder (`OME-TIFs`) in the same path as the original files with at least two files:
- one 5D (`ch, t, z, y, x`) `.ome.tif` file containing the intensity data (without the `photon_counts` axis)
- one or more (in case of a timelapsed acquisition) 5D (`ch, photon_counts, z, y, x`) `.ome.tif` files containing the FLIM data (with the `photon_counts` axis), one file per timepoint.

The output files will always be 5D to be readily suitable for uploading to an OMERO server. If a dimension is missing, it will be added with a size of 1.

#### To `.zarr` (6D Output)

If a collection of raw (uncompressed) images are larger than 4GB, we recommend converting them to `.zarr`. This can be done via `Plugins > FLIM-phasor-plotter > Convert Folder (Stack) to zarr`(or `Layers -> Data -> Convert -> Folder (Stack) -> Convert Folder (Stack) to zarr` if napari version >= `0.5.0`).

_Warning: In the current version, lazy loading with `.zarr` is available, but processing may still load all data into memory, so keep track of your memory usage._

![](https://github.com/zoccoler/napari-flim-phasor-plotter/raw/main/images/convert_to_zarr.png)

Click on `Convert` to start the conversion. It will create a new "folder" (`.zarr`) in the same path as the original files. The `.zarr` file does **not** store any metadata, so keep the original files for reference.

## Limitations

The plugin does not support:
- Phasor calibration
- Round cluster selection or cursor selection (only free-hand selection is available)
- Pseudo-channel generation from selected clusters in the phasor plot
- FRET analysis
- Tile processing
- Fitting of decay curves

## Contributing

Contributions are very welcome. Tests can be run with [tox], please ensure
the coverage at least stays the same before you submit a pull request.

## License

Distributed under the terms of the [BSD-3] license,
"napari-flim-phasor-plotter" is free and open source software. 

If you use this plugin in a publication, please cite us: https://doi.org/10.5281/zenodo.12620956

## Issues

If you encounter any problems, please [file an issue] along with a detailed description.

[napari]: https://github.com/napari/napari
[Cookiecutter]: https://github.com/audreyr/cookiecutter
[@napari]: https://github.com/napari
[MIT]: http://opensource.org/licenses/MIT
[BSD-3]: http://opensource.org/licenses/BSD-3-Clause
[GNU GPL v3.0]: http://www.gnu.org/licenses/gpl-3.0.txt
[GNU LGPL v3.0]: http://www.gnu.org/licenses/lgpl-3.0.txt
[Apache Software License 2.0]: http://www.apache.org/licenses/LICENSE-2.0
[Mozilla Public License 2.0]: https://www.mozilla.org/media/MPL/2.0/index.txt
[cookiecutter-napari-plugin]: https://github.com/napari/cookiecutter-napari-plugin

[file an issue]: https://github.com/zoccoler/napari-flim-phasor-plotter/issues

[napari]: https://github.com/napari/napari
[tox]: https://tox.readthedocs.io/en/latest/
[pip]: https://pypi.org/project/pip/
[PyPI]: https://pypi.org/
