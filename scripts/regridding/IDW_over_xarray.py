# -*- coding: utf-8 -*-
"""
Created on Wed Dec  9 19:51:51 2020

@author: Philipe_Leal
"""
import pandas as pd
import numpy as np

import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import os, sys
import matplotlib.ticker as mticker
pd.set_option('display.max_rows', 5000)
pd.set_option('display.max_columns', 5000)
import xarray as xr



def get_k_nearest_values_from_vector(arr, k):
    
    idx = np.argsort(arr)
    
    if k<0:
        return arr, idx
    
    if k>0:
    
        return arr[idx[:k]], idx


def apply_kernel_over_distance_array(dd, p):
    
    
    dd = dd**(-p)         # dd = weight = 1.0 / (dd**power)
    dd = dd/np.sum(dd)    # normalized weights
    
    return dd



def get_interpolatedValue(xd,yd,Vd, xpp,ypp, p,smoothing, k=4):
    dx = xpp - xd;   dy = ypp - yd
    dd = np.sqrt(dx**p + dy**p + smoothing**p)         # distance
    dd = np.where(np.abs(dd) <10**(-3), 10**(-3), dd)  # limit too small distances
    
    
    dd_Nearest, idx = get_k_nearest_values_from_vector(dd, k) # getting k nearest
    
    dd_Nearest = apply_kernel_over_distance_array(dd_Nearest, p)
    
    Vd[np.isnan(Vd)] = 0 # Setting nans to zero
    
    if k>0:
    
        K_nearest_Values = Vd[idx[:k]]
        
    else:
        K_nearest_Values = Vd
    
    print('dd_Nearest shape', dd_Nearest.shape)
    print('K_nearest_Values shape', K_nearest_Values.shape)
    
    Vi = np.dot(dd_Nearest,K_nearest_Values)     # interpolated value = scalar product <weight, value>
    return Vi

def interpolateDistInvers(xd,yd,Vd, xp,yp, power,smoothing, k):
    nx = len(xp)
    
    VI = np.zeros_like(xp)            # initialize the output with zero
    for i in range(nx):              # run through the output grid
        VI[i] = get_interpolatedValue(xd,yd,Vd, xp[i],yp[i], power, smoothing, k)
    return VI.T


def run_InvDist_interpolation(output_grid,
                              input_grid,
                              input_grid_values,
                              power=2.0,   
                              smoothing=0.1,
                              k=4):
    
    xp, yp = output_grid.T    
    xs, ys = input_grid.T                 
    


    #---- run through the grid and get the interpolated value at each point
    Vp = interpolateDistInvers(xs,ys,input_grid_values, xp,yp, power,smoothing, k)
    return Vp


def xr_to_2D_array(da, xcor='xc', ycor='yc'):
    
    data = da.data.ravel()
    xcor = da.coords[xcor].data.ravel()
    ycor = da.coords[ycor].data.ravel()
    
    print(xcor.shape, ycor.shape, data.shape)
    
    input_grid = np.stack([xcor, ycor], axis=1)
    
    return input_grid, data


def create_output_grid(xmin, xmax, xres, ymin, ymax, yres):
    Xcoords = np.arange(xmin,xmax, xres)
    
    Ycoords = np.arange(ymin, ymax, yres)
    
    xgrid, ygrid = [x.ravel() for x in np.meshgrid(Xcoords, Ycoords)]
     
    output_grid = np.stack([xgrid, ygrid], axis=1)
    
    output_shape = (Xcoords.size, Ycoords.size)
    
    return output_grid, output_shape, Xcoords, Ycoords


def get_coord_limits_from_dataarray(da, xcor='xc', ycor='yc'):
    
    
    xmin = float(da.coords[xcor].min())
    xmax = float(da.coords[xcor].max())
    
    ymin = float(da.coords[ycor].min())
    ymax = float(da.coords[ycor].max())
    
    return xmin, xmax, ymin, ymax
    
    

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
if '__main__' == __name__:
    
    ds = xr.tutorial.open_dataset('rasm').load()
    Tair = ds['Tair']
    
    Tair_T1 = Tair.isel(time=0)
    
    input_grid, input_grid_values = xr_to_2D_array(Tair_T1)
    
    xres = 5
    yres = 5
    
    K = 100
    
    xmin, xmax, ymin, ymax = get_coord_limits_from_dataarray(Tair_T1)
    
    
    output_grid, output_shape, Xcoords, Ycoords = create_output_grid(xmin, xmax, xres, ymin, ymax, yres)
    
    Interp_IDW = run_InvDist_interpolation(output_grid,
                              input_grid,
                              input_grid_values,
                              power=2.0,   
                              smoothing=0.1, k=K)
    
    
    Interp_IDW = Interp_IDW.reshape(output_shape)

    
    dataArray_interpolated = rebuild_dataarray(Interp_IDW, 
                                               Xcoords, 
                                               Ycoords,
                                               xdim='lon', 
                                               ydim='lat')
    
    
    
    plot_dataArray(Tair_T1, transform=ccrs.PlateCarree(), 
                   x='xc', y='yc', figsup='Data Original')
    
    
    
    plot_dataArray(dataArray_interpolated, transform=ccrs.PlateCarree(), 
                   x='lon', y='lat', figsup='Interp - IDW')
    