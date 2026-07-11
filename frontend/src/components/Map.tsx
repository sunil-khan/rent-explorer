import { useState, useCallback, useMemo } from "react";
import ReactMapGL, {
  Source,
  Layer,
  Popup,
  NavigationControl,
  type MapLayerMouseEvent,
  type ViewStateChangeEvent,
} from "react-map-gl/maplibre";
import type { Map as MaplibreMap } from "maplibre-gl";
import type { Listing, BBox } from "../types";

const HELSINKI_CENTER = { longitude: 24.88, latitude: 60.22, zoom: 11 };

/** MapLibre stringifies GeoJSON properties — parse back to number or null */
const parseNum = (v: unknown): number | null => {
  if (v === null || v === undefined || v === "null" || v === "") return null;
  const n = Number(v);
  return isNaN(n) ? null : n;
};

// Choropleth interpolation stops for median_eur_per_m2
const CHOROPLETH_STOPS: (number | string)[] = [
  10,
  "#ffffcc",
  15,
  "#c2e699",
  20,
  "#78c679",
  25,
  "#31a354",
  30,
  "#006837",
];

interface MapProps {
  listings: Listing[];
  areaStats: GeoJSON.FeatureCollection | null;
  onBBoxChange: (bbox: BBox) => void;
  areaMedians?: Record<string, number>;
  onMapClick?: (lat: number, lng: number) => void;
  radiusCenter?: { lat: number; lng: number } | null;
  radiusMeters?: number;
}

function buildCirclePolygon(
  center: { lat: number; lng: number },
  radiusMeters: number
): GeoJSON.FeatureCollection {
  const points = 64;
  const coords: [number, number][] = [];
  const km = radiusMeters / 1000;
  for (let i = 0; i <= points; i++) {
    const angle = (i / points) * 2 * Math.PI;
    const dx = km / (111.32 * Math.cos((center.lat * Math.PI) / 180));
    const dy = km / 110.574;
    coords.push([
      center.lng + dx * Math.cos(angle),
      center.lat + dy * Math.sin(angle),
    ]);
  }
  return {
    type: "FeatureCollection",
    features: [
      {
        type: "Feature",
        geometry: { type: "Polygon", coordinates: [coords] },
        properties: {},
      },
    ],
  };
}

