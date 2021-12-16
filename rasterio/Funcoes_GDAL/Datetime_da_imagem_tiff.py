# -*- coding: utf-8 -*-
"""
Created on Mon Jun  4 15:35:37 2018

@author: Philipe Leal
"""

def Importando_bibliotecas():
    import os, sys
    import datetime
    import astropy.time
    import dateutil.parser
    module_path = r'C:\Users\Philipe Leal\Dropbox\Profissao\Python\Datetime'
    sys.path.insert(0, module_path)
    
    from JD_to_datetime import jd_to_date
    
    
def retorna_datetime_geotiff(tiff_path):
    Importando_bibliotecas()
      
    Base_name = os.path.basename(tiff_path)
    
    Base_name = Base_name.split(sep='.tif')[0]
    Base_name = Base_name.split(sep='LGN00_')[0]
    
    Year = (Base_name[-7:-3])
    
    
    Year_jd = dateutil.parser.parse(Year)
    Year_jd = astropy.time.Time(Year_jd)

    
    
    Julian_day = (Base_name[-3:])
    
    Date_jd = Year_jd.jd + int(Julian_day)
    
    
    Tiff_datetime = datetime.datetime(*jd_to_date(Date_jd)[0:4])
    
    return Tiff_datetime


def exemplo():
    Importando_bibliotecas()
    
    tiff_path = r'C:\Doutorado\2_Trimestre\Disciplinas\Comportamento Espectral de Alvos\Ponzoni\Imagens_Landsat_8\LC82250722016135LGN00\LC82250722016135LGN00_B1.tif'
    
    Base_name = os.path.basename(tiff_path)
    
    Base_name = Base_name.split(sep='.tif')[0]
    Base_name = Base_name.split(sep='LGN00_')[0]
    
    Year = (Base_name[-7:-3])
    
    
    Year_jd = dateutil.parser.parse(Year)
    Year_jd = astropy.time.Time(Year_jd)
    print("Ano em dia juliano: ", Year_jd.jd)
    
    
    Julian_day = (Base_name[-3:])
    
    Date_jd = Year_jd.jd + int(Julian_day)
    
    
    Tiff_datetime = datetime.datetime(*jd_to_date(Date_jd)[0:4])
    
    print("Data da imagem: ", Tiff_datetime)


