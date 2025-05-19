import json
from datetime import date
from typing import List

import requests

from app.models.hotel import OstrovokHotel
from app.models.point import Point
from app.services.get_hotels.base import BaseHotelAPI


class OstrovokHotelAPI(BaseHotelAPI):
    def __init__(self, api_key: str, key_id: str):
        super().__init__()
        self.base_url = "https://api.worldota.net/api/b2b/v3"
        self.api_key = api_key
        self.key_id = key_id
        self.auth = (key_id, api_key)
        self.headers = {
            "Content-Type": "application/json",
        }

    def _parse_hotels(self, data: dict) -> list[OstrovokHotel]:
        """Parse Ostrovok API response into list of YaHotel objects"""
        hotels = []

        for hotel_data in data.get("data", {}).get("hotels", []):
            # Basic hotel info
            hotel = OstrovokHotel(
                ostrovok_id=str(hotel_data.get("hid")),
                name=hotel_data.get("id", "").replace("_", " ").title(),
                address="",  # Ostrovok geo search doesn't provide address
                url="",  # Would need to construct or get from another endpoint
                phones=[],  # Not available in this response
                hours="",  # Not available in this response
            )

            hotels.append(hotel)

        return hotels

    def search_hotels_by_geo(
        self,
        point: Point,
        checkin: date,
        checkout: date,
        adults: int = 2,
        children_ages: list[int] | None = None,
        radius: int = 5,
        language: str = "en",
        residency: str = "ru",
        currency: str = "RUB",
    ) -> List[OstrovokHotel]:
        """Search hotels by geographical coordinates using Ostrovok API"""
        url = f"{self.base_url}/search/serp/geo/"

        guests = [{"adults": adults}]
        if children_ages:
            guests[0]["children"] = children_ages

        payload = {
            "checkin": checkin.strftime("%Y-%m-%d"),
            "checkout": checkout.strftime("%Y-%m-%d"),
            "latitude": point.lat,
            "longitude": point.lon,
            "radius": radius,  # in km
            "residency": residency,
            "language": language,
            "currency": currency,
            "guests": guests,
        }

        try:
            response = requests.post(
                url, auth=self.auth, headers=self.headers, json=payload, timeout=10
            )
            response.raise_for_status()
            data = response.json()

            if data.get("status") != "ok":
                raise Exception(f"API error: {data.get('error')}")

            return self._parse_hotels(data)

        except requests.exceptions.RequestException as e:
            raise Exception(f"HTTP request failed: {e}")
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to decode JSON response: {e}")

    def get_hotel_rooms(
        self,
        hotel_id: str,
        checkin_date: date,
        checkout_date: date,
        adults: int,
        children_ages: list[int] | None = None,
        language: str = "ru",
        residency: str = "ru",
        currency: str = "RUB",
        timeout: int = 10,
    ) -> list[dict]:
        """Get available rooms for a specific hotel from Ostrovok API"""

        url = "https://ostrovok.ru/hotel/search/v1/site/hp/search"

        paxes = [{"adults": adults}]
        if children_ages:
            paxes[0]["child_ages"] = children_ages

        payload = {
            "arrival_date": checkin_date.strftime("%Y-%m-%d"),
            "departure_date": checkout_date.strftime("%Y-%m-%d"),
            "hotel": hotel_id,
            "currency": currency,
            "lang": language,
            "paxes": paxes,
            "search_uuid": "38bb2fd6-69d3-4e4a-881a-83cea09de1e6",
            "region_id": 2395,
        }

        try:
            response = requests.post(
                url,
                headers={
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=timeout,
            )
            response.raise_for_status()
            data = response.json()

            return self._parse_rooms(data)

        except requests.exceptions.RequestException as e:
            print(f"Error fetching rooms: {e}")
            return []
        except json.JSONDecodeError as e:
            print(f"Failed to decode JSON response: {e}")
            return []

    def _parse_rooms(self, data: dict) -> List[dict]:
        """Parse room data from Ostrovok API response"""
        rooms_list = []
        rates = data.get("rates") or []

        for rate in rates:
            room_info = {
                "rate_hash": rate.get("hash"),
                "room_type": rate.get("room_name"),
                "price": float(
                    rate.get("payment_options", {})
                    .get("payment_types", [{}])[0]
                    .get("amount", 0)
                ),
                "currency": rate.get("payment_options", {})
                .get("payment_types", [{}])[0]
                .get("currency_code", "RUB"),
                "cancellation_policy": self._parse_cancellation(
                    rate.get("cancellation_info", {})
                ),
                "meal": rate.get("meal", ["none"])[0],
                "bed_type": self._parse_bed_type(rate.get("room_data_trans", {})),
                "occupancy": rate.get("occupancy", 1),
                "available": rate.get("allotment", 0) > 0,
            }

            rooms_list.append(room_info)

        return rooms_list

    def _parse_cancellation(self, cancellation_info: dict) -> dict:
        """Parse cancellation policy from API response"""
        policies = []
        for policy in cancellation_info.get("policies", []):
            policies.append(
                {
                    "from": policy.get("start_at"),
                    "to": policy.get("end_at"),
                    "penalty": policy.get("penalty", {}).get("amount"),
                }
            )

        return {
            "policies": policies,
            "free_cancellation_before": cancellation_info.get(
                "free_cancellation_before"
            ),
        }

    def _parse_bed_type(self, room_trans: dict) -> str:
        """Extract bed type from room translation data"""
        ru_data = room_trans.get("ru", {})
        return ru_data.get("bedding_type", "").split(",")[0].strip() if ru_data else ""

    def search_hotels_by_address(self, address) -> OstrovokHotel:
        url = "https://ostrovok.ru/api/site/multicomplete.json"

        ostrovok_hotels = []

        params = {
            "query": address,
            "locale": "ru",
            "country_code": "RU",
        }

        response = requests.get(url, params=params)

        if response.json()["hotels"]:
            ostrovok_hotel = response.json()["hotels"][0]
        else:
            return None
        ostrovok_hotels.append(ostrovok_hotel)

        return OstrovokHotel(
            ostrovok_id=ostrovok_hotel["otahotel_id"],
            name=ostrovok_hotel["hotel_name"],
            address=ostrovok_hotel["hotel_address"],
            url=None,
            hours=None,
            phones=[],
        )


# ostrovok_api = OstrovokAPI(
#     api_key="08d64714-763a-4d65-9945-c036c465635f",
#     key_id="12839"
# )
