from sqlalchemy import Column, String, Integer, Numeric, Date, Index
from geoalchemy2 import Geometry

from app.database import Base


class Listing(Base):
    __tablename__ = "listings"

    listing_id = Column(String, primary_key=True)
    geom = Column(Geometry("POINT", srid=4326), nullable=False)
    rooms = Column(Integer, nullable=True)
    size_m2 = Column(Numeric(6, 1), nullable=True)
    rent_eur = Column(Integer, nullable=True)
    property_type = Column(String(20), nullable=False)
    listed_date = Column(Date, nullable=False)

    # GiST index on geom is auto-created by GeoAlchemy2
    __table_args__ = (
        Index("idx_listings_property_type", "property_type"),
        Index("idx_listings_rooms", "rooms"),
        Index("idx_listings_rent", "rent_eur"),
    )


class Area(Base):
    __tablename__ = "areas"

    area_code = Column(String, primary_key=True)
    area_name = Column(String(50), nullable=False)
    geom = Column(Geometry("POLYGON", srid=4326), nullable=False)

    # GiST index on geom is auto-created by GeoAlchemy2
