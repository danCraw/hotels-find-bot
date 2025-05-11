from pydantic import BaseModel


class Hotel(BaseModel):
    name: str
    address: str
    url: str | None
    hours: str | None
    phones: list[str] | None
    rooms: int | None = 0

class YaHotel(Hotel):
    ya_id: str
