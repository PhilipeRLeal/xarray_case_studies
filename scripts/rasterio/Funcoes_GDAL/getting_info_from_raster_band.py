# -*- coding: utf-8 -*-
"""
Created on Fri May 11 11:36:53 2018

@author: Philipe Leal
"""

from osgeo import gdal, ogr, osr
import sys, os
File_path = r'C:\Users\Philipe Leal\Google Drive\estudos_osgeo\fazenda_antonio_.tif'


try:
    src_ds = gdal.Open( File_path )
    print("Dataset aberto corretamente")
except RuntimeError:
    print ('Unable to open INPUT.tif')

    sys.exit(1)

print (src_ds.GetMetadata())



# getting info from raster bands:

for band in range( src_ds.RasterCount ):
    band += 1
    print ("[ GETTING BAND ]: ", band)
    srcband = src_ds.GetRasterBand(band)
    if srcband is None:
        continue

    stats = srcband.GetStatistics( True, True )
    if stats is None:
        continue

    print ("[ STATS ] =  Minimum=%.3f, Maximum=%.3f, Mean=%.3f, StdDev=%.3f" % ( \
                stats[0], stats[1], stats[2], stats[3]))
    
