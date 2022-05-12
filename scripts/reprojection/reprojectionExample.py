
"""
Created on Wed May  4 08:36:08 2022

@author: ziongh
"""


from gdal import Dataset, InfoOptions
from osgeo import gdal
import xarray as xr
import numpy as np


def read_data(filename):

    dataset = gdal.Open(filename)

    if not isinstance(dataset, Dataset):
        raise FileNotFoundError("Impossible to open the netcdf file")

    return dataset


def readInfo(ds, infoFormat="json"):
    "how to: https://gdal.org/python/"

    info = gdal.Info(ds, options=InfoOptions(format=infoFormat))

    return info


def listAllSubDataSets(infoDict: dict):

    subDatasetVariableKeys = [x for x in infoDict["metadata"]["SUBDATASETS"].keys()
                              if "_NAME" in x]

    subDatasetVariableNames = [infoDict["metadata"]["SUBDATASETS"][x]
                               for x in subDatasetVariableKeys]

    formatedsubDatasetVariableNames = []

    for x in subDatasetVariableNames:

        s = x.replace('"', '').split(":")[-1]
        s = ''.join(s)
        formatedsubDatasetVariableNames.append(s)

    return formatedsubDatasetVariableNames


if "__main__" == __name__:

    filename = r"D:\Projetos\INPE\Processamento_de_Imagens_usando_Python\data\GOES\S10635333_201704251845.nc"

    ds = xr.tutorial.load_dataset("air_temperature")

    ds["NewVariable"] = ds["air"] * 2 + 1
    filename = "test.nc"
    ds.to_netcdf(filename)

    ds = read_data(filename)

    infoDict = readInfo(ds)

    netcdfVariableNames = listAllSubDataSets(infoDict)

    from reprojection import reproject

    # Desired extent
    extent = [-64.0, -35.0, -35.0, -15.0]  # Min lon, Max lon, Min lat, Max lat

    filenamesToReproject = []
    reprojectedFileNameToSave = filename.split(
        ".nc")[0] + "_reprojected.nc"

    for varname in netcdfVariableNames:
        from_filename = "NETCDF:" + filename + ':' + varname

        filenamesToReproject.append(from_filename)

        # # Open the file
        # ncfile = gdal.Open(from_filename)
        # metadata = ncfile.GetMetadata()
        # undef = float(metadata.get(varname + '#_FillValue', 'nan'))

        # ImageArray = ncfile.ReadAsArray(0, 0,
        #                                 ncfile.RasterXSize,
        #                                 ncfile.RasterYSize).astype(float)

        # ImageArray = np.where(ImageArray == undef, np.nan, ImageArray)

    reproject(reprojectedFileNameToSave,
              filenamesToReproject,
              array=None,
              extent=extent,  # [Minlon, Maxlon, Minlat, Maxlat]
              undef=np.nan,
              warpOptions=["multi", "overwrite"])
