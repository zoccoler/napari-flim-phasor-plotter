from pathlib import Path
import napari
import dask.array as da
import dask
from natsort import natsorted
import numpy as np
from napari_flim_phasor_calculator._reader import get_current_tz

folder_path = r"C:\Users\mazo260d\Desktop\Conni_BiA_PoL\stack_as_tif"
folder_path = Path(folder_path)

def read_tif_data_2D(path):
    from skimage.io import imread
    image = imread(path)
    return image

def read_tif_data_3D(file_paths, image_slice_max_shape):
    file_paths = natsorted(file_paths)
    z_list = []
    for file_path in file_paths:
        if file_path.suffix == '.tif':
            current_t, current_z = get_current_tz(file_path)
            data = read_tif_data_2D(file_path)
            if current_z is not None:
                image = np.zeros(image_slice_max_shape, dtype=data.dtype)
                image[:data.shape[0], :data.shape[1], :data.shape[2], :data.shape[3]] = data
                z_list.append(image)
    image_3D = np.stack(z_list)
    # move channel and microtime to the beginning (putting z behind them): from (z, ch, mt, y, x) to (ch, mt, z, y, x)
    image_3D = np.moveaxis(image_3D, [-4, -3], [0, 1])
    return image_3D

@dask.delayed
def read_tif_data_2D_delayed(path):
    return read_tif_data_2D(path)

@dask.delayed
def read_tif_data_3D_delayed(file_paths, image_slice_max_shape):
    return read_tif_data_3D(file_paths, image_slice_max_shape)

# Read all slices to get slice max shape and dtype (not ideal but for now it is OK)
slice_shape_list = []
for file_path in folder_path.iterdir():
    if file_path.suffix == '.tif':
        image_2D = read_tif_data_2D(file_path)
        slice_shape_list.append(image_2D.shape)
slice_max_shape = max(slice_shape_list)
print('last_slice_shape = ', image_2D.shape,'image_dtype = ', image_2D.dtype)
print('max_slice_shape = ', slice_max_shape)

# Get max z slices by reading all file names
def get_max_zslices(file_paths):
    max_z = max([get_current_tz(file_path) for file_path in file_paths if file_path.suffix == '.tif'])[1]
    if max_z is None:
        return 1
    return max_z
def get_max_time(file_paths):
    max_time = max([get_current_tz(file_path) for file_path in file_paths if file_path.suffix == '.tif'])[0]
    if max_time is None:
        return 1
    return max_time
file_paths = [file_path for file_path in folder_path.iterdir() if file_path.suffix == '.tif']
max_z = get_max_zslices(file_paths)
print('max_z slices = ', max_z)
max_t = get_max_time(file_paths)
print('max_time = ', max_t)

## Read 3D data without dask
# file_paths = [file_path for file_path in folder_path.iterdir() if file_path.suffix == '.tif']
# image_3D = read_tif_data_3D(file_paths, image_slice_max_shape=slice_max_shape)
# print('image_3D shape = ', image_3D.shape)

# Make timelapse (single timepoint in this case) of 3D stacks
def make_timelapse_of_3D_stacks(file_paths, image_stack_shape):
    # Make a dask stack
    t_list = []
    z_path_list = []
    previous_t = 1
    for file_path in file_paths:
        if file_path.suffix == '.tif':
            current_t, current_z = get_current_tz(file_path)
            #If time changed, append to t_list and clear z_list
            if current_t is not None:
                if current_t > previous_t:
                    z_stack = read_tif_data_3D(z_path_list, image_slice_max_shape = image_stack_shape[1:])
                    t_list.append(z_stack)
                    z_path_list = []
                    previous_t = current_t
                else:
                    z_path_list.append(file_path)
    # If no timepoints, make zstack
    if current_t is None:
        z_path_list = file_paths
        z_stack = read_tif_data_3D(z_path_list, image_slice_max_shape = image_stack_shape[1:])
    # Append last time point
    t_list.append(z_stack)
    timelapse_of_3D_stacks = np.stack(t_list)
    # move channel and microtime to the beginning (putting t behind them): (ch, mt, t, z, y, x)
    timelapse_of_3D_stacks =  np.moveaxis(timelapse_of_3D_stacks, [-5, -4], [0, 1])
    return timelapse_of_3D_stacks


