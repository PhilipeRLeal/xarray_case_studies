
# -*- coding: utf-8 -*-
"""
Created on Mon Feb 17 17:48:35 2020

@author: lealp
"""



from idw import idw


def gdf_heatmap(gdf, df_column, 
                dx=0.1, dy=0.1, 
                smooth=0,
                function='gaussian',
                verbose=True):
    
     
        
    
    
    z = gdf[df_column].values
    
    x = gdf.geometry.apply(lambda x: x.x)
    y = gdf.geometry.apply(lambda x: x.y)
    
    
    Array_Interpolated = idw(x,y, z, 
                       dx=dx, dy=dy, 
                       smooth=smooth,
                       function=function,
                       verbose=verbose)
    
    return {'array': Array_Interpolated, 
            'x':x, 
            'y': y,
            'dx':dx,
            'dy':dy}
