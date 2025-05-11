import json

import requests

from app.config import OPEN_ROUTE_SERVICE_API_KEY
from app.models.point import Point


def openrouteservice_city_geocoding(city: str) -> Point:
    city_geocode_url = f'https://api.openrouteservice.org/geocode/search?api_key={OPEN_ROUTE_SERVICE_API_KEY}&text={city}'
    response = requests.request("GET", city_geocode_url)
    all_data = json.loads(response.text)
    coords = all_data['features'][0]['geometry']['coordinates']
    point = Point(lat=coords[1], lon=coords[0]) # в openrouteservice сначала lon, затем lat
    return point


def openrouteservice_reverse_geocoding(point: Point) -> str:
    reverse_url = f'https://api.openrouteservice.org/geocode/reverse?api_key={OPEN_ROUTE_SERVICE_API_KEY}&point.lon={point.lon}&point.lat={point.lat}'

    response = requests.get(reverse_url)
    response.raise_for_status()  # Проверка на ошибки HTTP

    data = response.json()

    features = data.get('features', [])

    for feature in features:
        props = feature.get('properties', {})
        if props.get('layer') == 'locality':
            return props.get('name')

    if features:
        return features[0].get('properties', {}).get('name')

    return None