export default function Map({
  listings,
  areaStats,
  onBBoxChange,
  areaMedians,
  onMapClick,
  radiusCenter,
  radiusMeters = 1000,
}: MapProps) {
  const [selectedListing, setSelectedListing] = useState<Listing | null>(null);

  // Pre-compute area bounding boxes once (areas are rectangular grids)
  const areaBBoxes = useMemo(() => {
    if (!areaStats || !areaMedians) return [];
    return areaStats.features.map((feature) => {
      const areaCode = (feature.properties as { area_code: string }).area_code;
      const coords = (feature.geometry as GeoJSON.Polygon).coordinates[0];
      const lngs = coords.map((c) => c[0]);
      const lats = coords.map((c) => c[1]);
      return {
        median: areaMedians[areaCode],
        minLng: Math.min(...lngs),
        maxLng: Math.max(...lngs),
        minLat: Math.min(...lats),
        maxLat: Math.max(...lats),
      };
    }).filter((a) => a.median !== undefined);
  }, [areaStats, areaMedians]);

  const listingsGeoJSON: GeoJSON.FeatureCollection = useMemo(
    () => ({
      type: "FeatureCollection",
      features: listings.map((l) => {
        let valueScore: number | null = null;
        if (l.eur_per_m2 !== null && areaBBoxes.length > 0) {
          // Simplified bbox check — sufficient for rectangular grid areas
          for (const area of areaBBoxes) {
            if (
              l.longitude >= area.minLng &&
              l.longitude <= area.maxLng &&
              l.latitude >= area.minLat &&
              l.latitude <= area.maxLat
            ) {
              valueScore = area.median - l.eur_per_m2;
              break;
            }
          }
        }
        return {
          type: "Feature" as const,
          geometry: {
            type: "Point" as const,
            coordinates: [l.longitude, l.latitude],
          },
          properties: {
            ...l,
            value_score: valueScore ?? 0,
            has_value_score: valueScore !== null ? 1 : 0,
          },
        };
      }),
    }),
    [listings, areaBBoxes],
  );

  const circleGeoJSON = useMemo<GeoJSON.FeatureCollection | null>(() => {
    if (!radiusCenter || radiusMeters <= 0) return null;
    return buildCirclePolygon(radiusCenter, radiusMeters);
  }, [radiusCenter, radiusMeters]);

  const handleMoveEnd = useCallback(
    (e: ViewStateChangeEvent) => {
      const map = e.target as MaplibreMap;
      const bounds = map.getBounds();
      onBBoxChange({
        min_lng: bounds.getWest(),
        min_lat: bounds.getSouth(),
        max_lng: bounds.getEast(),
        max_lat: bounds.getNorth(),
      });
    },
    [onBBoxChange],
  );

  const handleClick = useCallback(
    (e: MapLayerMouseEvent) => {
      const feature = e.features?.[0];
      if (feature && feature.layer?.id === "listings-layer") {
        const props = feature.properties;
        if (props) {
          const listing: Listing = {
            listing_id: String(props.listing_id),
            latitude: Number(props.latitude),
            longitude: Number(props.longitude),
            rooms: parseNum(props.rooms),
            size_m2: parseNum(props.size_m2),
            rent_eur: parseNum(props.rent_eur),
            property_type: String(props.property_type),
            listed_date: String(props.listed_date),
            eur_per_m2: parseNum(props.eur_per_m2),
          };
          setSelectedListing(listing);
        }
      } else {
        setSelectedListing(null);
        if (onMapClick) {
          onMapClick(e.lngLat.lat, e.lngLat.lng);
        }
      }
    },
    [onMapClick],
  );

  return (
    <ReactMapGL
      initialViewState={HELSINKI_CENTER}
      style={{ width: "100%", height: "100%" }}
      mapStyle="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json"
      onMoveEnd={handleMoveEnd}
      onClick={handleClick}
      interactiveLayerIds={["listings-layer"]}
    >
      <NavigationControl position="top-right" />

      {/* Choropleth fill layer */}
      {areaStats && (
        <Source id="areas" type="geojson" data={areaStats}>
          <Layer
            id="areas-fill"
            type="fill"
            paint={{
              "fill-color": [
                "interpolate",
                ["linear"],
                ["coalesce", ["get", "median_eur_per_m2"], 0],
                ...CHOROPLETH_STOPS,
              ],
              "fill-opacity": 0.5,
            }}
          />
          <Layer
            id="areas-outline"
            type="line"
            paint={{ "line-color": "#333", "line-width": 1 }}
          />
        </Source>
      )}

      {/* Listings circle points with value signal colors */}
      <Source id="listings" type="geojson" data={listingsGeoJSON}>
        <Layer
          id="listings-layer"
          type="circle"
          paint={{
            "circle-radius": 5,
            "circle-color": [
              "case",
              ["==", ["get", "has_value_score"], 0],
              "#999",
              [
                "interpolate",
                ["linear"],
                ["get", "value_score"],
                -10, "#e74c3c",  // expensive (red)
                0, "#f1c40f",    // average (yellow)
                10, "#2ecc71",   // good value (green)
              ],
            ],
            "circle-stroke-width": 1,
            "circle-stroke-color": "#fff",
          }}
        />
      </Source>

      {/* Radius search circle */}
      {circleGeoJSON && (
        <Source id="radius-circle" type="geojson" data={circleGeoJSON}>
          <Layer
            id="radius-fill"
            type="fill"
            paint={{ "fill-color": "#3498db", "fill-opacity": 0.1 }}
          />
          <Layer
            id="radius-outline"
            type="line"
            paint={{ "line-color": "#3498db", "line-width": 2 }}
          />
        </Source>
      )}

      {/* Listing detail popup */}
      {selectedListing && (
        <Popup
          longitude={selectedListing.longitude}
          latitude={selectedListing.latitude}
          onClose={() => setSelectedListing(null)}
          closeOnClick={false}
        >
          <div style={{ fontSize: 13, lineHeight: 1.4 }}>
            <strong>{selectedListing.listing_id}</strong>
            <br />
            {selectedListing.rent_eur != null && (
              <>
                Rent: €{selectedListing.rent_eur}/mo
                <br />
              </>
            )}
            {selectedListing.size_m2 != null && (
              <>
                Size: {selectedListing.size_m2} m²
                <br />
              </>
            )}
            {selectedListing.eur_per_m2 != null && (
              <>
                €/m²: {selectedListing.eur_per_m2}
                <br />
              </>
            )}
            {selectedListing.rooms != null && (
              <>
                Rooms: {selectedListing.rooms}
                <br />
              </>
            )}
            Type: {selectedListing.property_type}
          </div>
        </Popup>
      )}
    </ReactMapGL>
  );
}
