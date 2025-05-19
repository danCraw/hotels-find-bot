import json
from datetime import date
from typing import List

import requests

from app.models.hotel import Hotel
from app.models.point import Point
from app.services.get_hotels.base import BaseHotelAPI


class OSMHotelAPI(BaseHotelAPI):
    """Hotel API client for OpenStreetMap Nominatim"""

    def search_hotels_by_geo(
        self,
        point: Point,
        checkin: date,
        checkout: date,
        radius: int = 50,
        language: str = "ru",
    ) -> List[Hotel]:
        """
        Search hotels using OpenStreetMap Nominatim API
        Returns list of Hotel objects with available data
        """
        url = "https://nominatim.openstreetmap.org/search"

        radius_deg = radius * 0.009

        viewbox = (
            point.lon - radius_deg,
            point.lat - radius_deg,
            point.lon + radius_deg,
            point.lat + radius_deg,
        )

        params = {
            "q": "гостиница|отель|hotel",
            "format": "jsonv2",
            "viewbox": ",".join(map(str, viewbox)),
            "bounded": 1,
            "countrycodes": "ru",
            "limit": 500,
            "addressdetails": 1,
            "namedetails": 1,
            "extratags": 1,
            "accept-language": language,
            "featuretype": "hotel",
        }

        try:
            response = requests.get(
                url,
                params=params,
                headers={"User-Agent": "RussianHotelsFinder/1.0"},
                timeout=10,
            )
            response.raise_for_status()

            items = response.json()
            return self._parse_hotels(items)

        except requests.exceptions.RequestException as e:
            raise Exception(f"Ошибка запроса к OSM: {e}")
        except (json.JSONDecodeError, KeyError) as e:
            raise Exception(f"Ошибка обработки данных: {e}")

    def _parse_hotels(self, data: list) -> List[Hotel]:
        """Parse OSM Nominatim response into Hotel objects"""
        hotels = []

        for item in data:
            # Название (предпочтение русскому названию)
            name = (
                item.get("namedetails", {}).get("name:ru")
                or item.get("name")
                or "Без названия"
            )

            addr = item.get("address", {})

            # Получаем город (предпочтение: city -> town -> village -> hamlet)
            city = (
                addr.get("city")
                or addr.get("town")
                or addr.get("village")
                or addr.get("hamlet")
                or "Россия"
            )

            # Получаем улицу и дом
            street = addr.get("road", "")
            house_number = addr.get("house_number", "")

            # Формируем адрес в нужном формате
            address = f"{city}, {street}" if street else city
            if house_number:
                address += f", {house_number}"

            # Обработка телефонов
            phones = []
            if phone := item.get("extratags", {}).get("phone"):
                phone = phone.replace(" ", "")
                phones.append(f"+7 {phone[1:]}" if phone.startswith("8") else phone)

            hotels.append(
                Hotel(
                    name=name.strip(),
                    address=address,
                    url=item.get("extratags", {}).get("website"),
                    hours=item.get("extratags", {}).get("opening_hours"),
                    phones=phones or None,
                    rooms=None,
                    avg_price=None,
                )
            )

        return hotels

    def get_hotel_rooms(
        self,
        hotel_id: str,
        checkin_date: date,
        checkout_date: date,
        adults: int,
        children_ages: list[int] | None = None,
    ) -> list[dict]:
        """OSM doesn't provide room information"""
        return []
