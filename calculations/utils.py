import requests
import json
from config import YANDEX_API, OPEN_ROUTE_SERVICE_API_KEY, YANDEX_SEARCH_ORGANIZATION_API
from models.point import Point

payload = {}
headers = {}


# def openrouteservice_city_geocoding(city: str) -> dict:
#     city_geocode_url = f'https://api.openrouteservice.org/geocode/search?api_key={OPEN_ROUTE_SERVICE_API_KEY}&text={city}'
#     response = requests.request("GET", city_geocode_url, headers=headers, data=payload)
#     with open('./calculations/path_data/openrouteservice_city.json', 'w') as outfile:
#         outfile.write(response.text)
#     # with open('./calculations/path_data/openrouteserviceCity.json') as json_file:
#     #     all_data = json.load(json_file)
#     all_data = json.loads(response.text)
#     coords = all_data['features'][0]['geometry']['coordinates']
#     coordinates = {'lat': coords[1], 'lon': coords[0]}  # в openrouteservice сначала lon, затем lat
#     return coordinates

def yandex_city_geocoding(city: str) -> dict:
    CITY_GEOCODE_URL = f'https://geocode-maps.yandex.ru/1.x/?apikey={YANDEX_API}&geocode={city}&format=json'
    response = requests.request("GET", CITY_GEOCODE_URL, headers=headers, data=payload)
    with open('./calculations/path_data/city_geocoding.json', 'w') as outfile:
        outfile.write(response.text)
    all_data = json.loads(response.text)
    coords = str(all_data['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['Point']['pos']).split()
    lon, lat = coords
    coordinates = {'lat': lat, 'lon': lon}  # в openrouteservice сначала lon, затем lat
    return coordinates


def yandex_reverse_geocoding(lon: float, lat: float):
    REVERSE_GEOCODE_URL = f'https://geocode-maps.yandex.ru/1.x/?apikey={YANDEX_API}&geocode={lon},{lat}&format=json'
    response = requests.request("GET", REVERSE_GEOCODE_URL, headers=headers, data=payload)
    print(response)
    with open('./calculations/path_data/reverse_geocoding.json', 'w') as outfile:
        outfile.write(response.text)
    all_data = json.loads(response.text)
    text = str(all_data['response']['GeoObjectCollection']['featureMember'][0]
                 ['GeoObject']['metaDataProperty']['GeocoderMetaData']['text'])
    return text

def time_from_text_to_seconds(time: str):
    words = time.split()
    time_in_seconds = 0
    try:
        if len(words) == 2:  # 4 часа; 5 часов; 42 минуты; 50 минут
            if words[1] == 'часа' or words[1] == 'часов':
                time_in_seconds = int(words[0]) * 3600
            elif words[1] == 'минуты' or words[1] == 'минут':
                time_in_seconds = int(words[0]) * 60
        elif len(words) == 4:  # 4 часа 5 минут; 5 часов 42 минуты и тд
            time_in_seconds = int(words[0]) * 3600 + int(words[2]) * 60
    except:
        raise Exception("Пожалуйста, введите данные в верном формате")
    finally:
        return time_in_seconds


def build_route(lat_from, lon_from, lat_to, lon_to):
    path_url = f'https://api.openrouteservice.org/v2/directions/driving-car?api_key={OPEN_ROUTE_SERVICE_API_KEY}&start={lon_from},{lat_from}&end={lon_to},{lat_to}'
    response = requests.request("GET", path_url, headers=headers, data=payload)
    with open('./calculations/path_data/route.json', 'w') as outfile:
        outfile.write(response.text)
    all_data = json.loads(response.text)
    features = all_data['features']
    segments = features[0]['properties']['segments']
    coordinates = features[0]['geometry']['coordinates']
    # print(len(coordinates))
    total_route_length = segments[0]['distance']  # meters
    total_route_duration = segments[0]['duration']  # seconds
    steps = segments[0]['steps']
    # print(len(steps))
    # print(type(steps))
    route_data = {'length': total_route_length, 'duration': total_route_duration, 'steps': steps,
                  'coordinates': coordinates}
    return route_data


def find_coordinates_by_time(time: int, route_data) -> []:  # возвращает координаты, где примерно будет пользователь через время time
    cur_time = 0
    path_steps = route_data['steps']
    path_coords = route_data['coordinates']
    coordinates = dict({'lat': None, 'lon': None})
    for step in path_steps:
        if time > cur_time:
            dif = time - cur_time
            if dif < 300:
                lon, lat = path_coords[step['way_points'][-1]]
                coordinates = dict({'lat': lat, 'lon': lon})
                print('one')
                break
            elif step['duration'] > time - cur_time:
                step_duration = step['duration']  # 2400
                difference_time = time - cur_time  # 1500
                part_in_the_list_of_coords = difference_time / step_duration  # от 0 до 1
                lon, lat = path_coords[step['way_points'][int(len(step['way_points']) * part_in_the_list_of_coords)]]
                coordinates = Point(lat=lat, lon=lon)
                print('two')
                break
            cur_time += step['duration']
    print(f'time: {time}, cur_time: {cur_time}')
    print(f'coord: {coordinates}')
    return coordinates


def find_hotel_by_coordinates(point: Point):
    url = f'https://search-maps.yandex.ru/v1/?text=hotel&ll={point.lon},{point.lat}&lang=ru_RU&apikey={YANDEX_SEARCH_ORGANIZATION_API}'
    response = requests.request("GET", url, headers=headers, data=payload)
    with open('./calculations/path_data/hotels.json', 'w') as outfile:
        outfile.write(response.text)
    print(response)
    all_data = json.loads(response.text)
    print(all_data)
    hotels_data = all_data['features']
    hotels = []
    for h in hotels_data:
        hotel = dict()
        hotel_data = h['properties']['CompanyMetaData']
        hotel_name = hotel_data['name']
        hotel['name'] = hotel_name
        hotel_address = hotel_data['address']
        hotel['address'] = hotel_address
        if 'url' in hotel_data:
            hotel_url = hotel_data['url']
            hotel['url'] = hotel_url
        hotel_phones = []
        if 'Phones' in hotel_data:
            for phone in hotel_data['Phones']:
                number = phone['formatted']
                hotel_phones.append(number)
            hotel['phones'] = hotel_phones
        if 'Hours' in hotel_data:
            hotel_hours = hotel_data['Hours']['text']
            hotel['hours'] = hotel_hours
        hotels.append(hotel)
    return hotels
