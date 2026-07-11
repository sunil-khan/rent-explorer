const LEGEND_ITEMS = [
  { label: "≤ €10/m²", color: "#ffffcc" },
  { label: "€15/m²", color: "#c2e699" },
  { label: "€20/m²", color: "#78c679" },
  { label: "€25/m²", color: "#31a354" },
  { label: "≥ €30/m²", color: "#006837" },
];

export default function Legend() {
  return (
    <div style={{ padding: 16, borderTop: "1px solid #ddd" }}>
      <h3 style={{ margin: "0 0 8px" }}>Median €/m² by Area</h3>
      {LEGEND_ITEMS.map((item) => (
        <div
          key={item.label}
          style={{ display: "flex", alignItems: "center", marginBottom: 4, fontSize: 12 }}
        >
          <div
            style={{
              width: 16,
              height: 16,
              backgroundColor: item.color,
              border: "1px solid #999",
              marginRight: 8,
              flexShrink: 0,
            }}
          />
          {item.label}
        </div>
      ))}
    </div>
  );
}
