
from Py6S import *
import datetime
import math
import os
import sys
import matplotlib.pyplot as plt
sys.path.append(os.path.join(os.path.dirname(os.getcwd()),'bin'))
from atmospheric import Atmospheric
import numpy as np

import ee
ee.Initialize()

from utils import partial_functions


class Atmospheric_Corr(partial_functions):
    def __init__(self, 
                 image, 
                 toa,
                 geom=ee.Geometry.Point(-157.816222, 21.297481), 
                 date=ee.Date('2017-01-01')):
        
        if toa== None:
            print('Assuming that TOA is image.divide(10000)')
            toa = image.divide(10000)
            
        super(Atmospheric_Corr, self).__init__(image, toa, geom, date)
        
    def correct_all_bands(self, quality_band='QA60'):
        
        bands = self.image.bandNames().getInfo()
        output = self.image.select(bands[0])
        
        for band in bands[1:]:
            
            if 'qa' not in band.lower():
                try:
                    new_band = self._surface_reflectance(band)
                    print('Band {0} has been corrected'.format(band))
                    
                except:
                    print('Band {0} had not its atmospheric corrected'.format(band))
                    new_band = self.image.select(band)
                    
                output = output.addBands(new_band)
                
                # Adding the last quality band, plus some metadata:    
                output = output.set('solar_azimuth',
                                    self.image.get('MEAN_SOLAR_AZIMUTH_ANGLE'))\
                               .set('solar_zenith',
                                    self.image.get('MEAN_SOLAR_ZENITH_ANGLE'))
                               
        self.Image_ATM_Corrected = output
        return output
        
if '__main__' == __name__:
    
    date = ee.Date('2017-01-01')
    geom = ee.Geometry.Point(-157.816222, 21.297481)
    region = ee.Geometry.Polygon([[-30, 20], [0, 20],[0, -30], [-30, -30], [-30, 20]])
    
    # The first Sentinel 2 image
    S2 = ee.Image(
      ee.ImageCollection('COPERNICUS/S2')
        .filterBounds(geom)
        .filterDate(date,date.advance(3,'month'))
        .sort('system:time_start')
        .first()
      )
    
    # top of atmosphere reflectance
    toa = S2.divide(10000)
    
    AT = Atmospheric_Corr(S2, toa, geom, date)
    
    AT.correct_all_bands()

    