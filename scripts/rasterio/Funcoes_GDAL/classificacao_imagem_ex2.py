# -*- coding: utf-8 -*-
"""
Created on Mon Jun 25 10:35:31 2018

@author: Philipe Leal
"""

# file:///C:/Users/Philipe%20Leal/OneDrive/Documentos/Referencias_mendeley/Geoestatistica_Python/Joel%20Lawhead.pdf
# pg. 253 do PDF
import numpy as np
from osgeo import gdal_array

Before_image = r'C:\Users\Philipe Leal\Downloads\before.tif'

After_image = r'C:\Users\Philipe Leal\Downloads\after.tif'

Arr1 =  gdal_array.LoadFile(Before_image).astype(np.int16)
Arr2 = gdal_array.LoadFile(After_image)[1].astype(np.int16)

diff = Arr2 - Arr1

# Set up our classification scheme to try
# and isolate significant changes by dividing the image into classes according to its histogram
classes = np.histogram(diff, bins=5)[1]

# The color black is repeated to mask insignificant changes (ex: water)
lut = [[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 255, 0],
 [255, 0, 0]]
# Starting value for classification
start = 1
# Set up the output image
rgb = np.zeros((3, diff.shape[0], diff.shape[1], ), np.int8)
# Process all classes and assign colors
for i in range(len(classes)):
    mask = np.logical_and(start <= diff, diff <= classes[i])
    for j in range(len(lut[i])):
        rgb[j] = np.choose(mask, (rgb[j], lut[i][j]))
        start = classes[i]+1
        
# Save the output image
output = gdal_array.SaveArray(rgb, r"C:\Users\Philipe Leal\Downloads\change.tif", format="GTiff", 
                              prototype=After_image)
output = None