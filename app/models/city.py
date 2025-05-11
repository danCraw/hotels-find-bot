from pydantic import BaseModel
from app.models.point import Point


class City(BaseModel):
    name: str
    point: Point
