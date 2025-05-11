from dataclasses import dataclass
from typing import List

from app.models.city import City


@dataclass
class Guest:
    name: str
    age: int = None

@dataclass
class BookingData:
    departure: City
    destination: City
    travel_time: str
    adults: int
    children: List[Guest]