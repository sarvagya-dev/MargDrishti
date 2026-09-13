# MARGDRISHTI

Build a React + Vite + Tailwind CSS app called MargDrishti — an AI-powered road risk intelligence system for Indian highways.

DESIGN SYSTEM

- Light theme only. White and light-neutral surfaces.

- Headings: navy #1a2744. Body: slate grey.

- Risk colours: red #dc2626 = HIGH, amber #d97706 = MEDIUM, green #16a34a = LOW

- No dark backgrounds, no neon, no gradients, no glassmorphism

- Feel: clean professional government GIS software

ROUTING

- /authority → Authority Overview (desktop layout)

- /authority/cluster/:id → Cluster Investigation (Phase 2)

- /authority/cases → Cases Page (Phase 3)

- /driver → Driver Interface (Phase 4)

Set up all routes now. /authority/cluster/:id, /authority/cases, /driver can be placeholder pages for now.

MOCK DATA — src/mock/data.js

export const hotspots = [

  { id: "HS001", road_segment: "NH-48", location: "Gurugram, Haryana", risk_score: 91, risk_level: "HIGH", confidence: 0.93, vehicle_count: 3, event_count: 7, latitude: 28.4595, longitude: 77.0266, direction: "Northbound", first_observed: "2024-01-15T14:12:00", last_observed: "2024-01-15T14:47:00", event_types: ["Sudden Deceleration", "Trajectory Deviation", "Road Anomaly"] },

  { id: "HS002", road_segment: "NH-44", location: "Panipat, Haryana", risk_score: 68, risk_level: "MEDIUM", confidence: 0.79, vehicle_count: 4, event_count: 6, latitude: 29.3909, longitude: 76.9635, direction: "Southbound", first_observed: "2024-01-15T13:05:00", last_observed: "2024-01-15T13:52:00", event_types: ["Hard Braking", "Trajectory Deviation"] },

  { id: "HS003", road_segment: "NH-27", location: "Lucknow, UP", risk_score: 44, risk_level: "LOW", confidence: 0.61, vehicle_count: 2, event_count: 3, latitude: 26.8467, longitude: 80.9462, direction: "Eastbound", first_observed: "2024-01-15T12:30:00", last_observed: "2024-01-15T12:48:00", event_types: ["Road Anomaly"] },

  { id: "HS004", road_segment: "NH-8", location: "Jaipur, Rajasthan", risk_score: 87, risk_level: "HIGH", confidence: 0.89, vehicle_count: 5, event_count: 9, latitude: 26.9124, longitude: 75.7873, direction: "Westbound", first_observed: "2024-01-15T11:20:00", last_observed: "2024-01-15T12:15:00", event_types: ["Sudden Deceleration", "Hard Braking", "Road Anomaly"] }

];

export const vehicles = {

  "HS001": [

    { id: "V-2841", event_type: "Sudden Deceleration", timestamp: "14:12" },

    { id: "V-3067", event_type: "Trajectory Deviation", timestamp: "14:28" },

    { id: "V-1195", event_type: "Road Anomaly", timestamp: "14:47" }

  ],

  "HS002": [

    { id: "V-4421", event_type: "Hard Braking", timestamp: "13:05" },

    { id: "V-2093", event_type: "Trajectory Deviation", timestamp: "13:22" },

    { id: "V-3814", event_type: "Hard Braking", timestamp: "13:40" },

    { id: "V-1756", event_type: "Trajectory Deviation", timestamp: "13:52" }

  ],

  "HS003": [

    { id: "V-5102", event_type: "Road Anomaly", timestamp: "12:30" },

    { id: "V-3388", event_type: "Road Anomaly", timestamp: "12:48" }

  ],

  "HS004": [

    { id: "V-6201", event_type: "Sudden Deceleration", timestamp: "11:20" },

    { id: "V-4477", event_type: "Hard Braking", timestamp: "11:35" },

    { id: "V-2930", event_type: "Road Anomaly", timestamp: "11:52" },

    { id: "V-5543", event_type: "Sudden Deceleration", timestamp: "12:05" },

    { id: "V-1847", event_type: "Hard Braking", timestamp: "12:15" }

  ]

};

