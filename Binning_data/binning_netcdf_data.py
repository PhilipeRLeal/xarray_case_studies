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


from extreme_events.extreme_classifier import Extreme_Classifier as EEC


def parse_extremes(x, distribution_type='Positive', b=False):
    
    y = np.where(np.abs(x)==np.inf, 0, x)  
    
    y = np.where(np.isnan(y), 0, y)
    
    if np.all(y) == 0:
        
        return x
    
    else:
        
        EE = EEC(distribution_type=distribution_type, verbose=False)
        
        EE.fit(y)
        
        Classified = EE.predict(y, b)
        
        
        return np.where(Classified.codes == Classified.categories[-1], 1, 0)




def xarray_parse_extremes(ds, dim=['time'], dask='allowed', new_dim_name=['classes'], kwargs={'b': False, 'distribution_type':'Positive'}):
    
    filtered = xr.apply_ufunc(parse_extremes,
                                  ds,
                                  dask=dask,
                                  vectorize=True,
                                  input_core_dims=[dim],
                                  #exclude_dims = [dim],
                                  output_core_dims=[new_dim_name],
                                  kwargs=kwargs,
                                  output_dtypes=[float],
                                 
                                  join='outer',
                                  dataset_fill_value=np.nan,
                                  ).compute()
    
    
    
    return filtered



if '__main__' == __name__:
    
    
    from datetime import date, timedelta    
    
    import matplotlib.pyplot as plt
    
    
    def get_offset(x, tim_start=(1,1,1)):
        
            
        days = x                 # This may work for floats in general, but using integers
                                #   is more precise (e.g. days = int(9465.0))
        
        start = date(*tim_start)      # This is the "days since" part
        
        delta = timedelta(days)     # Create a time delta object from the number of days
        
        offset = start + delta      # Add the specified number of days to 1990
        
        
        return offset
        
        
    
    ds = xr.tutorial.open_dataset('rasm', decode_times=False).load()
    
    def parse_datetime(time):
        return pd.to_datetime([str(get_offset(x)) for x in time])
    
    ds.coords['time'] = parse_datetime(ds.coords['time'].values)
    
    ds = ds.chunk({'time': -1}).persist()
    
    
    ds = xr.decode_cf(ds)
    
        
    ds_monthly_anual = xarray_parse_extremes(ds['Tair'] , ['time'], 
                                             dask='allowed')
    
    facet = ds_monthly_anual.plot.contour(x='x', y='y', col='classes', col_wrap=5)
    
    plt.show()