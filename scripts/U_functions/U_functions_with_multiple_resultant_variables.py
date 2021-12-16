# -*- coding: utf-8 -*-
"""
Created on Tue Nov  5 18:00:18 2019

@author: lealp
"""



import numpy as np
import xarray as xr


 #https://gist.github.com/scottyhq/8daa7290298c9edf2ef1eb05dc3b6c60

x_size = 10

y_size = 10
time_size = 30
lon = np.arange(50, 50+x_size)

lat = np.arange(10, 10+y_size)

time = np.arange(10, 10+time_size)

array = np.random.randn(y_size, x_size, time_size)

ds = xr.DataArray(data=array, coords = {'lon':lon, 'lat':lat, 'time':time}, dims=('lon', 'lat', 'time'))

ds.isel({'time':0}).plot(x='lon', y='lat')

def f (x):
    
    
    return (x, x**2, x**3, x**4)


def f_xarray(ds, dim=['time'], 
              dask='allowed', 
              new_dim_name=['predicted']):   
    
    
    filtered = xr.apply_ufunc(f,
                                  ds,
                                      dask=dask,
                                      vectorize=True,
                                      input_core_dims=[dim],
                                      #exclude_dims = dim, # This must not be setted.
                                      output_core_dims= [['x', 'x2', 'x3', 'x4']], #[new_dim_name],
                                      #kwargs=kwargs,
                                      #output_dtypes=[float],
                                      #dataset_join='outer',
                                      #dataset_fill_value=np.nan,
                                      ).compute()
        
    return filtered


ds2 = f_xarray(ds)