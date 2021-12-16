
import numpy as np

from dask.diagnostics import ProgressBar

import xarray as xr

## If you want expand along a new dimension, you need to: 

    ## (1) return a numpy array instead of a tuple;
    ## (2) specify the new dimension in `output_core_dims:

def _min_max_new_dim(x):
    return np.array([np.min(x), np.max(x)])




def min_max_new_dim(da, 
                    dims=['time', 'lat', 'lon'], 
                    output_core_dims=['min_max'],
                    dim_coords=['min', 'max']):
    
    
    coords = {output_core_dims[0]: dim_coords}
    
    with ProgressBar():
        
        results = xr.apply_ufunc(_min_max_new_dim, 
                              da, 
                              input_core_dims=[dims],
                              vectorize=True,
                              output_core_dims=[output_core_dims])
        
    return results.assign_coords(coords)


## Alternatively, you can return a tuple of arrays from the applied function,
    # which can later be concatenated into a new dimension of the xarray dataArray
    # This is more costly, because it requires a concatenation step after the
    # apply_ufunc;

## in which case you'll get out:
    # A 'Tuple' of xarray objects from apply_ufunc:

def _min_max_new_var(x):
    return (np.min(x), np.max(x))




def min_max_new_coord(da, 
                    dims=['time', 'lat', 'lon'], 
                    new_dim_name='limits', 
                    dim_coords=['min', 'max']):
    
    with ProgressBar():
        
        results2 = xr.apply_ufunc(_min_max_new_var, 
                                  da, 
                                  input_core_dims=[dims],
                                  output_core_dims=[[], []],
                                  vectorize=True)
        
        concatenated = xr.concat(results2, 
                                 dim=new_dim_name)
        
        coords = {new_dim_name: dim_coords}
        
        return concatenated.assign_coords(coords)
        
        
def generate_data_exame():
    
    
    lat = 100
    
    lon = 100
    
    time=30
    
    array = np.random.gamma(2, 3, size=(time*lon*lat))
    array = array.reshape(time, lon, lat)
    
    xdata = xr.DataArray(data = array, 
                         coords={'time':np.arange(time),
                                 'lon':np.arange(lon),
                                 'lat':np.arange(lat)},
                        dims=('time', 'lon','lat'),
                        name='gamma_random_data'
                        )
                        
    
    return xdata

                    


if '__main__' == __name__:
    
    # Data generation for analysis
    
    xdata = generate_data_exame()
                        
    results = min_max_new_dim(xdata, 
                    dims=['time', 'lat', 'lon'], 
                    output_core_dims=['limits'],
                    dim_coords=['min', 'max'])


    results2 = min_max_new_coord(xdata, 
                    dims=['time', 'lat', 'lon'], 
                    new_dim_name='limits', 
                    dim_coords=['min', 'max'])  



                    