import { useState, useCallback, useMemo } from "react";
import Map from "./components/Map";
import FilterPanel from "./components/FilterPanel";
import SummaryPanel from "./components/SummaryPanel";
import Legend from "./components/Legend";
import RadiusSearch from "./components/RadiusSearch";
import { useListings } from "./hooks/useListings";
import { useAreaStats } from "./hooks/useAreaStats";
import { useNearbyListings } from "./hooks/useNearbyListings";
import type { Filters, BBox } from "./types";

function App() {
  const [filters, setFilters] = useState<Filters>({});
  const [bbox, setBBox] = useState<BBox | undefined>();
  const { listings } = useListings(filters, bbox);
  const { data: areaStats } = useAreaStats();

  // Radius search state
  const [radiusActive, setRadiusActive] = useState(false);
  const [radiusCenter, setRadiusCenter] = useState<{ lat: number; lng: number } | null>(null);
  const [radiusM, setRadiusM] = useState(1000);
  const { listings: nearbyListings } = useNearbyListings(
    radiusCenter?.lat ?? null,
    radiusCenter?.lng ?? null,
    radiusM,
    filters
  );

  // Compute area medians for value signal
  const areaMedians = useMemo(() => {
    if (!areaStats) return undefined;
    const medians: Record<string, number> = {};
    for (const feature of areaStats.features) {
      const props = feature.properties as {
        area_code: string;
        median_eur_per_m2: number | null;
      };
      if (props.median_eur_per_m2 !== null) {
        medians[props.area_code] = props.median_eur_per_m2;
      }
    }
    return medians;
  }, [areaStats]);

  const handleBBoxChange = useCallback((newBBox: BBox) => {
    setBBox(newBBox);
  }, []);

  const handleMapClick = useCallback(
    (lat: number, lng: number) => {
      if (radiusActive) {
        setRadiusCenter({ lat, lng });
      }
    },
    [radiusActive]
  );

  return (
    <div style={{ display: "flex", height: "100vh" }}>
      <div
        style={{
          width: 280,
          flexShrink: 0,
          borderRight: "1px solid #ddd",
          overflowY: "auto",
          background: "#fafafa",
        }}
      >
        <FilterPanel filters={filters} onChange={setFilters} />
        <SummaryPanel listings={listings} />
        <Legend />
        <RadiusSearch
          active={radiusActive}
          onToggle={() => {
            setRadiusActive((prev) => {
              if (prev) setRadiusCenter(null);
              return !prev;
            });
          }}
          radiusM={radiusM}
          onRadiusChange={setRadiusM}
          center={radiusCenter}
          resultCount={nearbyListings.length}
        />
      </div>
      <div style={{ flex: 1, position: "relative", overflow: "hidden" }}>
        <Map
          listings={listings}
          areaStats={areaStats}
          areaMedians={areaMedians}
          onBBoxChange={handleBBoxChange}
          onMapClick={handleMapClick}
          radiusCenter={radiusCenter}
          radiusMeters={radiusM}
        />
      </div>
    </div>
  );
}

export default App;
