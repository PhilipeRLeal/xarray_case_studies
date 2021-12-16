# -*- coding: utf-8 -*-
"""
Created on Thu Dec 10 11:07:28 2020

@author: Philipe_Leal
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os, sys
import geopandas as gpd
import cartopy.crs as ccrs
import matplotlib.ticker as mticker
pd.set_option('display.max_rows', 5000)
pd.set_option('display.max_columns', 5000)
import xarray as xr


from IDW_over_xarray import (get_coord_limits_from_dataarray, 
                             create_output_grid, 
                             xr_to_2D_array)

from scipy.interpolate import griddata

from submodules.array_to_xarray import rebuild_dataarray
    
def plot_dataArray(arr, transform=ccrs.PlateCarree(), x='lon', y='lat', figsup=None):
    
    fig, ax = plt.subplots(subplot_kw={'projection':ccrs.PlateCarree()})
    
    arr.plot(ax=ax, transform=transform, 
             x=x, y=y, 
             add_colorbar=True)
    ax.gridlines(draw_labels=True)
    ax.coastlines()
    
    fig.suptitle(figsup)
    
    fig.show()


def interpolate_using_gridata(points, point_values, output_grid, 
                              output_shape, 
                              method='nearest', 
                              skip_nans=True,
                              ):
    
    
    if skip_nans:
        nanmean = np.nanmean(point_values)
        
        point_values = point_values - nanmean
        
        point_values[np.isnan(point_values)] = 0
    
    grid_z_nearest = griddata( np.flip(points, axis=1), 
                              point_values, 
                              (output_grid[:,1], 
                               output_grid[:,0]), method=method)
    
    if skip_nans:
        grid_z_nearest = grid_z_nearest + nanmean
    
    return grid_z_nearest.reshape(output_shape)
    
if '__main__' == __name__:
    
    ds = xr.tutorial.open_dataset('rasm').load()
    Tair = ds['Tair']
    
    Tair_T1 = Tair.isel(time=0)
    Tair_T1.coords['xc'] = (Tair_T1.coords['xc'] + 180) % 360 - 180
    Tair_T1.coords['yc'] = (Tair_T1.coords['yc'] + 90) % 180 - 90
    
    
    plot_dataArray(Tair_T1, transform=ccrs.PlateCarree(), 
                   x='xc', y='yc', figsup='Data Original')
    
    
    points, point_values = xr_to_2D_array(Tair_T1)
    
    
    
    xres = 5
    yres = 5
    
    
    xmin, xmax, ymin, ymax = get_coord_limits_from_dataarray(Tair_T1)
    
    
    output_grid, output_shape, Xcoords, Ycoords = create_output_grid(xmin, xmax, xres, ymin, ymax, yres)
    
    
    
    methods = ['nearest', 'linear', 'cubic']
    
    R = {}
    for method in methods:
        
        R[method] = interpolate_using_gridata(points, point_values, output_grid, 
                              output_shape, 
                              method=method, 
                              skip_nans=False,
                              )
   
  
        
        dataArray_interpolated = rebuild_dataarray(R[method], 
                                                   Xcoords, 
                                                   Ycoords,
                                                   xdim='lon', 
                                                   ydim='lat')
        
        
        plot_dataArray(dataArray_interpolated, transform=ccrs.PlateCarree(), 
                       x='lon', y='lat', figsup='Interp - {0}'.format(method))
        
    
    
    
    