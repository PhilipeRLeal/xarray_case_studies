# -*- coding: utf-8 -*-

# Import modules
import ee 
from Py6S import *
import datetime
import math
import os
import sys
sys.path.append(os.path.join(os.path.dirname(os.getcwd()),'bin'))
from atmospheric import Atmospheric 

# Initialize Earth Engine
ee.Initialize()

# Spectral Response functions
def spectralResponseFunction(bandname):
    """
    Extract spectral response function for given band name
    """
    bandSelect = {
        'B1':PredefinedWavelengths.S2A_MSI_01,
        'B2':PredefinedWavelengths.S2A_MSI_02,
        'B3':PredefinedWavelengths.S2A_MSI_03,
        'B4':PredefinedWavelengths.S2A_MSI_04,
        'B5':PredefinedWavelengths.S2A_MSI_05,
        'B6':PredefinedWavelengths.S2A_MSI_06,
        'B7':PredefinedWavelengths.S2A_MSI_07,
        'B8':PredefinedWavelengths.S2A_MSI_08,
        'B8A':PredefinedWavelengths.S2A_MSI_8A,
        'B9':PredefinedWavelengths.S2A_MSI_09,
        'B10':PredefinedWavelengths.S2A_MSI_10,
        'B11':PredefinedWavelengths.S2A_MSI_11,
        'B12':PredefinedWavelengths.S2A_MSI_12,
        }

    return Wavelength(bandSelect[bandname])

# TOA Reflectance to Radiance
def toa_to_rad(bandname, solar_z, scene_date, toa, info):
    """
    Converts top of atmosphere reflectance to at-sensor radiance
    """
    
    # solar exoatmospheric spectral irradiance
    ESUN = info['SOLAR_IRRADIANCE_'+bandname]
    solar_angle_correction = math.cos(math.radians(solar_z))

    # Earth-Sun distance (from day of year)
    doy = scene_date.timetuple().tm_yday
    d = 1 - 0.01672 * math.cos(0.9856 * (doy-4))
    # http://physics.stackexchange.com/
    # questions/177949/earth-sun-distance-on-a-given-day-of-the-year

    # conversion factor
    multiplier = ESUN*solar_angle_correction/(math.pi*d**2)

    # at-sensor radiance
    rad = toa.select(bandname).multiply(multiplier)

    return rad

# Radiance to Surface Reflectance
def surface_reflectance(bandname, solar_z, scene_date, toa, info, s):
    """
    Calculate surface reflectance from at-sensor radiance given waveband name
    """
    
    # run 6S for this waveband
    s.wavelength = spectralResponseFunction(bandname)
    # execute 6S objects
    s.run()

    # extract 6S outputs
    Edir = s.outputs.direct_solar_irradiance         # irradiancia solar directa
    Edif = s.outputs.diffuse_solar_irradiance        # irradiancia solar difusa
    Lp   = s.outputs.atmospheric_intrinsic_radiance  # path radiance
    absorb  = s.outputs.trans['global_gas'].upward   # absorption transmissivity
    scatter = s.outputs.trans['total_scattering']\
        .upward                                      # scattering transmissivity
    tau2 = absorb*scatter                            # total transmissivity

    # Note: s.outputs are calculated starting from 6S objects defined in `conversion` function

    # radiance to surface reflectance
    rad = toa_to_rad(bandname, solar_z, scene_date, toa, info)
    ref = rad.subtract(Lp).multiply(math.pi).divide(tau2*(Edir+Edif))

  
    return ref


