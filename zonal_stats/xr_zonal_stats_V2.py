from rasterio import features
import numpy as np
import pandas as pd
from affine import Affine
import xarray as xr
import geopandas as gpd
import glob

from shapely import speedups
speedups.disable()
pd.set_option("display.max_rows", 5000)

def get_transform_from_latlon(lat, lon):
    """ input 1D array of lat / lon and output an Affine transformation
    """
    lat = np.asarray(lat)
    lon = np.asarray(lon)
    trans = Affine.translation(lon[0], lat[0])
    scale = Affine.scale(lon[1] - lon[0], lat[1] - lat[0])
    return trans * scale

def get_xr_mask(shapes, coords, latitude='latitude', longitude='longitude',
                 fill=np.nan, **kwargs):
    """Rasterize a list of (geometry, fill_value) tuples onto the given
    xray coordinates. This only works for 1d latitude and longitude
    arrays.

    usage:
    -----
    1. read shapefile to geopandas.GeoDataFrame
          `states = gpd.read_file(shp_dir+shp_file)`
    2. encode the different shapefiles that capture those lat-lons as different
        numbers i.e. 0.0, 1.0 ... and otherwise np.nan
          `shapes = (zip(states.geometry, range(len(states))))`
    3. Assign this to a new coord in your original xarray.DataArray
          `ds['states'] = rasterize(shapes, ds.coords, longitude='X', latitude='Y')`

    arguments:
    ---------
    : **kwargs (dict): passed to `rasterio.rasterize` function

    attrs:
    -----
    :transform (affine.Affine): how to translate from latlon to ...?
    :raster (numpy.ndarray): use rasterio.features.rasterize fill the values
      outside the .shp file with np.nan
    :spatial_coords (dict): dictionary of {"X":xr.DataArray, "Y":xr.DataArray()}
      with "X", "Y" as keys, and xr.DataArray as values

    returns:
    -------
    :(xr.DataArray): DataArray with `values` of nan for points outside shapefile
      and coords `Y` = latitude, 'X' = longitude.


    """
    transform = get_transform_from_latlon(coords[latitude], coords[longitude])
    out_shape = (len(coords[latitude]), len(coords[longitude]))
    raster = features.rasterize(shapes, 
                                out_shape=out_shape,
                                fill=fill, transform=transform,
                                dtype=float, **kwargs)
    spatial_coords = {latitude: coords[latitude], longitude: coords[longitude]}
    return xr.DataArray(raster, coords=spatial_coords, dims=(latitude, longitude))

def _xr_rasterize(xr_da, geometry, reducers,
                longitude='longitude', latitude='latitude'):
    
    """ 
    Description:
        
        This function is the base function for analysis of the \
        zonal statistics over a netcdf, by using a geopandas GeoSeries \
        as initial geometric inputs.
        
        
        Returns
            geopandas geodataframe (with the new statistics per variable of the netcdf)
            
    """
    

    # 2. create a list of tuples (shapely.geometry, id)
    
    shape = [(geometry, 1)]

    # 3. create a new coord in the xr_da which will be set to the id in `shapes`
    coord_name="zones"
    xr_da[coord_name] = get_xr_mask(shape, xr_da.coords, 
                               longitude=longitude, latitude=latitude)

    zonal_stats_df =  (xr_da.to_dataframe().reset_index().groupby(coord_name).agg(reducers)
                       .T.unstack().unstack().to_frame(name='stats'))
    
    zonal_stats_df.index.names = ['zone', 'agg', 'var']
    
    # Adding geometry to geopandas GeodataFrame
    zonal_stats_df['geometry'] = geometry
    
    return gpd.GeoDataFrame(zonal_stats_df)


def xr_rasterize(xr_da, gdf, 
                 reducers=['count', 'max', 'min', 'median', 'mean', 'std'],
                 longitude='longitude', latitude='latitude'):
    
    '''
    Description:
        
        This function applies a zonal statistics over a netcdf, by using a geopandas GeoSeries
        as initial geometric inputs.
        
    
    Parameters:
    
        xr_da (xr.DataArray or xr.DataSet)
        
        gdf (gpd.GeoDataFrame, gpd.GeoSeries)
        
        reducers (list of reduction functions): 
            Standard functions are['count', 'max', 'min', 'median', 'mean', 'std']
            
        longitude (string): name of the spatial coordinate relative to the xaxis
            Standard is 'longitude'
            Other dataset use for example: 'lon', 'x', 'xc'...
            
        latitude (string): name of the spatial coordinate relative to the yaxis
            Standard is 'latitude'
            Other dataset use for example: 'lat', 'y', 'yc'...
    
    
    Returns
        geopandas geodataframe (with the new statistics per variable of the netcdf)


    # code origin: https://stackoverflow.com/questions/51398563/python-mask-netcdf-data-using-shapefile

    
    '''
    
    
    
    if isinstance(gdf, str):
        gdf = gpd.read_file(gdf)
    
    results = []
    
    for index, geom in gdf.geometry.items():
        result = _xr_rasterize(xr_da=ds,  
                               geometry=geom,
                               reducers=reducers, 
                               longitude='lon', 
                               latitude='lat')

    ####### Setting index:
    
        result_initial_index = result.index.names
        
        temp_index_name = 'old_index'
        
        if isinstance(gdf.index, pd.MultiIndex):

            old_index_names = gdf.index.names
            order = (list(old_index_names) + list(result_initial_index))
        
        elif isinstance(gdf.index, pd.Index) and not isinstance(gdf.index, pd.MultiIndex):
            old_index_name = str(gdf.index.name)
            
            order = ( [old_index_name] + list(result_initial_index))
        
        else:
            pass

        if isinstance(gdf.index, pd.Index) and not isinstance(gdf.index, pd.MultiIndex):
            
            result[temp_index_name] = index
            result = result.rename({temp_index_name:old_index_name}, axis=1)
            
        elif isinstance(gdf.index, pd.MultiIndex):
            
            
            if len(result)>0:
                result[temp_index_name] = [index] * result.shape[0]
            
                result[old_index_names] = result[temp_index_name].apply(pd.Series)
            

                result = result.drop(temp_index_name, axis=1)
                result = result.set_index(old_index_names, append=True)

            
            # Adding empty columns (old shp index to the empty result gdf)
            
            elif len(result) == 0:
                result = result.reindex(result.columns.tolist() + old_index_names, axis=1)
        
        result = result.reset_index()    
                    
        # Concat
        results.append(result)

        
    ######### Final steps for gdf conversion   
    
    gdf_results = gpd.GeoDataFrame(pd.concat(results, axis=0, ignore_index=True),
                                  crs = gdf.crs).set_index(order)
    
    return gdf_results
    