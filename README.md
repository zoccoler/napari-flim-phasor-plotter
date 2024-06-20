# napari-flim-phasor-plotter

[![License BSD-3](https://img.shields.io/pypi/l/napari-flim-phasor-plotter.svg?color=green)](https://github.com/zoccoler/napari-flim-phasor-plotter/raw/main/LICENSE)
[![PyPI](https://img.shields.io/pypi/v/napari-flim-phasor-plotter.svg?color=green)](https://pypi.org/project/napari-flim-phasor-plotter)
[![Python Version](https://img.shields.io/pypi/pyversions/napari-flim-phasor-plotter.svg?color=green)](https://python.org)
[![tests](https://github.com/zoccoler/napari-flim-phasor-plotter/workflows/tests/badge.svg)](https://github.com/zoccoler/napari-flim-phasor-plotter/actions)
[![codecov](https://codecov.io/gh/zoccoler/napari-flim-phasor-plotter/branch/main/graph/badge.svg)](https://codecov.io/gh/zoccoler/napari-flim-phasor-plotter)
[![napari hub](https://img.shields.io/endpoint?url=https://api.napari-hub.org/shields/napari-flim-phasor-plotter)](https://napari-hub.org/plugins/napari-flim-phasor-plotter)

Napari-flim-phasor-plotter is a [napari](https://napari.org/stable/) plugin to interactively load and show raw fluorescence lifetime imaging microscopy (FLIM) single images and series and generate phasor plots. These are Fourier transforms of the decay data being visualized using the [napari-clusters-plotter](https://github.com/BiAPoL/napari-clusters-plotter) plotter, adapted to suit the FLIM context. This allows qualitative and quantitative downstream analysis of FLIM images.  

----------------------------------

## Usage

### Opening a Raw FLIM Image

Drag and drop a compatible file format (check supported file formats [here below](#input-data)) to open a FLIM image. It gets displayed in two layer: a 'raw FLIM image series' (a sequence of intensity images each corresponding to an individual time point of the FLIM 'micro-time'), and a timely summed up image (usually just known as the 'intensity' image). Scrolling through the FLIM time series provides a first glimpse of lifetimes across image regions.

### Phasor Plotting

Call the plugin from the menu `Plugins > FLIM phasor plotter > Calculate Phasors` to generate a phasor plot by pixel-wise Fourier transformation of the decay data. Hereby, select the FLIM image to be used (it should be the layer with the raw data), specify the laser pulse frequency (if information is present in the file metadata, this field will be updated after phasor calculation). Choose a harmonic for optimal visualization, define an intensity threshold (here in absoluete values) to exclude pixels of low photon counts, and optionally apply a number of iterations `n` of a 3x3 median filter. `Run` creates the phasor plot and an additional labels layer in the layer list. Below is a demonstration:

![](https://github.com/zoccoler/napari-flim-phasor-plotter/raw/main/images/napari_FLIM_phasor_calculator_Demo.gif)

### Phasor Plot Navigation

 Use the toolbar on top of the plot to navigate through the plot. For example, by activating the zoom tool button (magnifying glass icon), you can zoom in (with left click) or out (with right click), just *remember to disbale the zoom tool after using it by clicking on the icon once again*.

Change the colormap of the phasor plot from various `Colormaps` by clicking on the pulldown `Expand for advanced options`. There, you can also choose to display the color range in log scale by checking the `Log scale` checkbox. Optionally, add tau lines to the plot by specifying a range of lifetimes to be displayed (write them separated by commas) in the field `Tau lines` anc click on `Show/hide` to visualize them on top of the phasor plot.

### Phasor Plot Analysis

 Manually encircle a region of interest in the phasor plot to highlight the corresponding pixels in the newly created image layer. Hold ‘Shift’ to select and visualize several clusters as a way to investigate image regions of similar FLIM patterns.

### Saving Results

 Save your segmentation results by selecting (clicking on) the corresponding `Labels` layer (usually named `cluster_ids_in_space`) and then going to `File -> Save Selected Layer`. This can save the layer as a `.tif` file. To save a screenshot of the phasor plot, click on the `Save` button on the toolbar. To save the phasor plot as a `.csv` file, go to `Tools -> Measurement -> Show table (nsr)` and a new widget will show up. From the `labels layer` dropdown, choose the layer that contains the table, whose name starts with `Labelled_pixels_from_`... and then click on the `Run` button. This should bring the table with `G` and `S` values for each pixel. Click on the `Save as csv...` button to save the table as a `.csv` file.

### Sample Data

The plugin comes with a few sample FLIM raw images:

- '2D' raw FLIM images:
  - Hazelnut (originally a '.ptu' file)
  - Seminal Receptacle (originally a '.sdt' file)
- '3D' raw FLIM image stack (Hazelnut 3D)
  - Hazelnut 3D (originally a series of '.ptu' files)
- '2D' synthetic FLIM image
  - Lifetime Cat

 To load it, go to `File > Open Sample -> FLIM phasor plotter`.

### Input Data

This plugin integrates with [napari-clusters-plotter plugin](https://github.com/BiAPoL/napari-clusters-plotter).

This plugin can read the following FLIM file types:
  - `.ptu`
  - `.sdt`
  - `.tif`
  - `.zarr`

This plugin works with the following data shapes:
  - 2D FLIM images (actually 3D data where FLIM counts are in the first axis).
  - 3D FLIM images (actually 4D data where FLIM counts are in the first axis).
  - 3D timelapse FLIM images (actually 5D data where FLIM counts are in the first axis).
  - Multichannel '.tif' or '.zarr' data may need to be loaded separately.

If you read your files using this plugin, it returns and works with the data axes in the following order (data from multiple detectors are displayed as distinct napari layers):

(`flim_counts`, `time`, `z`, `y`, `x`)

Even if the data is 2D, the plugin will add a unitary `time` and a `z` axis.
It also provides the standard intensity image in another layer by summing the `flim_counts` dimension.

### Data Conversion

If a collection of raw (uncompressed) images are larger than 4GB, we recommend converting them to `.zarr`. This can be done via `Plugins > napari-flim-phasor-plotter > Convert to zarr`.

_Warning: In the current version, lazy loading with `.zarr` is available, but processing may still load all data into memory, so keep track of your memory usage._

![](https://github.com/zoccoler/napari-flim-phasor-plotter/raw/main/images/convert_to_zarr.png)

### Loading Stacks

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

## Limitations

The plugin does not yet support:
- Phasor calibration
- Round cluster selection (only free-hand selection is available)
- Pseudo-channel generation from selected clusters in the phasor plot
- FRET analysis


## Installation

We recommend installing `napari-flim-phasor-plotter` with [mamba](https://mamba.readthedocs.io/en/latest/) after having [Miniforge](https://github.com/conda-forge/miniforge?tab=readme-ov-file#miniforge) installed in your computer. Follow these steps from a terminal.

Click [here](https://github.com/conda-forge/miniforge?tab=readme-ov-file#download) to choose the right download option for your OS.

Create a conda environment:

    mamba create -n napari-flim-phasor-env python=3.9
    
Activate the environment:

    mamba activate napari-flim-phasor-env
    
Then install `napari` and `napari-clusturs-plotter` (plus git if on Windows):

    mamba install -c conda-forge napari napari-clusters-plotter git pyqt

_Optional, but we **strongly** recommend having the `devbio-napari` plugin bundle also installed for post-processing. This can be done with:_

    mamba install -c conda-forge devbio-napari

Finally install `napari-flim-phasor-plotter` plugin with:

    pip install napari-flim-phasor-plotter
 
Alternatively, clone this repository and install the latest plugin development version with:

    pip install git+https://github.com/zoccoler/napari-flim-phasor-plotter.git

## Contributing

Contributions are very welcome. Tests can be run with [tox], please ensure
the coverage at least stays the same before you submit a pull request.

## License

Distributed under the terms of the [BSD-3] license,
"napari-flim-phasor-plotter" is free and open source software

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
