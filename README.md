# napari-flim-phasor-plotter

[![License BSD-3](https://img.shields.io/pypi/l/napari-flim-phasor-plotter.svg?color=green)](https://github.com/zoccoler/napari-flim-phasor-plotter/raw/main/LICENSE)
[![PyPI](https://img.shields.io/pypi/v/napari-flim-phasor-plotter.svg?color=green)](https://pypi.org/project/napari-flim-phasor-plotter)
[![Python Version](https://img.shields.io/pypi/pyversions/napari-flim-phasor-plotter.svg?color=green)](https://python.org)
[![tests](https://github.com/zoccoler/napari-flim-phasor-plotter/workflows/tests/badge.svg)](https://github.com/zoccoler/napari-flim-phasor-plotter/actions)
[![codecov](https://codecov.io/gh/zoccoler/napari-flim-phasor-plotter/branch/main/graph/badge.svg)](https://codecov.io/gh/zoccoler/napari-flim-phasor-plotter)
[![napari hub](https://img.shields.io/endpoint?url=https://api.napari-hub.org/shields/napari-flim-phasor-plotter)](https://napari-hub.org/plugins/napari-flim-phasor-plotter)

Napari-flim-phasor-plotter is a [napari] plugin to interactively load and show raw fluorescence lifetime imaging microscopy (FLIM) single images and series and generate phasor plots. These are Fourier transforms of the decay data being visualized using the [napari-clusters-plotter](https://github.com/BiAPoL/napari-clusters-plotter) and allow qualitative and quantitative downstream analysis of FLIM images.  

----------------------------------

## Usage

Open a FLIM image to visualize it both as a 'FLIM image series' being a sequence of intensity images each corresponding to an individual time point of the FLIM 'micro-time', plus as a timely summed up image. Scrolling through the FLIM time series provides a first glimpse of lifetimes across image regions.

Call the plugin from the menu `Plugins > FLIM phasor plotter > Make FLIM Phasor Plot` to generate a phasor plot by pixel-wise Fourier transformation of the decay data. Hereby, select the FLIM image to be used, specify the laser pulse frequency if not read properly from metadata. Define an intensity threshold to exclude pixels of low photon counts, optionally a median filter, and a harmonic for optimal visualization. `Run` creates the phasor plot and an additional labels layer in the layer list. Below is a demonstration:

![](https://github.com/zoccoler/napari-flim-phasor-plotter/raw/main/images/napari_FLIM_phasor_calculator_Demo.gif)

Change the color-code of the phasor plot to a density plot of various ‘Colormaps’ from the pulldown `Expand for advanced options` and select `HISTOGRAM`. Manually encircle a region of interest in the phasor plot to highlight the corresponding pixels in the newly created image layer. Hold ‘Shift’ to select and visualize several clusters to investigate image regions of similar FLIM patterns. 

### Input Data

This plugin integrates with [napari-clusters-plotter plugin](https://github.com/BiAPoL/napari-clusters-plotter).

This plugin can read the following FLIM file types:
  - ".ptu"
  - ".sdt"
  - ".tif"
  - ".zarr"

This plugin works with the following data shapes:
  - 2D FLIM images (actually 3D data where FLIM counts are in the first axis).
  - 3D FLIM images (actually 4D data where FLIM counts are in the first axis).
  - 3D timelapse FLIM images (actually 5D data where FLIM counts are in the first axis).
  - Multichannel '.tif' or '.zarr' data may need to be loaded separately.

The plugin outputs data axes in the following order (data from multiple detectors are displayed as distinct napari layers):

(`flim_counts`, `time`, `z`, `y`, `x`)

It also outputs the standard intensity image in another layer by summing the `flim_counts` dimension.

### Data Conversion

If a collection of raw (uncompressed) images are larger than 2GB, we recommend converting them to `.zarr`. This can be done via `Plugins > napari-flim-phasor-plotter > Convert to zarr`.

![](https://github.com/zoccoler/napari-flim-phasor-plotter/raw/main/images/convert_to_zarr.png)

If you have multiple slices or time-points as separated files, you can choose a folder containing the files. In order for the plugin to properly build a stack, the file names must contain some indication about which slice or time-point they represent, i.e., **each file name should contain a `_t` and/or `_z` followerd by a number**.

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


## Installation

You can install `napari-flim-phasor-plotter` via [pip]. Currently, only the development version is available.

Create a conda environment:

    conda create -n napari-flim-phasor-env python=3.9
    
Activate the environment:

    conda activate napari-flim-phasor-env
    
Then install napari and napari-clusturs-plotter (plus git if on Windows):

    conda install -c conda-forge napari napari-clusters-plotter git
    
And finally install the plugin development version with:

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
