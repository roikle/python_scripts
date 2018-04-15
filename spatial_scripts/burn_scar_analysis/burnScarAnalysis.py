import sys

try:
    from osgeo import gdal
except:
    sys.exit("Error: can't find required gdal module")

try:
    import numpy
except:
    sys.exit("Error: can't find required numpy module")

class burnScarAnalysis:
    def __init__(self):
        self.outDriver = gdal.GetDriverByName("GTiff")

    def _outputRaster(self, inputArray, outputRaster):
        print("Outputing raster result...")
        outputRaster = self.outDriver.Create(str(outputRaster), self.rows, self.cols, 1, gdal.GDT_Float32)
        
        # write NBRarray to output file
        outputRaster.GetRasterBand(1).WriteArray(inputArray)
        outputRaster.SetGeoTransform(self.geoTransform)
        outputRaster.SetProjection(self.projection)

        # Close output raster
        outputRaster = None

    def _getImgSpecs(self, raster):
        print("Getting Image Specifications ...")
        inputRaster = gdal.Open(raster)
        self.geoTransform = inputRaster.GetGeoTransform()
        self.projection = inputRaster.GetProjection()
        [self.cols,self.rows] = inputRaster.ReadAsArray().shape

        # Close input raster
        inputRaster = None

class nbr(burnScarAnalysis):
    def __init__(self, *args):
        burnScarAnalysis.__init__(self)
        self.redBand = gdal.Open(sys.argv[1])
        self.redBandArray = self.redBand.ReadAsArray()
        self.nirBand = gdal.Open(sys.argv[2])
        self.nirBandArray = self.nirBand.ReadAsArray()
        self.outputRaster = sys.argv[3]
        self.maskValue = -9999
    
    def _closeDatasets(self):
        print("Closing Datasets ...")
        self.redBand = None
        self.nirBand = None

    # Create a mask indicating invalid pixels
    # - Mask out invalid Landsat 8 surface reflectance values (< 0 | > 10000)
    # - Mask out when denominator equals 0
    def _createMask(self):
        print("Creating Mask ...")
        self.mask = numpy.where((self.redBandArray < 0) 
        | (self.nirBandArray < 0) 
        | (self.redBandArray > 10000) 
        | (self.nirBandArray > 10000) 
        | (self.redBandArray + self.nirBandArray == 0), 0, 1)

    # Normalized Burn Ratio 
    # NBR = (Red - NIR)/(Red + NIR)
    def _createNBR(self):
        print("Creating Normalized Burn Ratio ...")
        NBRArray = numpy.choose(self.mask,(self.maskValue, 
        (self.redBandArray - self.nirBandArray)/
        (self.redBandArray + self.nirBandArray)))
        self._outputRaster(NBRArray,self.outputRaster)

preFireNBR = nbr(sys.argv[1], sys.argv[2], sys.argv[3])
preFireNBR._getImgSpecs(sys.argv[1])
preFireNBR._createMask()
preFireNBR._createNBR()
preFireNBR._closeDatasets()
