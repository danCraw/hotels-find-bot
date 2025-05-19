import requests

from app.models.hotel import YaHotel
from app.models.point import Point
from app.services.get_hotels.base import BaseHotelAPI
from datetime import date


class YandexHotelAPI(BaseHotelAPI):
    """Hotel API client for Yandex Travel"""

    def __init__(self, api_key: str, oauth_token: str):
        super().__init__()
        self.api_key = api_key
        self.oauth_token = oauth_token
        self.search_url = "https://search-maps.yandex.ru/v1/"

    def search_hotels_by_geo(
        self,
        point: Point,
        checkin: date,
        checkout: date,
        radius: int = 50,
        language: str = "ru",
    ) -> list[YaHotel]:
        """Find hotels by coordinates using yandex search organization API"""
        params = {
            "ll": f"{point.lon},{point.lat}",
            "lang": "ru_RU",
            "apikey": self.api_key,
            "text": "отель|гостиница|hotel",
            "type": "biz",
            "results": 500,
        }

        try:
            response = requests.get(self.search_url, params=params)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"HTTP request failed: {e}")

        hotels_data = data.get("features", [])
        hotels: list[YaHotel] = []

        for h in hotels_data:
            hotel_data = h.get("properties", {}).get("CompanyMetaData", {})
            hotel_model = YaHotel(
                ya_id=hotel_data.get("id"),
                name=hotel_data.get("name"),
                address=hotel_data.get("address"),
                url=hotel_data.get("url"),
                phones=[
                    phone.get("formatted") for phone in hotel_data.get("Phones", [])
                ],
                hours=hotel_data.get("Hours", {}).get("text"),
            )
            hotels.append(hotel_model)

        return hotels

    def get_hotel_rooms(
        self,
        hotel_id: str,
        checkin_date: date,
        checkout_date: date,
        adults: int,
        children_ages: list[int] | None = None,
    ) -> list[dict]:
        """Get available rooms from Yandex Travel API"""
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
            "Authorization": f"OAuth {self.oauth_token}",
            "Content-Type": "application/json",
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
