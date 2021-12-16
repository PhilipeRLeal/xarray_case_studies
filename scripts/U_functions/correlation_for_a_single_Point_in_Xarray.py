"""
Created on Thu May 17 12:12:49 2018
@author: Martin Jung 
@email: M.jung@sussex.ac.uk
Idea:
Set up a xarray-dask environment to be run on landsat stacks
Calculate pixelwise mann-kendal tests and retain sign. slopes
"""
# Necessary defaults
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
import pandas as pd
import os, sys

# Xarray
import xarray as xr
# Dask stuff

from dask.diagnostics import ProgressBar

from numba import jit #  Speedup for python functions

# ----------------------

# Function derived from: http://martin-jung.github.io/post/2018-xarrayregression/

# Parameters
dates = pd.date_range('1984-01-01', periods=34,freq = "A").year


@jit(nogil=True)
def mk_cor(x,y, pthres = 0.05):
    """
    Uses the scipy stats module to calculate a Mann-Kendall correlation test
    :x vector: Input pixel vector to run tests on
    :y vector: The date input vector
    :pthres: Significance of the underlying test
    :direction: output only direction as output (-1 & 1)
    """
    # Check NA values
    co = np.count_nonzero(~np.isnan(x))
    if co < 4:
        return -9999
    # The test
    tau, p_value = stats.kendalltau(x, y)
    
    # Criterium to return results
    return tau
    

def kendall_correlation(x,y,dim='year'):

    return xr.apply_ufunc(
        mk_cor, x , y,
        input_core_dims=[[dim], [dim]],
        vectorize=True,
        dask='parallelized',
        output_dtypes=[float]
        )



def get_Teleconnection(ds_chunked, x, dim='month'):
   
    ds = ds_chunked #.rename({'x': 'Longitude', 'y': 'Latitude', 'band': 'year' })                         
    # -------------------- #
    print("Starting to process %s GB of data" % ( round(ds.nbytes * (2 ** -30),2 ) ) )
    
    
    with ProgressBar():
        r = kendall_correlation(ds, x, dim).compute()
    # Rename the data 
    r = r.rename({'air': 'Correlation'})
   
    return r

from shapely.geometry import Point
import geopandas as gpd

def to_geodataframe(x):
    
    P = gpd.GeoSeries(Point(x.coords['lon'], x.coords['lat']))
    
    
    return P


# Function   
if __name__ == '__main__':
    """
    Main function to load all files and test stuff
    """
    print("Start processing")
    #get_Teleconnection(sys.argv[1], sys.argv[2], sys.argv[3])
    
    # Testing
        
    ds = xr.tutorial.open_dataset('air_temperature').load()
    
    ds_month = ds.resample(time='M').mean()
    
    ds_month['month'] = ds_month['time.month'].values
    
    ds_month = ds_month.set_coords('month')
    
    
    ds_month2 = ds_month.drop_dims('time')
    
    ds_month2['air'] = ( ('month', 'lat', 'lon'), ds_month['air'])
    
    
    ds_chunked = ds_month2.chunk({'lon': 100, 'lat': 100})
    
    
    
    x = ds_month.sel(dict(lat=50, lon=170), method='nearest')
    
    x['air'] = ( ('month' ), x['air'])
    
    
    x = x.reset_index('time', drop=True)

    
    r = get_Teleconnection(ds_chunked,x,  dim='month')
    
    # Plotting
    
    import cartopy.crs as ccrs
    
    
    
    fig, ax = plt.subplots(subplot_kw={'projection':ccrs.PlateCarree()})
    
    r['Correlation'].plot(ax=ax, cmap='viridis')
    
    P = to_geodataframe(x)
    
    P_min = to_geodataframe(r.where(r==r.min(), drop=True))
    
    P.plot(ax=ax, markersize=12, color='red', label='Point of reference', transform=ccrs.PlateCarree())
    P_min.plot(ax=ax, markersize=12, color='blue', label='Point of Teleconnection', transform=ccrs.PlateCarree())
    
    gdl = ax.gridlines(draw_labels=True)
    
    fig.legend()
    
    fig.show()