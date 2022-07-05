#!/usr/bin/env python
# coding: utf-8


# Ref:

# https://stackoverflow.com/questions/40342355/how-can-i-generate-a-regular-geographic-grid-using-python
from collections import namedtuple
from multiprocessing import Pool
import shapely
import pyproj
import geopandas as gpd
import numpy as np
from time import time
import pandas as pd
import copy
import matplotlib.pyplot as plt
import os

from serial_gridding import getRoi


def splitGrid(xmin,
              ymin,
              xmax,
              ymax,
              nsplits
              ):
    dx = (xmax - xmin)/nsplits
    dy = (ymax - ymin)/nsplits

    XBlocks = np.arange(xmin, xmax + dx, dx).copy()
    XBlocks = [(xmin, xmax) for xmin, xmax in zip(XBlocks[:-1], XBlocks[1:])]
    YBlocks = np.arange(ymin, ymax + dy, dy).copy()
    YBlocks = [(ymin, ymax) for ymin, ymax in zip(YBlocks[:-1], YBlocks[1:])]

    return XBlocks, YBlocks


def generate_regularGrid(xmin: float,
                         ymin: float,
                         xmax: float,
                         ymax: float,
                         origin_crs: str,
                         target_crs: str,
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
        the spacing distance between grid (in target units). The default is 5.
    dy : Float, optional.
        the spacing distance between grid (in target units). The default is 5.
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

    RegularGrid = []

    x = copy.copy(xmin)

    while x < xmax:
        if verbose:
            print(
                'x <= xmax : {0:.4f} <- {1:.4f}: {2}'.format(x,
                                                             xmax,
                                                             x < xmax)
            )
        y = copy.copy(ymin)
        while y < ymax:
            if verbose:
                print(
                    'y <= ymax : {0:.4f} <- {1:.4f}: {2}'.format(y,
                                                                 ymax,
                                                                 y < ymax)
                )

            p = shapely.geometry.box(x, y, x + dx, y + dy)
            RegularGrid.append(p)
            y = copy.copy(y + dy)
        x = copy.copy(x + dx)

    RegularGrid = gpd.GeoSeries(RegularGrid,
                                crs=target_crs,
                                name='geometry')

    if return_grid_in_original_crs:

        RegularGrid = RegularGrid.to_crs(origin_crs)

    return RegularGrid


def solveOverlappingPolygons(geoSeries):
    polygons = geoSeries.geometry
    non_overlapping = list()
    overlappingPolygons = list()
    for n, p in enumerate(polygons[:-1], 1):
        overlappingCases = [p.overlaps(g) for g in polygons[n:]]
        if not any(overlappingCases):
            non_overlapping.append(p)
        else:
            for g in polygons[n:][overlappingCases]:
                p = p.difference(g)
            overlappingPolygons.append(p)

    RegularGrid = gpd.GeoSeries(non_overlapping,
                                crs=geoSeries.crs,
                                name=geoSeries.name)

    overlappingPolygons = gpd.GeoSeries(overlappingPolygons,
                                        crs=geoSeries.crs,
                                        name=geoSeries.name)

    return RegularGrid.append(overlappingPolygons)

def _parallelGridding(listOfBounds,
                      nProcesses=None,
                      origin_crs='epsg:4326',
                      target_crs='epsg:5880',
                      dx=500_000,
                      dy=500_000,
                      return_grid_in_original_crs=True,
                      verbose=False):

    T0 = time()

    iterables = [(xmin, ymin, xmax, ymax,
                  origin_crs,
                  target_crs,
                  dx,
                  dy,
                  return_grid_in_original_crs,
                  verbose) for (xmin, ymin, xmax, ymax) in listOfBounds]

    with Pool(nProcesses) as p:
        Results = p.starmap(generate_regularGrid, iterables)

    geoSeries = pd.concat(Results)

    geoSeries = solveOverlappingPolygons(geoSeries)

    dt = time() - T0
    if verbose:
        print('Parallel Processing Time Taken: {0}'.format(dt))
    return geoSeries, dt


def parallelGridding(roi,
                     nsplits,
                     nProcesses,
                     origin_crs,
                     target_crs,
                     *args,
                     **kwargs
                     ):
    (xmin,
     ymin,
     xmax,
     ymax) = roi.bounds

    Transformer = pyproj.Transformer.from_crs(
        origin_crs, target_crs, always_xy=True)

    xmin, ymin = Transformer.transform(xmin, ymin)

    xmax, ymax = Transformer.transform(xmax, ymax)

    xmin = copy.copy(xmin) - 2 * kwargs.get("dx")
    ymin = copy.copy(ymin) - 2 * kwargs.get("dy")

    XBlocks, YBlocks = splitGrid(xmin, ymin, xmax, ymax, nsplits=nsplits)
    bounds = namedtuple("Bounds", ["xmin","ymin","xmax","ymax"])
    listOfBounds = [bounds(xmin, ymin, xmax, ymax)
                    for (xmin, xmax) in XBlocks for (ymin, ymax)
                    in YBlocks]
    if kwargs.get("verbose", False):
        [print(bounds) for bounds in listOfBounds]

    RegularGrid, dt = _parallelGridding(listOfBounds,
                                        nProcesses,
                                        origin_crs,
                                        target_crs,
                                        *args,
                                        **kwargs)
    return RegularGrid, dt


if __name__ == '__main__':
    T0 = time()
    ROI, GeoSeries = getRoi()
    nProcesses = os.cpu_count()-2
    print("Using {0} Cores".format(nProcesses))
    verbose = False
    RegularGrid, dt = parallelGridding(ROI,
                                       nsplits=nProcesses,
                                       nProcesses=nProcesses,
                                       origin_crs='epsg:4326',
                                       target_crs='epsg:5880',
                                       dx=200000,
                                       dy=200000,
                                       return_grid_in_original_crs=False,
                                       verbose=verbose)

    GeoSeries = GeoSeries.to_crs(RegularGrid.crs)
    ax = GeoSeries.plot(facecolor='blue')

    RegularGrid.plot(ax=ax,
                     edgecolor='gray',
                     linewidth=0.2,
                     facecolor=(0.5, 0.5, 0.5, 0.2))
    plt.show()

    dt = time() - T0
    print('Total Time Taken: {0}'.format(dt))