from pydantic import BaseModel, Field
from typing import Optional, Dict, List

class EventCreate(BaseModel):
    vehicle_id: str = Field(..., description="Unique vehicle identifier")
    timestamp: str = Field(..., description="ISO 8601 formatted timestamp string")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude in decimal degrees (-90 to 90)")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude in decimal degrees (-180 to 180)")
    speed: float = Field(..., ge=0.0, description="Speed in km/h")
    acceleration: float = Field(..., description="Acceleration in m/s²")
    heading: float = Field(..., ge=0.0, le=360.0, description="Heading in degrees (0 to 360)")
    event_type: str = Field(..., description="Type of event, e.g., HARD_BRAKING")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0 and 1")
    source: Optional[str] = Field(default="PHONE", description="Event source: PHONE, SIMULATOR, or DEMO_SEED")

class EventResponse(EventCreate):
    id: int
    created_at: Optional[str] = None

    class Config:
        from_attributes = True

class HotspotResponse(BaseModel):
    hotspot_id: str = Field(..., description="Unique cluster / hotspot identifier")
    latitude: float = Field(..., description="Centroid latitude of the cluster")
    longitude: float = Field(..., description="Centroid longitude of the cluster")
    risk_score: int = Field(..., ge=0, le=100, description="Anomaly-relative risk score (0–100)")
    status: str = Field(..., description="LOW | MEDIUM | HIGH")
    unique_vehicles: int = Field(..., description="Number of distinct vehicles that contributed events")
    total_events: int = Field(..., description="Total number of events in this cluster")
    event_breakdown: Dict[str, int] = Field(..., description="Count per event_type")
    possible_chain: bool = Field(..., description="True if consecutive-vehicle chain reaction was detected")
    first_detected: str = Field(..., description="ISO 8601 timestamp of the earliest event in cluster")
    last_observed: str = Field(..., description="ISO 8601 timestamp of the most recent event in cluster")


class EvidenceResponse(BaseModel):
    id: int
    event_id: int
    content_type: str
    filename: str
    created_at: Optional[str] = None
    # Playback URL derived at response time — not stored in DB
    url: str

    class Config:
        from_attributes = True


class EventWithEvidenceResponse(EventResponse):
    """EventResponse extended with a list of linked evidence clips."""
    evidence: List[EvidenceResponse] = []
