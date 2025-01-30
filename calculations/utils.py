import requests
import json
from config import YANDEX_GEOCODE_API_KEY, OPEN_ROUTE_SERVICE_API_KEY, YANDEX_SEARCH_ORGANIZATION_API, \
    YANDEX_SEARCH_ORGANIZATION_URL, OPEN_ROUTE_SERVICE_API_URL, YANDEX_GEOCODE_API_URL
from models.hotel import Hotel
from models.point import Point
from models.step import Step


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


def yandex_city_geocoding(city: str) -> Point:
    """Get the coordinates of the city using yandex geocoding API"""

    url = YANDEX_GEOCODE_API_URL

    params = {
        'apikey': YANDEX_GEOCODE_API_KEY,
        'geocode': city,
        'format': 'json'
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an exception for HTTP errors
    except requests.exceptions.RequestException as e:
        raise Exception(f"HTTP request failed: {e}")

    city_geocoding_path = './calculations/path_data/city_geocoding.json'
    with open(city_geocoding_path, 'w') as outfile:
        outfile.write(response.text)

    try:
        all_data = response.json()
    except json.JSONDecodeError as e:
        raise Exception(f"Failed to decode JSON response: {e}")

    try:
        coords = all_data['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['Point']['pos'].split()
        lon, lat = coords
    except (KeyError, IndexError) as e:
        raise Exception(f"Failed to extract coordinates from JSON response: {e}")

    point = Point(lat=lat, lon=lon)
    return point


def yandex_reverse_geocoding(lon: float, lat: float):
    REVERSE_GEOCODE_URL = f'https://geocode-maps.yandex.ru/1.x/?apikey={YANDEX_GEOCODE_API_KEY}&geocode={lon},{lat}&format=json'
    response = requests.request("GET", REVERSE_GEOCODE_URL)
    
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
    """Get the route between two points using openrouteservice API"""

    api_url = OPEN_ROUTE_SERVICE_API_URL
    params = {
        'api_key': OPEN_ROUTE_SERVICE_API_KEY,
        'start': f'{lon_from},{lat_from}',
        'end': f'{lon_to},{lat_to}'
    }

    try:
        response = requests.get(api_url, params=params)
        response.raise_for_status()  # Raise an exception for HTTP errors
    except requests.exceptions.RequestException as e:
        raise Exception(f"HTTP request failed: {e}")

    route_data_path = './calculations/path_data/route.json'
    with open(route_data_path, 'w') as outfile:
        outfile.write(response.text)

    try:
        all_data = response.json()
    except json.JSONDecodeError as e:
        raise Exception(f"Failed to decode JSON response: {e}")

    features = all_data.get('features', [])
    if not features:
        raise Exception("No features found in the response")

    segments = features[0].get('properties', {}).get('segments', [])
    if not segments:
        raise Exception("No segments found in the response")

    coordinates = features[0].get('geometry', {}).get('coordinates', [])
    length = segments[0].get('distance', 0)  # meters
    duration = segments[0].get('duration', 0)  # seconds
    steps = segments[0].get('steps', [])

    route_data = {
        'coordinates': coordinates,
        'length': length,
        'duration': duration,
        'steps': steps
    }
    return route_data


def find_coordinates_by_time(time: int, route_data: dict) -> Point:
    """Find the coordinates of the point on the route by time"""

    cur_time = 0
    path_steps: list[Step] = route_data['steps']
    path_coords = route_data['coordinates']

    for step in path_steps:
        step_ = Step(**step)
        if time <= cur_time + step_.duration:
            if time == cur_time:
                lon, lat = path_coords[step_.way_points[0]]
            else:
                part_in_the_list_of_coords = (time - cur_time) / step_.duration
                index = int(len(step_.way_points) * part_in_the_list_of_coords)
                lon, lat = path_coords[step_.way_points[index]]
            return Point(lat=lat, lon=lon)
        cur_time += step_.duration

    # If time exceeds the total duration, return the last coordinate
    lon, lat = path_coords[-1]
    point = Point(lat=lat, lon=lon)
    return point


def find_hotel_by_coordinates(point: Point) -> list[Hotel]:
    """Find hotels by coordinates using yandex search organization API"""

    url = YANDEX_SEARCH_ORGANIZATION_URL

    params = {
        'll': f'{point.lon},{point.lat}',
        'lang': 'ru_RU',
        'apikey': YANDEX_SEARCH_ORGANIZATION_API
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an exception for HTTP errors
    except requests.exceptions.RequestException as e:
        raise Exception(f"HTTP request failed: {e}")

    hotels_data_path = './calculations/path_data/hotels.json'
    with open(hotels_data_path, 'w') as outfile:
        outfile.write(response.text)

    try:
        all_data = response.json()
    except json.JSONDecodeError as e:
        raise Exception(f"Failed to decode JSON response: {e}")

    hotels_data = all_data.get('features', [])
    hotels: list[Hotel] = []

    for h in hotels_data:
        hotel_data = h.get('properties', {}).get('CompanyMetaData', {})
        hotel_model = Hotel(
            name=hotel_data.get('name'),
            address=hotel_data.get('address'),
            url=hotel_data.get('url'),
            phones=[phone.get('formatted') for phone in hotel_data.get('Phones', [])],
            hours=hotel_data.get('Hours', {}).get('text'),
        )

        hotels.append(hotel_model)

    return hotels

def get_ostrovok_hotels(hotels: list[Hotel]) -> list[dict]:
    url = "https://ostrovok.ru/api/site/multicomplete.json"

    ostrovok_hotels = []

    for hotel in hotels:
        params = {
            "query": hotel.name,
            "locale": "ru"
        }

        response = requests.get(url, params=params)
        ostrovok_hotel = response.json()['hotels'][0]
        ostrovok_hotels.append(ostrovok_hotel)

    return ostrovok_hotels

async def find_rooms_by_params(hotel_name: str, adults: int, children: int):
    url = "https://ostrovok.ru/hotel/search/v1/site/reviews/"
    params = {
        "hotel": hotel_name,
        "lang": "ru",
        "page": 1,
        "sort": "rate_desc",
        "adults": adults,
        "children": children,
        "client_uid": "E4DBF44D76FE3067356C6A6902D6FB16"
    }

    response = requests.get(url, params=params)

    return response.json()
