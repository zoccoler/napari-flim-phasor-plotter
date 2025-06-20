(intro)=

# napari-flim-phasor

Here you find documentation for the napari-flim-phasor-plotter plugin, a [napari](https://napari.org/stable/) plugin to interactively load and show raw fluorescence lifetime imaging microscopy (FLIM) single images and series and generate phasor plots. These are Fourier transforms of the decay data being visualized using the [napari-clusters-plotter](https://github.com/BiAPoL/napari-clusters-plotter) plotter, adapted to suit the FLIM context. This allows qualitative and quantitative downstream analysis of FLIM images.

## Quick demo

![](https://github.com/zoccoler/napari-flim-phasor-plotter/raw/main/images/napari_FLIM_phasor_calculator_Demo.gif)



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

## Table of Contents

Here is an automatically generated Table of Contents:

```{tableofcontents}
```

## Limitations / Future Work

The plugin does not yet support:
- Phasor calibration
- Round cluster selection or cursor selection (only free-hand selection is available)
- Pseudo-channel generation from selected clusters in the phasor plot
- FRET analysis
- Tile processing
- Fitting of decay curves

[github]: https://github.com/zoccoler/napari-flim-phasor-plotter "GitHub source code repository for this project"
[tutorial]: https://docs.readthedocs.io/en/stable/tutorial/index.html "Official Read the Docs Tutorial"
[jb-docs]: https://jupyterbook.org/en/stable/ "Official Jupyter Book documentation"