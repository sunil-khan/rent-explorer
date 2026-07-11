import { useState, useEffect, useRef, useCallback } from "react";
import type { Listing, Filters, BBox } from "../types";
import { fetchListings } from "../api/client";

export function useListings(filters: Filters, bbox?: BBox) {
  const [listings, setListings] = useState<Listing[]>([]);
  const [loading, setLoading] = useState(true);
  const timeoutRef = useRef<ReturnType<typeof setTimeout>>();
  const abortRef = useRef<AbortController>();

  const load = useCallback(() => {
    // Cancel any in-flight request
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setLoading(true);
    fetchListings(filters, bbox, controller.signal)
      .then((data) => {
        if (!controller.signal.aborted) setListings(data);
      })
      .catch((err) => {
        if (err.name !== "AbortError") console.error(err); // TODO: surface errors to UI
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    filters.rent_min,
    filters.rent_max,
    filters.rooms,
    filters.property_type,
    bbox?.min_lng,
    bbox?.min_lat,
    bbox?.max_lng,
    bbox?.max_lat,
  ]);

  useEffect(() => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    timeoutRef.current = setTimeout(load, 300);
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      abortRef.current?.abort();
    };
  }, [load]);

  return { listings, loading };
}
