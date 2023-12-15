from pydantic import BaseModel


class Point(BaseModel):
    lat: int
    lon: int
