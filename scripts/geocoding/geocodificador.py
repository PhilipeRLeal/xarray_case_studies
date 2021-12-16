import pandas as pd
import numpy as np
import os, sys
import geopandas as gpd
import geopy

import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import seaborn as sns

from shapely.geometry import Point
from geopy.extra.rate_limiter import RateLimiter
import warnings


def geocode_OpenMapQuest(name, 
                         country_codes=None, 
                         API_Key = 'arjIxMIcVzqDJx7fYrv854lrGLAj5geM',
                         **kwargs):
    
    min_delay_seconds = kwargs.pop('min_delay_seconds', 5)
    
    
    exactly_one= kwargs.pop('exactly_one', True)
    
    OPenMapQuest_Geocoder = geopy.geocoders.OpenMapQuest(api_key=API_Key, 
                                                         country_bias=country_codes
                                                        , **kwargs)
    
    geocode = RateLimiter(OPenMapQuest_Geocoder.geocode,
                          min_delay_seconds=min_delay_seconds)
    with warnings.catch_warnings():
        warnings.filterwarnings(action='ignore')
        
        geocoded = geocode(query=name, 
                               country_codes=country_codes,
                               exactly_one=exactly_one)
    
    if geocoded is None:
        return np.nan
    
    else:
        Points = []
        
        if isinstance(geocoded, list):

            for geocode in geocoded:
                location, point = geocode
                P = Point(reversed(point))
                Points.append(P)

            return Points
        
        else:
            location, point = geocoded
            return [Point(reversed(point))]
            

def geocode_via_GeoLake(name, 
                        country_codes=None, 
                        api_key='ykbklV3MvgAMu3tLJQ7f',
                        **kwargs):
    
    min_delay_seconds = kwargs.pop('min_delay_seconds', 5)
    exactly_one= kwargs.pop('exactly_one', True)
    
    Geolake_Geocoder = geopy.geocoders.Geolake(api_key=api_key, 
                                               **kwargs)
    
    geocode = RateLimiter(Geolake_Geocoder.geocode, 
                          min_delay_seconds=min_delay_seconds)
    
    with warnings.catch_warnings():
        warnings.filterwarnings(action='ignore')
        
        geocoded = geocode(query=name, country_codes=country_codes,
                               exactly_one=exactly_one)
    
    if geocoded is None:
        return np.nan
    
    else:
        Points = []
        
        if isinstance(geocoded, list):

            for geocode in geocoded:
                location, point = geocode
                P = Point(reversed(point))
                Points.append(P)

            return Points
        
        else:
            location, point = geocoded
            return [Point(reversed(point))]
    
def get_point(R1, R2):
    if np.isnan(R1) and isinstance(R2, list):
        return R2
    
    elif isinstance(R1, list) and np.isnan(R2):
        return R1
    
    elif isinstance(R1, list) and isinstance(R2, list):
        return R1
    
    else:
        R = np.nan
        
    if isinstance(R, str):
        R = np.nan
    return R

def _geocoding(name, 
              country_codes='BR', min_delay_seconds=5, 
              **kwargs):
    
    api_key_GeoLake=kwargs.pop('api_key_GeoLake'),
    api_key_OpenMapQuest=kwargs.pop('api_key_OpenMapQuest'),
    
    R1 = geocode_via_GeoLake(name, country_codes, 
                             api_key_GeoLake,
                             min_delay_seconds=min_delay_seconds, 
                             
                             **kwargs)
    
    R2 = geocode_OpenMapQuest(name, country_codes, 
                              api_key_OpenMapQuest,
                              min_delay_seconds=min_delay_seconds, 
                              
                              **kwargs)
    
    return get_point(R1, R2)

from tqdm import tqdm
tqdm.pandas()

def df_geocoder(df, api_key_GeoLake,
                api_key_OpenMapQuest,
                logradouro='full_name',
                exactly_one=False,
                country_codes='BR', 
                min_delay_seconds=5):
    '''
    Description:
        This function geocodes every entry in a given dataframe line by line.
        It uses two geocoding Web Servers (GeoLake and OpenMapQuest) during the analysis.
    
    ----------------------------------
    
    Parameters:
        df: (pandas dataframe):
        
        api_key_GeoLake: the user API for the GeoLake Web Service
        
        api_key_OpenMapQuest: the user API for the OpenMapQuest Web Service,
        
        
        logradouro: the dataframe's column name containing the full path to geocode
        
        exactly_one (bool): Default is False. If False, all possible geocodings are returned for later filtering
                            If True, only the first geocode is returned to the dataframe
        
        country_codes=(string or None): it filters the returned geocodes per country (i.e.: 'BR', )
        
        min_delay_seconds(int): how many seconds are allowed to be waited until Web Service Return
    
    ----------------------------------
    Return 
        Geopandas.GeoDataFrame
    
    '''
    
    df = df.copy()
    df['geocoded'] = df[logradouro].progress_apply(lambda x: _geocoding(x, 
                                                                       api_key_GeoLake=api_key_GeoLake,
                                                                       api_key_OpenMapQuest=api_key_OpenMapQuest,
                                                                       country_codes=country_codes,
                                                                       min_delay_seconds=5,
                                                                       exactly_one=exactly_one))

    r = (df.set_index([logradouro])['geocoded'].apply(pd.Series)
         .stack().reset_index()
         .drop({'level_1'}, axis=1)
        ).copy()
    
    r.columns = [logradouro, 'geometry']

    return gpd.GeoDataFrame(r.merge(df, on=logradouro), crs={'init':'epsg:4326'}).drop({'geocoded'}, axis=1)
