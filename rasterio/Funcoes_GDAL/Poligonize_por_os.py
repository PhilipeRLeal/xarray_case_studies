# -*- coding: utf-8 -*-
"""
Created on Sat May 26 11:15:21 2018

@author: Philipe_Leal
"""

# Licao em:  "http://www.gdal.org/gdal_polygonize.html"

import os
from osgeo import gdal, osr, ogr
import numpy as np

            
File_path = r'C:\Doutorado\3_Trimestre\Analise_Espacial\Enner_Milton\OLI_8\LO82210752017285CUB00_B2.tif'
band = "1"
ogr_format = 'ESRI Shapefile'
Destination_folder = r"C:\Users\Philipe Leal\Desktop\Teste"
os.mkdir(Destination_folder)
layer = str(os.path.basename(File_path).split(sep='.')[0]) + ".shp"
fieldname = "Attr"

# """gdal_polygonize.py [-8] [-nomask] [-mask filename] raster_file [-b band]
#                [-q] [-f ogr_format] out_file [layer] [fieldname]"""


os.system("gdal_polygonize [-4] [-nomask] [-mask filename]" + File_path + " [-b " + band +"] \
          [-f " + ogr_format + "] " + Destination_folder + " ["+layer+"] ["+fieldname+"]")
                
    
# -8: (GDAL >= 1.10) Use 8 connectedness. Default is 4 connectedness.
# -nomask: Do not use the default validity mask for the input band (such as nodata, or alpha masks).
# -mask filename: use the first band of the specified file as a validity mask (zero is invalid, non-zero is valid). If not specified, the default validity mask for the input band (such as nodata, or alpha masks) will be used (unless -nomask is specified)
# -b band: numero da banda a ser usada para poligonizacao: ex: [-b 1]
# -f ogr_format: ex: -f gtiff
# out_file: caminho do shapefile a ser criado
#layer: nome do layer para conter as feições (polígonos)
# fieldname: nome do atributo a ser criado no layer. Por padrão é "DN"
# -q: quiet mode ( não mostra o desenvolvimento do processamento)

src_ds = gdal.Open( File_path )
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