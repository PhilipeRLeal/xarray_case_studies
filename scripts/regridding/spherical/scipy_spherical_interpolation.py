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

from scipy.interpolate import LSQSphereBivariateSpline



def rebuild_dataarray(arr, xcoor, ycoor, xdim, ydim):
    
    return xr.DataArray(arr.T, 
                        coords={ydim:ycoor,
                                xdim:xcoor},
                        dims=[ydim,
                              xdim])
    
def plot_dataArray(arr, transform=ccrs.PlateCarree(), x='lon', y='lat', figsup=None):
    
    fig, ax = plt.subplots(subplot_kw={'projection':ccrs.PlateCarree()})
    
    arr.plot(ax=ax, transform=transform, 
             x=x, y=y, 
             add_colorbar=True)
    ax.gridlines(draw_labels=True)
    ax.coastlines()
    
    fig.suptitle(figsup)
    
    fig.show()



def fix_radian_limits(arr, is_lon=True):
    
    if is_lon:
    
        arr = np.arccos(np.cos(arr))
    else:
        arr = np.arcsin(np.sin(arr))
    
    return arr

def interpolate_using_spherical_coords(points,
                                      point_values, 
                                      output_grid, 
                                      skip_nans=True,
                                      ):
   
    if skip_nans:
       nanmean = np.nanmean(point_values)
        
       point_values = point_values - nanmean
        
       point_values[np.isnan(point_values)] = 0
    
    
    lons , lats  =  np.deg2rad(points.T)
    lons = fix_radian_limits(lons, is_lon=True)
    lats = fix_radian_limits(lats, is_lon=False)
    
    
    new_lon, new_lat = [np.deg2rad(x) for x in output_grid]
    
    new_lon = fix_radian_limits(new_lon, is_lon=True)
    new_lat = fix_radian_limits(new_lat, is_lon=False)
    
    
    print('lon min: ', lons.min(), 
          'lon max: ', lons.max(), 
          'lat min: ', lats.min(), 
          'lat max: ', lats.max(),
          'new_lon min: ', new_lon.min(), 
          'new_lon max: ', new_lon.max(),
          'new_lat min: ', new_lat.min(), 
          'new_lat max: ', new_lat.max()
          )
    
    
    knotst, knotsp = new_lat, new_lon
    knotst[0] += .0001
    knotst[-1] -= .0001
    knotsp[0] += .0001
    knotsp[-1] -= .0001
    
    
   
    
    lut = LSQSphereBivariateSpline(np.sort(lats), 
                                   np.sort(lons),
                                   point_values, 
                                   knotst, knotsp)
    
     
    data_interp = lut(new_lat, new_lon)
    
    if skip_nans:
        data_interp = data_interp + nanmean
    
    return data_interp
    
if '__main__' == __name__:
    
    ds = xr.tutorial.open_dataset('rasm').load()
    Tair = ds['Tair']
    
    Tair_T1 = Tair.isel(time=0)
    #Tair_T1.coords['xc'] = (Tair_T1.coords['xc'] + 180) % 360 - 180
    #Tair_T1.coords['yc'] = (Tair_T1.coords['yc'] + 90) % 180 - 90
    
        
    
    points, point_values = xr_to_2D_array(Tair_T1)
    

    
    xres = 20
    yres = 20
    
    xmin, xmax, ymin, ymax = get_coord_limits_from_dataarray(Tair_T1)
    
    
    output_grid, output_shape, Xcoords, Ycoords = create_output_grid(xmin, xmax, xres, ymin, ymax, yres)
    
    
        
    R = interpolate_using_spherical_coords(points,
                                           point_values, 
                                           (Xcoords, Ycoords), 
                                           skip_nans=True,
                                  )
   
  
    
    dataArray_interpolated = rebuild_dataarray(R, 
                                               Xcoords, 
                                               Ycoords,
                                               xdim='lon', 
                                               ydim='lat')
    
    
    
    plot_dataArray(Tair_T1, transform=ccrs.PlateCarree(), 
                   x='xc', y='yc', figsup='Data Original')
    
    
    
    plot_dataArray(dataArray_interpolated, transform=ccrs.PlateCarree(), 
                   x='lon', y='lat', figsup='Interp - Spherical nearest')
    

    
    
    