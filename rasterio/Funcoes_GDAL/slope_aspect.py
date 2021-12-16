# -*- coding: utf-8 -*-
"""
Created on Mon Jun 25 11:49:49 2018

@author: Philipe Leal
"""

import numpy as np
import matplotlib.pyplot as plt
from osgeo import *


# Shaded elevation parameters
# Sun direction
azimuth = 315.0
# Sun angle
altitude = 45.0
# Elevation exagerationexaggeration
z = 1.0
# Resolution
scale = 1.0
# No data value for output
NODATA = -9999

# Needed for numpy conversions
deg2rad = 3.141592653589793 / 180.0
rad2deg = 180.0 / 3.141592653589793

cols = 9
rows = 9
nd = 2
Imagem = np.random.rand(cols,row)*255


# Filtrar imagem com base numa máscara 3x3 em x e y directions:
x = ((z * Imagem[0] + z * Imagem[3] + z * Imagem[3] + z *
 Imagem[6]) - (z * Imagem[2] + z * Imagem[5] + z * Imagem[5] + z *
 Imagem[8])) / (8.0 * 9 * scale)
 
y = ((z * Imagem[6] + z * Imagem[7] + z * Imagem[7] + z * \
      Imagem[8]) - (z * Imagem[0] + z * Imagem[1] + z * Imagem[1] + z * Imagem[2])) / (8.0 * 9 * scale)

# Calculate slope in degrees:
slope = np.zeros_like(Imagem)

for i in range(len(x)):
    for j in range(len(y)):
        slope[i,j] = 90.0 - np.arctan(np.sqrt(x[i]**2 + y[j]**2)) * rad2deg


# Calculate aspect
aspect = np.zeros_like(Imagem)
for i in range(len(x)):
    for j in range(len(y)):
        aspect[i,j] = np.arctan2(x[i], y[j])

# Calculate the shaded relief
shaded = np.sin(altitude * deg2rad) * np.sin(slope * deg2rad) + \
 np.cos(altitude * deg2rad) * np.cos(slope * deg2rad) * \
 np.cos((azimuth - 90.0) * deg2rad - aspect)

# Scale values from 0-1 to 0-255
shaded = shaded * 255

# Rebuild the new header
header = "ncols {}\n".format(shaded.shape[1])
header += "nrows {}\n".format(shaded.shape[0])
header += "xllcorner {}\n".format(1+ (1 * (cols - shaded.shape[1])))
header += "yllcorner {}\n".format(1 + (1 * (rows -shaded.shape[0])))
header += "cellsize {}\n".format(1)
header += "NODATA_value {}\n".format(NODATA)
# Set no-data values
for pane in Imagem:
    slope[pane == nd] = NODATA
    aspect[pane == nd] = NODATA
    shaded[pane == nd] = NODATA
    
# Open the output file, add the header, save the slope grid
    
slopegrid = r'C:\Users\Philipe Leal\Downloads\slopegrid.asc'    
    
aspectgrid = r'C:\Users\Philipe Leal\Downloads\aspectgrid.asc'    

shadegrid = r'C:\Users\Philipe Leal\Downloads\shadegrid.asc'   
with open(slopegrid, "w") as f:
    f.write(bytes(header, "UTF-8")
    np.savetxt(f, slope)
# Open the output file, add the header, save the aspectgrid
with open(aspectgrid, "wb") as f:
    f.write(bytes(header, "UTF-8")
    np.savetxt(f, aspect)
# Open the output file, add the header, save the relief grid
with open(shadegrid, "wb") as f:
    f.write(bytes(header, 'UTF-8'))
    np.savetxt(f, shaded)
