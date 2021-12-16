import xarray as xr
import numpy as np


def prepare_xdata(ds, spatial_coords=['lon', 'lat']):
    
    for c, coef in zip(spatial_coords, [180, 360]):

        ds.coords[c] = (ds.coords[c] + coef) % (coef*2) - coef

    dims = list(ds.dims)
    ds = ds.sortby(list(ds.dims))
    
    return ds


def get_min_max_coords(coords):
    
    return np.array([coords.min(), coords.max()])

def regrid(xres, yres, data_array, xcoord='lon', ycoord='lat'):
    
    xmin, xmax = get_min_max_coords(data_array.coords[xcoord])
    ymin, ymax = get_min_max_coords(data_array.coords[ycoord])
    
    xbins = np.arange(xmin-xres/2, xmax + xres/2, xres)
    ybins = np.arange(ymin - ymin/2, ymax + ymin/2, yres)
    
    y = data_array.coords['lat'].values.ravel()
    x = data_array.coords['lon'].values.ravel()
    # Bin the data onto a 10x10 grid
    # Have to reverse x & y due to row-first indexing
    zi, yi, xi = np.histogram2d(x, y, bins=[xbins,ybins], weights=data_array.values.flatten(), normed=False)
    counts, _, _ = np.histogram2d(x, y, bins=[xbins,ybins])
    
    counts = np.where(np.isclose(counts, np.array([0])), np.nan, counts)
    zi = np.where(np.isclose(zi, np.array([0])), np.nan, zi)
    
    zi = zi / counts
    #zi = np.ma.masked_invalid(zi)
    
    yshape = yi.size -1
    xshape = xi.size -1
    
    return xr.DataArray(zi.reshape( (yshape,
                                     xshape
                                    )), 
                        
                        coords={'lon':yi[:-1],
                                'lat':xi[:-1]}, 
                        
                        dims=['lon', 'lat'],
                       name=data_array.name)

def interpolate_temporal_dataset(ds, xres, yres , spatial_coords=['lon', 'lat'], time_dim='time'):

    ds = prepare_xdata(ds, spatial_coords=spatial_coords)

    interp_dataArrays = []

    for i in ds.data_vars:
        
        das = []


        for idx, group in ds[i].groupby(time_dim):


            da = regrid(xres=xres, yres=yres, data_array=group)
            da = da.assign_coords({time_dim:idx})

            das.append(da)


        interp_dataArray = xr.concat(das, dim=time_dim)
        
        interp_dataArrays.append(interp_dataArray)
        
    interp_dataSet = xr.merge(interp_dataArrays)


    return interp_dataSet

def interpolate_non_temporal_dataset(ds, xres, yres , spatial_coords=['lon', 'lat']):
    
    ds = prepare_xdata(ds, spatial_coords=spatial_coords)
    
    das = []
    for i in ds.data_vars:
        
        
        da = ds[i]
        da = regrid(xres=xres, yres=yres, data_array=da)

        das.append(da)

    interp_dataSet_non_temporal = xr.merge(das)

    
    return interp_dataSet_non_temporal



if '__main__' == __name__:

    interpolate_temporal_dataset(ds, xres, yres , spatial_coords=['lon', 'lat'], time_dim='time')