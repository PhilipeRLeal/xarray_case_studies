# -*- coding: utf-8 -*-
"""
Created on Thu Oct  1 15:53:21 2020

@author: Philipe_Leal
"""
import pandas as pd
import numpy as np
from rasterio import shutil as rio_shutil

import rasterio
import rasterio.mask
import os

from rasterio.warp import calculate_default_transform, Resampling
from rasterio.vrt import WarpedVRT
from rasterio.crs import CRS

from rasterio.warp import reproject


########3 Getting main data



def helper_filepath(tiff_file_path):

    ref_dir = os.path.dirname(os.path.dirname(tiff_file_path))
    to_dir = os.path.join(ref_dir , 'resampled')
    
    if not os.path.exists(to_dir):
        os.makedirs(to_dir)
    name = os.path.basename(tiff_path).split('.')[0]
    
    temp_file = os.path.join(to_dir, '{0}.tif'.format(name))
    
    return temp_file

def unwarped_reproject_tiff(tiff_file_path, resolution=(250, 250), epsg = 5880):
    
    temp_file = helper_filepath(tiff_file_path)
    dst_crs = CRS.from_epsg(epsg)
    
    with rasterio.open(tiff_file_path) as src:
        dst_transform, dst_width, dst_height = calculate_default_transform(
                    src.crs, dst_crs, src.width, src.height, *src.bounds,
                    resolution=resolution)
        
        
    
        data = src.read()
    
        kwargs = src.meta
        kwargs['transform'] = dst_transform
        
       
        
        
        
        dst = rasterio.open(temp_file, 'w', **kwargs)

        for i, band in enumerate(data, 1):
            dest = np.zeros_like(band)

            reproject(
                band,
                dest,
                src_transform=src.transform,
                src_crs=src.crs,
                dst_transform=dst_transform,
                dst_crs=src.crs,
                resampling=Resampling.nearest)

            dst.write(dest, indexes=i)

            
        return dst


def warped_reproject_tiff(tiff_file_path, resolution=(250, 250), epsg = 5880):
    temp_file = helper_filepath(tiff_file_path)
    dst_crs = CRS.from_epsg(epsg)
    
    with rasterio.open(tiff_file_path) as src:
        dst_transform, dst_width, dst_height = calculate_default_transform(
                    src.crs, dst_crs, src.width, src.height, *src.bounds,
                    resolution=resolution)
        
        
        vrt_options = {
                        'resampling': Resampling.cubic,
                        'crs': dst_crs,
                        'transform': dst_transform,
                        'height': dst_height,
                        'width': dst_width,
                    }
    
        
    


        with WarpedVRT(src, **vrt_options) as vrt:

            # At this point 'vrt' is a full dataset with dimensions,
            # CRS, and spatial extent matching 'vrt_options'.

            # Read all data into memory.
            data = vrt.read()

            # Process the dataset in chunks.  Likely not very efficient.
            for _, window in vrt.block_windows():
                data = vrt.read(window=window)

            # Dump the aligned data into a new file.  A VRT representing
            # this transformation can also be produced by switching
            # to the VRT driver.
            
            
            
            rio_shutil.copy(vrt, temp_file, driver='GTiff')
        
    return temp_file


def reproject_tiff(tiff_file_path, resolution=(250, 250), epsg = 5880, warped=False):
    
    if warped == True:
        return warped_reproject_tiff(tiff_file_path, resolution, epsg)
    
    else:
        unwarped_reproject_tiff(tiff_file_path, resolution, epsg)



if '__main__' == __name__:
    
    main_dir = r'C:\Users\Philipe Leal\Downloads\temp\Global Impervious Surfaces products'
    
    valid_tiffs = pd.read_csv( os.path.join(main_dir , 'Valid_files.csv')).paths
    
    print('Valid Total Files: ', len(valid_tiffs))
    
    epsg = 5880
    src_file_names = []
    
    for tiff_path in valid_tiffs:
        enum = 0
        src = reproject_tiff(tiff_path, resolution = (50, 50), epsg = epsg, warped=True)
        
        src_file_names.append(src)
    
    src_df = pd.Series(src_file_names)
    
    src_df.to_csv( os.path.join(main_dir , 'Resampled_and_Valid_files.csv'))
        
    