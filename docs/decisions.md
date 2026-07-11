# Engineering Decisions

## Architecture

**FastAPI over Flask.** FastAPI provides auto-generated OpenAPI docs, built-in request validation via Pydantic, and async support. For a spatial API with typed query parameters, FastAPI reduces boilerplate significantly — endpoint parameter validation is declarative, not manual.

**SQLAlchemy + GeoAlchemy2 over raw SQL.** ORM for listings queries (type safety, composable filters), raw SQL for the area stats aggregation where PostgreSQL-specific syntax (`PERCENTILE_CONT`, `FILTER`, `ST_AsGeoJSON`) is cleaner than ORM gymnastics. Pragmatic mix, not dogmatic.

**react-map-gl + MapLibre GL JS.** WebGL-based rendering handles the listing count efficiently. MapLibre is fully open source (no API key). The same stack scales to deck.gl for millions of points without a rewrite.

**Service layer.** Routes stay thin (parameter parsing + response). Services contain query logic and are independently testable. At this scale it is light overhead; in a growing codebase it prevents route files from becoming unmanageable.

## Data Handling

**NULLs over skipping.** Three listings have missing fields (L0452: rooms, L0490: rent, L0687: size). We insert them with NULLs rather than discarding. This preserves data for queries that don't depend on the missing field — a listing with no rent still appears on the map and its location is valid for proximity search. Medians in `/areas/stats` exclude NULLs via `FILTER (WHERE ... IS NOT NULL)`.

**Out-of-area skip.** L0780 (lat 61.05) is ~95km north of Helsinki. Unlike missing fields, an out-of-area coordinate makes the listing fundamentally unusable for this dataset. We skip it on import and log the reason.

## Spatial Indexing

**GiST indexes** on both `listings.geom` and `areas.geom`. The bbox filter in `/listings` uses the `ST_Within` operator which leverages the GiST index for fast spatial lookup. The `/listings/near` endpoint casts to `geography` for accurate geodesic distance in meters rather than degrees.

**B-tree indexes** on `property_type`, `rooms`, `rent_eur` for attribute filter performance. At 850 rows these aren't necessary, but they signal awareness of query optimization for larger datasets.

## Frontend State

**Hooks over state library.** Three custom hooks (`useListings`, `useAreaStats`, `useNearbyListings`) manage all data fetching. No Redux/Zustand needed — the state is simple (filters + bbox + radius search) and flows one direction. Adding a state library for this would be over-engineering.

**Debounced bbox refetch.** Map pan/zoom triggers a 300ms debounced refetch of `/listings` with the new viewport bbox. This prevents flooding the API during continuous panning while keeping the map responsive.

## Trade-offs

| Chose | Over | Why |
|-------|------|-----|
| Query-time spatial join | Pre-computed area_code | Correctness over speed (see below) |
| All listings in one response | Pagination | 850 rows is small; pagination adds client complexity |
| Inline styles | CSS framework | Minimal UI scope; no build config overhead |
| Client-side median | Server-computed summary | Avoids extra endpoint; listings already in memory |
| Client-side value signal | Server-computed | Same data already available, no extra round-trip |

## Scalability

**Current state:** ~850 listings, 12 areas. All queries are sub-millisecond.

**At 100K listings:**
- Add pagination to `/listings` (cursor-based, not offset)
- Add map clustering (MapLibre supports Supercluster)
- `/areas/stats` stays fast with GiST indexes

**At 1M+ listings:**
- Materialized view for area stats, refreshed on schedule
- Vector tiles instead of GeoJSON for map rendering
- Connection pooling (PgBouncer)
- Read replicas for API queries
- Consider PostGIS `ST_ClusterKMeans` for dynamic clustering

## Non-Trivial Engineering Decision

**Query-time spatial join vs pre-computed area assignment**

When loading listings, we could pre-compute which area each listing belongs to and store `area_code` directly on the listing row. This makes `/areas/stats` a simple `GROUP BY area_code` — fast and index-friendly. Instead, we compute `ST_Contains(area.geom, listing.geom)` at query time.

We chose query-time joins because area boundaries are not immutable. In a real platform, districts get redrawn, new zones are added, boundaries are corrected. Pre-computing creates a dual-write problem: every boundary change requires reprocessing all listings, and stale assignments silently corrupt aggregations. With query-time joins, the next request automatically reflects updated boundaries — zero reprocessing, zero data integrity risk.

The cost is a spatial join on every `/areas/stats` call. For 850 listings × 12 areas with GiST indexes, this is sub-millisecond. At scale (millions of listings), the answer is a materialized view refreshed on a schedule — giving pre-computed read performance with query-time correctness, and the refresh interval becomes an explicit, tunable trade-off between freshness and cost.
