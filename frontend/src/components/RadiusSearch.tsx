interface RadiusSearchProps {
  active: boolean;
  onToggle: () => void;
  radiusM: number;
  onRadiusChange: (r: number) => void;
  center: { lat: number; lng: number } | null;
  resultCount: number;
}

export default function RadiusSearch({
  active,
  onToggle,
  radiusM,
  onRadiusChange,
  center,
  resultCount,
}: RadiusSearchProps) {
  return (
    <div style={{ padding: 16, borderTop: "1px solid #ddd" }}>
      <h3 style={{ margin: "0 0 8px" }}>Radius Search</h3>
      <button
        onClick={onToggle}
        style={{
          padding: "6px 12px",
          background: active ? "#e74c3c" : "#3498db",
          color: "#fff",
          border: "none",
          borderRadius: 4,
          cursor: "pointer",
          width: "100%",
          marginBottom: 8,
        }}
      >
        {active ? "Cancel" : "Click map to search"}
      </button>

      {active && (
        <>
          <label style={{ display: "block", fontSize: 13, marginBottom: 8 }}>
            Radius: {radiusM}m
            <input
              type="range"
              value={radiusM}
              onChange={(e) => onRadiusChange(Number(e.target.value))}
              min={100}
              max={5000}
              step={100}
              style={{ display: "block", width: "100%", marginTop: 4 }}
            />
          </label>
          {center && (
            <div style={{ fontSize: 12, color: "#666" }}>
              Center: {center.lat.toFixed(4)}, {center.lng.toFixed(4)}
              <br />
              Found: <strong>{resultCount}</strong> listings
            </div>
          )}
        </>
      )}
    </div>
  );
}
