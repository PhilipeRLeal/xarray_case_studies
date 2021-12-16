# -*- coding: utf-8 -*-
"""
Created on Mon Jun 25 11:05:16 2018

@author: Philipe Leal
"""

from osgeo import gdal, gdal_array
import gdalnumeric
try:
    import numpy
except:
    import Numeric as numpy

Tif_path = r'C:\Users\Philipe Leal\Downloads\before.tif'

class_defs = [(1, 10, 20),
              (2, 20, 30),
              (3, 128, 255)]

src_ds = gdal.Open(Tif_path)
xsize = src_ds.RasterXSize
ysize = src_ds.RasterYSize

src_image = gdalnumeric.LoadFile( Tif_path)


dst_image = numpy.zeros((ysize,xsize))

mask = numpy.zeros_like(src_image)

for class_info in class_defs:
    class_id = class_info[0]
    class_start = class_info[1]
    class_end = class_info[2]

    class_value = numpy.ones((ysize,xsize)) * class_id

    mask = numpy.bitwise_and(
        numpy.greater_equal(src_image,class_start),
        numpy.less_equal(src_image,class_end))

    print(mask)
    dst_image = numpy.choose( mask, (dst_image,class_value) )

# usando gdalnumeric:
    # obs: não há inserção de projeção neste método
gdalnumeric.SaveArray( dst_image, r'C:\Users\Philipe Leal\Downloads\classes.tif' )


# usando gdal_array:
    # ele copia os metadados do arquivo de origem:
output = gdal_array.SaveArray(dst_image, r'C:\Users\Philipe Leal\Downloads\classes.tif', format="GTiff", 
                              prototype=src_ds)
output = None