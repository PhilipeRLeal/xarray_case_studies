#!/usr/bin/env python
# coding: utf-8

# In[1]:


import numpy as np
import glob 
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt

import cartopy.crs as ccrs
import os, sys
import zipfile


# In[2]:


import rioxarray
import xarray as xr
import concurrent.futures
import rasterio
import affine
from rasterio.crs import CRS
from rasterio.enums import Resampling
from rasterio import shutil as rio_shutil
from rasterio.vrt import WarpedVRT
from rasterio.warp import reproject, calculate_default_transform


# In[ ]:





# In[3]:


def find_files(base_dir, ending="jp2"):
    
    list_of_paths = []
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith(ending):
                
                
                list_of_paths.append(os.path.join(root, file))
    return list_of_paths


# In[15]:



def unzip_file(filepath):
    with zipfile.ZipFile(filepath, 'r') as zip_ref:

        dir_to_extract = os.path.join(os.path.dirname(filepath), 'unziped')

        if not os.path.exists(dir_to_extract):
            os.makedirs(dir_to_extract)


        zip_ref.extractall(dir_to_extract)

        print('File {0} is unzipped'.format(os.path.basename(filepath)), end='\n'*2)

    
def unzip_files(filenames, max_workers=4):
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
    
        data_gen = (unzip_file(filepath) for filepath in filenames )

        executor.map(unzip_file, data_gen)
    
    
       


# In[16]:


sentinel_base_dir = r'C:\Users\Philipe Leal\Downloads\Curso_SR_IB_USP\IMAGENS_SENTINEL'

filenames = find_files(sentinel_base_dir, 'zip')

print('N° of compressed files', len(filenames))

unzip_files(filenames)


sentinel_unzipped_paths = find_files(sentinel_base_dir, ending="jp2")

print('N° of unzipped datasets', len(sentinel_unzipped_paths))


# # Resampling:

# In[6]:


def get_transform_res(transform):
    
    return (transform.a, transform.e)

def get_bounds(filename):
    with rasterio.open(filename) as dst:
        return dst.bounds

    
    
def get_crs(filepath):
    if isinstance(filepath, rasterio.DatasetReader):
        dataset = filepath
        
    else:
        dataset = rasterio.open(filepath)
    
    kwargs = dataset.meta.copy()
    crs = kwargs['crs']
    
    dataset.close()
    
    return crs    
    

def get_dim_sizes_from_ds(filepath):
    if isinstance(filepath, rasterio.DatasetReader):
        ds = filepath
        
    else:
        ds = rasterio.open(filepath)

    height, width = ds.height, ds.width
    
    ds.close()
    
    return height, width
    
    
def check_ds_resolution(filepath):
    
    if isinstance(filepath, rasterio.DatasetReader):
        dataset = filepath
        
    else:
        dataset = rasterio.open(filepath)
    
    
    kwargs = dataset.meta.copy()
    transform = kwargs['transform']
    
    dataset.close()
        
    return get_transform_res(transform)


# In[7]:


for filepath in sentinel_unzipped_paths:
    print(os.path.basename(filepath), check_ds_resolution(filepath))


# In[8]:


def resample_ds_by_scale_factor(filepath, upscale_factor=2):
    if isinstance(filepath, rasterio.DatasetReader):
        ds = filepath
        
    else:
        ds = rasterio.open(filepath)
    
    
    # Ensuring that scalinf factor is 2D
    
    if np.size(upscale_factor) == 1:
        upscale_factor = [upscale_factor, upscale_factor]
    
    else:
        pass
    
    
    new_height = int(ds.height * upscale_factor[1]) # <== multiplication
    new_width = int(ds.width * upscale_factor[0]) # <== multiplication
    
    
    data = ds.read(
                   out_shape=(
                            ds.count,
                            new_height,
                            new_width
                           ),
                   resampling=Resampling.bilinear
              )


    # scale image transform
    new_transform = ds.transform * ds.transform.scale(
                                                        (ds.width / new_width),
                                                        (ds.height / new_height)
                                                    )
   
    
    # creating a new_profile
    
    new_profile = ds.profile.copy()
    new_profile.update(transform=new_transform, driver='GTiff', 
                   height=new_height, width=new_width, crs=ds.crs)
    
    for key, value in new_profile.items():
        print('\t', key, ': ', value)
    print()

    
    # Closing dataset reader
    ds.close()
    
    
    return data, new_transform, new_profile



# resample_ds(sentinel_unzipped_paths[0])

def resample_ds_by_res(filepath, xtarget_resolution=2, ytarget_resolution=2, verbose=False):
    
    dx, dy = check_ds_resolution(filepath)
    
    if verbose:
        print('dx: {0} \t dy:{1}'.format(dx, dy))
    
    
    xscale_factor = abs(dx/xtarget_resolution)
    yscale_factor = abs(dy/ytarget_resolution)
    
    upscale_factor = (xscale_factor, yscale_factor) 
    
    resampled_array, new_transform, new_profile = resample_ds_by_scale_factor(filepath, 
                                                                              upscale_factor=upscale_factor)
    
    if verbose:
        print('dx: {0} \t dy:{1}'.format( *get_xy_transform_res(new_transform)  ))
    
    return resampled_array, new_transform, new_profile
    

    
