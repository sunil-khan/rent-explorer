import csv
import json
import logging
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import engine, Base
from app.models import Listing, Area  # noqa: F401 — needed so Base.metadata knows about tables

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATA_DIR = Path("/data")

# Margin in degrees added to area extent for bounds validation (~5km)
BOUNDS_MARGIN = 0.05


def get_bounds_from_areas(session: Session) -> dict:
    """Derive listing bounds dynamically from loaded area polygons."""
    result = session.execute(text(
        "SELECT ST_XMin(ext) AS lng_min, ST_XMax(ext) AS lng_max, "
        "ST_YMin(ext) AS lat_min, ST_YMax(ext) AS lat_max "
        "FROM (SELECT ST_Extent(geom) AS ext FROM areas) sub"
    )).mappings().one()
    return {
        "lat_min": float(result["lat_min"]) - BOUNDS_MARGIN,
        "lat_max": float(result["lat_max"]) + BOUNDS_MARGIN,
        "lng_min": float(result["lng_min"]) - BOUNDS_MARGIN,
        "lng_max": float(result["lng_max"]) + BOUNDS_MARGIN,
    }


def seed_listings(session: Session, bounds: dict) -> None:
    csv_path = DATA_DIR / "listings.csv"
    skipped = 0
    inserted = 0

    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            listing_id = row["listing_id"]
            # Parse and validate coordinates
            try:
                lat = float(row["latitude"])
                lng = float(row["longitude"])
            except (ValueError, KeyError):
                logger.warning("Skipping %s: invalid coordinates", listing_id)
                skipped += 1
                continue

            # Skip listings outside area bounds (derived from loaded area polygons)
            if not (
                bounds["lat_min"] <= lat <= bounds["lat_max"]
                and bounds["lng_min"] <= lng <= bounds["lng_max"]
            ):
                logger.warning(
                    "Skipping %s: out of area (%.4f, %.4f)", listing_id, lat, lng
                )
                skipped += 1
                continue

            # Convert optional fields — missing values become NULL in DB
            rooms = int(float(row["rooms"])) if row.get("rooms") else None
            size_m2 = float(row["size_m2"]) if row.get("size_m2") else None
            rent_eur = int(float(row["rent_eur"])) if row.get("rent_eur") else None

            # Log which fields are missing for traceability
            if rooms is None or size_m2 is None or rent_eur is None:
                missing = [k for k in ("rooms", "size_m2", "rent_eur") if not row.get(k)]
                logger.info("%s: NULL fields %s", listing_id, missing)

            # Create listing with point geometry in WKT format
            listing = Listing(
                listing_id=listing_id,
                geom=f"SRID=4326;POINT({lng} {lat})",
                rooms=rooms,
                size_m2=size_m2,
                rent_eur=rent_eur,
                property_type=row["property_type"],
                listed_date=row["listed_date"],
            )
            session.add(listing)
            inserted += 1

    session.commit()
    logger.info("Listings: %d inserted, %d skipped", inserted, skipped)


def seed_areas(session: Session) -> None:
    geojson_path = DATA_DIR / "helsinki_areas.geojson"

    with open(geojson_path) as f:
        data = json.load(f)

    for feature in data["features"]:
        props = feature["properties"]
        geom_json = json.dumps(feature["geometry"])

        session.execute(
            text(
                "INSERT INTO areas (area_code, area_name, geom) "
                "VALUES (:code, :name, ST_SetSRID(ST_GeomFromGeoJSON(:geom), 4326))"
            ),
            {
                "code": props["area_code"],
                "name": props["area_name"],
                "geom": geom_json,
            },
        )

    session.commit()
    logger.info("Areas: %d inserted", len(data["features"]))


def main() -> None:
    # Destructive re-seed: drops and recreates tables for a guaranteed clean state
    logger.info("Creating tables...")
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS listings CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS areas CASCADE"))
        conn.commit()
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        seed_areas(session)
        bounds = get_bounds_from_areas(session)
        logger.info("Derived bounds from areas: %s", bounds)
        seed_listings(session, bounds)

    logger.info("Seed complete.")


if __name__ == "__main__":
    main()
