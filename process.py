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


def get_neighborhood_from_kml(results, kml_path):
  test_lat, test_lon = (results['geometry']['location']['lat'],
                        results['geometry']['location']['lng'])
  test_point = Point(float(test_lat), float(test_lon))
  kml = etree.parse(kml_path)
  placemarks = kml.findall('//kml:Placemark', namespaces=NSMAP)
  found_neighborhood = None
  for placemark in placemarks:
    el = placemark.find(COORDINATES, namespaces=NSMAP)
    coords = []
    for coord in el.text.split(' '):
      lat, lon, _ = coord.split(',')
      coords.append((float(lon), float(lat)))
    poly = MultiPoint(coords).convex_hull
    if poly.contains(test_point):
      name = placemark.find('kml:name', namespaces=NSMAP)
      found_neighborhood = name.text
  if found_neighborhood is None:
    return get_neighborhood(results)
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
    if is_csv:
      address = '{}, {}, {} {}'.format(
          row['Primary Street Address'],
          row['Primary City'],
          row['Primary State'],
          row['Primary Zip Code'])
    if is_json:
      address = row.get('Address', row.get(' Address'))
    url = URL + urllib.quote(address)
    resp = urllib.urlopen(url).read()
    data = json.loads(resp)
    results = data['results']
    if not results:
      raise Exception('{}; UNABLE TO GEOCODE'.format(address))
    results = data['results'][0]
    if kml_path:
      neighborhood = get_neighborhood_from_kml(results, kml_path)
      neighborhood = neighborhood.encode('utf-8')
    else:
      neighborhood = get_neighborhood(results)
    print '{}; {}'.format(address, neighborhood)



def main():
  process('austin.json', 'austin.kml')


if __name__ == '__main__':
  main()
