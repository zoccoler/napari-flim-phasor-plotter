# -*- coding: utf-8 -*-
"""
Created on Mon Dec 19 09:11:43 2022

@author: mazo260d
"""

import napari
from napari_flim_phasor_calculator._widget import make_flim_phasor_plot
from napari_flim_phasor_calculator._synthetic import create_time_array, make_synthetic_flim_data
viewer = napari.Viewer()

laser_frequency = 60 # MHz
amplitude = 1
tau_list = [0.1, 0.2, 0.5, 1, 2, 5, 10, 25, 40] # ns
number_of_harmonics = 5
number_of_time_points = 1000

time_array = create_time_array(laser_frequency, number_of_time_points)
flim_data = make_synthetic_flim_data(time_array, amplitude, tau_list)
flim_data = flim_data.reshape(number_of_time_points, 3, 3)


layer = viewer.add_image(flim_data, rgb = False)#, metadata={'TTResult_SyncRate': 39100000})

# this time, our widget will be a MagicFactory or FunctionGui instance
my_widget = make_flim_phasor_plot()

viewer.window.add_plugin_dock_widget(plugin_name = 'napari-flim-phasor-calculator',
                                     widget_name='Make FLIM Phasor Plot')

# if we "call" this object, it'll execute our function
my_widget(layer, laser_frequency = laser_frequency, threshold = 30)



