from pathlib import Path
import numpy as np
from skimage import io
from napari_flim_phasor_calculator._reader import read_ptu_data_2D

folder_path = r"C:\Users\mazo260d\Desktop\Conni_BiA_PoL\embryo_FLIM_data\raw_data_embryo_stack_3tps_43pl_2ch\embryo_43pl_2ch_3tps"
# Use Path from pathlib
folder_path = Path(folder_path)
output_path = folder_path.parent / 'output_as_tif'
output_path.mkdir(exist_ok = True)

for path in folder_path.iterdir():
    if path.suffix == '.ptu':
        print(path.stem)
        image = read_ptu_data_2D(path)
        file_name = path.stem + '.tif'
        io.imsave(output_path / file_name, image)

        