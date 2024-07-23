from pydantic import BaseModel
from models.point import Point


class City(BaseModel):
    name: str
    point: Point
