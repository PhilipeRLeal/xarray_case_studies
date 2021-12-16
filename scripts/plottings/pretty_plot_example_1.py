# -*- coding: utf-8 -*-
"""
Created on Fri Jun  8 18:32:22 2018

@author: Philipe_Leal
"""

from netCDF4 import Dataset
import matplotlib.pyplot as plt
import matplotlib as mpl
import cartopy
import cartopy.crs as ccrs
import numpy as np
from osgeo import gdal, ogr
import cartopy.feature as cfeature
from metpy.plots import ctables
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
from matplotlib import patheffects
import datetime

Shp_path = r'C:\Doutorado\Relatorio_Peixes\ZEEs\ZEE_Antares.shp'
nc_path = r'C:\Doutorado\Relatorio_Peixes\Imagens_PP\RCP45_All_Models_Future_Climate_2055.nc'


Netcdf_ds = Dataset(nc_path)

Lista_vars = list(Netcdf_ds.variables.keys())

Anomaly = Netcdf_ds['anomaly'][:]



Lat = Netcdf_ds['lat'][:]
Lon = Netcdf_ds['lon'][:]

ymin = np.min(Lat)
ymax = np.max(Lat)
xmin = np.min(Lon)
xmax = np.max(Lon)
ncols = np.size(Lon)
nrows= np.size(Lat) 
maskvalue = 1

xres=(xmax-xmin)/float(ncols)
yres=(ymax-ymin)/float(nrows)
geotransform=(xmin,xres,0,ymax,0, -yres)

src_ds = ogr.Open(Shp_path)
src_lyr=src_ds.GetLayer()

dst_ds = gdal.GetDriverByName('MEM').Create('', ncols, nrows, 1 ,gdal.GDT_Byte)
dst_rb = dst_ds.GetRasterBand(1)
dst_rb.Fill(0) #initialise raster with zeros
dst_rb.SetNoDataValue(0)
dst_ds.SetGeoTransform(geotransform)

err = gdal.RasterizeLayer(dst_ds, [maskvalue], src_lyr)
dst_ds.FlushCache()

mask_arr=dst_ds.GetRasterBand(1).ReadAsArray()

Anomaly_mask = np.ma.masked_array(Anomaly, mask= mask_arr)


# Plotando:
proj = ccrs.PlateCarree(central_longitude=0)
cmap = ctables.registry.get_colortable('NWSReflectivityExpanded')

norm = mpl.colors.Normalize(vmin=np.nanmin(Anomaly_mask), vmax=np.nanmax(Anomaly_mask))

fig = plt.figure(figsize=(10, 10))
ax = fig.add_subplot(1, 1, 1, projection=proj)
ax.coastlines(resolution='50m', color='black')
ax.add_feature(cfeature.STATES, linestyle=':', edgecolor='black')
ax.add_feature(cfeature.BORDERS, linewidth=2, edgecolor='black')
#ax.set_extent([-180, 180, -90, 90], cartopy.crs.Geodetic())
ax.coastlines(resolution='50m')
ax.add_feature(cartopy.feature.STATES)
ax.add_feature(cartopy.feature.BORDERS, linewidth=2, edgecolor='black')
ax.gridlines(draw_labels=True)
ax.xlabels_top = ax.ylabels_right = False
ax.xformatter = LONGITUDE_FORMATTER
ax.yformatter = LATITUDE_FORMATTER

timestamp = datetime.datetime.today()

text_time = ax.text(0.89, 1.12, timestamp.strftime('%d/%m/%Y'), verticalalignment='baseline',
                   horizontalalignment='center', transform=ax.transAxes,
                   color='white', fontsize='x-large', weight='bold')

text_unidades = ax.text(1.2, 0.5, str(Netcdf_ds['anomaly'].units), verticalalignment='baseline',
               horizontalalignment='center', transform=ax.transAxes,
               color='black', fontsize='large', weight='bold', rotation=90)

text_experimental = ax.text(0.5, 1.23, 'Anomalia PP',
           horizontalalignment='center', transform=ax.transAxes,
           color='white', fontsize='large', weight='bold')

# Make the text stand out even better using matplotlib's path effects
outline_effect = [patheffects.withStroke(linewidth=2, foreground='black')]
text_time.set_path_effects(outline_effect)

text_experimental.set_path_effects(outline_effect)


proj = ccrs.PlateCarree(central_longitude=180)
cax = ax.imshow(Anomaly_mask, extent = ([-180, 180, -90, 90]),
          cmap=cmap, norm = norm, origin='lower', transform=proj)

plt.colorbar(cax, shrink=0.7)
plt.show()

