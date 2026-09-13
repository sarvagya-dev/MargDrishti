import "leaflet/dist/leaflet.css";
import { MapContainer, TileLayer, CircleMarker, Popup } from "react-leaflet";
import { RISK_HEX } from "@/lib/risk";

export default function ClusterMap({ hotspot }) {
  const color = RISK_HEX[hotspot.risk_level];
  return (
    <MapContainer
      center={[hotspot.latitude, hotspot.longitude]}
      zoom={12}
      scrollWheelZoom={false}
      style={{ height: "100%", width: "100%" }}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <CircleMarker
        center={[hotspot.latitude, hotspot.longitude]}
        radius={14}
        pathOptions={{ color: "#1a2744", weight: 3, fillColor: color, fillOpacity: 0.55 }}
      >
        <Popup>
          <div style={{ minWidth: 150 }}>
            <div style={{ color: "#1a2744", fontWeight: 700 }}>{hotspot.road_segment}</div>
            <div style={{ fontSize: 12, color: "#475569" }}>{hotspot.location}</div>
            <div style={{ fontSize: 12, color, fontWeight: 700 }}>
              {hotspot.risk_level} · {hotspot.risk_score}
            </div>
          </div>
        </Popup>
      </CircleMarker>
    </MapContainer>
  );
}
