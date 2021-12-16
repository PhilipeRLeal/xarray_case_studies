# -*- coding: utf-8 -*-
"""
Created on Thu Nov 14 12:24:09 2019

@author: lealp
"""



import xarray as xr

from dask.diagnostics import ProgressBar
import dask
import glob
import os
import cftime

def read_netcdfs(files, concat_dim, transform_func=None):
    with ProgressBar():
        paths = sorted(glob.glob(files))
        open_kwargs = dict(decode_cf=True, decode_times=False)
        
        
        open_tasks = [dask.delayed(xr.open_dataset)(f, **open_kwargs) for f in paths]
        
        # fixing strange time convention format:
        open_tasks = [dask.delayed(modify_time_conventions)(task) for task in open_tasks]
       
        
        if transform_func is not None:
            
            open_tasks = [dask.delayed(transform_func)(task) for task in open_tasks]
        
        
        else:
            pass
        
        
        # once dask computes, it returns a tuple. So, for the xarray to 
        # concatenate the files, one must catch the datasets in the 1° 
        # position of that tuple of 1D.
        
        datasets = dask.compute(open_tasks)[0]
        
        combined = xr.concat(datasets, dim=concat_dim)  
        return combined


def process_one_path(path, transform_func=None):
    # use a context manager, to ensure the file gets closed after use
    
    open_kwargs = dict(decode_cf=True, decode_times=False)
    print('processing file: ', os.path.basename(path))
    
    
    with xr.open_dataset(path, **open_kwargs) as ds:
        
        # fixing strange time convention format:
        ds = modify_time_conventions(ds)
        # transform_func should do some sort of selection or
        # aggregation
        if transform_func is not None:
            ds = transform_func(ds)
        # load all data from the transformed dataset, to ensure we can
        # use it after closing each original file
        ds.load()
        return ds



def read_in_memory_all_netcdfs(files, concat_dim, transform_func=None):
    
    with ProgressBar():
    
        paths = sorted(glob.glob(files))
        datasets = [process_one_path(p, transform_func) for p in paths]
        combined = xr.concat(datasets, concat_dim)
        return combined


def modify_time_conventions(ds):
    try:
        units = ds['time'].attrs['units']
        
        print('\n', units)
        
        date_origin = cftime.num2date(ds['time'], units=units)
        
        
        ds['time'] = ('time', date_origin)
    except:
        pass
    
    return ds


if '__main__' == __name__:
        
    
    #combined = read_netcdfs(r'G:\SODA\*.nc', transform_func=None, concat_dim='time')
    
    # here we suppose we only care about the combined mean of each file;
    # you might also use indexing operations like .sel to subset datasets
    
    def transform (ds):
        with ProgressBar():
            
            return ds.groupby('time').mean(xr.ALL_DIMS)
    
    
    combined2 = read_in_memory_all_netcdfs(r'G:\SODA/*.nc', 
                                           concat_dim='time',
                            transform_func=transform)
                            
                            
    print(combined2)                            
    


