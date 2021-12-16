# -*- coding: utf-8 -*-
"""
Created on Wed Oct  9 18:28:44 2019

@author: lealp
"""



import xarray as xr
import numpy as np
from scipy import stats


# https://stackoverflow.com/questions/47314800/dask-performance-apply-along-axis/47315238#47315238

def _calc_slope(x, y):
    '''wrapper that returns the slop from a linear regression fit of x and y'''
    slope = stats.linregress(x, y)[0]  # extract slope only
    return slope


def linear_trend(obj, dim='time'):
    
    time_nums = xr.DataArray(obj[dim].values.astype(np.float),
                             dims=dim,
                             coords={dim: obj[dim]},
                             name='time_nums')
    
    trend = xr.apply_ufunc(_calc_slope, time_nums, obj,
                           vectorize=True,
                           input_core_dims=[[dim], [dim]],
                           output_core_dims=[[]],
                           output_dtypes=[np.float],
                           dask='parallelized')

    return trend



ds = xr.tutorial.open_dataset('air_temperature').load()


Slopes = linear_trend(ds['air'], dim='time')