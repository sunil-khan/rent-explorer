from typing import Optional

from sqlalchemy import func, cast, case, Numeric
from sqlalchemy.orm import Session
from geoalchemy2 import Geography

from app.models import Listing


def query_listings(
    db: Session,
    min_lng: Optional[float] = None,
    min_lat: Optional[float] = None,
    max_lng: Optional[float] = None,
    max_lat: Optional[float] = None,
    rent_min: Optional[int] = None,
    rent_max: Optional[int] = None,
    rooms: Optional[int] = None,
    property_type: Optional[str] = None,
) -> list[dict]:
    # Compute eur_per_m2 in SQL — consistent with ST_X/ST_Y pattern
    eur_per_m2 = case(
        (
            (Listing.rent_eur.isnot(None)) & (Listing.size_m2.isnot(None)) & (Listing.size_m2 > 0),
            func.round(cast(Listing.rent_eur, Numeric) / Listing.size_m2, 2),
        ),
        else_=None,
    ).label("eur_per_m2")

    query = db.query(
        Listing.listing_id,
        func.ST_Y(Listing.geom).label("latitude"),
        func.ST_X(Listing.geom).label("longitude"),
        Listing.rooms,
        Listing.size_m2,
        Listing.rent_eur,
        Listing.property_type,
        Listing.listed_date,
        eur_per_m2,
    )

    if all(v is not None for v in [min_lng, min_lat, max_lng, max_lat]):
        bbox = func.ST_MakeEnvelope(min_lng, min_lat, max_lng, max_lat, 4326)
        query = query.filter(Listing.geom.ST_Within(bbox))

    if rent_min is not None:
        query = query.filter(Listing.rent_eur >= rent_min)
    if rent_max is not None:
        query = query.filter(Listing.rent_eur <= rent_max)
    if rooms is not None:
        query = query.filter(Listing.rooms == rooms)
    if property_type is not None:
        query = query.filter(Listing.property_type == property_type)

    return [
        {
            "listing_id": row.listing_id,
            "latitude": row.latitude,
            "longitude": row.longitude,
            "rooms": row.rooms,
            "size_m2": float(row.size_m2) if row.size_m2 is not None else None,
            "rent_eur": row.rent_eur,
            "property_type": row.property_type,
            "listed_date": row.listed_date,
            "eur_per_m2": float(row.eur_per_m2) if row.eur_per_m2 is not None else None,
        }
        for row in query.all()
    ]


def query_listings_near(
    db: Session,
    lat: float,
    lng: float,
    radius_m: int,
    rent_min: Optional[int] = None,
    rent_max: Optional[int] = None,
    rooms: Optional[int] = None,
    property_type: Optional[str] = None,
) -> list[dict]:
    point = func.ST_SetSRID(func.ST_MakePoint(lng, lat), 4326)
    point_geog = cast(point, Geography)
    listing_geog = cast(Listing.geom, Geography)

    # Compute eur_per_m2 in SQL — consistent with ST_X/ST_Y pattern
    eur_per_m2 = case(
        (
            (Listing.rent_eur.isnot(None)) & (Listing.size_m2.isnot(None)) & (Listing.size_m2 > 0),
            func.round(cast(Listing.rent_eur, Numeric) / Listing.size_m2, 2),
        ),
        else_=None,
    ).label("eur_per_m2")

    query = db.query(
        Listing.listing_id,
        func.ST_Y(Listing.geom).label("latitude"),
        func.ST_X(Listing.geom).label("longitude"),
        Listing.rooms,
        Listing.size_m2,
        Listing.rent_eur,
        Listing.property_type,
        Listing.listed_date,
        eur_per_m2,
        func.ST_Distance(listing_geog, point_geog).label("distance_m"),
    ).filter(
        func.ST_DWithin(listing_geog, point_geog, radius_m)
    )

    if rent_min is not None:
        query = query.filter(Listing.rent_eur >= rent_min)
    if rent_max is not None:
        query = query.filter(Listing.rent_eur <= rent_max)
    if rooms is not None:
        query = query.filter(Listing.rooms == rooms)
    if property_type is not None:
        query = query.filter(Listing.property_type == property_type)

    query = query.order_by("distance_m")

    return [
        {
            "listing_id": row.listing_id,
            "latitude": row.latitude,
            "longitude": row.longitude,
            "rooms": row.rooms,
            "size_m2": float(row.size_m2) if row.size_m2 is not None else None,
            "rent_eur": row.rent_eur,
            "property_type": row.property_type,
            "listed_date": row.listed_date,
            "eur_per_m2": float(row.eur_per_m2) if row.eur_per_m2 is not None else None,
            "distance_m": round(row.distance_m, 1),
        }
        for row in query.all()
    ]
