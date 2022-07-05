#!/usr/bin/env python
# coding: utf-8


# Ref:

# https://stackoverflow.com/questions/40342355/how-can-i-generate-a-regular-geographic-grid-using-python


from cartopy.io import shapereader
import shapely
import pyproj
import geopandas as gpd
from time import time
import pandas as pd
import copy
import matplotlib.pyplot as plt


def get_bounds(df: gpd.GeoDataFrame,
               country=str,
               colname='ABBREV') -> tuple:
    """Get Bounds from Geopandas.

    Parameters
    ----------
    df : gpd.GeoDataFrame
        DESCRIPTION.
    country : TYPE, optional
        DESCRIPTION. The default is str.
    colname : TYPE, optional
        DESCRIPTION. The default is 'ABBREV'.

    Returns
    -------
    tuple (ROI,
           Geopandas.GeoSeries)
        ROI = shapely.geometry.box(minx, miny, maxx, maxy)
        Geopandas.GeoSeries

    """
    mask = df[colname].str.contains(country).fillna(False)

    c_df = df[mask]

    minx, miny, maxx, maxy = c_df.geometry.total_bounds

    ROI = shapely.geometry.box(minx, miny, maxx, maxy)

    return ROI, c_df.geometry


def getRoi():
    """Generate a ROI for Brazil.

    Returns
    -------
    ROI : TYPE
        DESCRIPTION.
    geometry : TYPE
        DESCRIPTION.

    """
    # # Fetching some basic data

    # Get geometries
    shpfilename = shapereader.natural_earth(resolution='50m',
                                            category='cultural',
                                            name='admin_0_countries')
    reader = shapereader.Reader(shpfilename)

    Countries = pd.DataFrame()

    for x in reader.records():
        S = pd.Series(x.attributes)
        S['geometry'] = x.geometry

        Countries = Countries.append(S, ignore_index=True)

    Countries = gpd.GeoDataFrame(Countries, crs="EPSG:4326")

    # Determine bounding box
    ROI, geometry = get_bounds(Countries, 'Brazil')

    return ROI, geometry


class RegularGridder():
    def __init__(self,
                 origin_crs,
                 target_crs):
        self._transformer = pyproj.Transformer.from_crs(
            origin_crs, target_crs, always_xy=True)

    @property
    def transformer(self) -> pyproj.Transformer:
        """Retrieve the pyproj.Transformer for reprojecting data coordinates.

        Returns
        -------
        pyproj.Transformer

        """
        return self._transformer

    @transformer.setter
    def transformer(self,
                    transformer: pyproj.Transformer):
        """Reset the pyproj.transformer instance.

        Parameters
        ----------
        pyproj.Transformer
            DESCRIPTION.

        Returns
        -------
        pyproj.Transformer

        """
        if not isinstance(transformer, pyproj.Transformer):
            msg = ("The provided Transformer is not of correct Type. \n" +
                   "\tType expected: {0}; \n\tActual type {1}"
                   )
            raise TypeError(msg.format(pyproj.Transformer,
                                       type(transformer)
                                       )
                            )
        else:
            self._transformer = transformer

            return self._transformer

    def generate_regularGrid(self,
                             xmin,
                             ymin,
                             xmax,
                             ymax,
                             dx=5,  # in target units
                             dy=5,  # in target units
                             return_grid_in_original_crs=False,
                             verbose=False) -> gpd.GeoSeries:
        """Generate a Regular Gridded Surface.

        Parameters
        ----------
        xmin : Float
            DESCRIPTION.
        ymin : Float
            DESCRIPTION.
        xmax : Float
            DESCRIPTION.
        ymax : Float
            DESCRIPTION.
        origin_crs : TYPE
            DESCRIPTION.
        target_crs : TYPE
            DESCRIPTION.
        dx : Float, optional.
            the spacing distance between grid (in target units).
                The default is 5.
        dy : Float, optional.
            the spacing distance between grid (in target units).
                The default is 5.
        return_grid_in_original_crs : Bool, optional
            Boolean parameter that constrols whether the grid should
            be returned in the original crs, or not.
            If True, the grid will be returned in the original crs
            If False (default), the grid will be returned in the target crs.

        verbose : Bool, optional
            DESCRIPTION. The default is False.

        Returns
        -------
        RegularGrid : geopandas.GeoSeries
            the regular grid.
        dt : datetime.timedelta
            The timedelta taken for generating this grid.
        """
        T0 = time()

        RegularGrid = []

        xmin, ymin = self.transformer.transform(xmin, ymin)

        xmax, ymax = self.transformer.transform(xmax, ymax)

        x = copy.copy(xmin) - 2*dx

        while x <= xmax:
            if verbose:
                print(
                    'x <= xmax : {0:.4f} <- {1:.4f}: {2}'.format(x,
                                                                 xmax,
                                                                 x < xmax)
                )
            y = copy.copy(ymin) - 2*dy
            while y <= ymax:
                if verbose:
                    print(
                        'y <= ymax : {0:.4f} <- {1:.4f}: {2}'.format(y,
                                                                     ymax,
                                                                     x < ymax)
                    )

                p = shapely.geometry.box(x, y, x + dx, y + dy)
                RegularGrid.append(p)
                y += dy
            x += dx

        RegularGrid = gpd.GeoSeries(RegularGrid,
                                    crs=self.transformer.target_crs.to_wkt(),
                                    name='geometry')

        if return_grid_in_original_crs:

            RegularGrid = RegularGrid.to_crs(
                self.transformer.source_crs.to_wkt()
            )

        dt = time() - T0
        if verbose:
            print('Serial Time Taken: {0}'.format(dt))

        return RegularGrid, dt


if "__main__" == __name__:

    ROI, GeoSeries = getRoi()

    # Choosing a projected coordinate system
    #     (therefore, in meters for a given ROI)

    T0 = time()
    return_grid_in_original_crs = True
    regGridder = RegularGridder(origin_crs='epsg:4326',
                                target_crs='epsg:5880')

    RegularGrid, dt = regGridder.generate_regularGrid(*ROI.bounds,
                                                      dx=200000,
                                                      dy=200000,
                                                      return_grid_in_original_crs=return_grid_in_original_crs,
                                                      verbose=False)
    import cartopy.crs as ccrs
    from pyproj.crs import CRS
    if return_grid_in_original_crs:
        projection = ccrs.PlateCarree()
        fig, ax = plt.subplots(subplot_kw={"projection": projection})
        GeoSeries = GeoSeries.to_crs(RegularGrid.crs)

        GeoSeries.plot(ax=ax,
                       facecolor='blue', transform=projection)
        RegularGrid.plot(ax=ax, transform=projection,
                         edgecolor='gray',
                         linewidth=0.2,
                         facecolor=(0.5, 0.5, 0.5, 0.2))
        fig.show()
    else:
        projection = None
        fig, ax = plt.subplots()
        GeoSeries = GeoSeries.to_crs(RegularGrid.crs)

        GeoSeries.plot(ax=ax,
                       facecolor='blue')
        RegularGrid.plot(ax=ax,
                         edgecolor='gray',
                         linewidth=0.2,
                         facecolor=(0.5, 0.5, 0.5, 0.2))
        fig.show()

    dt = time() - T0
    print('Time Taken: {0}'.format(dt))
