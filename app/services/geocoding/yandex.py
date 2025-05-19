import json

import requests

from app.config import YANDEX_GEOCODE_API_URL, YANDEX_GEOCODE_API_KEY
from app.models.point import Point


def yandex_city_geocoding(city: str) -> Point:
    """Get the coordinates of the city using yandex geocoding API"""

    url = YANDEX_GEOCODE_API_URL

    params = {"apikey": YANDEX_GEOCODE_API_KEY, "geocode": city, "format": "json"}

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an exception for HTTP errors
    except requests.exceptions.RequestException as e:
        raise Exception(f"HTTP request failed: {e}")

    try:
        all_data = response.json()
    except json.JSONDecodeError as e:
        raise Exception(f"Failed to decode JSON response: {e}")

    try:
        coords = all_data["response"]["GeoObjectCollection"]["featureMember"][0][
            "GeoObject"
        ]["Point"]["pos"].split()
        lon, lat = coords
    except (KeyError, IndexError) as e:
        raise Exception(f"Failed to extract coordinates from JSON response: {e}")

    point = Point(lat=lat, lon=lon)
    return point


def yandex_reverse_geocoding(lon: float, lat: float):
    REVERSE_GEOCODE_URL = f"https://geocode-maps.yandex.ru/1.x/?apikey={YANDEX_GEOCODE_API_KEY}&geocode={lon},{lat}&format=json"
    response = requests.request("GET", REVERSE_GEOCODE_URL)

    with open("./calculations/path_data/reverse_geocoding.json", "w") as outfile:
        outfile.write(response.text)
    all_data = json.loads(response.text)
    text = str(
        all_data["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"][
            "metaDataProperty"
        ]["GeocoderMetaData"]["text"]
    )
    return text
