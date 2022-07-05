from rasterio import features
import numpy as np
from affine import Affine
import xarray as xr
import geopandas as gpd
import glob
from shapely.geometry import Polygon, Point, LinearRing
from shapely import speedups


def get_transform_from_latlon(lat, lon):
    """Input 1D array of lat / lon and output an Affine transformation."""
    lat = np.asarray(lat)
    lon = np.asarray(lon)
    trans = Affine.translation(lon[0], lat[0])
    scale = Affine.scale(lon[1] - lon[0], lat[1] - lat[0])
    return trans * scale


def get_xr_mask(shapes, coords, latitude='latitude', longitude='longitude',
                fill=np.nan, **kwargs):
    """Rasterize a list of (geometry, fill_value) tuples onto the given
    xray coordinates. This only works for 1d latitude and longitude
    arrays.

    usage:
    -----
    1. read shapefile to geopandas.GeoDataFrame
          `states = gpd.read_file(shp_dir+shp_file)`
    2. encode the different shapefiles that capture those lat-lons as different
        numbers i.e. 0.0, 1.0 ... and otherwise np.nan
          `shapes = (zip(states.geometry, range(len(states))))`
    3. Assign this to a new coord in your original xarray.DataArray
          `ds['states'] = rasterize(shapes, ds.coords, longitude='X', latitude='Y')`

    arguments:
    ---------
    : **kwargs (dict): passed to `rasterio.rasterize` function

    attrs:
    -----
    :transform (affine.Affine): how to translate from latlon to ...?
    :raster (numpy.ndarray): use rasterio.features.rasterize fill the values
      outside the .shp file with np.nan
    :spatial_coords (dict): dictionary of {"X":xr.DataArray, "Y":xr.DataArray()}
      with "X", "Y" as keys, and xr.DataArray as values

    returns:
    -------
    :(xr.DataArray): DataArray with `values` of nan for points outside shapefile
      and coords `Y` = latitude, 'X' = longitude.


    """
    transform = get_transform_from_latlon(coords[latitude], coords[longitude])
    out_shape = (len(coords[latitude]), len(coords[longitude]))
    raster = features.rasterize(shapes,
                                out_shape=out_shape,
                                fill=fill, transform=transform,
                                dtype=float, **kwargs)
    spatial_coords = {latitude: coords[latitude], longitude: coords[longitude]}
    return xr.DataArray(raster, coords=spatial_coords, dims=(latitude, longitude))


def xr_rasterize(xr_da, shp_gpd, reducers,
                 longitude='longitude', latitude='latitude'):
    """ Create a new coord for the xr_da indicating whether or not it
         is inside the shapefile

        Creates a new coord - "coord_name" which will have integer values
         used to subset xr_da for plotting / analysis/

        Usage:
        -----
        precip_da = add_shape_coord_from_data_array(precip_da, "awash.shp", "awash")
        awash_da = precip_da.where(precip_da.awash==0, other=np.nan)
    """
    # 1. read in shapefile
    if isinstance(shp_gpd, (gpd.GeoSeries, gpd.GeoDataFrame)):
        pass

    else:
        shp_gpd = gpd.GeoSeries(shp_gpd)

    # 2. create a list of tuples (shapely.geometry, id)

    shapes = [(shape, n+1) for n, shape in enumerate(shp_gpd.geometry)]

    # 3. create a new coord in the xr_da which will be set to the id in `shapes`
    coord_name = "zones"
    xr_da[coord_name] = get_xr_mask(shapes, xr_da.coords,
                                    longitude=longitude, latitude=latitude)

    zonal_stats_df = (xr_da.to_dataframe().groupby(coord_name).agg(reducers)
                      .T.unstack().unstack().to_frame(name='stats'))

    zonal_stats_df.index.names = ['zone', 'agg', 'var']

    return zonal_stats_df


if __name__ == '__main__':

    files = glob.glob(
        r'C:\Users\Philipe Leal\Downloads\temp\Images_WGET\NASAS\*.nc4')

    ds = xr.open_mfdataset(files[:200])

    speedups.disable()
    extremes = Polygon(
        [(-60, -50), (-60, 45), (10, 45), (10, -50), (-60, -50)])
    zones = xr_rasterize(ds,
                         extremes,
                         [np.mean, 'count', np.max, np.min],
                         'lon', 'lat')

    zones

    # Example 2

    import cartopy.feature as cfeature
    states_provinces = cfeature.NaturalEarthFeature(
        category='cultural',
        name='admin_1_states_provinces_lines',
        scale='50m',
        facecolor='none')

    global_zones = xr_rasterize(ds,
                                list(states_provinces.geometries())[:10],
                                [np.mean, 'count', np.max, np.min],
                                'lon', 'lat')

    global_zones
