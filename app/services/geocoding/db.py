from sqlalchemy import Column, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

from app.models.point import Point

Base = declarative_base()


class Geocoding(Base):
    __tablename__ = "geocoding"

    city = Column(String, primary_key=True)
    lon = Column(Float)
    lat = Column(Float)


def db_city_geocoding(session: Session, city_name: str) -> Point | None:
    record = session.query(Geocoding).filter(Geocoding.city.ilike(city_name)).first()
    if record:
        return Point(lat=record.lat, lon=record.lon)
    return None


def db_reverse_geocoding(session: Session, lat: float, lon: float) -> str | None:
    record = (
        session.query(Geocoding)
        .filter(Geocoding.lat == lat, Geocoding.lon == lon)
        .first()
    )
    if record:
        return record.city
    return None
