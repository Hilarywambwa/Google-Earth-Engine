#The Earth Engine Python API comes with a ee.batch module that allows you to launch batch exports and manage tasks.
#The ee.batch.Export function and a Python for-loop iterate over image collection and export each image. 
#The ee.batch module also enables controlling of Tasks and automating exports.
import ee
import geopandas as gpd
ee.Initialize()

geometry = ee.Geometry.Point([107.61303468448624, 12.130969369851766])
s2 = ee.ImageCollection('COPERNICUS/S2_HARMONIZED')
rgbVis = {
  'min': 0.0,
  'max': 3000,
  'bands': ['B4', 'B3', 'B2'],
}

# Write a function for Cloud masking
def maskS2clouds(image):
  qa = image.select('QA60')
  cloudBitMask = 1 << 10
  cirrusBitMask = 1 << 11
  mask = qa.bitwiseAnd(cloudBitMask).eq(0).And(
             qa.bitwiseAnd(cirrusBitMask).eq(0))
  return image.updateMask(mask) \
      .select("B.*") \
      .copyProperties(image, ["system:time_start"])

filtered = s2 \
  .filter(ee.Filter.date('2019-01-01', '2020-01-01')) \
  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30)) \
  .filter(ee.Filter.bounds(geometry)) \
  .map(maskS2clouds)

# Write a function that computes NDVI for an image and adds it as a band
def addNDVI(image):
  ndvi = image.normalizedDifference(['B5', 'B4']).rename('ndvi')
  return image.addBands(ndvi)

withNdvi = filtered.map(addNDVI)

#Obtain and print image IDs
image_ids = withNdvi.aggregate_array('system:index').getInfo()
print('Total images: ', len(image_ids))

# Export with 100m resolution 
for i, image_id in enumerate(image_ids):
  image = ee.Image(withNdvi.filter(ee.Filter.eq('system:index', image_id)).first())
  task = ee.batch.Export.image.toDrive(**{
    'image': image.select('ndvi'),
    'description': 'Image Export {}'.format(i+1),
    'fileNamePrefix': image_id,
    'folder':'earthengine',
    'scale': 100,
    'region': image.geometry(),
    'maxPixels': 1e10
  })
  task.start()
  print('Started Task: ', i+1)
  
#Get a list of tasks and information on them
tasks = ee.batch.Task.list()
for task in tasks:
  task_id = task.status()['id']
  task_state = task.status()['state']
  print(task_id, task_state)
  
 #Cancelling tasks
tasks = ee.batch.Task.list()
for task in tasks:
    task_id = task.status()['id']
    task_state = task.status()['state']
    if task_state == 'RUNNING' or task_state == 'READY':
        task.cancel()
        print('Task {} canceled'.format(task_id))
    else:
        print('Task {} state is {}'.format(task_id, task_state))