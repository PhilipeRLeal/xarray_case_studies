# -*- coding: utf-8 -*-
"""
Created on Mon Jun 25 18:22:10 2018

@author: Philipe Leal
"""

from osgeo import gdal_array
import operator
from functools import reduce

def histogram(a, bins=list(range(0, 256))):
    fa = a.flat
    n = gdal_array.numpy.searchsorted(gdal_array.numpy.sort(fa),
    bins)
    n = gdal_array.numpy.concatenate([n, [len(fa)]])
    hist = n[1:]-n[:-1]
    return hist

def stretch(a):
    """
    Performs a histogram stretch on a gdal_array array image.
    """
    hist = histogram(a)
    lut = []
    for b in range(0, len(hist), 256):
 # step size
        step = reduce(operator.add, hist[b:b+256]) / 255
 # create equalization lookup table
    n = 0
    for i in range(256):
        lut.append(n / step)
        n = n + hist[i+b]
    gdal_array.numpy.take(lut, a, out=a)
    
    asrc = r"C:\Doutorado\Estudo_Python\GIS_in_Python\swap.tif"

    return asrc

src = r"C:\Doutorado\Estudo_Python\GIS_in_Python\swap.tif"
arr = gdal_array.LoadFile(src)
stretched = stretch(arr)
output = gdal_array.SaveArray(arr, r"C:\Doutorado\Estudo_Python\GIS_in_Python\stretched.tif", format="GTiff", prototype=src)
output = None