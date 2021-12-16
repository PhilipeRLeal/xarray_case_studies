

import pandas as pd
import os

def common_reader(path, separator=','):
    
    if path.endswith('xls') or path.endswith('xlsx'):
        df = pd.read_excel(path, sep=separator)
        
    else:
        df = pd.read_csv(path, sep=separator)
        
    return df


import sys


sys.path.insert(0, r'C:\Users\Philipe Leal\Dropbox\Profissao\Python\OSGEO\OGR_Vetor\geocoding')

import geocodificador


geocodificador = geocodificador.df_geocoder



if '__main__' == __name__:
    
    from_path = input('original file full-path (xls or csv or txt): ')
    separator = input('define columns separator: (",", ";", other): ')
    to_path = input('to_file_path (shp): ')
    api_key_OpenMapQuest = input('api_key_OpenMapQuest: ')
    api_key_GeoLake = input('api_key_GeoLake: ')
    logradouro = input('logradouro: ')
    exactly_one = input('exactly_one: ')
    country_codes = input('country_codes: ')
    min_delay_seconds = input('min_delay_seconds: ')

        
    df = common_reader(from_path, separator)
    
        
    df2 = geocodificador(df, 
                         api_key_OpenMapQuest=api_key_OpenMapQuest, # 'arjIxMIcVzqDJx7fYrv854lrGLAj5geM',
                         api_key_GeoLake=api_key_GeoLake, #'ykbklV3MvgAMu3tLJQ7f',
                         logradouro=logradouro,
                         exactly_one=exactly_one,
                         country_codes=country_codes,
                         min_delay_seconds=min_delay_seconds)
    
    df2.to_file(to_path)
