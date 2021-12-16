
import xarray as xr



def rebuild_dataarray(arr, xcoor, ycoor, xdim, ydim):
    
    return xr.DataArray(arr.T, 
                        coords={ydim:ycoor,
                                xdim:xcoor},
                        dims=[ydim,
                              xdim])