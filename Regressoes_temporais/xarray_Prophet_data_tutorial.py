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
from fbprophet import Prophet

# https://stackoverflow.com/questions/56626011/using-prophet-on-netcdf-file-using-xarray

 #https://gist.github.com/scottyhq/8daa7290298c9edf2ef1eb05dc3b6c60
ds = xr.tutorial.open_dataset('rasm').load()

def parse_datetime(time):
    return pd.to_datetime([str(x) for x in time])

ds.coords['time'] = parse_datetime(ds.coords['time'].values)


ds = ds.isel({'x':slice(175,180), 'y':slice(160,170)})
ds.isel({'time':0}).Tair.plot()

ds = ds.chunk({'x':40, 'y':40})

def fillna_in_array(x):
    y = np.where(np.abs(x)==np.inf, 0, x)  
    
    y = np.where(np.isnan(y), 0, y)
    
    if np.all(y) == 0:
        
        y = np.arange(len(y))
    return y
    


def xarray_Prophet(y, time, periods=30, freq='D'):
    '''
    This is a vectorized u_function of the Prophet prediction module.
    
    It returns an array of values containing original and predicted values
    according to the provided temporal sequence.
    
    Parameters:
        
        y (array): an array containing the y past values that will be 
                   used for the prediction.
        
        time (array): an array containing the time intervals of each respective 
                      entrance of the sampled y
        
        periods (positive int): the number of times it will be used for prediction
        
        freq (str): the frequency that will be used in the prediction:
            (i.e.: 'D', 'M', 'Y', 'm', 'H'...)
            
    Returns:
        
        array of predicted values of y (yhat)
                    
    '''
    
    
    # Here, we ensure that all data is filled. Since Xarray has some Issues with
    # sparse matrices, It is a good solution for all NaN, inf, or 0 values for 
    # sampled y data
    
    with ProgressBar():
        y = fillna_in_array(y)
        
        
        # here the processing really starts:
        
            
        forecast = pd.DataFrame()
        
        forecast['ds'] = pd.to_datetime(time)
        forecast['y'] = y
        
        
        m1 = Prophet(weekly_seasonality=True, 
                     daily_seasonality=False).fit(forecast)  
        
        forecast = m1.make_future_dataframe(periods=periods, freq=freq)
        
        # In here, the u_function should return a simple 1-D array, 
        # or a pandas  series.
        # Therefore, we select the attribute 'yat' from the 
        # FProphet prediction dataframe to return solely a 1D data.
    
    forecasted = m1.predict(forecast)
    
    return forecasted['yhat'].values

def predict_y(ds, 
              dim=['time'], 
              dask='allowed', 
              new_dim_name=['predicted'], 
              periods=30, freq='D'):
    
    '''
    Function Description:
        
        This function is a vectorized parallelized wrapper of 
        the "xarray_Prophet".
        
        It returns a new Xarray object (dataarray or Dataset) with the new 
        dimension attached.
        
    Parameters:
        ds (xarray - DataSet/DataArray)
        
        dim (list of strings): a list of the dimension that will be used in the 
        reduction (temporal prediction)
        
        dask (str):  allowed 
        
        new_dim_name (list of strings): it contains the name that will be used
                                        in the reduction operation.
        
        periods (positive int): the number of steps to be predicted based
                                      on the parameter "freq".
                                      
        
        freq (str): the frequency that will be used in the prediction:
            (i.e.: 'D', 'M', 'Y', 'm', 'H'...)                                      
                                      
   
       
    Returns:
        
        Xarray object (Dataset or DataArray): the type is solely dependent on 
                                              the ds object's type.
        
    '''

    ds = ds.sortby('time', False)
    
    time = np.unique(ds['time'].values)
    
    kwargs = {'time':time,
              'periods': periods,
              'freq':freq}
    
#        columns_of_prediction = ['ds', 'trend', 'yhat_lower', 'yhat_upper', 
#                                 'trend_lower', 'trend_upper', 'additive_terms',
#                                 'additive_terms_lower', 
#                                 'additive_terms_upper', 'weekly', 
#                                 'weekly_lower', 
#                                 'weekly_upper', 'yearly', 'yearly_lower', 
#                                 'yearly_upper', 'multiplicative_terms',
#                                 'multiplicative_terms_lower', 
#                                 'multiplicative_terms_upper',
#                                 'yhat']
    
    filtered = xr.apply_ufunc(xarray_Prophet,
                                  ds,
                                  dask=dask,
                                  vectorize=True,
                                  input_core_dims=[dim],
                                  #exclude_dims = dim, # This must not be setted.
                                  output_core_dims= [new_dim_name], 
                                  kwargs=kwargs,
                                  #output_dtypes=[float],
                                  dataset_join='outer',
                                  dataset_fill_value=np.nan,
                                  ).compute()
        
    return filtered


#ds.Tair.stack(point=('x', 'y')).groupby('point').apply(xarray_Prophet, time=ds['time']).unstack('point')

da_binned = predict_y( ds = ds, 
                       dim = ['time'], 
                       dask='allowed',
                       new_dim_name=['predicted'],
                       periods=30).rename({'predicted':'time'})