def save_dataset(resampled_array, new_profile, to_directory, filename):
    
    # For saving new file:
    if not 'tif' in filename:
        filename = filename + '.tif'
    
    # making sure the directory exists prior to saving the file:
    if not os.path.exists(to_directory):
        os.makedirs(to_directory)
    
    to_path = os.path.join(to_directory, filename)
    
    with rasterio.open(to_path,'w', **new_profile) as dst:
        dst.write(resampled_array)
            
        print('dst is saved', '\n', 'in: \n ', to_path)
    


# # resampling and saving using tiff driver

# In[9]:



def resample_and_save_via_tif(filepath, 
                              to_directory,
                              xtarget_resolution=20, 
                              ytarget_resolution=20,
                              verbose=False
                              ):
    
    filename = os.path.basename(filepath).split('.')[0]
    resampled_array, new_transform, new_profile = resample_ds_by_res(filepath, 
                                                                     xtarget_resolution=xtarget_resolution, 
                                                                     ytarget_resolution=ytarget_resolution,
                                                                     verbose=verbose)
    
    
    save_dataset(resampled_array, new_profile, to_directory, filename=filename)
    
    
    print('\n\n')
    
    print('filename: {0}'.format(filename), ' resampled and saved')
    


# In[10]:


to_directory = r'C:\Users\Philipe Leal\Downloads\Curso_SR_IB_USP\IMAGENS_SENTINEL\S2\unziped\resampled'

for path in sentinel_unzipped_paths:
    
    resample_and_save_via_tif(path, 
                              to_directory,
                              xtarget_resolution=20, 
                              ytarget_resolution=40,
                              verbose=False,
                              )


# # Resampling and Saving using TIF driver in concurrent mode:

# In[11]:


with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:

    
    data_gen = (resample_and_save_via_tif(path, 
                                          to_directory,
                                          xtarget_resolution=20, 
                                          ytarget_resolution=20,
                                          verbose=False,
                                          ) for path in sentinel_unzipped_paths )
    
    executor.map(resample_and_save_via_tif, data_gen)
    


# # Resampling and Reprojection to a consistent Grid:
# 
# ## Using virtual driver:

# In[12]:


