# -*- coding: utf-8 -*-
"""
Created on Mon Nov  4 11:25:03 2019

@author: lealp
"""

import pandas as pd
pd.set_option('display.width', 50000)
pd.set_option('display.max_rows', 50000)
pd.set_option('display.max_columns', 5000)


import numpy as np
import xarray as xr

from dask.diagnostics import ProgressBar

import matplotlib.pyplot as plt

def binning_function(x, time,  distribution_type='Positive', b=False):
    
    y = np.where(np.abs(x)==np.inf, 0, x)  
    
    y = np.where(np.isnan(y), 0, y)
    
    if np.all(y) == 0:
        
        return np.where(y==0, np.nan, np.nan)
    
    else:
        
        Classified = pd.qcut(y, np.linspace(0.0, 1, 11))
        
        codes = Classified.codes + 1
        
        return codes


def xarray_parse_extremes(ds, dim=['time'], 
                          dask='allowed', 
                          new_var_name='classes', 
                          kwargs={'b': False, 
                                  'distribution_type':'Positive'}):
    
    
    kwargs['time'] = np.unique(ds['time'].values)

    filtered = xr.apply_ufunc(binning_function,
                                  ds,
                                  dask=dask,
                                  vectorize=True,
                                  input_core_dims=[dim],
                                  #exclude_dims = [dim],
                                  output_core_dims=[dim],
                                  kwargs=kwargs,
                                  output_dtypes=[int],
                                  
                                  )
    
    filtered.name = new_var_name

    
    return filtered


if '__main__' == __name__:
    
        
    ds = xr.tutorial.open_dataset('rasm').load()
    
    def parse_datetime(time):
        return pd.to_datetime([str(x) for x in time])
    
    ds.coords['time'] = parse_datetime(ds.coords['time'].values)
    
    
    ds.isel({'time':0}).Tair.plot()
    
    
    #ds = ds.sel({'x':slice(154, 159), 'y':slice(32, 40) })
    
    
    with ProgressBar():
        da_binned = xarray_parse_extremes(ds['Tair'].fillna(0), 
                                          ['time'], 
                                         dask='parallelized')
    
    binned = da_binned.copy(deep=True)
    
    binned_ds = binned.to_dataset()
    
    
    
    
    
    ########### Plotting
    
    plt.figure()
    
    
    ds['Tair'].isel({'time':3}).plot(cmap='viridis', ax=plt.subplot(1,2,1))
    binned.isel({'time':3}).plot(cmap='viridis', ax=plt.subplot(1,2,2))
    
    
    import matplotlib.pyplot as plt
    import matplotlib as mpl
    
    cmap = mpl.cm.viridis
    
    
    
    
    
    fig3, axs = plt.subplots(3,3, sharex=True, sharey=True)
    axs = axs.ravel()
    
    for i, ax in enumerate(axs):
        print(i)
        temp = binned.where(binned==i+1, 1, 0).sum('time')
       
        temp.plot(ax=ax, add_colorbar=False)
        
        bounds = np.arange(0,temp.max())
        norm = mpl.colors.BoundaryNorm(bounds, cmap.N)
        cb2 = mpl.colorbar.ColorbarBase(ax, cmap=cmap,
                                    norm=norm,
                                    boundaries=bounds,
                                    extend='both',
                                    ticks=bounds,
                                    spacing='proportional',
                                    orientation='vertical')
    
    fig3.show()
    
    