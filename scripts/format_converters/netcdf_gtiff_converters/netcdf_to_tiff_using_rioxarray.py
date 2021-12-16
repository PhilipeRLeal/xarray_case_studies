import rioxarray
import xarray
import numpy as np


def dataArray_to_tiff(da, lon_name='lon', lat_name='lat', crs="epsg:4326", pathname='test.tif'):


    da = da.rio.set_spatial_dims(lon_name, lat_name, False).rio.write_crs(crs)
    
    
    if len(interp_dataSet_Tmean.to_array().dims)==3:
    
        transposing_order = [x for x in da.dims if x not in [lon_name, lat_name]]
        transposing_order = transposing_order +[lat_name, lon_name]
        
    elif len(interp_dataSet_Tmean.to_array().dims) == 2:
        transposing_order = [lat_name, lon_name]
    
    else:
        raise('Dimensions must be at most 3, and not below 2')
    
    da = da.transpose(*transposing_order).rio.set_spatial_dims(lon_name, lat_name, False)
    
    da.rio.to_raster(pathname)
    
    
    return da