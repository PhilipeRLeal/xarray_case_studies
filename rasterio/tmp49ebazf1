# -*- coding: utf-8 -*-
"""
Created on Mon Aug 17 19:17:54 2020

@author: Philipe_Leal

# Reference from: https://www.earthdatascience.org/courses/use-data-open-source-python/intro-raster-data-python/raster-data-processing/reproject-raster/
"""


import os
import numpy as np
import rasterio as rio
from rasterio.warp import calculate_default_transform, reproject, Resampling


def reproject_and_export(inpath, outpath, new_crs):
    dst_crs = new_crs # CRS for web meractor 

    with rio.open(inpath) as src:
        transform, width, height = calculate_default_transform(
            src.crs, dst_crs, src.width, src.height, *src.bounds)
        kwargs = src.meta.copy()
        kwargs.update({
            'crs': dst_crs,
            'transform': transform,
            'width': width,
            'height': height
        })

        with rio.open(outpath, 'w', **kwargs) as dst:
            for i in range(1, src.count + 1):
                reproject(
                    source=rio.band(src, i),
                    destination=rio.band(dst, i),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs=dst_crs,
                    resampling=Resampling.nearest)
                
if '__main__' == __name__:
    
    reproject_and_export(inpath = os.path.join("data", "pre_DTM.tif"), 
             outpath = os.path.join("data", "pre_DTM_reproject_to_epsg_3857_.tif"), 
             new_crs = 'EPSG:3857')