def resample_and_save_via_vrt(filepaths,
                          xres=None,
                          yres=None,
                          crs_from_epsg=None,
                          directory = None,
                          stack=True,
                          stacked_filename = 'stacked.tif',
                          windowing=False):
    
    '''
    Description:
        Function that does 
            1) resamples 
            2) reprojects (if crs is provided), 
            3) stacks multiple files into a single one: (if stack ==True)
            4) exports files to user-defined CRS resolution. 
    
    
    '''

    if not os.path.exists(directory):
        os.makedirs(directory)
    
    
    input_files = filepaths

    # Destination CRS being taken from one of the datasets
    
    if crs_from_epsg == None:
    
        dst_crs = get_crs(filepaths[0])
        
    else:
        dst_crs = CRS.from_epsg(crs_from_epsg)

    

    # standard bounds that are in CRS coordinate
    origin_bounds = get_bounds(  filepaths[0]  )

    # Output standard image dimensions
    origin_height,  origin_width = get_dim_sizes_from_ds(filepaths[0])
    
    # Output image transform
    left, bottom, right, top = origin_bounds
    origin_xres = (right - left) / origin_width
    origin_yres = (top - bottom) / origin_height
    
    
    
    if xres == None or yres == None:
        
        # same heights and widths of the original dataset
        dst_height, dst_width = origin_height, origin_width
        
        # standard destination transform
        dst_transform = affine.Affine(origin_xres, 0.0, left,
                                  0.0, -origin_yres, top)
        
    
    else:
        # ensuring that all resolutions are being passed correctly by the user
        if xres == None:
            xres = yres
            
        elif yres == None:
            yres == xres
            
        else:
            pass
            
        
        dst_width  = abs(int( (right - left) / xres ))
        dst_height = abs(int( (top - bottom) / yres ))
        
        # transform with the new width resolutions
        dst_transform = affine.Affine(xres, 0.0, left,
                                  0.0, -yres, top)


    vrt_options = {
        'resampling': Resampling.cubic,
        'crs': dst_crs,
        'transform': dst_transform,
        'height': dst_height,
        'width': dst_width
    }
    
    
    print('Files being saved in: ', directory, '\n')
    
    
    if stack is False:

        for path in input_files:

            with rasterio.open(path) as src:
                # https://rasterio.readthedocs.io/en/latest/topics/virtual-warping.html
                with WarpedVRT(src, **vrt_options) as vrt:

                    # At this point 'vrt' is a full dataset with dimensions,
                    # CRS, and spatial extent matching 'vrt_options'.
                    
                    
                    name = os.path.basename(path).split('.')[0] + '.tif'

                    outfile = os.path.join(directory, 
                                           name + '_resampled_{0}x_{1}_y_reprojected_to_epsg{2}'.format(xres, 
                                                                                                        yres, 
                                                                                                        dst_crs.to_epsg()))
                    
                    # Read all data into memory.
                    if not windowing:
                        data = vrt.read()
                        
                        rio_shutil.copy(vrt, outfile, driver='GTiff')
                    
                    else:
                        
                    # Process the dataset in chunks.  Likely not very efficient.
                    
                    
                    # Dump the aligned data into a new file.  A VRT representing
                    # this transformation can also be produced by switching
                    # to the VRT driver.
                    
                        for _, window in vrt.block_windows():
                            data = vrt.read(window=window)
                            
                            rio_shutil.copy(vrt, outfile, driver='GTiff',
                                           window=window)

                    
                    
                    

                    print('{0}'.format(name), '\t\t is complete')
                
                
    if stack == True:
        # Adapted from Ref: https://gis.stackexchange.com/questions/223910/using-rasterio-or-gdal-to-stack-multiple-bands-without-using-subprocess-commands
        
        
        outfile = os.path.join(directory, stacked_filename)
        
        
        vrt_options.update( driver =  'GTiff',
                           transform =  dst_transform,
                           height  = dst_height,
                           width =  dst_width,
                           count =  len(input_files)
                        )
        

        with rasterio.open(outfile, 'w', dtype = np.float32,  **vrt_options) as dst:
            
            for idd, filename in enumerate(input_files, start=1):
                with rasterio.open(filename, 'r') as src:
                    
                    with WarpedVRT(src,  **vrt_options) as vrt:

                            # At this point 'vrt' is a full dataset with dimensions,
                            # CRS, and spatial extent matching 'vrt_options'.

                            
                            # making sure that the data only contains one band, therefore an 2Darray (xsize, ysize)
                            
                            if src.count == 1:
                                
                                if windowing:

                                    # Alternatie for processing the dataset in chunks.  Likely not very efficient.
                                    for _, window in vrt.block_windows():
                                        data = vrt.read(window=window).astype(np.float32).squeeze(0)
                                        dst.write_band(idd, data, window=window)

                                # Dump the aligned data into a new file.  A VRT representing
                                # this transformation can also be produced by switching
                                # to the VRT driver.
                                
                                else:
                                    # Read all data into memory.
                                    data = vrt.read().astype(np.float32).squeeze(0)

                                    dst.write_band(idd, data)


                    
        print('{0}'.format(stacked_filename), '\t is complete')


# In[21]:


stack_directory = r'C:\Users\Philipe Leal\Downloads\Curso_SR_IB_USP\IMAGENS_SENTINEL\S2\unziped\stacked'
unstacked_directory = r'C:\Users\Philipe Leal\Downloads\Curso_SR_IB_USP\IMAGENS_SENTINEL\S2\unziped\resampled'

for stacking, directory in zip([False], [unstacked_directory]):                
    resample_and_save_via_vrt(sentinel_unzipped_paths, 
                              xres=30,
                              yres=30,
                              crs_from_epsg=None,
                              directory=directory,
                             stack=stacking,
                             windowing=True)


# # Reprojection using conventional drivers

# In[ ]:


filepath = sentinel_unzipped_paths[0]

os.path.basename(filepath)


# In[ ]:


filepath = sentinel_unzipped_paths[0]
dirpath = r'C:\Users\Philipe Leal\Downloads\Curso_SR_IB_USP\IMAGENS_SENTINEL\S2\unziped\stacked'

dst_crs = 'EPSG:5880'


destinations, dst_transforms = {}, {}

with rasterio.open(filepath) as src:
    old_transform = src.transform
    transform, width, height = calculate_default_transform(
        src.crs, dst_crs, src.width, src.height, *src.bounds, resolution=(40,40))
    kwargs = src.meta.copy()
    
    kwargs.update({
        'crs': dst_crs,
        'transform': transform,
        'width': width,
        'height': height
    })
    
    
    name, ending = os.path.basename(filepath).split('.')
    new_name = name + '_reprojected_to_epsg{0}_using_conventional_driver'.format(dst_crs.split(':')[1]) + '.tif'
    print(new_name)
    
    with rasterio.open(os.path.join(dirpath, new_name), 'w', **kwargs) as dst:
    
        for i in range(1, src.count + 1):
            reproject(
                        source=rasterio.band(src, i),
                        destination=rasterio.band(dst, i),
                        src_transform=src.transform,
                        src_crs=src.crs,
                        dst_transform=transform,
                        dst_crs=dst_crs,
                        resampling=Resampling.nearest)
            
            