# Main function
def main_conversion(img, geom, region, s):

    # write image date
    date = img.date()

    # top of atmosphere reflectance
    toa = img.divide(10000)

    # METADATA
    info = img.getInfo()['properties']
    scene_date = datetime.datetime\
        .utcfromtimestamp(info['system:time_start']/1000)
    solar_z = info['MEAN_SOLAR_ZENITH_ANGLE']

    # ATMOSPHERIC CONSTITUENTS
    h2o = Atmospheric.water(geom,date).getInfo()
    o3 = Atmospheric.ozone(geom,date).getInfo()
    # Atmospheric Optical Thickness
    aot = Atmospheric.aerosol(geom,date).getInfo()

    # TARGET ALTITUDE (km)
    SRTM = ee.Image('CGIAR/SRTM90_V4')
    alt = SRTM.reduceRegion(reducer = ee.Reducer.mean(),
        geometry = geom.centroid()).get('elevation').getInfo()
    km = alt/1000 # i.e. Py6S uses units of kilometers
    
    

    # Atmospheric constituents
    s.atmos_profile = AtmosProfile.UserWaterAndOzone(h2o,o3)
    s.aero_profile = AeroProfile.Continental
    s.aot550 = aot

    # Earth-Sun-satellite geometry
    s.geometry = Geometry.User()
    s.geometry.view_z = 0               # cálculo asumiendo vision en NADIR
    s.geometry.solar_z = solar_z        # ángulo cenital solar
    s.geometry.month = scene_date.month # mes usado en la distancia Earth-Sun
    s.geometry.day = scene_date.day     # día usado en la distancia Earth-Sun
    s.altitudes\
        .set_sensor_satellite_level()   # Altitud del sensor
    s.altitudes\
        .set_target_custom_altitude(km) # Altitud de la superficie

    # ATMOSPHERIC CORRECTION (by waveband)
    output = img.select('QA60')
    
    band_list = ['B2','B3','B4','B5','B6','B7','B8','B8A','B11','B12']
    
    for band in band_list:
        print(band)
        output = output.addBands(surface_reflectance(band, solar_z, scene_date, toa, info, s))
         
    # set some properties for export
    dateString = scene_date.strftime("%Y-%m-%d")
    ref = output.set({'satellite':'Sentinel 2',
                      'fileID':info['system:index'],
                      'date':dateString,
                      'aerosol_optical_thickness':aot,
                      'water_vapour':h2o,
                      'ozone':o3})

    # define YOUR assetID 
    assetID = 'users/6s_test/S2SR_'+dateString

    # export
    export = ee.batch.Export.image.toAsset(\
         image=ref,
         description='sentinel2_atmcorr_export',
         assetId = assetID,
         region = region,
         crs = 'EPSG:4326',
         scale = 20)

   
    export.start()
    # print a message for each exported image
    
    print("image "+assetID+" exported")
    
    return None

# End of main function
if '__main__' == __name__:

    # 6S OBJECT
    # Instantiate
    s = SixS()    

    # study area
    geom = ee.Geometry.Polygon([[-0.9570796519011493,40.98197275411647],
                                [-0.5670650034636493,40.98197275411647],
                                [-0.5670650034636493,41.45919658393617],
                                [-0.9570796519011493,41.45919658393617],
                                [-0.9570796519011493,40.98197275411647]
                                ])

    # uncomment if ee.Geometry.Polygon doesn't work
    # geom = ee.Geometry.Rectangle(-0.996, 41.508, -0.568, 40.992)

    region = geom.buffer(1000).bounds().getInfo()['coordinates']




    # Filter the Sentinel 2 collection
    S2 = (ee.ImageCollection('COPERNICUS/S2')
                            .filterBounds(geom)
                            .filterDate('2015-10-01','2017-04-30')
                            .filterMetadata('MGRS_TILE', 'equals', '30TXL')
                            .filterMetadata('CLOUDY_PIXEL_PERCENTAGE', 'less_than', 20)
                            .sort('system:time_start')
                            .distinct('system:time_start')
          )

    # List with images to filter
    features = S2.getInfo()['features']
    
    print('N° of Features: ',len(features)) 
    
    # Automatic correction
    for i in features:
        id = i['id']
        main_conversion(ee.Image(id), geom, region, s)

    # End of code