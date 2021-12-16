# -*- coding: utf-8 -*-
"""
Created on Thu Mar 12 14:27:05 2020

@author: ricardoguimaraes
"""
import numpy as np
import pandas as pd

import geopandas as gpd

from gdf_heatmap import gdf_heatmap

from array_to_tiff import array_to_tiff


if '__main__' == __name__ :
    
    from shapely.geometry import Point
    import matplotlib.pyplot as plt
    
    df = pd.DataFrame({'x': np.random.normal(-45, 8, size=(100)), 
                       'y': np.random.normal(-4, 8, size=(100)), 
                       'z': np.random.normal(-40, 4, size=(100))}
                     )
    
    df['geometry'] = df.apply(lambda x: Point(x['x'], x['y']), axis=1)
    
    gdf = gpd.GeoDataFrame(df)
    
    Result = gdf_heatmap(gdf, df_column ='z',
                dx=0.5, dy=0.5, verbose=True,
                smooth=0.3,
                function='gaussian')
    
    
    array_to_tiff(Result['array'], Result['x'], 
            Result['y'],Result['dx'], Result['dy'], 
            to_file=r'C:\Users\lealp\Downloads\Temp\My_tiff')
    
    input('Press any to close')
    
    plt.close('all')
    
    del Result
    
    del gdf