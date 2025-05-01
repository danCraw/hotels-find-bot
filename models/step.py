from pydantic import BaseModel


class Step(BaseModel):
    duration: float
    way_points: list
