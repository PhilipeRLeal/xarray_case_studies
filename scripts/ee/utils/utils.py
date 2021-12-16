
from Py6S import *

import math

import ee
ee.Initialize()


class partial_functions():
    def __init__(self, 
                 image, 
                 toa,
                 geom=ee.Geometry.Point(-157.816222, 21.297481), 
                 date=ee.Date('2017-01-01')):
        
        self.meta_initializer(image, geom=geom, date=date)
        
        self.image = image
        
        self.toa = toa
    
    def meta_initializer(self, image, geom, date):
    
        SRTM = ee.Image('CGIAR/SRTM90_V4')# Shuttle Radar Topography mission covers *most* of the Earth
        
        self.alt = SRTM.reduceRegion(reducer = ee.Reducer.mean(), geometry = geom.centroid()).get('elevation').getInfo()
        self.km = self.alt/1000 # i.e. Py6S uses units of kilometers
        # Meta:
        
        self.info = image.getInfo()['properties']
        
        
        # i.e. Python uses seconds, EE uses milliseconds
        
        self.scene_date = datetime.datetime.utcfromtimestamp(self.info['system:time_start']/1000)
        
        
        self.solar_z = self.info['MEAN_SOLAR_ZENITH_ANGLE']
        
        self.h2o = Atmospheric.water(geom, date).getInfo()
        self.o3 = Atmospheric.ozone(geom,date).getInfo()
        self.aot = Atmospheric.aerosol(geom,date).getInfo()
        
        
        # Instantiate
        s = SixS()
        
        # Atmospheric constituents
        s.atmos_profile = AtmosProfile.UserWaterAndOzone(self.h2o,self.o3)
        s.aero_profile = AeroProfile.Continental
        s.aot550 = self.aot
        
        # Earth-Sun-satellite geometry
        s.geometry = Geometry.User()
        s.geometry.view_z = 0               # always NADIR (I think..)
        s.geometry.solar_z = self.solar_z        # solar zenith angle
        s.geometry.month = self.scene_date.month # month and day used for Earth-Sun distance
        s.geometry.day = self.scene_date.day     # month and day used for Earth-Sun distance
        s.altitudes.set_sensor_satellite_level()
        s.altitudes.set_target_custom_altitude(self.km)
        
        
        # setting attributes for class' instance:
        self.s = s
        
        
    
    
    def _spectralResponseFunction(self, bandname):
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
            'B8A':PredefinedWavelengths.S2A_MSI_09,
            'B9':PredefinedWavelengths.S2A_MSI_10,
            'B10':PredefinedWavelengths.S2A_MSI_11,
            'B11':PredefinedWavelengths.S2A_MSI_12,
            'B12':PredefinedWavelengths.S2A_MSI_13,
            }
        
        return Wavelength(bandSelect[bandname])
    
    
    def _toa_to_rad(self, bandname):
        """
        Converts top of atmosphere reflectance to at-sensor radiance
        """
        
        # solar exoatmospheric spectral irradiance
        ESUN = self.info['SOLAR_IRRADIANCE_'+bandname]
        solar_angle_correction = math.cos(math.radians(self.solar_z))
        
        # Earth-Sun distance (from day of year)
        doy = self.scene_date.timetuple().tm_yday
        d = 1 - 0.01672 * math.cos(0.9856 * (doy-4))# http://physics.stackexchange.com/questions/177949/earth-sun-distance-on-a-given-day-of-the-year
       
        # conversion factor
        multiplier = ESUN*solar_angle_correction/(math.pi*d**2)
    
        # at-sensor radiance
        rad = self.toa.select(bandname).multiply(multiplier)
        
        return rad
    
    
    def _surface_reflectance(self, bandname):
        """
        Calculate surface reflectance from at-sensor radiance given waveband name
        """
        
        # run 6S for this waveband
        self.s.wavelength = self._spectralResponseFunction(bandname)
        self.s.run()
        
        # extract 6S outputs
        Edir = self.s.outputs.direct_solar_irradiance             #direct solar irradiance
        Edif = self.s.outputs.diffuse_solar_irradiance            #diffuse solar irradiance
        Lp   = self.s.outputs.atmospheric_intrinsic_radiance      #path radiance
        absorb  = self.s.outputs.trans['global_gas'].upward       #absorption transmissivity
        scatter = self.s.outputs.trans['total_scattering'].upward #scattering transmissivity
        tau2 = absorb*scatter                                #total transmissivity
        
        # radiance to surface reflectance
        rad = self._toa_to_rad(bandname)
        ref = rad.subtract(Lp).multiply(math.pi).divide(tau2*(Edir+Edif))
        
        return ref
    
    
    def _rescale(self, img, thresholds):
        """
        Linear stretch of image between two threshold values.
        """
        return img.subtract(thresholds[0]).divide(thresholds[1] - thresholds[0])
    
    
    def _sentinelCloudScore(self, img):
        """
        Computes spectral indices of cloudyness and take the minimum of them.
        
        Each spectral index is fairly lenient because the group minimum 
        is a somewhat stringent comparison policy. side note -> this seems like a job for machine learning :)
        
        originally written by Matt Hancher for Landsat imagery
        adapted to Sentinel by Chris Hewig and Ian Housman
        """
        
        # cloud until proven otherwise
        score = ee.Image(1)
    
        # clouds are reasonably bright
        score = score.min(self._rescale(img.select(['B2']), [0.1, 0.5]))
        score = score.min(self._rescale(img.select(['B1']), [0.1, 0.3]))
        score = score.min(self._rescale(img.select(['B1']).add(img.select(['B10'])), [0.15, 0.2]))
        score = score.min(self._rescale(img.select(['B4']).add(img.select(['B3'])).add(img.select('B2')), [0.2, 0.8]))
    
        # clouds are moist
        ndmi = img.normalizedDifference(['B8A','B11'])
        score=score.min(self._rescale(ndmi, [-0.1, 0.1]))
    
        # clouds are not snow.
        ndsi = img.normalizedDifference(['B3', 'B11'])
        score=score.min(self._rescale(ndsi, [0.8, 0.6])).rename(['cloudScore'])
        
        return img.addBands(score)
    
    
    def _ESAcloudMask(self, img):
        """
        European Space Agency (ESA) clouds from 'QA60', i.e. Quality Assessment band at 60m
         
        parsed by Nick Clinton
        """
    
        qa = img.select('QA60')
    
        # bits 10 and 11 are clouds and cirrus
        cloudBitMask = int(2**10)
        cirrusBitMask = int(2**11)
    
        # both flags set to zero indicates clear conditions.
        clear = qa.bitwiseAnd(cloudBitMask).eq(0).And(\
               qa.bitwiseAnd(cirrusBitMask).eq(0))
        
        # clouds is not clear
        cloud = clear.Not().rename(['ESA_clouds'])
    
        # return the masked and scaled data.
        return img.addBands(cloud)  
    
    
    def _shadowMask(self, img, cloudMaskType):
        """
        Finds cloud shadows in images
        
        Originally by Gennadii Donchyts, adapted by Ian Housman
        """
        
        img = self.img
        
        def potentialShadow(self, cloudHeight):
            """
            Finds potential shadow areas from array of cloud heights
            
            returns an image stack (i.e. list of images) 
            """
            cloudHeight = ee.Number(cloudHeight)
            
            # shadow vector length
            shadowVector = zenith.tan().multiply(cloudHeight)
            
            # x and y components of shadow vector length
            x = azimuth.cos().multiply(shadowVector).divide(nominalScale).round()
            y = azimuth.sin().multiply(shadowVector).divide(nominalScale).round()
            
            # affine translation of clouds
            cloudShift = cloudMask.changeProj(cloudMask.projection(), cloudMask.projection().translate(x, y)) # could incorporate shadow stretch?
            
            return cloudShift
      
        # select a cloud mask
        cloudMask = img.select(cloudMaskType)
        
        # make sure it is binary (i.e. apply threshold to cloud score)
        cloudScoreThreshold = 0.5
        cloudMask = cloudMask.gt(cloudScoreThreshold)
    
        # solar geometry (radians)
        azimuth = ee.Number(img.get('solar_azimuth')).multiply(math.pi).divide(180.0).add(ee.Number(0.5).multiply(math.pi))
        zenith  = ee.Number(0.5).multiply(math.pi ).subtract(ee.Number(img.get('solar_zenith')).multiply(math.pi).divide(180.0))
    
        # find potential shadow areas based on cloud and solar geometry
        nominalScale = cloudMask.projection().nominalScale()
        cloudHeights = ee.List.sequence(500,4000,500)        
        potentialShadowStack = cloudHeights.map(potentialShadow)
        potentialShadow = ee.ImageCollection.fromImages(potentialShadowStack).max()
    
        # shadows are not clouds
        potentialShadow = potentialShadow.And(cloudMask.Not())
    
        # (modified) dark pixel detection 
        darkPixels = self.toa.normalizedDifference(['B3', 'B12']).gt(0.25)
    
        # shadows are dark
        shadows = potentialShadow.And(darkPixels).rename(['shadows'])
        
        # might be scope for one last check here. Dark surfaces (e.g. water, basalt, etc.) cause shadow commission errors.
        # perhaps using a NDWI (e.g. green and nir)
    
        return img.addBands(shadows)
    
    
    # Implements the Automatic Cloud Cover Assessment, with some changes
    # http:#landsathandbook.gsfc.nasa.gov/pdfs/ACCA_SPIE_paper.pdf
    def _calcConsACCA(self, img):
        ''' Do not implement Pass Two here for simplicity, hence these
        estimates are conservative (i.e., all ambiguous  is cloud) '''
        
        f1 = img.select('B3').lt(0.08) # B3 below 0.08 is non-cloud
        f2 = img.normalizedDifference(['B2','B5']).gt(0.7) # (B2-B5)/(B2+B5) above 0.7 is non-cloud
        f3 = img.select('B6').gt(300) # B6 above this is non-cloud
    
        clouds = (f1.Or(f2).Or(f3)).Not()
        
        return img.addBands(clouds.rename('cloud'))
    
    