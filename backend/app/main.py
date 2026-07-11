import asyncio
from contextlib import asynccontextmanager
import logging
import subprocess

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.routes.listings import router as listings_router
from app.routes.areas import router as areas_router
from app.database import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto-seed on startup if tables are empty
    needs_seed = True
    try:
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT EXISTS (SELECT FROM information_schema.tables "
                "WHERE table_schema = 'public' AND table_name = 'listings')"
            ))
            if result.scalar():
                count = conn.execute(text("SELECT count(*) FROM listings")).scalar()
                needs_seed = count == 0
    except Exception as e:
        logging.getLogger(__name__).warning("DB check failed, will seed: %s", e)

    if needs_seed:
        await asyncio.to_thread(subprocess.run, ["python", "-m", "scripts.seed"], check=True)
    yield


app = FastAPI(title="Rent Explorer API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(listings_router)
app.include_router(areas_router)


@app.get("/health")
def health():
    return {"status": "ok"}
