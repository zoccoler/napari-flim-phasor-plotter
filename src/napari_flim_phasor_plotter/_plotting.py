from napari_clusters_plotter._plotter import PlotterWidget
from qtpy.QtCore import QSize
import numpy as np


class PhasorPlotterWidget(PlotterWidget):
    def __init__(self, napari_viewer):
        super().__init__(napari_viewer)
        self.setMinimumSize(QSize(100, 300))

    def run(self,
            features,
            plot_x_axis_name,
            plot_y_axis_name,
            plot_cluster_name=None,
            redraw_cluster_image=True,
            ):
        super().run(features=features,
                    plot_x_axis_name=plot_x_axis_name,
                    plot_y_axis_name=plot_y_axis_name,
                    plot_cluster_name=plot_cluster_name,
                    redraw_cluster_image=redraw_cluster_image,)

        self.redefine_axes_limits(ensure_full_semi_circle_displayed=False)
        

    def redefine_axes_limits(self, ensure_full_semi_circle_displayed=True):
        # Redefine axes limits
        if ensure_full_semi_circle_displayed:
            self.add_phasor_circle(self.graphics_widget.axes)
            self.graphics_widget.axes.autoscale()
            self.graphics_widget.draw()
            current_ylim = self.graphics_widget.axes.get_ylim()
            current_xlim = self.graphics_widget.axes.get_xlim()
            ylim_0 = np.amin([current_ylim[0] - 0.1 * current_ylim[0], -0.1])
            ylim_1 = np.amax([current_ylim[1] + 0.1 * current_ylim[1], 0.7])
            xlim_0 = np.amin([current_xlim[0] - 0.1 * current_xlim[0], -0.1])
            xlim_1 = np.amax([current_xlim[1] + 0.1 * current_xlim[1], 1.1])
        else:
            self.graphics_widget.axes.autoscale()
            self.graphics_widget.draw()
            current_ylim = self.graphics_widget.axes.get_ylim()
            current_xlim = self.graphics_widget.axes.get_xlim()
            self.add_phasor_circle(self.graphics_widget.axes)
            ylim_0 = current_ylim[0] - 0.1 * current_ylim[0]
            ylim_1 = current_ylim[1] + 0.1 * current_ylim[1]
            xlim_0 = current_xlim[0] - 0.1 * current_xlim[0]
            xlim_1 = current_xlim[1] + 0.1 * current_xlim[1]
        self.graphics_widget.axes.set_ylim([ylim_0, ylim_1])
        self.graphics_widget.axes.set_xlim([xlim_0, xlim_1])
        self.graphics_widget.draw_idle()


    def add_phasor_circle(self, ax):
        '''
        Generate FLIM universal semi-circle plot
        '''
        import numpy as np
        angles = np.linspace(0, np.pi, 180)
        x = (np.cos(angles) + 1) / 2
        y = np.sin(angles) / 2
        ax.plot(x, y, 'white', alpha=0.3)
        return ax


    def add_tau_lines(self, ax, tau_list, frequency):
        import numpy as np
        if not isinstance(tau_list, list):
            tau_list = [tau_list]
        frequency = frequency * 1E6  # MHz to Hz
        w = 2 * np.pi * frequency  # Hz to radians/s
        for tau in tau_list:
            tau = tau * 1E-9  # nanoseconds to seconds
            g = 1 / (1 + ((w * tau)**2))
            s = (w * tau) / (1 + ((w * tau)**2))
            dot, = ax.plot(g, s, marker='o', mfc='none')
            array = np.linspace(0, g, 50)
            y = (array * s / g)
            ax.plot(array, y, color=dot.get_color())