export const cases = [

  { id: "CA-001", hotspot_id: "HS004", road_segment: "NH-8", location: "Jaipur", risk_level: "HIGH", status: "IN_PROGRESS", assigned_to: "Officer Sharma", created_at: "2024-01-15T11:30:00" },

  { id: "CA-002", hotspot_id: "HS002", road_segment: "NH-44", location: "Panipat", risk_level: "MEDIUM", status: "ASSIGNED", assigned_to: "Officer Patel", created_at: "2024-01-15T13:10:00" }

];

export const chartData = {

  eventsOverTime: [

    { day: "Mon", events: 3 }, { day: "Tue", events: 5 }, { day: "Wed", events: 4 },

    { day: "Thu", events: 8 }, { day: "Fri", events: 6 }, { day: "Sat", events: 9 }, { day: "Sun", events: 7 }

  ],

  eventTypes: [

    { type: "Sudden Decel.", count: 8 }, { type: "Hard Braking", count: 6 },

    { type: "Traj. Deviation", count: 5 }, { type: "Road Anomaly", count: 6 }

  ],

  caseStatus: [

    { status: "Open", count: 3 }, { status: "In Progress", count: 2 }, { status: "Resolved", count: 5 }

  ]

};

SERVICE LAYER — src/services/api.js

Import from mock data. Export these functions:

- getHotspots() → returns hotspots array

- getHotspotDetails(id) → returns single hotspot + its vehicles from vehicles[id]

- getDriverAlert() → returns { state: "CLEAR" } initially

- createCase(hotspotId) → creates new case, adds to cases array, returns it

- updateCaseStatus(caseId, status) → updates case in array, returns updated case

- triggerDriverAlert(hotspotId) → sets a module-level driverAlertState to "HIGH_RISK"

GLOBAL STATE — src/context/AppContext.jsx

Create a React context that holds:

- cases array (initialised from mock cases)

- driverAlertState (initialised as "CLEAR")

- addCase(newCase) function

- updateCase(caseId, status) function

- setDriverAlert(state) function

Wrap the entire app in this provider.

AUTHORITY OVERVIEW PAGE

Top nav (compact):

- Left: "MargDrishti" in navy bold

- Right: Overview | Cases | Driver View

- Cases → /authority/cases

- Driver View → /driver

Metrics row — 5 compact tiles:

High-Risk Hotspots: 2 | Active Clusters: 4 | Events Today: 25 | Contributing Vehicles: 14 | Open Cases: 3

Main two-column layout:

LEFT 65%: react-leaflet map, OpenStreetMap tiles, centred on India lat 23 lng 82 zoom 5

- Circle markers coloured by risk level

- Click marker: highlight it, show popup (road segment, risk score, risk level), navigate to /authority/cluster/:id

RIGHT 35%: Active Risk Clusters list

- Compact card per hotspot: road segment, risk badge, score, vehicle+event count

- Sorted HIGH → MEDIUM → LOW

- Click card → /authority/cluster/:id

Below layout — 3 small recharts:

1. Line chart: Risk Events Last 7 Days

2. Bar chart: Event Types Today

3. Pie chart: Case Status

All data via service layer only.

This project was built with [Lovable](https://lovable.dev).

## Build with Lovable

Continue developing this project in the [Lovable editor](https://lovable.dev/projects/92d17371-9186-4df7-bb85-33c87a0b970f).

- **Ship faster**: describe what you want to build and Lovable handles the code.
- **Stay in sync**: every change made in Lovable is committed straight to this repository.
- **Full ownership**: this code is yours. Push to `main` on GitHub and your changes sync back into Lovable, ready for your next prompt.

## Development

Prefer working locally? You need Node.js and npm — [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating).

```sh
git clone <this-repository-url>
cd <repository-name>
npm i
npm run dev
```
