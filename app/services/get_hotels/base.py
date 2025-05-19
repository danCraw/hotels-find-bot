from abc import ABC, abstractmethod
from datetime import date
from typing import List, Optional

from app.models.hotel import Hotel
from app.models.point import Point


class BaseHotelAPI(ABC):
    """Abstract base class for hotel API clients"""

    def __init__(self):
        self.headers = {
            "Content-Type": "application/json",
        }

    @abstractmethod
    def search_hotels_by_geo(
        self,
        point: Point,
        checkin: date,
        checkout: date,
        radius: int = 50,
        language: str = "ru",
    ) -> List[Hotel]:
        """Search hotels by geographical coordinates"""
        pass

    @abstractmethod
    def get_hotel_rooms(
        self,
        hotel_id: str,
        checkin_date: date,
        checkout_date: date,
        adults: int,
        children_ages: Optional[List[int]] = None,
    ) -> List[dict]:
        """Get available rooms for a specific hotel"""
        pass
