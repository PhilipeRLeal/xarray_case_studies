# -*- coding: utf-8 -*-
"""
Created on Fri Jun  1 22:26:23 2018

@author: Philipe_Leal
"""

#importacao de bibliotecas
import numpy as np
from osgeo import gdal
from osgeo import osr

# Definindo parametros da projecao e da geotransformacao a serem utilizados na construcao dos arquivos matriciais:

geotransform = (-82.00, 0.1, 0.0, 80.00, 0.0, -0.01)

#geotransform[0] /* top left x 
#geotransform[1] /* w-e pixel resolution 
#geotransform[2] /* 0 
#geotransform[3] /* top left y 
#geotransform[4] /* 0 
#geotransform[5] /* n-s pixel resolution (negative value) 

projecao = osr.SRS_WKT_WGS84

# definicao dos parametros do arquivo de saida em GTIFF
#notar que o tamanho do arquivo de saida do GTIFF é maior que o somatorios dos aquivos de ENVI somados entre si. Portanto, o metadados do gtiff é mais descritivo do que o do envi.

driver = gdal.GetDriverByName ("GTiff") # nome do formato dos arquivos de saida
xsize = 5000
ysize =6300
nbandas = 1


n = np.random.randn(nbandas, xsize,ysize)

nome_arquivo_saida = r"C:\Users\Philipe Leal\Desktop\Teste\Teste_valores_aleatorios.tif"

# definicoes dos arquivos de saida
File_output = driver.Create(nome_arquivo_saida, xsize, ysize, nbandas, gdal.GDT_Float32)
File_output.SetProjection(projecao)
for i in range(1, nbandas):
    print(i)
    File_output.GetRasterBand(i).WriteArray(n[i-1])

File_output.SetGeoTransform(geotransform)
File_output.FlushCache()
