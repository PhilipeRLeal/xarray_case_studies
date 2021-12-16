# -*- coding: utf-8 -*-
"""
Created on Tue Nov 12 14:37:32 2019

@author: lealp
"""

import pandas as pd
pd.set_option('display.width', 50000)
pd.set_option('display.max_rows', 50000)
pd.set_option('display.max_columns', 5000)


import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy
import matplotlib
import seaborn as sn
import glob
import os
import xarray as xr




ds = (xr.tutorial.open_dataset('air_temperature')
      .load()
      .chunk({'lon': 1000, 'lat': 1000})
      )


ds.isel({'time':slice(0,3)})['air'].plot.pcolormesh(col='time', col_wrap='time')

def ulinregress(x, y, degree=2): # the universal function
    
    coefs = np.polyfit(x, y, deg=degree)
    
    return coefs


def transform_time_in_days_since_epoch(time):
    
    return (time - np.datetime64("1950-01-01")) / np.timedelta64(1, 'D')

def get_time_reg_from_each_pixel_in_xarray(ds, dask='allowed', degree=2):
    
    
    time = transform_time_in_days_since_epoch(ds['time'])

    if dask == 'parallelized':
        vectorize=False
    else:
        vectorize=True
        
    Result =  xr.apply_ufunc(ulinregress, 
                        time, 
                        ds['air'], 
                        vectorize=vectorize,
                        dask=dask, 
                        kwargs={'degree':degree},
                        input_core_dims=[['time'], ['time']], 
                        output_dtypes=['d'], 
                        output_sizes={'Reg_degree': degree, }, 
                        output_core_dims=[['Reg_degree']]
                        )
    
    
    Result['Reg_degree'] = ['x_{0}'.format(i) for i in range(Result['Reg_degree'].size)]

    return Result.to_dataset(name='coefs')

ab = get_time_reg_from_each_pixel_in_xarray(ds, degree=5)


fig, axes = plt.subplots(2,3, figsize=(12,6.5), sharex=True, sharey=True)

axes = axes.ravel()
Mappables = []
for idx, degree in enumerate(ab.coords['Reg_degree']):
    print(idx)
    temp = ab.sel({'Reg_degree':degree})

    Mappable = temp['coefs'].plot.pcolormesh(x='lon', y='lat', 
                         add_colorbar=True,
                         ax=axes[idx])
    
    Mappables.append(Mappable)
fig.subplots_adjust(top=0.944,
                    bottom=0.092,
                    left=0.052,
                    right=0.952,
                    hspace=0.226,
                    wspace=0.4)
fig.show()

