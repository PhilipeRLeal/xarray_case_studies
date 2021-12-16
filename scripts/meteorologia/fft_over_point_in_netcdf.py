# -*- coding: utf-8 -*-
"""
Created on Tue Nov 19 13:39:54 2019

@author: lealp
"""

import pandas as pd
pd.set_option('display.width', 50000)
pd.set_option('display.max_rows', 50000)
pd.set_option('display.max_columns', 5000)


import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy
import matplotlib
import seaborn as sn
import warnings


import xarray as xr
import numpy as np


import scipy.fftpack


def fftPlot(sig, dim='time'):
    # here it's assumes analytic signal (real signal...)- so only half of the axis is required
    
    dt = 1 / sig[dim].size

    t = np.arange(0, sig.size) * dt
    
    if dim=='time':
    
        sampling_unit = get_frequency_from_xarray(sig)
        
        xlabel = 'Frequency [1/{0} time units]'.format(sampling_unit)
    else        :
        xlabel = 'Frequency [1/sampling units]'
        
    

    if sig.shape[0] % 2 != 0:
        warnings.warn("signal prefered to be even in size, autoFixing it...")
        t = t[0:-1]
        sig = sig[0:-1]

    sigFFT = np.fft.fft(sig) / t.shape[0]  # divided by size t for coherent magnitude

    freq = np.fft.fftfreq(t.shape[0], d=dt)

    # plot analytic signal - right half of freq axis needed only...
    firstNegInd = np.argmax(freq < 0)
    freqAxisPos = freq[0:firstNegInd]
    sigFFTPos = 2 * sigFFT[0:firstNegInd]  # *2 because of magnitude of analytic signal

    fig = plt.figure()
    plt.plot(freqAxisPos, np.abs(sigFFTPos))
    plt.xlabel(xlabel)
    plt.ylabel('mag')
    plt.title('Analytic FFT plot')
    fig.show()

    return fig


def fftPlot2(y, dim='time'):
    
    # distance between samples in that given dimension
    
    dt = 1 / y[dim].size
    
    freqs = np.fft.fftfreq(y.size, d=dt)
    
    # mask array to be used in the power spectra (only real part is required)
    # since the complex conjugate is the inverse of the real part
    
    mask = freqs>0
    
    # FFT and power spectra calculation
    fft_vals = np.fft.fft(y)
    
    # true theoretical fft
    
    fft_theo = 2*np.abs(fft_vals/y.size)
    
    fig, axs = plt.subplots(1,2)
    
    
    y.plot(ax=axs[0], color='salmon', label='original signal')
    
    
    axs[1].plot(freqs[mask], fft_theo[mask], label='true fft values')
    
    axs[1].set_ylabel('Amplitude')
    
    if dim=='time':
    
        sampling_unit = get_frequency_from_xarray(y)
        
        xlabel = 'Frequency [1/{0} time units]'.format(sampling_unit)
    else        :
        xlabel = 'Frequency [1/sampling units]'
        
    
    axs[1].set_xlabel(xlabel)
    
    fig.legend()
    
    fig.suptitle('FTT values')
    
    fig.show()
    
    return fig


def fftPlot3(sig, dim='time'):
    time_step = 1
    from scipy import fftpack
    sample_freq = fftpack.fftfreq(sig.size, d=time_step)
    sig_fft = fftpack.fft(sig)
    
    #Pelo fato de a energia resultante ser simétrica, 
    #apenas a parte positiva do espectro deve ser usada
    #para encontrar a frequência:
    
    pidxs = np.where(sample_freq > 0)
    freqs = sample_freq[pidxs]
    power = 2*np.abs(sig_fft/sig.size)[pidxs]
    f = plt.figure()
    plt.plot(freqs * sig.size, power)
    
    if dim=='time':
    
        sampling_unit = get_frequency_from_xarray(sig)
        
        xlabel = 'Frequency [1/{0} time units]'.format(sampling_unit)
    else        :
        xlabel = 'Frequency [1/sampling units]'
        
    plt.xlabel(xlabel)
    plt.ylabel('Amplitude')
    
    
    f.show()
    return f

def get_frequency_from_xarray(darray, dim='time'):
    
    freq_times = {'Y', 'M', 'D', 'h', 'm', 's', 'ms', 'ns'}
    
    
    T = darray[dim].diff(dim).values
    
    
    
    for freq in freq_times:
    
        unit = T.astype('timedelta64[{0}]'.format(freq)).max().astype(int)
        if unit == 1:
            major_freq= freq
            
            return major_freq
            
            
            

def main(x):
    
    
    fig = fftPlot(x, dim='time')
    
    
    fig2 = fftPlot2(x)
    
    fig3 = fftPlot3(x)
    
    

    

if '__main__' == __name__:
    
        
    ds = xr.tutorial.open_dataset('rasm').load()
    
    def parse_datetime(time):
        return pd.to_datetime([str(x) for x in time])
    
    ds.coords['time'] = parse_datetime(ds.coords['time'].values)
    
    ds = ds.fillna(0)
    
    P = ds['Tair'].sel({'x':195, 'y':12})
    
    main(P)
    
    
    
    filename = r'F:\Philipe\Doutorado\DADOS_CHIRPS\Por_Ano\*.nc'
    
    
    ncin = xr.open_mfdataset(filename, 
                             concat_dim='time', 
                             combine='nested',
                             chunks=dict(latitude=1000, longitude=1000))
    
    
    ncin.coords['time'] = parse_datetime(ncin.coords['time'].values)
    
    
    P2 = ncin['precip'].sel({'longitude':-46, 'latitude':-2}, method='nearest')
    
    P2 = P2.resample(time='M').sum('time')
    
    main(P2)