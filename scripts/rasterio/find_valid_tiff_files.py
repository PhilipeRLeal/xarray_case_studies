import pandas as pd
import numpy as np

import geopandas as gpd
import glob
import rasterio
import rasterio.mask
from shapely.geometry import box
import os



shp_file_path = r'C:\Doutorado\BD\IBGE\IBGE_Estruturas_cartograficas_Brasil\2017\Unidades_Censitarias\Setores_Censitarios\*shp'

gdf= gpd.read_file(glob.glob(shp_file_path)[0])
gdf_origin_bounds = gpd.GeoSeries(box(*gdf.total_bounds), crs=gdf.crs)
Para = gdf[gdf['CD_GEOCODM'].str.startswith('15')]


def get_bounds_from_gdf(gdf_bounds, epsg):
    
    return gdf_bounds.to_crs(epsg)
    
    
main_dir = r'C:\Users\Philipe Leal\Downloads\temp\Global Impervious Surfaces products\Global Impervious Surfaces products'
ending = '*.tif*'
tiff_files = glob.glob( os.path.join(main_dir, ending))


print('Total number of files in directory: ', len(tiff_files))

# Filtering files outside the Main GDF:
    
valid_tiffs = []    
    
for tiff_file_path in tiff_files:
    with rasterio.open(tiff_file_path) as src:
        #out_image, out_transform = rasterio.mask.mask(src, shapes, crop=True)
        out_meta = src.meta
        Bounds = box(*src.bounds)
        gdf_bounds = get_bounds_from_gdf(gdf_origin_bounds, out_meta['crs'].to_epsg()).values
        if (gdf_bounds.intersects(Bounds) or  gdf_bounds.within(Bounds) 
            or gdf_bounds.contains(Bounds) or gdf_bounds.crosses(Bounds)
            ):
            valid_tiffs.append(tiff_file_path)

print('Valid Total Files: ', len(valid_tiffs))

ref_dir = os.path.dirname(os.path.dirname(main_dir))

saving_paths = os.path.join(ref_dir, 'Valid_files.csv')

to_file = pd.Series(valid_tiffs, name='paths')
to_file.index.name = 'ID'
to_file.to_csv(saving_paths)