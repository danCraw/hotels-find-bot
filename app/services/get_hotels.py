import json

import requests

from app.models.hotel import Hotel, YaHotel
from app.models.point import Point


def find_hotels_by_coordinates(point: Point) -> list[YaHotel]:
    """Find hotels by coordinates using yandex search organization API"""

    # url = YANDEX_SEARCH_ORGANIZATION_URL
    #
    # params = {
    #     'll': f'{point.lon},{point.lat}',
    #     'lang': 'ru_RU',
    #     'apikey': YANDEX_SEARCH_ORGANIZATION_API
    # }
    #
    # try:
    #     response = requests.get(url, params=params)
    #     response.raise_for_status()  # Raise an exception for HTTP errors
    # except requests.exceptions.RequestException as e:
    #     raise Exception(f"HTTP request failed: {e}")
    #
    # hotels_data_path = './calculations/path_data/hotels.json'
    # with open(hotels_data_path, 'w') as outfile:
    #     outfile.write(response.text)

    try:
        all_data = {"type": "FeatureCollection", "properties": {"ResponseMetaData": {
            "SearchResponse": {"found": 1, "display": "multiple",
                               "boundedBy": [[36.69464461, 53.8201276], [37.30535539, 54.17909494]]},
            "SearchRequest": {"request": "hotel", "skip": 0, "results": 10,
                              "boundedBy": [[37.048427, 55.43644866], [38.175903, 56.04690174]]}}}, "features": [
            {"type": "Feature", "geometry": {"type": "Point", "coordinates": [36.961702, 54.150166]},
             "properties": {"name": "Усадьба Мосолов",
                            "description": "ул. 50 лет ВЛКСМ, 1, рабочий посёлок Дубна, Россия",
                            "boundedBy": [[36.957643, 54.147763], [36.965854, 54.152583]],
                            "uri": "ymapsbm1://org?oid=110497682322",
                            "CompanyMetaData": {"id": "110497682322", "name": "Усадьба Мосоло",
                                                "address": "Тульская область, Дубенский район, рабочий посёлок Дубна, улица 50 лет ВЛКСМ, 1",
                                                "url": "http://usadbamosolovo.ru/",
                                                "Phones": [{"type": "phone", "formatted": "+7 (980) 407-39-02"}],
                                                "Categories": [{"class": "hotels", "name": "Гостиница"}],
                                                "Hours": {"text": "ежедневно, 12:00–20:00", "Availabilities": [
                                                    {"Intervals": [{"from": "12:00:00", "to": "20:00:00"}],
                                                     "Everyday": True}]}, "Features": [
                                    {"id": "wheelchair_accessible_vocabulary",
                                     "value": [{"id": "wheelchair_accessible_na", "name": "недоступно"}],
                                     "name": "доступность помещения на инвалидной коляске", "type": "enum"}]}}}]}
    except json.JSONDecodeError as e:
        raise Exception(f"Failed to decode JSON response: {e}")

    hotels_data = all_data.get('features', [])
    hotels: list[Hotel] = []

    for h in hotels_data:
        hotel_data = h.get('properties', {}).get('CompanyMetaData', {})
        hotel_model = YaHotel(
            ya_id=hotel_data.get('id'),
            name=hotel_data.get('name'),
            address=hotel_data.get('address'),
            url=hotel_data.get('url'),
            phones=[phone.get('formatted') for phone in hotel_data.get('Phones', [])],
            hours=hotel_data.get('Hours', {}).get('text'),
        )

        hotels.append(hotel_model)

    return hotels


async def get_hotel_rooms(hotel_id, checkin_date, checkout_date, adults, children_ages=None):
    token = "YANDEX_TRAVEL_OAUTH_TOKEN"

    url = "https://whitelabel.travel.yandex-net.ru/hotels/offers/"

    params = {
        "hotel_id": hotel_id,
        "checkin_date": checkin_date,
        "checkout_date": checkout_date,
        "adults": adults,
    }

    if children_ages:
        params["children_ages"] = ",".join(map(str, children_ages))

    headers = {
        "Authorization": f"OAuth {token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get("complete", False):
            return data.get("rooms", [])
        return []
    except Exception as e:
        print(f"Error fetching rooms: {e}")
        return []
