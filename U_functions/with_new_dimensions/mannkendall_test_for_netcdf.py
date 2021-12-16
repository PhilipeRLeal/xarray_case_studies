# -*- coding: utf-8 -*-
"""
Created on Thu Jan 30 10:40:46 2020

@author: lealp
"""

import pandas as pd
pd.set_option('display.width', 50000)
pd.set_option('display.max_rows', 50000)
pd.set_option('display.max_columns', 5000)


import numpy as np

from dask.diagnostics import ProgressBar

import pymannkendall as mk
import xarray as xr

def apply_mk(x, alpha=0.05):
    
    '''
    The mannkendall test is described in: 
        1) http://www.scielo.br/pdf/eagri/v33n2/05.pdf
        2) https://vsp.pnnl.gov/help/Vsample/Design_Trend_Mann_Kendall.htm
    
    
    The algorithm is described in: https://pypi.org/project/pymannkendall/ 
    
    Returns: 2d-tuple containing the condition value (True/False) of the pvalue<alpha
    and the temporal trend coefficient
    
    '''
    
    result = mk.original_test(x, alpha=alpha)
    
    if result[1] == True:
        return np.array([result[1], result[-1]])
    
    else:
        return np.array([result[1], np.nan])
    

def mk_over_netcdf(da, dim='time', alpha=0.05):
    '''
    Description>
    
    This is a u_function that applies the mannkendall test over a netcdf
    xarray DataArray.
    
    Params:
        
        da (xarray dataArray)
        
        dim (string): the dimension in da to be analyzed
        
        alpha (float): the alpha probability coefficient to check
        
    Return Dataarray with the temporal trend coefficient, 
    associated with an additional dimension named "condition" that 
    is relative to the pvalue<alpha check.
    
    This new dimension in the dataarray, the values are: [True, False]
    
    References:
        https://stackoverflow.com/questions/53769509/xarray-apply-ufunc-to-get-the-min-and-max-for-every-variable
    '''
    
    
    
    kwargs = {'alpha':alpha}
    
    with ProgressBar():
        mk_da_results = xr.apply_ufunc(apply_mk,
                                       da,
                                       input_core_dims=[[dim]],
                                       kwargs=kwargs,
                                       vectorize=True,
                                       output_core_dims=[['condition']],
                                       dask='allowed').compute()
        
    return mk_da_results


if '__main__' == __name__:
    
        
    # Data generation for analysis
    data = np.random.rand(360,1)
    
    result = mk.original_test(data)
    
    lat = 100
    
    lon = 100
    
    time=100
    
    array = np.random.gamma(2, 3, size=(lat*lon*time))
    array = array.reshape(time, lon, lat)
    
    
    
    
    data = xr.DataArray(data = array, coords={'lon':np.arange(lon),
                                       'lat':np.arange(lat),
                                       'time':np.arange(time)},
                        dims=('lon','lat','time'),
                        name='gamma_random_data')
        
    
    mk_da_results = mk_over_netcdf(data)
    
    mk_da_results.sel({'condition':True}).plot()