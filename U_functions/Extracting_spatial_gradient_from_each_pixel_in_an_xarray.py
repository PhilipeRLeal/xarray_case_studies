# -*- coding: utf-8 -*-
"""
Created on Wed Oct  9 18:31:50 2019

@author: lealp
"""

import pandas as pd
pd.set_option('display.width', 50000)
pd.set_option('display.max_rows', 50000)
pd.set_option('display.max_columns', 5000)


import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs


import xarray as xr
import numpy as np

# https://stackoverflow.com/questions/51680659/disparity-between-result-of-numpy-gradient-applied-directly-and-applied-using-xa/51690873#51690873


def wrapped_gradient(da, coord, axis=-1):
    """Finds the gradient along a given dimension of a dataarray."""

    dims_of_coord = da.coords[coord].dims
    if len(dims_of_coord) == 1:
        dim = dims_of_coord[0]
    else:
        raise ValueError('Coordinate ' + coord + ' has multiple dimensions: ' + str(dims_of_coord))

    coord_vals = da.coords[coord].values

    return xr.apply_ufunc(np.gradient, da, coord_vals, kwargs={'axis': axis},
                      input_core_dims=[[dim], []], output_core_dims=[[dim]],
                      output_dtypes=[da.dtype])


def get_gradient(da, coords=['lat', 'lon'], axis=-1):
    
    results = []
    for coord in coords:
        results.append(wrapped_gradient(da, coord, axis=axis))
    
    
    result = xr.concat(results, dim='Geo_axis')
    
    result['Geo_axis'] = coords
    
    return result
    
# Test it out by comparing with applying np.gradient directly:
    
    

ds = xr.tutorial.open_dataset('air_temperature').load()

dmean = ds.mean('time')    
    

gradient = get_gradient(ds['air'])

gradient.isel({'time':0}).sel({'Geo_axis':'lat'}).plot()

