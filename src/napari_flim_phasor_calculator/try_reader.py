import napari
from pathlib import Path
viewer = napari.Viewer()

# files_path = r"C:\Users\mazo260d\Desktop\Conni_BiA_PoL\stack_smaller_as_tif"  # TIF FILES
files_path = r"C:\Users\mazo260d\Desktop\Conni_BiA_PoL\stack_smaller"  # PTU FILES
files_path = r"C:\Users\mazo260d\Desktop\Conni_BiA_PoL\stack_as_tif\stack_as_tif.zarr"   # ZARR
# Error plugin cannot read zarr or tif ("no plugin named...")
viewer.open(files_path, plugin='napari-flim-phasor-calculator')
napari.run()