## Read 3D timelapse data without dask (just a single timepoint for now)
# file_paths = [file_path for file_path in folder_path.iterdir() if file_path.suffix == '.tif']
# image_stack_shape = (max_z, *slice_max_shape)
# image_3D_timelapse = make_timelapse_of_3D_stacks(file_paths, image_stack_shape)
# print('image_3D timelapse shape = ', image_3D_timelapse.shape)

# @dask.delayed
def make_dask_timelapse_of_3D_stacks(file_paths, image_stack_shape, image_dtype):
    # Make a dask stack
    t_list = []
    z_path_list = []
    previous_t = 1
    for file_path in file_paths:
        if file_path.suffix == '.tif':
            current_t, current_z = get_current_tz(file_path)
            #If time changed, append to t_list and clear z_list
            if current_t is not None:
                if current_t > previous_t:
                    z_stack = da.from_delayed(read_tif_data_3D_delayed(file_paths, image_slice_max_shape=image_stack_shape[1:]), shape=image_stack_shape, dtype=image_2D.dtype)
                    t_list.append(z_stack)
                    z_path_list = []
                    previous_t = current_t
                else:
                    z_path_list.append(file_path)
    # If no timepoints, make zstack
    if current_t is None:
        z_path_list = file_paths
        z_stack = da.from_delayed(read_tif_data_3D_delayed(file_paths, image_slice_max_shape=image_stack_shape[1:]), shape=image_stack_shape, dtype=image_2D.dtype)
    # Append last time point
    t_list.append(z_stack)
    dask_timelapse_of_3D_stacks = da.stack(t_list)
    # chunk = (len(t_list), image_stack_shape[0], image_stack_shape[1], 1, 1, 1) # t, z, ch, mt, y, x
    # dask_timelapse_of_3D_stacks = dask_timelapse_of_3D_stacks.rechunk(chunk) # too slow, never finishes....
    # move channel and microtime to the beginning (putting t behind them): (ch, mt, t, z, y, x)
    dask_timelapse_of_3D_stacks =  da.moveaxis(dask_timelapse_of_3D_stacks, [-5, -4], [0, 1])
    return dask_timelapse_of_3D_stacks

# Read 3D data with dask
file_paths = [file_path for file_path in folder_path.iterdir() if file_path.suffix == '.tif']
image_stack_shape = (max_z, *slice_max_shape)
image_3D_dask = da.from_delayed(read_tif_data_3D_delayed(file_paths, image_slice_max_shape=slice_max_shape), shape=image_stack_shape, dtype=image_2D.dtype)
print('image_3D dask shape = ', image_3D_dask.shape)
print('image_3D dask chunks = ', image_3D_dask.chunks)

# Read 3D timelapse data with dask
file_paths = [file_path for file_path in folder_path.iterdir() if file_path.suffix == '.tif']
image_stack_shape = (max_z, *slice_max_shape)
image_3D_timelapse_dask = make_dask_timelapse_of_3D_stacks(file_paths, image_stack_shape=image_stack_shape, image_dtype=image_2D.dtype)
print('image_3D timelapse shape = ', image_3D_timelapse_dask.shape)


import skimage.io
import dask.array as da
import dask

imread = dask.delayed(read_tif_data_2D, pure=True)  # Lazy version of imread

lazy_images = [imread(path) for path in file_paths]   # Lazily evaluate imread on each path
sample = lazy_images[0].compute()  # load the first image (assume rest are same shape/dtype)

arrays = [da.from_delayed(lazy_image,           # Construct a small Dask array
                          dtype=sample.dtype,   # for every lazy value
                          shape=slice_max_shape)
          for lazy_image in lazy_images]

stack = da.stack(arrays, axis=0)                # Stack all small Dask arrays into one
print('stack shape and chunks = ', stack.shape, '\n', stack.chunks)

# Using map_blocks

def read_one_image(block_id, filenames=file_paths, axis=0):
    # a function that reads in one chunk of data
    path = filenames[block_id[axis]]
    image = read_tif_data_2D(path)
    return np.expand_dims(image, axis=axis)

# load the first image (assume rest are same shape/dtype)
sample = read_tif_data_2D(file_paths[0])

stack = da.map_blocks(
    read_one_image,
    dtype=sample.dtype,
    chunks=((1,) * len(file_paths),  *slice_max_shape)
)
print('stack shape and chunks = ', stack.shape, '\n', stack.chunks)
stack = stack.rechunk((max_z, *slice_max_shape))
print('stack shape and chunks = ', stack.shape, '\n', stack.chunks)


