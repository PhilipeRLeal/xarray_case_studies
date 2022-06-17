# -*- coding: utf-8 -*-
"""
Created on Thu Jun 16 18:55:36 2022

@author: ziongh
"""


from parallel_gridding import parallelGridding
from serial_gridding import generate_regularGrid, getRoi
import pandas as pd
import matplotlib.pyplot as plt
import os


def speedupEvaluate():
    ROI, GeoSeries = getRoi()
    kwargs = dict(origin_crs='epsg:4326',
                  target_crs='epsg:5880',
                  return_grid_in_original_crs=True,
                  verbose=False
                  )

    speedUps = {}

    for gridsize in range(50_000, 200_000, 50_000):
        kwargs["dx"] = gridsize
        kwargs["dy"] = gridsize
        speedUpPerCore = {}
        Result, serial_dt = generate_regularGrid(*ROI.bounds, **kwargs)
        print("Serial Gridding for gridize={0} DONE".format(gridsize))
        del Result
        for ncores in range(2, os.cpu_count()+1, 1):
            RegularGrid, paralel_dt = parallelGridding(ROI,
                                                       nsplits=4,
                                                       nProcesses=ncores,
                                                       **kwargs)
            print("Parallel Gridding for " +
                  "gridize={0} with {1} cores DONE".format(gridsize,
                                                           ncores)
                  )
            print()
            del RegularGrid

            speedUp = serial_dt/paralel_dt
            speedUpPerCore[ncores] = speedUp

        speedUps[gridsize] = speedUpPerCore

    speedUps = pd.DataFrame(speedUps)

    return speedUps


if __name__ == '__main__':
    speedUps = speedupEvaluate()
    ax = speedUps.plot()
    ax.set_ylabel("Speedup")
    ax.set_xlabel("GridSize (in meters)")
    plt.show()
