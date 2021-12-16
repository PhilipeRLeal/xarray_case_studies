# -*- coding: utf-8 -*-
"""
Created on Thu Dec 10 13:57:10 2020

@author: Philipe_Leal
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os, sys
import geopandas as gpd
import cartopy.crs as ccrs

pd.set_option('display.max_rows', 5000)
pd.set_option('display.max_columns', 5000)

import xarray as xr

from IDW_over_xarray import (create_output_grid, 
                             get_coord_limits_from_dataarray,
                             apply_kernel_over_distance_array)

from submodules.kdtree import (KDTree, get_tutorial_dataset)

from submodules.array_to_xarray import rebuild_dataarray

end =  '\n'*2 + '-'*40 +  '\n'*2 



def standard_plot_dataarray(da, xdim, ydim, suptitle):

    projection = ccrs.PlateCarree()
    fig, ax = plt.subplots(subplot_kw=dict(projection=projection))

    ax.coastlines()
    ax.gridlines(draw_labels=True)

    da.plot(ax=ax, x=xdim, y=ydim, transform=projection)
    
    fig.suptitle(suptitle)
    fig.tight_layout()
    
    
    fig.show()


if '__main__' == __name__:
    
    
    
    ######################################################################
    
    #   Getting data
    
    ######################################################################
    
    
    Tair = get_tutorial_dataset()
    
    
    da = Tair.mean('time')
    
    suptitle='Original data'
    standard_plot_dataarray(da, xdim='xc', ydim='yc', suptitle=suptitle)
    
    
    ######################################################################
    
    #   Getting Grid
    
    ######################################################################
    
    
    
    xmin, xmax, ymin, ymax = get_coord_limits_from_dataarray(da, 'xc', 'yc')
    
    xres = 5
    yres = 5
    K = 1
    
    pixels_XY, output_shape, Xcoords, Ycoords = create_output_grid(xmin=xmin, xmax=xmax, xres=xres, ymin=ymin, ymax=ymax, yres=yres)
    
    pixels_YX = np.flip(pixels_XY, axis=1)
    
    ##########################################################################
    
    
    
    
    ground_pixel_tree =  KDTree(da, xcor='xc', ycor='yc')
    
    
    ######################################################################
    
    #   Nearest K points for Paris
    
    ######################################################################
    
    
    
    
    paris = (48.8566, 2.3522)
   
    K = 3    
    pixels_index , distances = ground_pixel_tree.query(paris, k=K)
    
    dd= (1/distances)
    dd = dd/dd.sum()
    
    Nearest_da = da[pixels_index]
    
    Nearest_coords = Nearest_da.coords
    
    
    IDW = ground_pixel_tree.idw(paris, k=K)
    
    
    ################
    #   
    #   KNN mean with K = 1
    #
    #############
    
        
    
    K=1
    
    Pixels_IDW, distances = ground_pixel_tree.knn(pixels_YX, k=K)
    
    if hasattr(Pixels_IDW, 'knn'):
        Pixels_IDW_mean = Pixels_IDW.mean('knn')
        
    else:
        Pixels_IDW_mean = Pixels_IDW
    
    Pixels_IDW_mean = rebuild_dataarray(Pixels_IDW_mean.values.reshape(output_shape), 
                                        Xcoords, Ycoords, xdim='lon', ydim='lat')
    
    
    suptitle = 'KNN mean with K: {0}'.format(K)
    standard_plot_dataarray(Pixels_IDW_mean, xdim='lon', ydim='lat', suptitle=suptitle)
    
    
    
    
    ################
    #   
    #   KNN mean with K = N
    #
    #############
    
        
    
    K=10
    
    Pixels_IDW, distances = ground_pixel_tree.knn(pixels_YX, k=K)
    
    if hasattr(Pixels_IDW, 'knn'):
        Pixels_IDW_mean = Pixels_IDW.mean('knn')
        
    else:
        Pixels_IDW_mean = Pixels_IDW
    
    Pixels_IDW_mean = rebuild_dataarray(Pixels_IDW_mean.values.reshape(output_shape), 
                                        Xcoords, Ycoords, 
                                        xdim='lon', ydim='lat')
    
    
    suptitle = 'KNN mean with K: {0}'.format(K)
    standard_plot_dataarray(Pixels_IDW_mean, 
                            xdim='lon', ydim='lat', 
                            suptitle=suptitle)

    ############################################
    
    
    
    
    ################
    #   
    #   IDW
    #
    #############3
    
    K = 5
    Pixels_IDW = ground_pixel_tree.idw(pixels_YX, k=K)
    
    Pixels_IDW_da = rebuild_dataarray(Pixels_IDW.reshape(output_shape), Xcoords, Ycoords, xdim='lon', ydim='lat')
    
    suptitle = 'IDW with K: {0}'.format(K)
    
    standard_plot_dataarray(Pixels_IDW_da, xdim='lon', ydim='lat', suptitle=suptitle)
    
