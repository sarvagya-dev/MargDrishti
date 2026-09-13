import "leaflet/dist/leaflet.css";
import { MapContainer, TileLayer, CircleMarker, Popup } from "react-leaflet";
import { useNavigate } from "@tanstack/react-router";
import { RISK_HEX } from "@/lib/risk";

export default function RiskMap({ hotspots, selectedId, onSelect }) {
  const navigate = useNavigate();

  return (
    <MapContainer
      center={[23, 82]}
      zoom={5}
      scrollWheelZoom
      style={{ height: "100%", width: "100%" }}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {hotspots.map((h) => {
        const color = RISK_HEX[h.risk_level];
        const active = selectedId === h.id;
        return (
          <CircleMarker
            key={h.id}
            center={[h.latitude, h.longitude]}
            radius={active ? 16 : 11}
            pathOptions={{
              color: active ? "#1a2744" : color,
              weight: active ? 3 : 2,
              fillColor: color,
              fillOpacity: 0.55,
            }}
            eventHandlers={{
              click: () => onSelect?.(h.id),
            }}
          >
            <Popup>
              <div style={{ fontFamily: "inherit", minWidth: 170 }}>
                <div style={{ color: "#1a2744", fontWeight: 700, fontSize: 14 }}>
                  {h.road_segment}
                </div>
                <div style={{ color: "#475569", fontSize: 12, marginTop: 2 }}>{h.location}</div>
                <div style={{ marginTop: 6, fontSize: 12, color: "#334155" }}>
                  Risk score: <strong style={{ color }}>{h.risk_score}</strong>
                </div>
                <div style={{ fontSize: 12, color, fontWeight: 700 }}>{h.risk_level} RISK</div>
                <button
                  type="button"
                  onClick={() =>
                    navigate({ to: "/authority/cluster/$id", params: { id: h.id } })
                  }
                  style={{
                    marginTop: 8,
                    width: "100%",
                    background: "#1a2744",
                    color: "#fff",
                    border: "none",
                    borderRadius: 4,
                    padding: "6px 8px",
                    fontSize: 12,
                    cursor: "pointer",
                  }}
                >
                  Investigate cluster
                </button>
              </div>
            </Popup>
          </CircleMarker>
        );
      })}
    </MapContainer>
  );
}
