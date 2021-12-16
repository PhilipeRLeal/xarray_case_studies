
import numpy as np


class DewPoint():
    def __init__(self):
        pass
    
    @classmethod
    def get_dewpoint_from_McNOLDY(cls, T, RH):
        '''
        
        Formula from:
            http://bmcnoldy.rsmas.miami.edu/humidity_conversions.pdf
        
        Author info:
            BRIAN McNOLDY
            SENIOR RESEARCH ASSOCIATE
            • • •
            UNIVERSITY of MIAMI
            ROSENSTIEL SCHOOL of MARINE & ATMOSPHERIC SCIENCE
            
        Constants:
            a = 17.625
            b = 243.04
            T is in ºC
            Td is in ºC
            RH is in %
    
        Return dewpoint (float) (kelvin)
        
        '''
        a = 17.625
        b = 243.04
        
        
        numerator = (b * np.log( (RH/100) + (a*T/(b + T))))
        
        denominator =  (a - np.log(RH/100) - (a*T/(b + T)))
        
        
        Td = numerator /denominator
        
        return Td + 273.15
    
    
    @classmethod
    def get_dewpoint_from_SMPEFC(cls, T, e, es):
             
        '''
        
        Formula from:
            Science Math Physics Engineering And Finance Calculators
            https://www.ajdesigner.com/phphumidity/relative_humidity_equation.php
            
        Parameters:
                
            e: actual vapor pressure (pascal)
            
            es: saturated vapor pressure (pascal)
            
        Return dewpoint (float)
        '''
        f = 100*(e/es)
       
        
        Td = (f/100)**(1/8) * (112 + 0.9*T) + .1*T -112
        
        
        return Td 
    
if '__main__' == __name__:
    
    print( DewPoint.get_dewpoint_from_McNOLDY(30, 50)  )
    # 288.7K

             
    print( DewPoint.get_dewpoint_from_SMPEFC(300, 50, 100))