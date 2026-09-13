# MARGDRISHTI

### Collective Road-Risk Intelligence from Distributed Vehicle Behaviour

MargDrishti is a prototype for identifying **potential road-risk hotspots from abnormal vehicle behaviour**.

The core idea is simple:

> Instead of depending only on dedicated road-inspection vehicles, use participating vehicles already travelling on the road as distributed sensing nodes.

A single hard-braking event is noisy and does not prove that a road is hazardous. MargDrishti is designed to correlate **independent, geo-tagged behavioural events** across space and time, then convert repeated patterns into a transparent risk signal for investigation.

---

## Why MargDrishti?

Road conditions can change between scheduled inspections. Individual incidents are also difficult to interpret in isolation.

MargDrishti explores a complementary approach:

```text
Vehicles already on the road
          ↓
Behaviour + telemetry + visual evidence
          ↓
Geo-tagged events
          ↓
Multi-vehicle correlation
          ↓
Spatial-temporal clustering
          ↓
Risk scoring
          ↓
Potential road-risk hotspot
          ↓
Authority investigation
```

The system deliberately treats collective abnormal behaviour as **evidence of potential risk**, not as proof of a specific road defect.

---

# Current Prototype

The current repository is a **working prototype/demo, not a production deployment**.

It currently demonstrates:

- A FastAPI backend for event ingestion and processing
- SQLite-based event storage
- Geo-tagged vehicle events
- A vehicle/event simulator
- Risk scoring and hotspot generation
- An authority-facing React dashboard
- Map-based hotspot visualization
- Cluster investigation views
- A phone-facing event interface
- Evidence/event video handling in the prototype
- Automatic dashboard refresh for new hotspot data

The authority dashboard polls the `/hotspots` endpoint every 3 seconds, allowing a newly submitted phone event to appear without manually refreshing the page.

---

# Prototype Demonstration Architecture

The current prototype can be demonstrated with the **phone and PC acting as different parts of the system**.

```text
                 VEHICLE / PHONE
              ┌──────────────────┐
              │ Phone interface   │
              │ GPS location      │
              │ Event input       │
              └────────┬─────────┘
                       │
                       │ HTTP event
                       ▼
              ┌──────────────────┐
              │   BACKEND ON PC  │
              │                  │
              │ FastAPI           │
              │ SQLite            │
              │ Risk Engine       │
              │ Event processing  │
              └────────┬─────────┘
                       │
                       ▼
              ┌──────────────────┐
              │ AUTHORITY UI     │
              │ React dashboard  │
              │ Hotspots / map    │
              │ Clusters / cases  │
              └──────────────────┘
```

For a local demonstration, the backend runs on the PC. A phone can access the phone event interface through the backend's reachable URL (for example, through a tunnel when the phone is outside the local network).

This is a **prototype demonstration architecture**. It should not be interpreted as a production deployment.

---

# Three-Stage Evolution

## Stage 1 — Vehicle Event → Central Risk Platform

**Current prototype stage**

A vehicle/phone generates an abnormal driving event with information such as:

- GPS
- speed
- acceleration/deceleration
- direction
- timestamp
- event type
- confidence

The event is sent to the central backend, stored, processed and surfaced on the authority dashboard.

```text
Phone / simulated vehicle
          ↓
      Event + GPS
          ↓
     FastAPI backend
          ↓
     Risk processing
          ↓
   Risk hotspot / dashboard
```

The prototype also supports controlled event simulation and seeded hotspot data for demonstration.

---

## Stage 2 — Collective Multi-Vehicle Correlation

The next stage is to move from individual events to **collective intelligence**.

```text
Vehicle A ──┐
Vehicle B ──┤
Vehicle C ──┼──→ Central platform
Vehicle D ──┤
Vehicle E ──┘
                  ↓
        Spatial-temporal correlation
                  ↓
               Cluster
                  ↓
             Risk score
```

The key question becomes:

> Are multiple independent vehicles exhibiting abnormal behaviour at approximately the same location and time?

Repeated correlated observations should increase confidence, while isolated observations should remain low-confidence signals.

This is the central idea behind MargDrishti's distributed sensing model.

---

## Stage 3 — Road Anomaly Classification

Once reliable correlated hotspots exist, the system can progress from detecting **where abnormal behaviour is occurring** toward estimating **what may be causing it**.

Potential future contextual signals include:

- vehicle behaviour
- dashcam vision
- weather
- traffic conditions
- road geometry
- historical patterns

These could help distinguish potential cases such as:

- potholes
- obstacles/debris
- waterlogging
- wrong-way traffic
- accidents
- road closures
- other road anomalies

Stage 3 is a **future development direction**, not a claim that every listed anomaly is currently detected by this repository.

---

# The Critical Design Principle

### Cluster ≠ Hazard

Multiple vehicles braking at one location does not automatically mean that there is a pothole.

Possible explanations include:

- traffic congestion
- a signal
- a pedestrian crossing
- a speed breaker
- another vehicle entering the lane
- an accident
- an actual road defect
- an obstruction
- poor visibility
- road construction

Therefore, MargDrishti uses collective abnormal behaviour as an **evidence signal** for identifying potential road-risk hotspots.

