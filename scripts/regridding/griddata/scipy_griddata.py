# -*- coding: utf-8 -*-
"""
Created on Fri Dec 11 12:43:27 2020

@author: Philipe_Leal
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

import cartopy.crs as ccrs
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import matplotlib.ticker as mticker
pd.set_option('display.max_rows', 5000)
pd.set_option('display.max_columns', 5000)

from scipy.interpolate import griddata

import xarray as xr

from submodules.kdtree import (get_tutorial_dataset)

from submodules.array_to_xarray import rebuild_dataarray


from IDW_over_xarray import (create_output_grid, 
                             get_coord_limits_from_dataarray,
                             apply_kernel_over_distance_array)





def transform_coordinates(coords):
    """ Transform coordinates from geodetic to cartesian
    
    Keyword arguments:
    coords - a set of lan/lon coordinates (e.g. a tuple or 
             an array of tuples)
    """
    # WGS 84 reference coordinate system parameters
    A = 6378.137 # major axis [km]   
    E2 = 6.69437999014e-3 # eccentricity squared    
    
    coords = np.asarray(coords).astype(np.float)
    
    # is coords a tuple? Convert it to an one-element array of tuples
    if coords.ndim == 1:
        coords = np.array([coords])
    
    # convert to radiants
    lat_rad = np.radians(coords[:,0])
    lon_rad = np.radians(coords[:,1]) 
    
    # convert to cartesian coordinates
    r_n = A / (np.sqrt(1 - E2 * (np.sin(lat_rad) ** 2)))
    x = r_n * np.cos(lat_rad) * np.cos(lon_rad)
    y = r_n * np.cos(lat_rad) * np.sin(lon_rad)
    z = r_n * (1 - E2) * np.sin(lat_rad)
    
    return np.column_stack((x, y, z))


def standard_plot_dataarray(da, xdim, ydim, suptitle):

    projection = ccrs.PlateCarree()
    fig, ax = plt.subplots(subplot_kw=dict(projection=projection))

    ax.coastlines()
    gl = ax.gridlines(draw_labels=True)
    
    gl.xformatter = LONGITUDE_FORMATTER
    gl.yformatter = LATITUDE_FORMATTER

    da.plot(ax=ax, x=xdim, y=ydim, transform=projection)
    
    fig.suptitle(suptitle)
    fig.tight_layout()
    
    
    fig.show()



def gridding(lats, lons, data, new_lats, new_lons, method='cubic'):
        
        
    # grid and contour the data.
    gridded = griddata((lats.flatten(), lons.flatten()),
                        data,
                       (new_lats[None, :], new_lons[:, None]),
                       method=method)
    
    return gridded



def main(da, 
         xres, 
         yres, 
         xdim='xc', 
         ydim='yc', 
         newxdimname='lon',
         newydimname = 'lat',
         
         method='linear'):
    
    
    
    xmin, xmax, ymin, ymax = get_coord_limits_from_dataarray(da, xdim, ydim)
    
    pixels_XY, output_shape, Xcoords, Ycoords = create_output_grid(xmin=xmin, 
                                                                   xmax=xmax, 
                                                                   xres=xres, 
                                                                   ymin=ymin, 
                                                                   ymax=ymax, 
                                                                   yres=yres)
    
    pixels_YX = np.flip(pixels_XY, axis=1)
    
    
    lats = da.coords[xdim]
    lons = da.coords[ydim]
    
    points = np.stack([lats.values.ravel(), lons.values.ravel()], axis=1)
    
    
    X, Y, Z = transform_coordinates(points).T
    
    
    
    Xnew, Ynew, Znew = transform_coordinates(pixels_YX).T
    
    
    Ycoords, Xcoords = pixels_YX.T

    
    Gridded = gridding(Y, X, da.values.flatten(), Ynew, Xnew, method=method)
    
    
    
    Pixels_IDW_mean = rebuild_dataarray(Gridded.T, 
                                        Xcoords, Ycoords, 
                                        xdim=newxdimname, ydim=newydimname).sortby([newxdimname,newydimname])
    
    return Pixels_IDW_mean
    

if '__main__' == __name__:
    
    
    
    ######################################################################
    
    #   Getting data
    
    ######################################################################
    
    
    Tair = get_tutorial_dataset()
    
    
    da = Tair.mean('time')
    
    suptitle='Original data'
    standard_plot_dataarray(da, xdim='xc', ydim='yc', suptitle=suptitle)
    
    methods = ['nearest', 'linear', 'cubic']
    
    
    for method in methods:
        Pixels_IDW_mean = main(da.fillna(0), 
                               xres=10, 
                               yres=5, 
                               xdim='xc', 
                               ydim='yc', 
                               newxdimname='lon',
                               newydimname = 'lat',
                               method=method)
        
        
        suptitle = '{0} interpolated'.format(method)
        
        standard_plot_dataarray(Pixels_IDW_mean, xdim='lon', ydim='lat', 
                                suptitle=suptitle)