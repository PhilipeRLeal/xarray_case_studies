# -*- coding: utf-8 -*-
"""
Created on Tue Nov 12 13:40:46 2019

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
import glob
import os
import xarray as xr

basename = r'F:\Philipe\Doutorado\Dados_L8\Guarapiranga\2013-07-05\*.tif'


paths = glob.glob(basename)


DataArrays = []

for path in paths:
    

    file = os.path.basename(path)
    
    band = file.split('_')[-1].split('.')[0]
    
    
    print('band: ', band)
    
    
    try:
        
        temp = xr.open_rasterio(path,
                                 chunks={'x': 256, 'y': 256})
        
        shape = temp['band'].shape
        
        temp['band'] = np.array(band).reshape(shape)
        
        temp.name = 'Reflectance'
        
        temp = (temp * temp.attrs['scales']) + temp.attrs['offsets']
        
        DataArrays.append(temp)
        
    except:
        print('Error in : ', file, '\n')

ds = xr.concat(DataArrays, dim='band',
               join='outer')





from dask.diagnostics import ProgressBar
    
    
print('\n'*2,'plotting', '\n'*3)

def _insert_custom_cbars(ax, vmin, vmax, cmap, label='some unit'):
    import matplotlib as mpl
    
    norm = mpl.colors.Normalize(vmin=vmin, vmax=vmax)
    
    cb1 = mpl.colorbar.ColorbarBase(ax, cmap=cmap,
                                    norm=norm,
                                    extendfrac='auto',
                                    spacing='uniform',
                                    orientation='vertical')
    cb1.set_label(label)
    
    return cb1

def add_cbar_to_DataArray(dataarray, 
                          ax, 
                          cmap=plt.cm.get_cmap('viridis'),
                          label='some unit'):
    
    vmin = dataarray.min(xr.ALL_DIMS)
    vmax = dataarray.max(xr.ALL_DIMS)
    
    return _insert_custom_cbars(ax, vmin, vmax, label)


def to_geodataframe(dataarray):
    from shapely.geometry import Point
    import geopandas as gpd
    
    df = dataarray.to_dataframe()
    
    idx_names = df.index.names
    
    df = df.reset_index()
    
    
    Points = []
    for x in dataarray.coords['x']:
        for y in dataarray.coords['y']:
            
            Points.append(Point(x,y))
            
    df['geometry'] = Points
    
    df = df.set_index(idx_names)
    
    return gpd.GeoDataFrame(df, geometry='geometry', crs={'init':'epsg:4326'})
    
with ProgressBar():  

    fig, axes = plt.subplots(3,3, sharex=True, sharey=True)
    axes = axes.ravel()
    for idx, band in enumerate(ds['band']):
        
        temp = ds.sel({'band':band})
        
        gdf = to_geodataframe(temp)
        
        gdf.plot(ax=axes[idx],
                 legend=False,
                 column='band',
                 cmap=plt.cm.get_cmap('viridis'))
                       
                    
        add_cbar_to_DataArray(temp, axes[idx])
    
    
    fig.show()
   
   