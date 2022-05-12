# Training: Python and GOES-R Imagery: Script 8 - Functions for download data from AWS
#-----------------------------------------------------------------------------------------------------------
# Required modules
import os                                # Miscellaneous operating system interfaces
import numpy as np                       # Import the Numpy package

import math                              # Mathematical functions
from osgeo import osr                    # Python bindings for GDAL
from osgeo import gdal                   # Python bindings for GDAL
from reprojection import reproject       # local package for reprojection
from loaders import (loadCPT,
                     download_CMI,
                     download_PROD,
                     download_GLM)       # loaders of satellite data (local package)
#from netCDF4 import Dataset             # Read / Write NetCDF4 files
#import matplotlib.pyplot as plt         # Plotting library
#import cartopy, cartopy.crs as ccrs     # Plot maps
##import sys

#-----------------------------------------------------------------------------------------------------------
# Functions to convert lat / lon extent to array indices 
def geo2grid(lat, lon, nc):
    """
    Description:
        This function converts lat / lon extent to array indices with respect to the 
        offsets and scales extracted from the netcdf (Dataset) object.
        
    Returns
        x,y: tuple of ints representing the indexes to slice the array with respect to the given
             lat/lon coordinates.
    
    """

    # Apply scale and offset 
    xscale, xoffset = nc.variables['x'].scale_factor, nc.variables['x'].add_offset
    yscale, yoffset = nc.variables['y'].scale_factor, nc.variables['y'].add_offset
    
    offsets = {"xoffset":xoffset,
               "yoffset":yoffset}
    scales = {"xscale":xscale,
              "yscale":yscale}

    x, y = latlon2xy(lat, lon, offsets, scales)

    return y, x

def latlon2xy(lat:float,
              lon:float, 
              offsets = {"xoffset":0,
                         "yoffset":0},
              scales = {"xscale":1,
                        "yscale":1},
              semi_major_axis=6378137, # (meters) - goes_imagery_projection:semi_major_axis
              inverse_flattening = 298.257222096, #  goes_imagery_projection:inverse_flattening
              semi_minor_axis = 6356752.31414, # (meters) # goes_imagery_projection:semi_minor_axis
              e = 0.0818191910435, # ellipsis
              H = 42164160, # (meters) - goes_imagery_projection:perspective_point_height + goes_imagery_projection:semi_major_axis
              longitude_of_projection_origin = -1.308996939, # goes_imagery_projection: longitude_of_projection_origin
              ):
    """
    Description:
        This function converts lat / lon extent to array indices
        given default values of the Globe projection. In the future, this parameters may be directly imported from a cartopy.Globe object.
        
        
    Parameters:
        lat (float): the latitute value of the coordinate to be converted into xy position of the array
        
        lon (float): the longitude value of the coordinate to be converted into xy position of the array
        
        
        offsets (dict): dict containing the xoffset and yoffset to be applied to the x,y
            Default:
                offsets = {"xoffset":0,
                           "yoffset":0},
                         
        scales (dict): dict containing the xscale and yscale to be applied to the x,y
            Default: 
                scales = {"xscale":1,
                          "yscale":1},

        
        semi_major_axis (float): # The semi_major_axis of the satellite
            Default: 6378137 (meters) -> value with respect to the goes_imagery_projection
        
        inverse_flattening (float) the inverse_flattening of the satellite
            Default: 298.257222096 (meters) -> value with respect to the goes_imagery_projection
        
        semi_minor_axis (float) the semi_minor_axis of the satellite
            Default: 6356752.31414 (meters) -> value with respect to the goes_imagery_projection
        
        e (float): ellipsis
            Default: 0.0818191910435
        
        H (float): the summation of the perspective_point_height and the semi_major_axis of the satellite
            Default: 42164160 (meters); -> value with respect to the goes_imagery_projection
        
        longitude_of_projection_origin (float): the longitude_of_projection_origin of the satellite
            Default: -1.308996939; -> value with respect to the goes_imagery_projection
            
    Returns
        x,y: tuple of floats: values that may require a further processing of (xoffset and yoffsets) and (xscale and yscale)
    
    """

    # Convert to radians
    latRad = lat * (math.pi/180)
    lonRad = lon * (math.pi/180)

    # (1) geocentric latitude
    Phi_c = math.atan(((semi_minor_axis * semi_minor_axis)/(semi_major_axis * semi_major_axis)) * math.tan(latRad))
    
    # (2) geocentric distance to the point on the ellipsoid
    rc = semi_minor_axis/(math.sqrt(1 - ((e * e) * (math.cos(Phi_c) * math.cos(Phi_c)))))
    
    # (3) sx
    sx = H - (rc * math.cos(Phi_c) * math.cos(lonRad - longitude_of_projection_origin))
    
    # (4) sy
    sy = -rc * math.cos(Phi_c) * math.sin(lonRad - longitude_of_projection_origin)
    
    # (5)
    sz = rc * math.sin(Phi_c)

    # x,y
    x = math.asin((-sy)/math.sqrt((sx*sx) + (sy*sy) + (sz*sz)))
    y = math.atan(sz/sx)
    

    x = (x - offsets["xoffset"])/scale["xscale"]
    y = (y - offsets["yoffset"])/scale["yscale"]

    return x, y


def convertExtent2GOESProjection(extent):
    """
    Description:
        Function to convert lat / lon extent to GOES-16 extents
    
    
    """

    # GOES-16 viewing point (satellite position) height above the earth
    GOES16_HEIGHT = 35786023.0
    # GOES-16 longitude position
    GOES16_LONGITUDE = -75.0
	
    a, b = latlon2xy(extent[1], extent[0])
    c, d = latlon2xy(extent[3], extent[2])
    return (a * GOES16_HEIGHT, c * GOES16_HEIGHT, b * GOES16_HEIGHT, d * GOES16_HEIGHT)
