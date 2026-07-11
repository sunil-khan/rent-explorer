from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.area_service import get_area_stats
from app.schemas import AreaStatsResponse

router = APIRouter()


@router.get("/areas/stats", response_model=AreaStatsResponse)
def areas_stats(db: Session = Depends(get_db)):
    return get_area_stats(db)
