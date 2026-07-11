from typing import Any, TypedDict

from sqlalchemy import text
from sqlalchemy.orm import Session
import json


class AreaStatsResult(TypedDict):
    type: str
    features: list[dict[str, Any]]


def get_area_stats(db: Session) -> AreaStatsResult:
    query = text("""
        SELECT
            a.area_code,
            a.area_name,
            ST_AsGeoJSON(a.geom) AS geometry,
            COUNT(l.listing_id) AS listing_count,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY l.rent_eur)
                FILTER (WHERE l.rent_eur IS NOT NULL) AS median_rent,
            PERCENTILE_CONT(0.5) WITHIN GROUP (
                ORDER BY l.rent_eur::float / NULLIF(l.size_m2, 0)
            ) FILTER (
                WHERE l.rent_eur IS NOT NULL AND l.size_m2 IS NOT NULL AND l.size_m2 > 0
            ) AS median_eur_per_m2
        FROM areas a
        LEFT JOIN listings l ON ST_Contains(a.geom, l.geom)
        GROUP BY a.area_code, a.area_name, a.geom
        ORDER BY a.area_code
    """)

    rows = db.execute(query).mappings().all()

    features = []
    for row in rows:
        features.append({
            "type": "Feature",
            "geometry": json.loads(row["geometry"]) if row["geometry"] else None,
            "properties": {
                "area_code": row["area_code"],
                "area_name": row["area_name"],
                "listing_count": row["listing_count"],
                "median_rent": int(round(float(row["median_rent"]))) if row["median_rent"] is not None else None,
                "median_eur_per_m2": round(float(row["median_eur_per_m2"]), 2) if row["median_eur_per_m2"] is not None else None,
            },
        })

    return {
        "type": "FeatureCollection",
        "features": features,
    }
