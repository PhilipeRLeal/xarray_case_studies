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
    
# selecao de uma banda:
    
srcband = src_ds.GetRasterBand(1)

# importando dataset de shapefiles:

dst_layer = ogr.Open(os.path.join(os.path.dirname(File_path), "poligonos.shp"))

# poligonização do raster:
if os.path.exists(os.path.join(os.path.dirname(File_path), "poligonos.shp")):
    driver = ogr.GetDriverByName('ESRI Shapefile')
    driver.DeleteDataSource(os.path.join(os.path.dirname(File_path), "poligonos.shp"))
dst_ds = None

prj = src_ds.GetProjection()
targetSR = osr.SpatialReference(wkt=prj)
targetSR.ImportFromWkt(src_ds.GetProjectionRef()) 

dst_layername = os.path.join(os.path.dirname(File_path), "poligonized_stuff.shp")
driver = ogr.GetDriverByName('ESRI Shapefile')
dst_ds = driver.CreateDataSource(dst_layername)
dst_layer = dst_ds.CreateLayer(dst_layername, geom_type=ogr.wkbPolygon, srs = targetSR )



# Remove output shapefile if it already exists

    
gdal.Polygonize(srcband, None, dst_layer, -1, [], callback=None )
    
dst_ds = None
targetSR = None
targetSR = None

# importando raster vetorizado:

Poligonized_ds = driver.Open(dst_layername, 0) # 0= read only

# importando vetor linha:


Line_path = r'C:\Users\Philipe Leal\Google Drive\estudos_osgeo\linha.shp'

Linha_ds = driver.Open(Line_path, 0) # 0= read only

Layer_lin = Linha_ds.GetLayer(Linha_ds.GetLayerCount()-1)
Feature_lin = Layer_lin.GetFeature(0)
Lin_geometry = Feature_lin.GetGeometryRef()

# get layer:
Layer_poly = Poligonized_ds.GetLayer(Poligonized_ds.GetLayerCount()-1)

Feature = Layer_poly.GetFeature(0)
Geom_poli = Feature.GetGeometryRef()

Geom_poli.Intersects(Lin_geometry)

### -----------------

if os.path.exists(os.path.join(os.path.dirname(File_path), "SomeFilename.shp")):
    driver = ogr.GetDriverByName('ESRI Shapefile')
    driver.DeleteDataSource(os.path.join(os.path.dirname(File_path), "SomeFilename.shp"))


dst_ds = None
dstshp = None
dstshp = driver.CreateDataSource(r'C:\Users\Philipe Leal\Google Drive\estudos_osgeo\SomeFilename.shp')
dstlayer = dstshp.CreateLayer('mylayer',geom_type=ogr.wkbPolygon)
Poly_id_Field = ogr.FieldDefn("poly_id", ogr.OFTInteger)
Line_id_Field = ogr.FieldDefn("line_id", ogr.OFTInteger)

dstlayer.CreateField(Poly_id_Field)
dstlayer.CreateField(Line_id_Field)
Area = {}
Lista_geom_poli_com_interseccao = []
n=0
y = 0

for i in range(0, Layer_poly.GetFeatureCount()):
    feature = Layer_poly.GetFeature(i)
    geom1 = feature.GetGeometryRef()
    Area[i] = geom1.Area()

   
    for j in range(0, Layer_lin.GetFeatureCount()):
        feature_lin = Layer_lin.GetFeature(j)
        geom2 = feature_lin.GetGeometryRef()

   # select only the intersections
        if geom1.Intersects(geom2) or geom1.Crosses(geom2) or geom1.Touches(geom2): 
            print("geom2 intersepta ou cruza ou toca geom1")
            Lista_geom_poli_com_interseccao.append([i,j])
            y+=1
            
    
          
            dstfeature = ogr.Feature(dstlayer.GetLayerDefn())
            dstfeature.SetGeometry(geom1)
            dstfeature.SetField("poly_id", i)
    
            
            dstfeature.SetField("line_id", j)
            dstlayer.CreateFeature(dstfeature)
        else:
            n = n+1
            

    
    print("n: ", n)  
    print("y: ", y) 
    
    dstfeature = ogr.Feature(dstlayer.GetLayerDefn())
    dstfeature.Destroy() 

for J in Lista_geom_poli_com_interseccao:   
    print("Os vetores (poligono e linha (respectivamente) com contato entre si são: {0}, {1}".format(J[0], J[1]))         
        
    
        
          
dstshp = None        
dstlayer = None      
          
          
          