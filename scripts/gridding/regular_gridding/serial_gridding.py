#!/usr/bin/env python
# coding: utf-8


# Ref:

# https://stackoverflow.com/questions/40342355/how-can-i-generate-a-regular-geographic-grid-using-python


import shapely
import pyproj
import multiprocessing
import geopandas as gpd
import numpy as np
from time import time
import pandas as pd
import os
import copy
    

# # Fetching some basic data


# Get geometries 
shpfilename = shpreader.natural_earth(resolution='50m',
                                      category='cultural',
                                      name='admin_0_countries')
reader = shpreader.Reader(shpfilename)

Countries = pd.DataFrame()

for x in reader.records():
    S = pd.Series(x.attributes)
    S['geometry'] = x.geometry

    Countries = Countries.append(S, ignore_index=True)

Countries = gpd.GeoDataFrame(Countries, crs="EPSG:4326")

def get_bounds(df, country=str, colname = 'ABBREV'):
    '''
    Returns
        ROI = shapely.geometry.box(minx, miny, maxx, maxy)

    '''
    
    mask = df[colname].str.contains(country).fillna(False)
    
    c_df = df[mask]
    
    minx, miny, maxx, maxy = c_df.geometry.total_bounds
    
    ROI = shapely.geometry.box(minx, miny, maxx, maxy)
    
    return ROI, c_df.geometry

    
# Determine bounding box
ROI, geometry = get_bounds(Countries, 'Brazil')


# Choosing a projected coordinate system (therefore, in meters for a given ROI)


def generate_regularGrid(xmin, ymin, xmax, ymax,
                         origin_crs, target_crs,
                         dx = 5, # in target units
                         dy = 5, # in target units
                         return_grid_in_original_crs=False,
                         verbose=False):
    T0 = time()
    Transformer = pyproj.Transformer.from_crs(origin_crs, target_crs, always_xy=True)
    RegularGrid = []
    
    
    xmin, ymin = Transformer.transform(xmin, ymin)
    
    xmax, ymax = Transformer.transform(xmax, ymax)
    
    x = copy.copy(xmin) - dx
    
    ddy = np.mean([ymin, ymax])
    ddx = np.mean([xmin, xmax])
    while x <= xmax:
        if verbose:
            print('x <= xmax : {0:.4f} <- {1:.4f}: {2}'.format(x, xmax, x < xmax))
        y = copy.copy(ymin)  - dy
        while y <= ymax:
            if verbose:
                print('y <= ymax : {0:.4f} <- {1:.4f}: {2}'.format(y, ymax, x < ymax))

            p = shapely.geometry.box(x, y, x + dx, y + dy)
            RegularGrid.append(p)
            y += dy
        x += dx
    
    RegularGrid = gpd.GeoSeries(RegularGrid, crs=target_crs, name='geometry')

    if return_grid_in_original_crs:

        RegularGrid = RegularGrid.to_crs(origin_crs)
    
    dt = time() - T0
    
    print('Time Taken: {0}'.format(dt))

    return RegularGrid, dt


T0 = time()

RegularGrid = generate_regularGrid(*ROI.bounds,
                                  origin_crs='epsg:4326',
                                  target_crs='epsg:5880', # SIRGAS 2000 - Polyconic
                                  dx= 500_000,
                                  dy = 500_000,
                                  return_grid_in_original_crs=True,
                                  verbose=False)

ax = geometry.plot(facecolor='blue')
RegularGrid.plot(ax=ax, edgecolor='k', facecolor=(0.5,0.5,0.5,0.2))
plt.show()

dt = time() - T0
print('Time Taken: {0}'.format(dt))
