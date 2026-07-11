from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.listing_service import query_listings, query_listings_near
from app.schemas import ListingResponse, ListingNearResponse

router = APIRouter()


@router.get("/listings", response_model=list[ListingResponse])
def get_listings(
    min_lng: Optional[float] = Query(None),
    min_lat: Optional[float] = Query(None),
    max_lng: Optional[float] = Query(None),
    max_lat: Optional[float] = Query(None),
    rent_min: Optional[int] = Query(None),
    rent_max: Optional[int] = Query(None),
    rooms: Optional[int] = Query(None),
    property_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    bbox_params = [min_lng, min_lat, max_lng, max_lat]
    if any(p is not None for p in bbox_params) and not all(p is not None for p in bbox_params):
        raise HTTPException(400, "All four bbox params required together: min_lng, min_lat, max_lng, max_lat")

    return query_listings(
        db,
        min_lng=min_lng,
        min_lat=min_lat,
        max_lng=max_lng,
        max_lat=max_lat,
        rent_min=rent_min,
        rent_max=rent_max,
        rooms=rooms,
        property_type=property_type,
    )


@router.get("/listings/near", response_model=list[ListingNearResponse])
def get_listings_near(
    lat: float = Query(...),
    lng: float = Query(...),
    radius_m: int = Query(..., gt=0),
    rent_min: Optional[int] = Query(None),
    rent_max: Optional[int] = Query(None),
    rooms: Optional[int] = Query(None),
    property_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    return query_listings_near(
        db, lat=lat, lng=lng, radius_m=radius_m,
        rent_min=rent_min, rent_max=rent_max,
        rooms=rooms, property_type=property_type,
    )
