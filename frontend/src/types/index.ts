export interface Listing {
  listing_id: string;
  latitude: number;
  longitude: number;
  rooms: number | null;
  size_m2: number | null;
  rent_eur: number | null;
  property_type: string;
  listed_date: string;
  eur_per_m2: number | null;
}

export interface ListingNear extends Listing {
  distance_m: number;
}

export interface Filters {
  rent_min?: number;
  rent_max?: number;
  rooms?: number;
  property_type?: string;
}

export interface BBox {
  min_lng: number;
  min_lat: number;
  max_lng: number;
  max_lat: number;
}
