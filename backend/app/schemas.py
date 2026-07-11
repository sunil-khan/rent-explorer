from datetime import date
from typing import Optional

from pydantic import BaseModel


class ListingResponse(BaseModel):
    listing_id: str
    latitude: float
    longitude: float
    rooms: Optional[int] = None
    size_m2: Optional[float] = None
    rent_eur: Optional[int] = None
    property_type: str
    listed_date: date
    eur_per_m2: Optional[float] = None

    model_config = {"from_attributes": True}


class ListingNearResponse(ListingResponse):
    distance_m: float


class AreaProperties(BaseModel):
    area_code: str
    area_name: str
    listing_count: int
    median_rent: Optional[int] = None
    median_eur_per_m2: Optional[float] = None


class AreaFeature(BaseModel):
    type: str = "Feature"
    geometry: dict
    properties: AreaProperties


class AreaStatsResponse(BaseModel):
    type: str = "FeatureCollection"
    features: list[AreaFeature]
