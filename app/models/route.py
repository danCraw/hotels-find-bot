from pydantic import BaseModel

from app.models.step import Step


class Route(BaseModel):
    coordinates: list[float]
    length: int
    duration: int
    steps: list[Step]
