from lxml import etree
from shapely.geometry import Point
from shapely.geometry import Polygon
from shapely.geometry import MultiPoint
import csv
import json
import urllib

KEY = 'AIzaSyCoY05WH-mI8y3_NDUcwEzvjznLR1YAInQ'
URL = 'https://maps.googleapis.com/maps/api/geocode/json?key={}&address='.format(KEY)
NSMAP = {'kml': 'http://www.opengis.net/kml/2.2'}
COORDINATES = 'kml:Polygon/kml:outerBoundaryIs/kml:LinearRing/kml:coordinates'
COORDINATES_2 = 'kml:MultiGeometry/kml:Polygon/kml:outerBoundaryIs/kml:LinearRing/kml:coordinates'


MARKETS_TO_KMLS = {
    'Atlanta': 'atlanta.kml',
    'Charlotte': 'charlotte.kml',
    'Nashville': 'nashville.kml',
    'Raleigh-Durham': 'rdu.kml',
    'Salt Lake City': 'slc.kml',
}


def get_neighborhood_from_kml(lat_lon, kml_path):
  test_lat, test_lon = lat_lon
  test_point = Point(float(test_lat), float(test_lon))
  kml = etree.parse(kml_path)
  placemarks = kml.findall('//kml:Placemark', namespaces=NSMAP)
  found_neighborhood = None
  for el in kml.findall('.//kml:coordinates', namespaces=NSMAP):
    coords = []
    for coord in el.text.split(' '):
      lat, lon, _ = coord.split(',')
      coords.append((float(lon), float(lat)))
    poly = MultiPoint(coords).convex_hull
    if poly.contains(test_point):
      placemark = el.getparent().getparent().getparent().getparent()
      if 'MultiGeometry' in str(placemark.tag):
        placemark = placemark.getparent()
      val = placemark.find('kml:ExtendedData/kml:Data[@name=\'32CitiesNa\']/kml:value', namespaces=NSMAP)
      if val is not None:
        found_neighborhood = val.text
  return found_neighborhood


def get_neighborhood(results):
  for component in results['address_components']:
    for type in component['types']:
      if 'neighborhood' in type:
        return '{} (API)'.format(component['long_name'])
    for type in component['types']:
      if 'locality' in type:
        return '{} (API, Locality)'.format(component['long_name'])


def process(path, kml_path=None):
  is_csv = False
  is_json = False
  if path.endswith('.csv'):
    is_csv = True
    rows = csv.DictReader(open(path))
  elif path.endswith('.json'):
    is_json = True
    rows = json.load(open(path))
  for row in rows:
    lat_lon = (row['Latitude'], row['Longitude'])
    kml_path = MARKETS_TO_KMLS[row['Market']]
    if 'rdu' not in kml_path:
#    if 'atlanta' not in kml_path and 'rdu' not in kml_path:
      continue
    neighborhood = get_neighborhood_from_kml(lat_lon, kml_path)
    address = row['Property Address']
    print '{} -> {}'.format(address, neighborhood)



def main():
  process('idol.csv')


if __name__ == '__main__':
  main()
