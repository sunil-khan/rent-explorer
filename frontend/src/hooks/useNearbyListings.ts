import { useState, useEffect, useRef } from "react";
import type { ListingNear, Filters } from "../types";
import { fetchListingsNear } from "../api/client";

export function useNearbyListings(
  lat: number | null,
  lng: number | null,
  radiusM: number,
  filters: Filters = {}
) {
  const [listings, setListings] = useState<ListingNear[]>([]);
  const [loading, setLoading] = useState(false);
  const timeoutRef = useRef<ReturnType<typeof setTimeout>>();
  const abortRef = useRef<AbortController>();

  useEffect(() => {
    if (lat === null || lng === null || radiusM <= 0) {
      setListings([]);
      setLoading(false);
      return;
    }

    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    timeoutRef.current = setTimeout(() => {
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      setLoading(true);
      fetchListingsNear(lat, lng, radiusM, filters, controller.signal)
        .then((data) => {
          if (!controller.signal.aborted) setListings(data);
        })
        .catch((err) => {
          if (err.name !== "AbortError") console.error(err); // TODO: surface errors to UI
        })
        .finally(() => {
          if (!controller.signal.aborted) setLoading(false);
        });
    }, 300);

    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      abortRef.current?.abort();
    };
  }, [lat, lng, radiusM, filters.rent_min, filters.rent_max, filters.rooms, filters.property_type]);

  return { listings, loading };
}
