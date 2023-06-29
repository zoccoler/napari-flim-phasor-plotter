# napari-flim-phasor-plotter

[![License BSD-3](https://img.shields.io/pypi/l/napari-flim-phasor-plotter.svg?color=green)](https://github.com/zoccoler/napari-flim-phasor-plotter/raw/main/LICENSE)
[![PyPI](https://img.shields.io/pypi/v/napari-flim-phasor-plotter.svg?color=green)](https://pypi.org/project/napari-flim-phasor-plotter)
[![Python Version](https://img.shields.io/pypi/pyversions/napari-flim-phasor-plotter.svg?color=green)](https://python.org)
[![tests](https://github.com/zoccoler/napari-flim-phasor-plotter/workflows/tests/badge.svg)](https://github.com/zoccoler/napari-flim-phasor-plotter/actions)
[![codecov](https://codecov.io/gh/zoccoler/napari-flim-phasor-plotter/branch/main/graph/badge.svg)](https://codecov.io/gh/zoccoler/napari-flim-phasor-plotter)
[![napari hub](https://img.shields.io/endpoint?url=https://api.napari-hub.org/shields/napari-flim-phasor-plotter)](https://napari-hub.org/plugins/napari-flim-phasor-plotter)

A napari plugin to generate an ineractive phasor plot for TCSPC FLIM data. 

----------------------------------

## Usage

Open a raw TCSPC FLIM image in napari and call the plugin from the Plugins menu. Specify the laser frequency, which harmonic and a threshold for the phasor plot. Optionally, apply median filters. Below is a demonstration:

![](https://github.com/zoccoler/napari-flim-phasor-plotter/raw/main/images/napari_FLIM_phasor_calculator_Demo.gif)

Manually draw curves on the plot to get the corresponding pixels highlighted in a new labels layer. Hold 'SHIFT' while drawing to add more than two colors.

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
