# -*- coding: utf-8 -*-
"""
Created on Mon Nov 11 15:55:49 2019

@author: lealp
"""

import pandas as pd
pd.set_option('display.width', 50000)
pd.set_option('display.max_rows', 50000)
pd.set_option('display.max_columns', 5000)


import numpy as np

from extreme_events.extreme_classifier import Extreme_Classifier as EEC
from scipy.optimize import brute, fmin


def find_best_pdf_given_bins(bins, 
                             y, 
                             distribution_type='Positive', 
                             verbose=False, 
                             b=False):
    
    
    EE = EEC(distribution_type=distribution_type, 
             bins_for_PDF=bins,
             verbose=verbose)
        
    EE.fit(y)
    
    
    SSE = float(EE.get_params()['best sse'])
    
    print('SSE {0} for bin {1}'.format(SSE, bins))
    
    return SSE
    

def optimize_bins(y, 
                  lower_lim_for_bins=4,
                  distribution_type='Positive', 
                   
                  b=False, 
                  verbose=True):
    
    upper_lim = int(np.sqrt(y.size))
    lower_lim= lower_lim_for_bins
    
    if upper_lim == lower_lim:
        upper_lim +=3
    
    bin_ranges = (slice(lower_lim, upper_lim, 1),)
    
    print('ranging bins: ', bin_ranges)
    
    args = (y, distribution_type,
              verbose, b)
    
    
    global_min = brute(find_best_pdf_given_bins, 
                                      bin_ranges, 
                                      disp=True, 
                                      workers=-1,
                                      args=args,
                                      finish=fmin, 
                                      full_output=True)
    
    print('best brute bins function finished')
    
    print('n° bins: ', global_min)
    
    return global_min[0]
    
def brute_optimized_best_pdf_fitting(y, 
                                     distribution_type='Positive', 
                                     b=False, 
                                     verbose=True):
        
    best_n_bins =  optimize_bins(y, 
                                 distribution_type=distribution_type, 
                                 b=b, 
                                 verbose=verbose)
    
    
    EE = EEC(distribution_type=distribution_type, 
             bins_for_PDF=best_n_bins,
             verbose=verbose)
 
    EE.fit(y)
    
    Classified = EE.predict(y, b)
    
    print(Classified.categories)
    
    return Classified

if '__main__' == __name__:
    
    y = np.random.randn(300)
    
    distribution_type='Positive'
    b=False
    verbose=True
    
    Classified = brute_optimized_best_pdf_fitting(y, 
                                                  distribution_type, 
                                                  b=b, 
                                                  verbose=verbose)
    
    print(Classified)