import ee
ee.Initialize()
s2 = ee.ImageCollection('COPERNICUS/S2_HARMONIZED')
geometry = ee.Geometry.Polygon([[
  [82.60642647743225, 27.16350437805251],
  [82.60984897613525, 27.1618529901377],
  [82.61088967323303, 27.163695288375266],
  [82.60757446289062, 27.16517483230927]
]])

filtered = s2 \
    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30))\
    .filter(ee.Filter.date('2019-02-01', '2019-03-01'))\
    .filter(ee.Filter.bounds(geometry))

#Cloud masking
def maskS2clouds(image):
  qa = image.select('QA60')
  cloudBitMask = 1 << 10
  cirrusBitMask = 1 << 11
  mask = qa.bitwiseAnd(cloudBitMask).eq(0).And(
             qa.bitwiseAnd(cirrusBitMask).eq(0))
  return image.updateMask(mask) \
      .select("B.*") \
      .copyProperties(image, ["system:time_start"])
      
#NDVI function
def addNDVI(image):
    ndvi = image.normalizedDifference(['B8','B4']).rename('ndvi')
    return image.addBands(ndvi)
#addNDVI
withNDVI = filtered \
        .map(maskS2clouds) \
        .map(addNDVI)
        
#Named arguments to Earth Engine functions need to be in quotes.
#When passing the named arguments as a dictionary, it needs to be passed using the ** keyword.
composite = withNDVI.median()
ndvi = composite.select('ndvi')

stats = ndvi.reduceRegion(**{
  'reducer': ee.Reducer.mean(),
  'geometry': geometry,
  'scale': 10,
  'maxPixels': 1e10
  })
print(stats.get('ndvi').getInfo())