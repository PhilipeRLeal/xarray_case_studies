# -*- coding: utf-8 -*-
"""
Created on Mon Feb  3 20:09:01 2020

@author: lealp
"""


import ee
ee.Initialize()




class SR_COA_Components():
    
    # Function takes the MERIS_DN band and transforms into CI
    def _transformMERIS (self, img):
        
        ''' convert to CI based on 
          CI = 10.^((double(DN)-10-1)/(250/2.5)-4)
          (itself based on:
            DN =1+(250/2.5)*(4+LOG10(CI))+10
            see Stumpf et al., 2012
          ) 
        '''
        
        img = img.rename('MERIS_DN')
        justCI = img.select('MERIS_DN')
        land = justCI.eq(252)
        clouds = justCI.eq(253)
    
        justCI = justCI.mask(justCI.neq(252)) #mask land
    
        justCI = ee.Image(10).pow(
                                    justCI.double().subtract(10).subtract(1)
                                    .divide(250/2.5)
                                    .subtract(4)
                                  )
    
        #See Stumpf et al. 2012 for thresh of 0.001 ~= 10^5 cells/mL
        justCI=justCI.gte(0.001) 
        justCI = justCI.where(clouds,-0.01/6)
    
        return (img.addBands(justCI.rename('MERIS_CI'))
                 .addBands(land.rename('landmask')))
    
    
    
    #Specifies a threshold for hue to estimate green pixels
    def _calcGreenness(self, img):
        r = img.select(['B3'])
        g = img.select(['B2'])
        b = img.select(['B1'])
        I = r.add(g).add(b).rename(['I'])
        mins = r.min(g).min(b).rename(['mins'])
    
        H = mins.where(mins.eq(r),
        (b.subtract(r)).divide(I.subtract(r.multiply(3))).add(1) )
        H = H.where(mins.eq(g),
        (r.subtract(g)).divide(I.subtract(g.multiply(3))).add(2) )
        H = H.where(mins.eq(b),
        (g.subtract(b)).divide(I.subtract(b.multiply(3))) )
        Hthresh = H.lte(1.6) #threshold of 1.6 fit as described in Ho et al. (2017)
    
        return Hthresh
    
    
    # Implements the TOA algorithms after correcting for clouds
    def _calcAlgorithms(self, img):
        img = self._calcConsACCA(img)
        yesCloud = img.select("cloud")
        
        #add algorithm outputs as bands
        img2 = img.addBands(img.expression("b('B3')/b('B1')").select(["B3"],["RedToBlue"]))
        
        img3 = img2.addBands(img.expression("b('B3')/b('B4')").select(['B3'],['RedToNIR']) )
        img3 = img3.addBands(img.expression("b('B2')/b('B1')").select(['B2'],['GreenToBlue']) )
        img3 = img3.addBands(img.expression("( b('B1')-b('B3') )/b('B2')")
                               .select(['B1'],['BlueMinusRedOverGreen']) )
        
        img3 = img3.addBands(img.select('B4').select(['B4'],['NIR']) )
        img3 = img3.addBands(img.expression("b('B4')-b('B5')").select(['B4'],['NIRwithSAC']) )
    
        img_impnirwithsac = img3.expression("b('B4')-1.03*b('B5')").select(["B4"],["ImprovedNIRwithSAC"]) 
        gness=self._calcGreenness(img3)
        img_impnirwithsac = img_impnirwithsac.where(gness.eq(0),0)
        img3 = img3.addBands(img_impnirwithsac)
    
        img3=img3.addBands(img.expression("b('B4') - b('B3')").select(["B4"],["NIRminusRed"]))
        img3=img3.addBands(img.expression("(b('B4')-b('B5'))/(b('B3')-b('B5'))")
                             .select(["B4"],["NIRoverRedwithSAC"]))
        img3=img3.addBands(img.expression("( b('B4')-" +
                                            "(b('B4')-b('B1'))+(b('B1')-b('B5'))*(850-490)/(1650-490)" +
                                          ") / " + 
                                          "( b('B3')-" +
                                            "(b('B3')-b('B1'))+(b('B1')-b('B5'))*(660-490)/(1650-490)" + 
                                          ")").select(["B4"],["NIRoverRedwithBAC"]) )
        
        img3=img3.addBands(img.expression("(b('B4')-b('B3'))+0.5*(b('B3')-b('B5'))")
                             .select(["B4"],["CurvatureAroundRed"]))
        
        img3 = img3.addBands(img.expression("47.7-9.21*(2.9594+1.6203*b('B3'))/(2.1572+0.9198*b('B1'))+" +
                                           "29.7*(3.5046+0.8950*b('B4'))/(2.1572+0.9198*b('B1'))-" + 
                                           "118*(3.5046+0.8950*b('B4'))/(2.9594+1.6203*b('B3'))-" + 
                                           "6.81*(3.1591+1.0111*b('B5'))/(2.9594+1.6203*b('B3'))+" +
                                           "41.9*(2.8122+1.3984*b('B7'))/(2.9594+1.6203*b('B3'))-" + 
                                           "14.7*(2.8122+1.3984*b('B7'))/(3.5046+0.8950*b('B4'))")
                               .select(['constant'],['PhycocyaninDetection']) )

        
        # mask out clouds
    
        img4=img3.mask(yesCloud.neq(1))
        
        return img4