```text
Isolated event
     ↓
Insufficient evidence
     ↓
No immediate road-hazard declaration
```

versus:

```text
Multiple independent vehicles
          ↓
Similar abnormal behaviour
          ↓
Same road segment
          ↓
Appropriate time window
          ↓
Repeated observations
          ↓
Higher-confidence potential hotspot
```

A production system would require calibration against verified ground truth before its risk scores could be treated as operational predictions.

---

# Live Prototype Demonstration

A representative demonstration flow is:

```text
1. Normal traffic
       ↓
2. One abnormal event
       ↓
3. More events near the same location
       ↓
4. Events become spatially/temporally correlated
       ↓
5. Risk increases
       ↓
6. Hotspot appears on authority dashboard
       ↓
7. Investigator can inspect contributing evidence
```

The current prototype includes seeded hotspot/event data and supports injecting a real phone event. A new phone event can appear as a new hotspot on the authority dashboard after the dashboard's polling interval.

---

# Technology Stack

### Backend

- Python
- FastAPI
- Uvicorn
- SQLite
- REST APIs
- Custom risk/event processing logic

### Frontend

- React
- Vite
- JavaScript / JSX
- TypeScript components
- CSS/UI component system
- Map and dashboard interfaces

### Prototype Inputs

- Phone-based event interface
- Simulated vehicle events
- Geo-tagged event metadata
- Event/evidence data

---

# Repository Structure

```text
MargDrishti/
│
├── Backend/
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── risk_engine.py
│   ├── simulator.py
│   ├── demo_seed.py
│   ├── reset_db.py
│   ├── phone.html
│   ├── dashboard.html
│   ├── requirements.txt
│   └── test_*.py
│
├── Frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── context/
│   │   ├── lib/
│   │   ├── routes/
│   │   └── services/
│   ├── package.json
│   └── vite.config.ts
│
└── .gitignore
```

Runtime database files, Python bytecode, generated media and other local artifacts are intentionally excluded from version control.

---

# Running the Prototype Locally

## 1. Backend

From the project root:

```powershell
cd Backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The backend will be available at:

```text
http://localhost:8000
```

## 2. Frontend

Open a second terminal:

```powershell
cd Frontend
npm install
npm run dev
```

Use the URL printed by Vite.

## 3. Basic backend verification

```powershell
curl http://localhost:8000/
```

The prototype should return a healthy service response.

You can also inspect:

```text
/hotspots
/events
```

for hotspot and event data.

---

# Phone Demonstration

The backend exposes a phone-facing interface.

For a phone to reach the backend while it is running on the PC, the backend must be reachable from the phone. A tunnel can be used for the demonstration when required.

Example flow:

```text
Phone
  ↓
Phone event interface
  ↓
POST event
  ↓
PC backend
  ↓
SQLite + risk processing
  ↓
/hotspots
  ↓
Authority dashboard
```

The authority dashboard refreshes hotspot data periodically, so newly submitted events can become visible without a manual browser refresh.

---

# Production Architecture — Future

The eventual vehicle node should not continuously upload raw video.

A more practical architecture is:

```text
Camera + GPS + IMU / vehicle telemetry
                ↓
          Edge processing
                ↓
          Event detected?
                ↓
               YES
                ↓
       Preserve short clip
                ↓
     Attach telemetry + GPS
                ↓
          Upload event
```

During normal driving, a rolling local buffer can be maintained. When an abnormal event is detected, only the relevant surrounding clip and metadata need to be preserved/uploaded.

This can reduce:

- bandwidth
- cloud storage
- unnecessary video processing
- privacy exposure

Production deployments should also support **store-and-forward** behaviour for periods without connectivity.

---

# Future Roadmap

### Stage 1
**Vehicle event ingestion + central risk platform**

- Phone/vehicle event interface
- Event metadata
- Backend/API
- Risk scoring
- Authority dashboard

### Stage 2
**Collective intelligence**

- Multiple real participating vehicles
- Spatial-temporal clustering
- Independent-event correlation
- Improved confidence scoring
- Larger-scale event ingestion

### Stage 3
**Road anomaly intelligence**

- Vision-based contextual evidence
- Traffic/weather/road-context fusion
- Road anomaly classification
- Historical pattern analysis
- Better calibrated risk prediction

### Beyond Stage 3

The long-term direction is a **Road Risk Intelligence platform/API** that can provide risk information to road authorities, fleet operators, navigation systems and other relevant infrastructure.

---

# Project Status

**Status: Prototype / SIH demonstration**

This repository is not a production-deployed road monitoring system. It demonstrates the core technical concept and a path toward a distributed road-risk intelligence platform.

The current implementation focuses on:

```text
Vehicle events
+
Geo-tagged metadata
+
Event simulation
+
Risk processing
+
Hotspot visualization
+
Authority investigation
+
Evidence
```

---

## Core Concept

> **Make the vehicles already travelling on the road into distributed sensing nodes, and use their collective behaviour to surface potential road-risk hotspots.**

MargDrishti is intended as a complementary layer of road intelligence—not a replacement for formal road inspection or authority verification.
