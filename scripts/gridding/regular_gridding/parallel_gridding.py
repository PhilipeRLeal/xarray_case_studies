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



# Choosing a projected coordinate system (therefore, in meters for a given ROI)



def info():
    #print('module name:', __name__)
    print('parent process:', os.getppid())
    print('process id:', os.getpid(), '  -----> Complete')

def _regularGrid_multiprocessing(x, y,
                                 dx, dy,
                                 q=None):
    

    p = shapely.geometry.box(x, y, x + dx, y + dy)
    if q:
        q.put(p)
    else:
        return p
    
    info()


def fetch_base_points(xmin,
                      ymin, xmax, ymax, 
                      dx, dy,
                      use_Queue=False,
                      verbose=False):

    combinations = []
    processess = []
    if use_Queue:
        q =  multiprocessing.Queue()
    
    x = copy.copy(xmin) - dx

    while x <= xmax:
        if verbose:
            print('x <= xmax : {0} <- {1}: {2}'.format(x, xmax, x < xmax))
        y = copy.copy(ymin) - dy
        while y <= ymax:
            if verbose:
                print('y <= ymax : {0} <- {1}: {2}'.format(y, ymax, x < ymax))

            if use_Queue:
                p = multiprocessing.Process(target=_regularGrid_multiprocessing, args=(x, y, dx, dy, q))
                processess.append(p)
                p.start()

            else:
                combinations.append( (x, y, dx, dy))

            y += dy
        x += dx
        
    if use_Queue:
        return processess
    
    else:
        return combinations

def regularGrid_multiprocessing(xmin, ymin, xmax, ymax,
                                origin_crs, target_crs,
                                dx = 5, # in target units
                                dy = 5, # in target units
                                return_grid_in_original_crs=False,
                                use_pool=True,
                                verbose=False):
    T0 = time()
    Transformer = pyproj.Transformer.from_crs(origin_crs, target_crs , always_xy=True)

    xmin, ymin = Transformer.transform(xmin, ymin)

    xmax, ymax = Transformer.transform(xmax, ymax)

    if use_pool:
        combinations = fetch_base_points(xmin, ymin, xmax, ymax, dx, dy, use_Queue=False, verbose=verbose)
        with multiprocessing.Pool(multiprocessing.cpu_count()) as myPool:
            RegularGrid = myPool.starmap(_regularGrid_multiprocessing, combinations)


    else: # Using Processes

        combinations = fetch_base_points(xmin, ymin, xmax, ymax, dx, dy, use_Queue=True, verbose=verbose)
        [p.join() for p in processess]
        
        RegularGrid = q.get()

    RegularGrid = gpd.GeoSeries(RegularGrid, crs=target_crs, name='geometry')

    if return_grid_in_original_crs:

        RegularGrid = RegularGrid.to_crs(origin_crs)
    
    dt = time() - T0
    
    return RegularGrid, dt



if __name__ == '__main__':
    
    runs = {'Pool':True, 'Process':False, 'serial':None}
    speedups = {'Pool':[],
                        
                'Process':[],
                          
                'serial':[],
                          
                }
    
    
    Range = range(1000_000, 100_000, -50000)
    
    if len(Range) > 20:
        raise TypeError('Range is too long')
    
    for key, method in runs.items():
        for i in Range:

            dts = []
            for i in range(5):
                
                if key == 'serial':
                    RegularGrid, dt = generate_regularGrid(*ROI.bounds,
                                                   origin_crs='epsg:4326',
                                                   target_crs='epsg:5880', # SIRGAS 2000 - Polyconic
                                                   dx= i,
                                                   dy = i,
                                                   return_grid_in_original_crs=True,
                                                   verbose=False)


                else:

                    RegularGrid, dt = regularGrid_multiprocessing(*ROI.bounds,
                                                                origin_crs='epsg:4326',
                                                                target_crs='epsg:5880', # SIRGAS 2000 - Polyconic
                                                                dx= i,
                                                                dy = i,
                                                                return_grid_in_original_crs=False,
                                                                use_pool=method,
                                                                verbose=False)
                del RegularGrid
                    
            speedups[key].append(dt)
            
                
        
    speedups = pd.DataFrame(speedups)
    sppedups.index.name = 'Trials'
    sppedups.columns.name = 'Runs'
    speedups = sppedups.stack()
    print(speedups.head())
    ######################### Plotting

    import matplotlib.pyplot as plt
    import seaborn as sns

        
    sns.boxplot(df = speedups, x='Trials', y=['Runs'])
    plt.title('Speed ups')
        
    plt.figure()
    ax = geometry.plot(facecolor='blue')
    RegularGrid.plot(ax=ax, edgecolor='k', facecolor=(0.5,0.5,0.5,0.2))
    plt.title('Gridding using {0}'.format(key))
    plt.show()



