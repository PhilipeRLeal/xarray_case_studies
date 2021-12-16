# -*- coding: utf-8 -*-
"""
Created on Mon Jun 25 15:02:46 2018

@author: Philipe Leal
"""

# conversão de UTM em Lat Long

import utm
y = 479747.0453210057
x = 5377685.825323031
zone = 32
band = 'U'
print(utm.to_latlon(y, x, zone, band))

utm.from_latlon(-12.512, -34.475, force_zone_number=23)
