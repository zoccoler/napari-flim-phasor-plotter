from napari.layers import Layer
from napari_clusters_plotter._plotter import PlotterWidget
from qtpy.QtCore import QSize
from qtpy.QtWidgets import QHBoxLayout, QLineEdit, QLabel, QPushButton, QWidget
import numpy as np
import warnings


class PhasorPlotterWidget(PlotterWidget):
    def __init__(self, napari_viewer):
        super().__init__(napari_viewer)
        self.setMinimumSize(QSize(100, 300))
        self.frequency = None
        self.harmonic = 1

        self.tau_lines_container = QWidget()
        self.tau_lines_container.setLayout(QHBoxLayout())
        self.tau_lines_container.layout().addWidget(QLabel("Tau lines:"))
        self.tau_lines_line_edit_widget = QLineEdit()
        self.tau_lines_line_edit_widget.setPlaceholderText(
            "Comma-separated list of tau values in ns"
        )
        self.tau_lines_container.layout().addWidget(
            self.tau_lines_line_edit_widget
        )
        self.tau_lines_button = QPushButton("Show/hide")
        self.tau_lines_button.setCheckable(True)
        self.tau_lines_button.setChecked(False)
        self.tau_lines_container.layout().addWidget(self.tau_lines_button)
        self.advanced_options_container.layout().addWidget(
            self.tau_lines_container
        )
        self.tau_lines_button.clicked.connect(self.on_show_hide_tau_lines)

        # Start with histogram plot
        self.plotting_type.setCurrentIndex(1)
        # Start with log scale
        self.log_scale.setChecked(True)

    def run(
        self,
        features,
        plot_x_axis_name,
        plot_y_axis_name,
        plot_cluster_name,
        redraw_cluster_image=True,
        force_redraw=True,
        ensure_full_semi_circle_displayed=False,
    ):
        super().run(
            features=features,
            plot_x_axis_name=plot_x_axis_name,
            plot_y_axis_name=plot_y_axis_name,
            plot_cluster_name=plot_cluster_name,
            redraw_cluster_image=redraw_cluster_image,
            force_redraw=force_redraw,
        )
        if self.tau_lines_button.isChecked():
            self.add_tau_lines_from_widget()
        self.redefine_axes_limits(
            ensure_full_semi_circle_displayed=ensure_full_semi_circle_displayed
        )

    def _draw_cluster_image(
        self,
        is_tracking_data: bool,
        plot_cluster_name: str,
        cluster_ids,
        cmap_dict=None,
    ) -> Layer:
        visualized_layer = super()._draw_cluster_image(
            is_tracking_data, plot_cluster_name, cluster_ids, cmap_dict
        )
        image_layer_name = self.layer_select.value.name.replace(
            "Labelled_pixels_from_", ""
        )
        visualized_layer.name = "Phasor_clusters_from_" + image_layer_name
        visualized_layer.opacity = 0.5
        return visualized_layer

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
        """
        Generate FLIM universal semi-circle plot
        """
        angles = np.linspace(0, np.pi, 180)
        x = (np.cos(angles) + 1) / 2
        y = np.sin(angles) / 2
        ax.plot(x, y, "white", alpha=0.3)
        return ax

    def add_tau_lines(self, ax, tau_list, frequency, harmonic=1):
        if not isinstance(tau_list, list):
            tau_list = [tau_list]
        frequency = frequency * 1e6  # MHz to Hz
        w = 2 * np.pi * frequency  # Hz to radians/s
        w = w * harmonic
        for tau in tau_list:
            tau = tau * 1e-9  # nanoseconds to seconds
            g = 1 / (1 + ((w * tau) ** 2))
            s = (w * tau) / (1 + ((w * tau) ** 2))
            (dot,) = ax.plot(g, s, marker="o", mfc="none")
            array = np.linspace(0, g, 50)
            y = array * s / g
            ax.plot(array, y, color=dot.get_color(), alpha=0.2)
            ax.annotate(
                text=f"{tau * 1E9:.2f} ns",
                xy=(g, s),
                fontsize=8,
                color=dot.get_color(),
                annotation_clip=True,
            )

    def add_tau_lines_from_widget(self):
        tau_lines_text = self.tau_lines_line_edit_widget.text()
        tau_list = [
            float(tau) for tau in tau_lines_text.split(",") if tau
        ]  # and tau != 'Comma-separated list of tau values in ns']
        if tau_list:
            if self.frequency:
                self.add_tau_lines(
                    self.graphics_widget.axes,
                    tau_list,
                    frequency=self.frequency,
                    harmonic=self.harmonic,
                )
                self.graphics_widget.draw_idle()
            else:
                warnings.warn(
                    "Frequency is not set. Please calculate phasor plot first."
                )

    def on_show_hide_tau_lines(self):
        if self.tau_lines_button.isChecked():
            # draw tau lines
            self.add_tau_lines_from_widget()
        else:
            # reset plot to clear tau lines
            self.graphics_widget.reset()
            # redraw phasor plot
            self.run(
                features=self.layer_select.value.features,
                plot_x_axis_name=self.plot_x_axis.currentText(),
                plot_y_axis_name=self.plot_y_axis.currentText(),
                plot_cluster_name=self.plot_cluster_id.currentText(),
                redraw_cluster_image=False,
            )
