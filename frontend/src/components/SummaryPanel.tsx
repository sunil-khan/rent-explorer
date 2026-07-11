import { useMemo } from "react";
import type { Listing } from "../types";

interface SummaryPanelProps {
  listings: Listing[];
}

function median(values: number[]): number | null {
  if (values.length === 0) return null;
  const sorted = [...values].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 !== 0
    ? sorted[mid]
    : (sorted[mid - 1] + sorted[mid]) / 2;
}

export default function SummaryPanel({ listings }: SummaryPanelProps) {
  const medianEurPerM2 = useMemo(() => {
    const values = listings
      .map((l) => l.eur_per_m2)
      .filter((v): v is number => v !== null);
    return median(values);
  }, [listings]);

  return (
    <div style={{ padding: 16, borderTop: "1px solid #ddd" }}>
      <h3 style={{ margin: "0 0 8px" }}>Current View</h3>
      <div style={{ fontSize: 13 }}>
        <div>Listings: <strong>{listings.length}</strong></div>
        <div>
          Median €/m²:{" "}
          <strong>{medianEurPerM2 !== null ? medianEurPerM2.toFixed(1) : "—"}</strong>
        </div>
      </div>
    </div>
  );
}
