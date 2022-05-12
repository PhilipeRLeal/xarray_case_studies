
"""
Created on Wed May  4 08:36:08 2022

@author: ziongh
"""


from gdal import Dataset, InfoOptions
from osgeo import gdal
import xarray as xr
import numpy as np
from reprojection import reproject
import os


def read_data(filename):

    dataset = gdal.Open(filename)

    if not isinstance(dataset, Dataset):
        raise FileNotFoundError("Impossible to open the netcdf file")

    return dataset


def generate_netcdf(filename):

    ds = xr.tutorial.load_dataset("air_temperature")

    ds["NewVariable"] = ds["air"] * 2 + 1

    ds.to_netcdf(filename)


def readInfo(ds, infoFormat="json"):
    "how to: https://gdal.org/python/"

    info = gdal.Info(ds,
                     options=InfoOptions(format=infoFormat,
                                         reportProj4=True,
                                         allMetadata=False,
                                         ),
                     )

    return info


def listAllSubDataSets(infoDict: dict):

    metadata = infoDict["metadata"]

    if metadata.get("SUBDATASETS"):

        subDatasetVariableKeys = [x for x in metadata["SUBDATASETS"].keys()
                                  if "_NAME" in x]

        subDatasetVariableNames = [metadata["SUBDATASETS"][x]
                                   for x in subDatasetVariableKeys]

        bandNames = []

        for x in subDatasetVariableNames:

            s = x.replace('"', '').split(":")[-1]
            s = ''.join(s)
            bandNames.append(s)

        return bandNames

    else:
        bandNames = []
        namesWithinBanditem = ['NETCDF_VARNAME',  "name",
                               "bandname", "BandName", "band_name",
                               "short_name"]

        for band in infoDict["bands"]:
            metadatas = list(band['metadata'].values())
            for metadata in metadatas:
                notPass = False
                for keyname in namesWithinBanditem:
                    if keyname in metadata:
                        if not notPass:
                            name = metadata[keyname]
                            bandNames.append(name)
                            notPass = True
                        else:
                            pass

        if bandNames:
            return bandNames
        else:
            return None


if "__main__" == __name__:

    filename1 = r".\GIS_study_cases\data_examples\remote_sensing_dataset\GOES\S10635333_201704251845.nc"
    filename2 = r".\GIS_study_cases\data_examples\remote_sensing_dataset\xarrayExample\test.nc"
    generate_netcdf(filename2)

    filenames = [filename1, filename2]

    for filename in filenames:

        dirname, fname = os.path.split(filename)
        fname, extention = os.path.splitext(fname)

        print("Reading: ", filename)
        ds = read_data(filename)

        infoDict = readInfo(ds)

        netcdfVariableNames = listAllSubDataSets(infoDict)
        if netcdfVariableNames == None:
            netcdfVariableNames = [filename]

        # Desired extent
        # Min lon, Max lon, Min lat, Max lat
        extent = [-64.0, -35.0, -35.0, -15.0]

        filenamesToReproject = []

        for varname in netcdfVariableNames:
            reprojectedFileName = os.path.join(dirname,
                                               fname +
                                               "_reprojected" + extention
                                               )
            print("Saving file in : \n\t", reprojectedFileName)
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

        reproject(reprojectedFileName,
                  filenamesToReproject,
                  array=None,
                  extent=extent,  # [Minlon, Maxlon, Minlat, Maxlat]
                  undef=np.nan,
                  warpOptions=["multi", "overwrite"])
