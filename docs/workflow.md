# Integrating Phasor Analysis into a Workflow

In this section, we use mostly the `napari-clusters-plotter` plugin to cluster the phasor plot and then visualize the segmentation results in the original FLIM image.

## Clustering

This plugin integrates with [napari-clusters-plotter plugin](https://github.com/BiAPoL/napari-clusters-plotter). Thus, you can use the [clustering widget](https://github.com/BiAPoL/napari-clusters-plotter?tab=readme-ov-file#clustering) provided by the `napari-clusters-plotter` plugin to segment the phasor plot automatically and then visualize the segmentation results in the original FLIM image. Access it via `Tools -> Measurement post-processing -> Clustering (ncp)`. Below is a demonstration:

![clustering](https://github.com/zoccoler/napari-flim-phasor-plotter/raw/main/images/clustering.gif)

## Post-processing

After cluster selection, it is common to have different labels (colors) for selected clusters. Within each label, it is also common to have disconnected regions and even isolated pixel in the segmentation. To address this, we offer a few basic post-processing functions. 

A common step is to select a single cluster of interest for further processing. By selecting the `Labels` layer (usually named `cluster_ids_in_space`) and checking the `show selected` checkbox, we can identify our cluster/label os interest by continuously increasing the label number until we find the desired cluster. After that, we can extract the chosen label as a mask via `Plugins -> FLIM phasor plotter -> Manual Label Extraction` (or `Layers -> Data -> Post-Processing -> Manual Label Extraction` if napari version >= `0.5.0`). This will create a new layer with the mask of the selected cluster.

To connect small isolated regions and remove small holes within the mask, we can use the `smooth_cluster_mask` function. This can be accessed via `Plugins -> FLIM phasor plotter -> Smooth Cluster Mask` (or `Layers -> Data -> Post-Processing -> Smooth Cluster Mask` if napari version >= `0.5.0`). This will remove holes with an area smaller than the specified `fill area px` in total number of pixels and connect regions within a given `smooth radius`. Don't forget to select the layer containing the mask before running the function, because this function expects a layer with a single label (like a binary mask).

Beyond this point, we can use other plugins, like the `napari-segment-blobs-and-things-with-membranes` and `napari-skimage-regionprops` plugins, to further process the mask. For example, we can perform instance segmentation on the mask via `Tools -> Segmentation / labeling -> Connectec component labeling (scikit-image, nsbatwm)`. We can also extract features from the objects via `Tools -> Measurement tables -> Objetct Features/Properties (scikit-image, nsr)`.

Below is a demonstration of the post-processing steps:

![post-processing](https://github.com/zoccoler/napari-flim-phasor-plotter/raw/main/images/post_processing.gif)

Also, this example workflow can be reproduced by running this jupyter notebook: [Example_workflow.ipynb](./notebooks/Example_workflow.ipynb).