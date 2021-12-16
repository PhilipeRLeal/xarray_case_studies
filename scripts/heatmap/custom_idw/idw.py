# -*- coding: utf-8 -*-
"""
Created on Thu Mar 12 15:06:05 2020

@author: ricardoguimaraes
"""


import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import Rbf
import cartopy
import cartopy.crs as ccrs

def idw(x, y, z, dx=2, dy=2,
        smooth=0,
        function='gaussian',
        verbose=True):
    
    """
    
    Description:
        
        This function receives 2D coordinates (i.e.: x, y)
        and an array of values z for spatial interpolation (heatmap)
    
    
    ----------------------------------------------------------------
    
    Parameters:
        
        x (array): the x coordinates of all points in the dataset
        
        --------------------------------------
        
        y(array): the y coordinates of all points in the dataset
        
        --------------------------------------
        
        z(array): the z values of all points in the dataset
        
        --------------------------------------
        
        dx(float): the size of the pixels in x coordinates (in crs units) 
            standard value is 2 
        
        --------------------------------------
        
        dy (float): the size of the pixels in y coordinates (in crs units) 
            standard value is 2
        
        --------------------------------------
        
        smooth (float): the smoothing coefficient.
            standard value is 0
        
        --------------------------------------
        
        function (string): standard is 'gaussian'. Acceptable names with respective function:
            
            'multiquadric': sqrt((r/self.epsilon)**2 + 1)
            'inverse': 1.0/sqrt((r/self.epsilon)**2 + 1)
            'gaussian': exp(-(r/self.epsilon)**2)
            'linear': r
            'cubic': r**3
            'quintic': r**5
            'thin_plate': r**2 * log(r)
            
        --------------------------------------
        
        verbose (bool): standard is True
        
    ----------------------------------------------------------------
        
    Returns
        HeatMap's (array)
    
    """
    
    # Setup: Generate data...
    
    
    xi = np.arange(x.min(), x.max(), dx)
    yi = np.arange(y.min(), y.max(), dy)
    
    xsize = xi.size
    
    ysize = yi.size
    
    xi, yi = np.meshgrid(xi, yi)
    xi, yi = xi.flatten(), yi.flatten()
    
    
    # Calculate scipy's RBF
    
    grid1 = scipy_idw(x,y,z,xi,yi, 
                      function=function,
                      smooth=smooth)
    grid1 = grid1.reshape((ysize, xsize))
    
    # # Calculate IDW using other systems:
    # grid2 = simple_idw(x,y,z,xi,yi)
    # grid2 = grid2.reshape((ysize, xsize))


    # grid3 = linear_rbf(x,y,z,xi,yi)
    # print (grid3.shape)
    # grid3 = grid3.reshape((ysize, xsize))


    # # Comparisons...
    # plot(x,y,z,grid1)
    # plt.title('Homemade IDW')
    
    
    # plotting:
    if verbose==True:
        fig = plot(x,y,z,grid1)
        fig.suptitle("Scipy's Rbf with function={0}\n smooth: {1:.2f}".format(function, smooth))

    # plot(x,y,z,grid3)
    # plt.title('Homemade linear Rbf')

    return grid1

def simple_idw(x, y, z, xi, yi):
    dist = distance_matrix(x,y, xi,yi)

    # In IDW, weights are 1 / distance
    weights = 1.0 / dist

    # Make weights sum to one
    weights /= weights.sum(axis=0)

    # Multiply the weights for each interpolated point by all observed Z-values
    zi = np.dot(weights.T, z)
    return zi

def linear_rbf(x, y, z, xi, yi):
    dist = distance_matrix(x,y, xi,yi)

    # Mutual pariwise distances between observations
    internal_dist = distance_matrix(x,y, x,y)

    # Now solve for the weights such that mistfit at the observations is minimized
    weights = np.linalg.solve(internal_dist, z)

    # Multiply the weights for each interpolated point by the distances
    zi =  np.dot(dist.T, weights)
    return zi


def scipy_idw(x, y, z, xi, yi, function='linear',
              smooth=0):
    interp = Rbf(x, y, z, function=function, smooth=smooth)
    return interp(xi, yi)


def distance_matrix(x0, y0, x1, y1):
    obs = np.vstack((x0, y0)).T
    interp = np.vstack((x1, y1)).T

    # Make a distance matrix between pairwise observations
    # Note: from <http://stackoverflow.com/questions/1871536>
    # (Yay for ufuncs!)
    d0 = np.subtract.outer(obs[:,0], interp[:,0])
    d1 = np.subtract.outer(obs[:,1], interp[:,1])

    return np.hypot(d0, d1)



def plot(x,y,z,grid):
    
    projection = ccrs.PlateCarree()
    fig, ax = plt.subplots(subplot_kw={'projection':projection})
    
    
    ax.gridlines()
    ax.add_feature(cartopy.feature.OCEAN, zorder=0)
    ax.add_feature(cartopy.feature.LAND, zorder=0, edgecolor='black')
    
    ax.set_global()
    
    ax.imshow(grid, extent=(x.min(), x.max(), y.max(), y.min()))
    
    ax.set_xlim(left= x.min(), right=x.max())
    ax.set_ylim(y.min(), y.max())
    
    ax.margins(x=0.05, y=0.05) # Values >0.0 zoom out
    
    Mappable = ax.scatter(x,y,c=z)
    fig.colorbar(Mappable)
    fig.show()
    
    return fig

if __name__ == '__main__':
    to_file = r'C:\Users\lealp\Downloads\temp\my_result'
    
    x, y, z = (np.random.normal(-45, 8, size=(100)), 
               np.random.normal(-4, 8, size=(100)), 
               np.random.normal(-40, 4, size=(100)))

    
    dx=0.1
    
    dy=0.1
    
    for i in np.linspace(0, 2, 10):
        Interpolated = idw(x,y, z, dx=dx, dy=dy, 
                           function='gaussian',
                           smooth=i, verbose=True)
        
    input('Press any to close: \n\t')
    plt.close('all')
        