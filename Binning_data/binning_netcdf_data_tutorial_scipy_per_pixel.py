# -*- coding: utf-8 -*-
"""
Created on Mon Nov 18 16:32:22 2019

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
import pandas as pd

from binning_netcdf_data_using_general_value_for_all_dimension import binned_statistic_1d

if '__main__' == __name__:
    
        
    ds = xr.tutorial.open_dataset('rasm').load()
    
    def parse_datetime(time):
        return pd.to_datetime([str(x) for x in time])
    
    ds.coords['time'] = parse_datetime(ds.coords['time'].values)
    da = ds['Tair'].fillna(0)
    
    ds_binned_per_pixel = (da.stack(point=['x', 'y'])
                           .groupby('point')
                           .apply(binned_statistic_1d, dim='time')
                           )