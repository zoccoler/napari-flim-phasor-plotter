from napari_clusters_plotter._plotter import PlotterWidget
from qtpy.QtCore import QSize

def add_phasor_circle(ax):
    '''
    Generate FLIM universal semi-circle plot
    '''
    import numpy as np
    import matplotlib.pyplot as plt
    angles = np.linspace(0, np.pi, 180)
    x =(np.cos(angles) + 1) / 2
    y = np.sin(angles) / 2
    ax.plot(x,y, 'yellow', alpha=0.3)
    return ax

def add_2d_histogram(ax, x, y):
    import matplotlib.pyplot as plt
    output = ax.hist2d(
        x=x,
        y=y,
        bins=10,
        cmap='jet',
        norm='log',
        alpha=0.5
        )
    return ax

class PhasorPlotterWidget(PlotterWidget):
    def __init__(self, napari_viewer):
        super().__init__(napari_viewer)
        self.setMinimumSize(QSize(100,300))
    def run(self,
            features,
            plot_x_axis_name,
            plot_y_axis_name,
            plot_cluster_name=None,
            redraw_cluster_image=True,):
        super().run(features=features,
                    plot_x_axis_name=plot_x_axis_name,
                    plot_y_axis_name=plot_y_axis_name,
                    plot_cluster_name=plot_cluster_name,
                    redraw_cluster_image=redraw_cluster_image,)
        add_phasor_circle(self.graphics_widget.axes)
        self.graphics_widget.draw()
        # To Do: Add 2d histogram
        # add_2d_histogram(self.graphics_widget.axes,
        #                  features[plot_x_axis_name],
        #                  features[plot_y_axis_name])
