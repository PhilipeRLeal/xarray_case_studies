# -*- coding: utf-8 -*-
"""
Created on Fri Dec 11 10:14:19 2020

@author: Philipe_Leal
"""

import numpy as np

from scipy import spatial
import xarray as xr

def get_tutorial_dataset():
    ds = xr.tutorial.open_dataset('rasm').load()
    Tair = ds['Tair']
    
    
    Tair.coords['xc'] = (Tair.coords['xc'] + 180) % 360 - 180
    Tair.coords['yc'] = (Tair.coords['yc'] + 90) % 180 - 90
    return Tair

class KDTree():
    
    """ A KD-tree implementation for fast point lookup on a 2D grid
    
    Keyword arguments: 
    dataset -- a xarray DataArray containing lat/lon coordinates
               (named 'lat' and 'lon' respectively)
               
    """
    
    def __init__(self, dataset, xcor, ycor):
        # store original dataset shape
        self.dataset = dataset
        self.shape = dataset.shape
        self.ndim = dataset.ndim
        # reshape and stack coordinates
        coords = np.column_stack((dataset.coords[ycor].values.ravel(),
                                  dataset.coords[xcor].values.ravel()))
        
        
        # construct KD-tree
        self.tree = spatial.cKDTree(self.transform_coordinates(coords))
        
        
    
    
    def transform_coordinates(self, coords):
        """ Transform coordinates from geodetic to cartesian
        
        Keyword arguments:
        coords - a set of lan/lon coordinates (e.g. a tuple or 
                 an array of tuples)
        """
        # WGS 84 reference coordinate system parameters
        A = 6378.137 # major axis [km]   
        E2 = 6.69437999014e-3 # eccentricity squared    
        
        coords = np.asarray(coords).astype(np.float)
        
        # is coords a tuple? Convert it to an one-element array of tuples
        if coords.ndim == 1:
            coords = np.array([coords])
        
        # convert to radiants
        lat_rad = np.radians(coords[:,0])
        lon_rad = np.radians(coords[:,1]) 
        
        # convert to cartesian coordinates
        r_n = A / (np.sqrt(1 - E2 * (np.sin(lat_rad) ** 2)))
        x = r_n * np.cos(lat_rad) * np.cos(lon_rad)
        y = r_n * np.cos(lat_rad) * np.sin(lon_rad)
        z = r_n * (1 - E2) * np.sin(lat_rad)
        
        return np.column_stack((x, y, z))
    
    
    def idw(self, point, k=5, power=2):
        
        
        
        Nearest_da, distances = self.knn(point, k=k)
        
        # Filling Nan with zeros for interpolation
        
        Nearest_da = Nearest_da.fillna(0)
        
        distances= distances**(-power)
        
        if np.ndim(point) == 1:
            n_points = 1
            
        elif np.ndim(point) > 1:
            n_points = np.shape(point)[0]
        
        print('N° Points', n_points)
        print('K: ', k)
        print('distances shape: ', distances.shape)
        
        print('distances summed shape: ', distances.sum(axis=1).shape)
        
        
        if k==1:
            distances = distances/distances.sum()
        
        else:
            
            
            distances = distances/distances.sum(axis=1).reshape((-1, 1))
            
            
        print('\n'*4)    
        
        if k==1:
            IDW = np.array(Nearest_da * distances)
        else:
            IDW = np.einsum('ij, ij -> i', Nearest_da, distances)
        
        return IDW
    
    
    def knn(self, point, k=1):
        
        
        pixels_index , distances = self.query(point, k=k)
        
        Nearest_da = self.dataset[pixels_index]
        
        return Nearest_da, distances
    
    
    
    def query(self, point, k=1):
        
        indexes, distances = self._query(point, k)
        
        if np.ndim(indexes[0])> 1:
            dims = ['pixel', 'knn']
        else:
            dims = ['pixel']
            
        xda = xr.DataArray(indexes[0], dims=dims)
        yda = xr.DataArray(indexes[1] , dims=dims)
         
      
        
        return (xda, yda), distances
            
        
    def _query(self, point, k=1):
        """ Query the kd-tree for nearest neighbour.

        Keyword arguments:
        point -- a (lat, lon) tuple or array of tuples
        """
        distances, indexes = self.tree.query(self.transform_coordinates(point), k=k)
        
        # regrid to 2D grid
        indexes = np.unravel_index(indexes, self.shape)
        
        # return DataArray indexers
        return indexes, distances
    
    def query_ball_point(self, point, radius):
        """ Query the kd-tree for all poinst within a given distance 
        radius (in meters) of each provided point(s)
        
        Keyword arguments:
        point -- a (lat, lon) tuple or array of tuples
        radius -- the search radius (km)
        """
        
        index = self.tree.query_ball_point(self.transform_coordinates(point),
                                           radius)

        # regrid to 2D grid 
        index = np.unravel_index(index[0], self.shape)
        
        # return DataArray indexers
        return xr.DataArray(index[0], dims='pixel'), \
               xr.DataArray(index[1], dims='pixel')


