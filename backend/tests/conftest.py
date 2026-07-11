import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.main import app


@pytest.fixture(scope="session")
def db_engine():
    engine = create_engine(settings.database_url)
    return engine


@pytest.fixture(scope="session")
def setup_test_data(db_engine):
    """Create test tables and data in a test schema, drop after all tests."""
    with db_engine.connect() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS test_rent"))
        conn.commit()

    # Create tables in test schema
    with db_engine.connect() as conn:
        conn.execute(text("SET search_path TO test_rent, public"))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS listings (
                listing_id VARCHAR PRIMARY KEY,
                geom geometry(Point, 4326) NOT NULL,
                rooms INTEGER,
                size_m2 NUMERIC(6,1),
                rent_eur INTEGER,
                property_type VARCHAR(20) NOT NULL,
                listed_date DATE NOT NULL
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS areas (
                area_code VARCHAR PRIMARY KEY,
                area_name VARCHAR(50) NOT NULL,
                geom geometry(Polygon, 4326) NOT NULL
            )
        """))
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_test_listings_geom ON listings USING gist (geom)"
        ))
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_test_areas_geom ON areas USING gist (geom)"
        ))

        # Insert test listings
        conn.execute(text("""
            INSERT INTO listings VALUES
            ('T001', ST_SetSRID(ST_MakePoint(24.94, 60.17), 4326), 2, 50.0, 1000, 'apartment', '2026-01-01'),
            ('T002', ST_SetSRID(ST_MakePoint(24.95, 60.18), 4326), 3, 80.0, 2000, 'townhouse', '2026-02-01'),
            ('T003', ST_SetSRID(ST_MakePoint(24.70, 60.22), 4326), 1, 30.0, 600, 'studio', '2026-03-01'),
            ('T004', ST_SetSRID(ST_MakePoint(24.94, 60.17), 4326), 2, 45.0, NULL, 'apartment', '2026-04-01'),
            ('T005', ST_SetSRID(ST_MakePoint(24.95, 60.18), 4326), 1, NULL, 800, 'studio', '2026-05-01')
        """))

        # Insert test areas
        conn.execute(text("""
            INSERT INTO areas VALUES
            ('T01', 'Test-West', ST_SetSRID(ST_MakeEnvelope(24.6, 60.15, 24.8, 60.25), 4326)),
            ('T02', 'Test-East', ST_SetSRID(ST_MakeEnvelope(24.8, 60.15, 25.0, 60.25), 4326))
        """))
        conn.commit()

    yield

    # Cleanup: drop test schema
    with db_engine.connect() as conn:
        conn.execute(text("DROP SCHEMA test_rent CASCADE"))
        conn.commit()


@pytest.fixture
def client(db_engine, setup_test_data):
    """TestClient that uses test schema."""
    def override_get_db():
        with Session(db_engine) as session:
            session.execute(text("SET search_path TO test_rent, public"))
            yield session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
