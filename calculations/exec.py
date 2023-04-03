import requests
import json
from config import OPEN_ROUTE_SERVICE_API_KEY

payload = {}
headers = {}


def city_geocoding(city: str) -> dict:
    city_geocode_url = f'https://api.openrouteservice.org/geocode/search?api_key={OPEN_ROUTE_SERVICE_API_KEY}&text={city}'
    response = requests.request("GET", city_geocode_url, headers=headers, data=payload)
    # with open('./calculations/path_data/openrouteserviceCity.json', 'w') as outfile:
    #     outfile.write(response.text)
    # with open('./calculations/path_data/openrouteserviceCity.json') as json_file:
    #     all_data = json.load(json_file)
    coords = json.loads(response.text)['features'][0]['geometry']['coordinates']
    coordinates = {'lat': coords[1], 'lon': coords[0]}  # в openrouteservice сначала lon, затем lat
    return coordinates

def build_route(lat_from, lon_from, lat_to, lon_to):
    # lat_from = from_coords['lat']
    # lon_from = from_coords['lon']
    # lat_to = to_coords['lat']
    # lon_to = to_coords['lon']
    path_url = f'https://api.openrouteservice.org/v2/directions/driving-car?api_key={OPEN_ROUTE_SERVICE_API_KEY}&start={lon_from},{lat_from}&end={lon_to},{lat_to}'
    response = requests.request("GET", path_url, headers=headers, data=payload)
    with open('./calculations/path_data/openrouteserviceVORONEZHSURGUT.json', 'w') as outfile:
        outfile.write(response.text)
    # with open('./calculations/path_data/openrouteservice.json') as json_file:
    #     all_data = json.load(json_file)
    all_data = json.loads(response.text)
    features = all_data['features']
    segments = features[0]['properties']['segments']
    coordinates = features[0]['geometry']['coordinates']
    print(len(coordinates))
    total_route_length = segments[0]['distance']  # meters
    total_route_time = segments[0]['duration']  # seconds
    steps = segments[0]['steps']
    print(len(steps))

#
#
# start_lat, start_lon = 55.755864, 37.617698
# city_lat, city_lon = 53.195878, 50.100202
#
# path = f'https://api.openrouteservice.org/v2/directions/driving-car?api_key={OPEN_ROUTE_SERVICE_API_KEY}&start={start_lon},{start_lat}&end={city_lon},{city_lat}'
# response = requests.request("GET", path, headers=headers, data=payload)
# with open('path_data/openrouteservice.path_data', 'w') as outfile:
#     outfile.write(response.text)
