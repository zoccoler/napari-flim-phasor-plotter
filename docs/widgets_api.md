# Widgets API

```{eval-rst}
.. currentmodule:: napari_flim_phasor_plotter.widgets

.. py:function:: make_flim_phasor_plot(image_layer, laser_frequency=40, harmonic=1, threshold=10, apply_median=False, median_n=1, apply_calibration=False, calibration_image_layer=None, calibration_lifetime=None, napari_viewer=None)
   :noindex:

   Calculate phasor components from FLIM image and plot them.

   Parameters
   ----------
   image_layer : napari.layers.Image
       napari image layer with FLIM data with dimensions (ut, time, z, y, x). microtime must be the first dimension. time and z are optional.
   laser_frequency : float, optional
       laser frequency in MHz. If using '.ptu' or '.sdt' files, this field is filled afterwards from the file metadata. By default 40.
   harmonic : int, optional
       the harmonic to display in the phasor plot, by default 1
   threshold : int, optional
       pixels with summed intensity below this threshold will be discarded, by default 10
   apply_median : bool, optional
       apply median filter to image before phasor calculation, by default False (median_n is ignored)
   median_n : int, optional
       number of iterations of median filter, by default 1
   apply_calibration : bool, optional
        if True, apply calibration to phasor coordinates (if calibration image and lifetime are also given), by default False
   calibration_image_layer : napari.layers.Image, optional
        napari image layer with calibration FLIM data (microtime first axis). If not given, no calibration is applied
   calibration_lifetime : float, optional
        lifetime (in ns) of calibration sample. If not given or 0, no calibration is applied
   napari_viewer : napari.Viewer, optional
       napari viewer instance, by default None

.. py:function:: apply_binning_widget(image_layer, bin_size=2, binning_3D=True)
   :noindex:

   Apply binning to image layer.

   Parameters
   ----------
   image_layer : napari.layers.Image
       napari image layer with FLIM data with dimensions (ut, time, z, y, x). microtime must be the first dimension. time and z are optional.
   bin_size : int, optional
       bin kernel size, by default 2
   binning_3D : bool, optional
       if True, bin in 3D, otherwise bin each slice in 2D, by default True

   Returns
   -------
   napari.layers.Image
       binned layer

.. autofunction:: manual_label_extract
.. autofunction:: get_n_largest_cluster_labels
.. autofunction:: split_n_largest_cluster_labels
.. autofunction:: smooth_cluster_mask

.. autoclass:: Split_N_Largest_Cluster_Labels
   :show-inheritance:

   .. rubric:: Methods Summary

   .. autosummary::
      ~Split_N_Largest_Cluster_Labels._get_layers
      ~Split_N_Largest_Cluster_Labels._get_valid_clusters_column_names
      ~Split_N_Largest_Cluster_Labels._on_run_clicked
```