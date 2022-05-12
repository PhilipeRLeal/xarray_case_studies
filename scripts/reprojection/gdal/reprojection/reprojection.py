
from gdal import Dataset
from osgeo import gdal
from osgeo import osr
import os
import numpy as np


def reproject(toFileName: str,
              ncfile: Dataset,
              array: np.ndarray,
              extent: list,  # [Minlon, Maxlon, Minlat, Maxlat]
              undef=np.nan,
              target_prj4="+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs",
              **kwargs) -> None:
    """
    Description:
        This function is a wrapper of the gdal.reproject method.

    Parameters:
        file_name (str): the filename that will be used to save the reprojected image

        ncfile (gdal.Dataset or list of strings):
            if gdal.Dataset:
                the gdal.Dataset object that will be reprojected.

            else if list of strings:
                the list of filenames that will be reprojected
                into the same extention, resolution and projection.


        array (np.ndarray): the gdal.Dataset that was written into memory by means of the "ReadAsArray" method.
            Only applicable if ther ncfile is *ncfile* is a *gdal.Dataset* object.
            Else: leave it as None

            example: ncfile.ReadAsArray(0, 0, img.RasterXSize, img.RasterYSize).astype(float)

        extent (list): a list containing the respective [Minlon, Maxlon, Minlat, Maxlat] of the image to reproject.

        undef: the Nan value to be used. By default, it is the np.nan

        target_prj4: the PROJ4 string of the targeted projection.

        kwargs: extra kwargs that are provided to the gdal.Warp


    Returns None


    Usage Example:


        # Variable
        variableName == "air":

        # Open the file
        img = gdal.Open(f'NETCDF:{input}/{file_name}.nc:' + variableName)

        # Data Quality Flag (DQF)
        dqf = gdal.Open(f'NETCDF:{input}/{file_name}.nc:DQF')

        # Read the header metadata
        metadata = img.GetMetadata()
        scale = float(metadata.get(var + '#scale_factor'))
        offset = float(metadata.get(var + '#add_offset'))
        undef = float(metadata.get(var + '#_FillValue'))
        dtime = metadata.get('NC_GLOBAL#time_coverage_start')

        # Load the data
        ds = img.ReadAsArray(0, 0,
                             img.RasterXSize,
                             img.RasterYSize).astype(float)

        ds_dqf = dqf.ReadAsArray(0, 0,
                                 dqf.RasterXSize,
                                 dqf.RasterYSize).astype(float)

        # Apply the scale, offset and convert to celsius
        ds = (ds * scale + offset) - 273.15

        # Apply NaN's where the quality flag is greater than 1
        ds[ds_dqf > 1] = np.nan

        # Tofilename = f'{output}/{file_name}_ret.nc'

        # Reproject the file

        reproject(Tofilename, img, ds, extent, undef)


    """

    # Read the original file projection and configure the output projection

    target_prj = osr.SpatialReference()
    target_prj.ImportFromProj4(target_prj4)

    WarpKwargs = {'format': 'netCDF',
                  'dstSRS': target_prj,
                  'outputBounds': (extent[0], extent[3], extent[2], extent[1]),
                  'outputBoundsSRS': target_prj,
                  'outputType': gdal.GDT_Float32,
                  'srcNodata': undef,
                  'dstNodata': 'nan',
                  'resampleAlg': gdal.GRA_NearestNeighbour}

    WarpKwargs.update(kwargs)

    # Reproject the data
    if isinstance(ncfile, Dataset):

        try:
            source_prj = osr.SpatialReference()
            source_prj.ImportFromProj4(ncfile.GetProjectionRef())
        except Exception as e:
            raise Exception("Unable to retrieve the projection from" +
                            " the netcdf file" + " \n"*2 + str(e))

        GeoT = ncfile.GetGeoTransform()
        driver = gdal.GetDriverByName('MEM')
        raw = driver.Create(
            'raw', array.shape[0], array.shape[1], 1, gdal.GDT_Float32)
        raw.SetGeoTransform(GeoT)
        raw.GetRasterBand(1).WriteArray(array)

        # Define the parameters of the output file

        WarpKwargs['srcSRS'] = source_prj

        try:
            # Write the reprojected file on disk
            gdal.Warp(toFileName, raw, **WarpKwargs)

        except Exception as e:
            raise Exception("Unable to reproject the netcdf file" +
                            "\n" + str(e))

    elif isinstance(ncfile, list):
        if not all([isinstance(x, str) for x in ncfile]):
            raise TypeError("ncfile must be a list of strings")

        else:

            try:
                # Write the reprojected file on disk
                gdal.Warp(toFileName, ncfile, **WarpKwargs)

            except Exception as e:
                raise Exception("Unable to reproject the netcdf file" +
                                "\n" + str(e))
