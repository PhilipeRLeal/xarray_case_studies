# -*- coding: utf-8 -*-
"""
Created on Mon Jun 25 17:44:46 2018

@author: Philipe Leal
"""

from osgeo import gdal_array, gdal
# name of our source image
src = r"C:\Doutorado\Estudo_Python\GIS_in_Python\FalseColor.tif"
# load the source image into an array
arr = gdal_array.LoadFile(src)
# swap bands 1 and 2 for a natural color image.
# We will use numpy "advanced slicing" to reorder the bands.
# Using the source image
output = gdal_array.SaveArray(arr[[1, 0, 2], :], 
                              r"C:\Doutorado\Estudo_Python\GIS_in_Python\swap.tif",
                              format="GTiff", prototype=src)
# Dereference output to avoid corrupted file on some platforms
output = None

import matplotlib.pyplot as plt
import numpy as np

arr = gdal_array.LoadFile(r"C:\Doutorado\Estudo_Python\GIS_in_Python\swap.tif")

Dataset = gdal.Open(r"C:\Doutorado\Estudo_Python\GIS_in_Python\swap.tif")

Geotransform = Dataset.GetGeoTransform()

Xsize = Dataset.RasterXSize
Ysize = Dataset.RasterYSize

ulX = Geotransform[0]
ulY = Geotransform[3]
dx = Geotransform[1]
dy = Geotransform[5]

Longitudes = []

for i in range(Xsize):
    Longitudes.append(ulX + dx*i) 

Latitudes = []   
for j in range(Ysize):
    Latitudes.append(ulX - dy*j) 

xx, yy = np.meshgrid(Longitudes, Latitudes)

BB = Dataset

arr_swap = np.swapaxes(arr, 0,2)

arr_swap = np.swapaxes(arr_swap, 1,0)
plt.pcolor(xx, yy, arr_swap[:,:,0])
plt.show()