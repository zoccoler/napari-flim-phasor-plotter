def test_binning():
    from napari_flim_phasor_plotter.filters import apply_binning
    import numpy as np

    input_flim_data = np.arange(100).reshape(
        2, 1, 2, 5, 5
    )  # (utime, time, z, y, x)

    output_binned_2D = np.array(
        [
            [
                [
                    [
                        [12, 16, 20, 24, 26],
                        [32, 36, 40, 44, 46],
                        [52, 56, 60, 64, 66],
                        [72, 76, 80, 84, 86],
                        [82, 86, 90, 94, 96],
                    ],
                    [
                        [112, 116, 120, 124, 126],
                        [132, 136, 140, 144, 146],
                        [152, 156, 160, 164, 166],
                        [172, 176, 180, 184, 186],
                        [182, 186, 190, 194, 196],
                    ],
                ]
            ],
            [
                [
                    [
                        [212, 216, 220, 224, 226],
                        [232, 236, 240, 244, 246],
                        [252, 256, 260, 264, 266],
                        [272, 276, 280, 284, 286],
                        [282, 286, 290, 294, 296],
                    ],
                    [
                        [312, 316, 320, 324, 326],
                        [332, 336, 340, 344, 346],
                        [352, 356, 360, 364, 366],
                        [372, 376, 380, 384, 386],
                        [382, 386, 390, 394, 396],
                    ],
                ]
            ],
        ]
    )
    output_binned_3D = np.array(
        [
            [
                [
                    [
                        [124, 132, 140, 148, 152],
                        [164, 172, 180, 188, 192],
                        [204, 212, 220, 228, 232],
                        [244, 252, 260, 268, 272],
                        [264, 272, 280, 288, 292],
                    ],
                    [
                        [224, 232, 240, 248, 252],
                        [264, 272, 280, 288, 292],
                        [304, 312, 320, 328, 332],
                        [344, 352, 360, 368, 372],
                        [364, 372, 380, 388, 392],
                    ],
                ]
            ],
            [
                [
                    [
                        [524, 532, 540, 548, 552],
                        [564, 572, 580, 588, 592],
                        [604, 612, 620, 628, 632],
                        [644, 652, 660, 668, 672],
                        [664, 672, 680, 688, 692],
                    ],
                    [
                        [624, 632, 640, 648, 652],
                        [664, 672, 680, 688, 692],
                        [704, 712, 720, 728, 732],
                        [744, 752, 760, 768, 772],
                        [764, 772, 780, 788, 792],
                    ],
                ]
            ],
        ]
    )

    image_binned_2D = apply_binning(
        input_flim_data, bin_size=2, binning_3D=False
    )
    image_binned_3D = apply_binning(
        input_flim_data, bin_size=2, binning_3D=True
    )

    assert np.array_equal(image_binned_2D, output_binned_2D)
    assert np.array_equal(image_binned_3D, output_binned_3D)


def test_median_filter():
    import numpy as np
    from napari_flim_phasor_plotter.phasor import get_phasor_components
    from napari_flim_phasor_plotter._synthetic import (
        make_synthetic_flim_data,
        create_time_array,
    )
    from napari_flim_phasor_plotter.filters import apply_median_filter

    s_median_filt_expected = np.array(
        [[0.026525, 0.194265], [0.026525, 0.194265]]
    )
    g_median_filt_expected = np.array(
        [[0.990589, 0.886187], [0.990589, 0.886187]]
    )

    # create synthetic data
    frequency = 40
    n_points = 10
    amplitudes = [1, 1, 2, 2]
    lifetimes = [0.8, 2, 0.8, 2]
    time_array = create_time_array(frequency, n_points)
    flim_data = make_synthetic_flim_data(
        time_array, amplitudes, lifetimes
    ).reshape(n_points, 2, 2)

    g, s, dc = get_phasor_components(flim_data)
    g_median_filt = apply_median_filter(g)
    s_median_filt = apply_median_filter(s)

    assert np.allclose(g_median_filt, g_median_filt_expected, atol=1e-5)
    assert np.allclose(s_median_filt, s_median_filt_expected, atol=1e-5)
