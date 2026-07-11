from datetime import date
from typing import Optional, TypedDict

from sqlalchemy import func, cast
from sqlalchemy.orm import Session
from geoalchemy2 import Geography

from app.models import Listing


class ListingResult(TypedDict):
    listing_id: str
    latitude: float
    longitude: float
    rooms: Optional[int]
    size_m2: Optional[float]
    rent_eur: Optional[int]
    property_type: str
    listed_date: date
    eur_per_m2: Optional[float]


class ListingNearResult(ListingResult):
    distance_m: float


def _compute_eur_per_m2(rent_eur, size_m2) -> float | None:
    if rent_eur is not None and size_m2 is not None and float(size_m2) > 0:
        return round(float(rent_eur) / float(size_m2), 2)
    return None


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
) -> list[ListingResult]:
    query = db.query(
        Listing.listing_id,
        func.ST_Y(Listing.geom).label("latitude"),
        func.ST_X(Listing.geom).label("longitude"),
        Listing.rooms,
        Listing.size_m2,
        Listing.rent_eur,
        Listing.property_type,
        Listing.listed_date,
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

    results = []
    for row in query.all():
        eur_per_m2 = _compute_eur_per_m2(row.rent_eur, row.size_m2)

        results.append({
            "listing_id": row.listing_id,
            "latitude": row.latitude,
            "longitude": row.longitude,
            "rooms": row.rooms,
            "size_m2": float(row.size_m2) if row.size_m2 is not None else None,
            "rent_eur": row.rent_eur,
            "property_type": row.property_type,
            "listed_date": row.listed_date,
            "eur_per_m2": eur_per_m2,
        })

    return results


def query_listings_near(
    db: Session,
    lat: float,
    lng: float,
    radius_m: int,
    rent_min: Optional[int] = None,
    rent_max: Optional[int] = None,
    rooms: Optional[int] = None,
    property_type: Optional[str] = None,
) -> list[ListingNearResult]:
    point = func.ST_SetSRID(func.ST_MakePoint(lng, lat), 4326)
    point_geog = cast(point, Geography)
    listing_geog = cast(Listing.geom, Geography)

    query = db.query(
        Listing.listing_id,
        func.ST_Y(Listing.geom).label("latitude"),
        func.ST_X(Listing.geom).label("longitude"),
        Listing.rooms,
        Listing.size_m2,
        Listing.rent_eur,
        Listing.property_type,
        Listing.listed_date,
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

    results = []
    for row in query.all():
        eur_per_m2 = _compute_eur_per_m2(row.rent_eur, row.size_m2)

        results.append({
            "listing_id": row.listing_id,
            "latitude": row.latitude,
            "longitude": row.longitude,
            "rooms": row.rooms,
            "size_m2": float(row.size_m2) if row.size_m2 is not None else None,
            "rent_eur": row.rent_eur,
            "property_type": row.property_type,
            "listed_date": row.listed_date,
            "eur_per_m2": eur_per_m2,
            "distance_m": round(row.distance_m, 1),
        })

    return results
