import "leaflet/dist/leaflet.css";
import {
  MapContainer,
  TileLayer,
  Polyline,
  CircleMarker,
  Tooltip,
} from "react-leaflet";

const CENTER = [28.4595, 77.0266];
const BLOCKED_ROUTE = [
  [28.4595, 77.0266],
  [28.475, 77.035],
  [28.49, 77.045],
];
const ALTERNATE_ROUTE = [
  [28.4595, 77.0266],
  [28.452, 77.04],
  [28.465, 77.055],
  [28.49, 77.045],
];
const END_POINT = [28.49, 77.045];

export default function DriverRerouteMap() {
  return (
    <MapContainer
      center={CENTER}
      zoom={13}
      scrollWheelZoom={false}
      style={{ height: "100%", width: "100%" }}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <Polyline
        positions={BLOCKED_ROUTE}
        pathOptions={{ color: "var(--color-risk-high)", weight: 5 }}
      />
      <Polyline
        positions={ALTERNATE_ROUTE}
        pathOptions={{ color: "var(--color-risk-low)", weight: 5 }}
      />
      <CircleMarker
        center={CENTER}
        radius={8}
        pathOptions={{
          color: "#1a2744",
          weight: 2,
          fillColor: "#3b82f6",
          fillOpacity: 1,
        }}
      >
        <Tooltip direction="top" offset={[0, -10]} permanent>
          📍 You are here
        </Tooltip>
      </CircleMarker>
      <CircleMarker
        center={END_POINT}
        radius={8}
        pathOptions={{
          color: "#1a2744",
          weight: 2,
          fillColor: "var(--color-risk-high)",
          fillOpacity: 1,
        }}
      >
        <Tooltip direction="top" offset={[0, -10]} permanent>
          ⛔ Road Blocked
          <br />
          ✅ Rejoin NH-48
        </Tooltip>
      </CircleMarker>
    </MapContainer>
  );
}
