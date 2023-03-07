import numpy as np

from napari_flim_phasor_calculator import napari_get_reader

# To do: Get a sample file to test reader

import napari
from pathlib import Path
viewer = napari.Viewer()
ptu_image_path = r"C:\Users\mazo260d\Desktop\Conni_BiA_PoL\copied_for_Marcelo\single_image\raw_FLIM_data\single_FLIM_image.ptu"
sdt_image_path = r"C:\Users\mazo260d\Desktop\Conni_BiA_PoL\Sample_files\sperm_seminal_receptacle_NADH_FLIM_2ch.sdt"
ptu_folder_path_timelapse = r"C:\Users\mazo260d\Desktop\Conni_BiA_PoL\embryo_FLIM_data\raw_data_embryo_stack_3tps_43pl_2ch\embryo_43pl_2ch_3tps"
ptu_folder_path_zstack = r"C:\Users\mazo260d\Desktop\Conni_BiA_PoL\stack" # neverending reading...
ptu_folder_path_zstack_smaller = r"C:\Users\mazo260d\Desktop\Conni_BiA_PoL\stack_smaller"

# ptu_image_path = r"Z:\Data\Conni_BiA_PoL\copied_for_Marcelo\single_image\raw_FLIM_data\single_FLIM_image.ptu"
# sdt_image_path = r"Z:\Data\Conni_BiA_PoL\Sample_files\sperm_seminal_receptacle_NADH_FLIM_2ch.sdt"
# ptu_folder_path_timelapse = r"Z:\Data\Conni_BiA_PoL\embryo_FLIM_data\raw_data_embryo_stack_3tps_43pl_2ch\embryo_43pl_2ch_3tps"
# ptu_folder_path_zstack = r"Z:\Data\Conni_BiA_PoL\stack"

# ptu_list = list(ptu_folder_path.glob('**/*.ptu'))
# viewer.open(ptu_list, stack=True)

# Open single sdt image
# viewer.open(sdt_image_path, plugin='napari-flim-phasor-calculator')
# # Open single ptu image
# viewer.open(ptu_image_path, plugin='napari-flim-phasor-calculator')
# Open z-stack
# viewer.open(ptu_folder_path_zstack, plugin='napari-flim-phasor-calculator')
# open time-lapse z-stack
viewer.open(ptu_folder_path_zstack_smaller, plugin='napari-flim-phasor-calculator')
napari.run()


# # tmp_path is a pytest fixture
# def test_reader(tmp_path):
#     """An example of how you might test your plugin."""

#     # write some fake data using your supported file format
#     my_test_file = str(tmp_path / "myfile.npy")
#     original_data = np.random.rand(20, 20)
#     np.save(my_test_file, original_data)

#     # try to read it back in
#     reader = napari_get_reader(my_test_file)
#     assert callable(reader)

#     # make sure we're delivering the right format
#     layer_data_list = reader(my_test_file)
#     assert isinstance(layer_data_list, list) and len(layer_data_list) > 0
#     layer_data_tuple = layer_data_list[0]
#     assert isinstance(layer_data_tuple, tuple) and len(layer_data_tuple) > 0

#     # make sure it's the same as it started
#     np.testing.assert_allclose(original_data, layer_data_tuple[0])


# def test_get_reader_pass():
#     reader = napari_get_reader("fake.file")
#     assert reader is None
