# -*- coding: utf-8 -*-
"""
Created on Wed Oct  9 15:54:50 2019

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
import xarray as xr

from scipy.stats import mode

def _mode(*args, **kwargs):
    """
    This function returns the mode from a 1D series.
    
    """
    
    
    vals = mode(*args, **kwargs)
    # only return the mode (discard the count)
    return vals[0].squeeze()


def get_mode (obj , dim=None, axis=-1):
    # note: apply always moves core dimensions to the end
    # usually axis is simply -1 but scipy's mode function doesn't seem to like that
    # this means that this version will only work for DataArray's (not Datasets)
    assert isinstance(obj, xr.core.dataarray.DataArray)
    
    axis = obj.ndim - 1
    return xr.apply_ufunc(_mode, obj,
                          input_core_dims=[[dim]],
                          kwargs={'axis': axis})
    
    
ds = xr.tutorial.open_dataset('air_temperature').load()

get_mode(ds['air'], dim='time')