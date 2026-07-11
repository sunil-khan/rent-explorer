import type { Filters } from "../types";

interface FilterPanelProps {
  filters: Filters;
  onChange: (filters: Filters) => void;
}

export default function FilterPanel({ filters, onChange }: FilterPanelProps) {
  return (
    <div style={{ padding: 16 }}>
      <h3 style={{ margin: "0 0 12px" }}>Filters</h3>

      <label style={{ display: "block", marginBottom: 8, fontSize: 13 }}>
        Rent min (€)
        <input
          type="number"
          value={filters.rent_min ?? ""}
          onChange={(e) =>
            onChange({
              ...filters,
              rent_min: e.target.value ? Number(e.target.value) : undefined,
            })
          }
          style={{ display: "block", width: "100%", marginTop: 4, padding: 4 }}
          placeholder="0"
        />
      </label>

      <label style={{ display: "block", marginBottom: 8, fontSize: 13 }}>
        Rent max (€)
        <input
          type="number"
          value={filters.rent_max ?? ""}
          onChange={(e) =>
            onChange({
              ...filters,
              rent_max: e.target.value ? Number(e.target.value) : undefined,
            })
          }
          style={{ display: "block", width: "100%", marginTop: 4, padding: 4 }}
          placeholder="5000"
        />
      </label>

      <label style={{ display: "block", marginBottom: 8, fontSize: 13 }}>
        Rooms
        <select
          value={filters.rooms ?? ""}
          onChange={(e) =>
            onChange({
              ...filters,
              rooms: e.target.value ? Number(e.target.value) : undefined,
            })
          }
          style={{ display: "block", width: "100%", marginTop: 4, padding: 4 }}
        >
          <option value="">All</option>
          <option value="1">1</option>
          <option value="2">2</option>
          <option value="3">3</option>
          <option value="4">4</option>
        </select>
      </label>

      <label style={{ display: "block", marginBottom: 8, fontSize: 13 }}>
        Property type
        <select
          value={filters.property_type ?? ""}
          onChange={(e) =>
            onChange({
              ...filters,
              property_type: e.target.value || undefined,
            })
          }
          style={{ display: "block", width: "100%", marginTop: 4, padding: 4 }}
        >
          <option value="">All</option>
          <option value="apartment">Apartment</option>
          <option value="studio">Studio</option>
          <option value="townhouse">Townhouse</option>
        </select>
      </label>
    </div>
  );
}
