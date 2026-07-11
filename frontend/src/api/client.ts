import type { Listing, ListingNear, Filters, BBox } from "../types";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export async function fetchListings(
  filters: Filters = {},
  bbox?: BBox,
  signal?: AbortSignal
): Promise<Listing[]> {
  const params = new URLSearchParams();

  if (bbox) {
    params.set("min_lng", String(bbox.min_lng));
    params.set("min_lat", String(bbox.min_lat));
    params.set("max_lng", String(bbox.max_lng));
    params.set("max_lat", String(bbox.max_lat));
  }
  if (filters.rent_min !== undefined) params.set("rent_min", String(filters.rent_min));
  if (filters.rent_max !== undefined) params.set("rent_max", String(filters.rent_max));
  if (filters.rooms !== undefined) params.set("rooms", String(filters.rooms));
  if (filters.property_type) params.set("property_type", filters.property_type);

  const resp = await fetch(`${API_URL}/listings?${params}`, { signal });
  if (!resp.ok) throw new Error(`Failed to fetch listings: ${resp.status}`);
  return resp.json();
}

export async function fetchAreaStats(signal?: AbortSignal): Promise<GeoJSON.FeatureCollection> {
  const resp = await fetch(`${API_URL}/areas/stats`, { signal });
  if (!resp.ok) throw new Error(`Failed to fetch area stats: ${resp.status}`);
  return resp.json();
}

export async function fetchListingsNear(
  lat: number,
  lng: number,
  radius_m: number,
  filters: Filters = {},
  signal?: AbortSignal
): Promise<ListingNear[]> {
  const params = new URLSearchParams({
    lat: String(lat),
    lng: String(lng),
    radius_m: String(radius_m),
  });
  if (filters.rent_min !== undefined) params.set("rent_min", String(filters.rent_min));
  if (filters.rent_max !== undefined) params.set("rent_max", String(filters.rent_max));
  if (filters.rooms !== undefined) params.set("rooms", String(filters.rooms));
  if (filters.property_type) params.set("property_type", filters.property_type);

  const resp = await fetch(`${API_URL}/listings/near?${params}`, { signal });
  if (!resp.ok) throw new Error(`Failed to fetch nearby listings: ${resp.status}`);
  return resp.json();
}
