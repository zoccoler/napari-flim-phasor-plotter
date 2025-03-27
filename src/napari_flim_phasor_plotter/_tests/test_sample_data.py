from napari_flim_phasor_plotter._sample_data import (
    load_seminal_receptacle_image,
    load_hazelnut_image,
    load_hazelnut_z_stack,
    load_lifetime_cat_synthtetic_single_image,
)


def test_loading_sample_data():
    """Test loading sample data."""
    receptacle_layerdatatuple_list = load_seminal_receptacle_image()
    receptacle_raw_flim_image, receptacle_intensity_image = (
        receptacle_layerdatatuple_list[0][0],
        receptacle_layerdatatuple_list[1][0],
    )

    hazelnut_layerdatatuple_list = load_hazelnut_image()
    hazelnut_raw_flim_image, hazelnut_intensity_image = (
        hazelnut_layerdatatuple_list[0][0],
        hazelnut_layerdatatuple_list[1][0],
    )

    hazelnut_z_stack_layerdatatuple_list = load_hazelnut_z_stack()
    hazelnut_z_stack_raw_flim_image, hazelnut_z_stack_intensity_image = (
        hazelnut_z_stack_layerdatatuple_list[0][0],
        hazelnut_z_stack_layerdatatuple_list[1][0],
    )

    cat_lifetime_layerdatatuple_list = (
        load_lifetime_cat_synthtetic_single_image()
    )
    cat_lifetime_raw_flim_image, cat_lifetime_intensity_image = (
        cat_lifetime_layerdatatuple_list[0][0],
        cat_lifetime_layerdatatuple_list[1][0],
    )

    assert receptacle_raw_flim_image.shape == (256, 1, 1, 512, 512)
    assert receptacle_intensity_image.shape == (1, 1, 512, 512)

    assert hazelnut_raw_flim_image.shape == (139, 1, 1, 256, 256)
    assert hazelnut_intensity_image.shape == (1, 1, 256, 256)

    assert hazelnut_z_stack_raw_flim_image.shape == (139, 1, 11, 256, 256)
    assert hazelnut_z_stack_intensity_image.shape == (1, 11, 256, 256)

    assert cat_lifetime_raw_flim_image.shape == (256, 1, 1, 256, 256)
    assert cat_lifetime_intensity_image.shape == (1, 1, 256, 256)
