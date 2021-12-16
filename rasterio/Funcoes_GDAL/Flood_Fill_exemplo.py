# -*- coding: utf-8 -*-
"""
Created on Mon Jun 25 19:14:48 2018

@author: Philipe Leal
"""

import sys
import numpy as np
from linecache import getline
sys.path.insert(0,r'C:\Users\Philipe Leal\Dropbox\Profissao\Python\OSGEO\Funcoes_GDAL')

from Flood_Fill import floodFill as ff

# Output ASCII DEM file
source = r"C:\Doutorado\Estudo_Python\GIS_in_Python\FloodFill\FloodFill\terrain.asc"

target = r"C:\Doutorado\Estudo_Python\GIS_in_Python\FloodFill\FloodFill\flood.asc"

img = np.loadtxt(source, skiprows=6)

# Mask elevations lower than 70 meters.
wet = np.where(img < 70, 1, 0)
print("Image masked")

# Parse the header using a loop and
# the built-in linecache module
hdr = [getline(source, i) for i in range(1, 7)]
values = [float(h.split(" ")[-1].strip()) for h in hdr]
cols, rows, lx, ly, cell, nd = values
xres = cell
yres = cell * -1
# Starting point for the
# flood inundation in pixel coordinates
sx = 2582

sy = 2057
print("Beginning flood fill")
fld = ff(sx, sy, wet)
print("Finished flood fill")
header = ""
for i in range(6):
    header += hdr[i]
print("Saving grid")
# Open the output file, add the hdr, save the array
with open(target, "wb") as f:
    f.write(bytes(header, 'UTF-8'))
    np.savetxt(f, fld, fmt="%1i")
print("Done!")