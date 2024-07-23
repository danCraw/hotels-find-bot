from pydantic import BaseModel


class Step(BaseModel):
    duration: int
    way_points: list
