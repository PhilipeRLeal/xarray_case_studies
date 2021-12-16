# -*- coding: utf-8 -*-
"""
Created on Mon Nov 11 11:40:01 2019

@author: Thais
"""

import numpy as np
import xarray as xr
import pandas as pd
import matplotlib.pyplot as plt



def calcula_anomalia(grouped, dask='allowed', return_also_anomaly_normed=True):
    '''
    Description:
        Esta função calcula anomalias sobre netcdfs com frequencias temporais
        definíveis pelo usuário.
        
    
    Parametros:
        grouped (xarray-dataset/dataArray): xarray.core.dataset.Dataset
        
      
        
         return_also_anomaly_normed (bool): define se deve retornar anomalia 
             e anomalia normalizada do dataset. Se "True", returna normalizada
             
    
    '''
   
    
    
    climatology_mean = grouped.mean('time').compute()
    climatology_std = grouped.std('time').compute()
    
    
    
    stand_anomalies = xr.apply_ufunc(
                                    lambda x, m, s: (x - m) / s,
                                    grouped,
                                    climatology_mean, 
                                    climatology_std,
                                    dask=dask,
                                    output_dtypes=[float], 
                                    output_sizes={'anom': 1, }, 
                                    output_core_dims=[[]])
    
    return stand_anomalies
   
    
    
def set_time_grouping_as_index(any_anomaly, 
                               freq='week'):
    '''
    Description:
        Esta função converte a frequência em índice do netcdf
    
    
     Parametros:
        freq (str): esta var. define a frequencia para cálculo da anomalia
            
    Return:
        DataSet (anomalia) com a frequencia de agregação como índice do dataset
        
    
    '''
    any_anomaly = any_anomaly.set_index({freq:freq})
    any_anomaly.coords[freq] = any_anomaly.variables[freq].values
    
    return any_anomaly

def parse_datetime(time):
    '''
    Description:
        converte string em tempo:
            
    return array temporal
    
    '''
    
    
    return pd.to_datetime([str(x) for x in time])

def exemplo():
    '''exemplo de uso'''
    
    ds = xr.tutorial.load_dataset('rasm')
    print(ds)

    
    ds.coords['time'] = parse_datetime(ds.coords['time'].values)
    
    ds = ds.resample(time='W').interpolate('linear')
    

    anom, anom_normed = calcula_anomalia(ds.groupby('time.week'))
    
    
    anom = set_time_grouping_as_index(anom)
    anom_normed = set_time_grouping_as_index(anom_normed)
    
    
    anom_normed.isel({'week':15, 'time':0}).Tair.plot()
    
if '__main__' == __name__:
    #exemplo()
    
    ds = (xr.open_mfdataset(r'Dados_Anuais/*.nc', 
                           concat_dim='time', 
                           combine='nested', 
                           chunks={'latitude':500,
                                   'longitude':400},
                           parallel=False)
         .sel({'latitude':slice(-45, 15),
               'longitude':slice(-60,-10)})
          )
    
    ds.coords['time'] = pd.date_range('1981-01-01', periods=ds['time'].size, freq='D')
    
    
    anomaly = calcula_anomalia(ds.groupby('time.month'), 
                                dask='allowed')
    
    print(anomaly)
    
    
    from dask.diagnostics import ProgressBar
    
    
    print('calculating monthly mean', '\n')
    with ProgressBar():     
        anom_monthly_mean = (anomaly['precip'].groupby('month').mean('time')    )# we can produce 3x4 subplots label month 1 as Jan, month 12 as Dec
    
    
    print('plotting', '\n'*3)
    with ProgressBar():
        anom_monthly_mean.plot.pcolormesh(x = 'longitude', y = 'latitude', 
                                col = 'month', 
                           col_wrap =3, 
                           cmap=plt.cm.get_cmap('viridis'))
        
    plt.show()
    