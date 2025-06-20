# Convert Module API

```{eval-rst}
.. currentmodule:: napari_flim_phasor_plotter.convert

.. py:function:: convert_folder_to_ome_tif(folder_path, x_pixel_size=0, y_pixel_size=0, z_pixel_size=0, pixel_size_unit="um", time_resolution_per_slice=0, time_unit="s", micro_time_resolution=0, micro_time_unit="ps", channel_names="", number_channels="0", cancel_button=False)
   :noindex:

   Convert a folder of FLIM images representing an image stack to OME-TIFF files.

   Parameters
   ----------
   folder_path : pathlib.Path
       Path to the folder containing the FLIM images.
   x_pixel_size : float, optional
       Pixel size along the x-axis, by default 0.
   y_pixel_size : float, optional
       Pixel size along the y-axis, by default 0.
   z_pixel_size : float, optional
       Pixel size along the z-axis, by default 0.
   pixel_size_unit : str, optional
       Unit of the pixel size, by default 'um'.
   time_resolution_per_slice : float, optional
       Time resolution per slice, by default 0.
   time_unit : str, optional
       Unit of the time resolution, by default 's'.
   micro_time_resolution : float, optional
       Time resolution for the TCSPC histogram, by default 0.
   micro_time_unit : str, optional
       Unit of the time resolution for the TCSPC histogram, by default 'ps'.
   channel_names : str, optional
       Names of the channels, separated by comma, by default ''.
   number_channels : str, optional
       Number of channels, by default 0. Not used, but required for the widget and filled from the metadata.
   cancel_button : bool, optional
       Cancel button for the widget, by default False.

   Returns
   -------
   None

.. py:function:: convert_file_to_ome_tif(file_path, x_pixel_size=0, y_pixel_size=0, pixel_size_unit="um", micro_time_resolution=0, micro_time_unit="ps", channel_names="", number_channels="0", cancel_button=False)
   :noindex:

   Convert a single FLIM file to an OME-TIFF file.

   Parameters
   ----------
   file_path : pathlib.Path
       Path to the FLIM image file.
   x_pixel_size : float, optional
       Pixel size along the x-axis, by default 0.
   y_pixel_size : float, optional
       Pixel size along the y-axis, by default 0.
   pixel_size_unit : str, optional
       Unit of the pixel size, by default 'um'.
   micro_time_resolution : float, optional
       Time resolution for the TCSPC histogram, by default 0.
   micro_time_unit : str, optional
       Unit of the time resolution for the TCSPC histogram, by default 'ps'.
   channel_names : str, optional
       Names of the channels, separated by comma, by default ''.
   number_channels : str, optional
       Number of channels, by default 0. Not used, but required for the widget and filled from the metadata.
   cancel_button : bool, optional
       Cancel button for the widget, by default False.

   Returns
   -------
   None

```