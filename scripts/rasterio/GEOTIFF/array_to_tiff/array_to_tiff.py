
# -*- coding: utf-8 -*-
"""
Created on Mon Feb 17 17:48:35 2020

@author: lealp
"""


from rasterio.transform import Affine
import rasterio



def array_to_tiff(array, x, y, dx, dy, to_file):
    
    if not to_file.endswith('.tif'):
        to_file = str(to_file) + '.tif'
    
    
    # Create the destination data source
    xpixel_size = dx    
    ypixel_size = dy
    #x_res = int((x.max() - x.min()) / pixel_size)
    #y_res = int((y.max() - y.min()) / pixel_size)
    
    
    geotransform = (x.min(), xpixel_size, 0.0, y.max(), 0.0, -ypixel_size)
    transform  = Affine.from_gdal(*geotransform)
    
    with rasterio.open(
                        to_file,
                        'w',
                        driver='GTiff',
                        height = array.shape[0],
                        width = array.shape[1],
                        count = 1,
                        dtype = array.dtype,
                        crs = '+proj=latlong',
                        transform = transform,
                    ) as dst:
                        dst.write(array, 1)
    

