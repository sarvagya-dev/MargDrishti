from fastapi import FastAPI, HTTPException, status, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from typing import List, Dict, Any
from pathlib import Path
import uuid

# Resolve project root (directory containing this file)
PROJECT_ROOT = Path(__file__).parent

# Evidence video storage directory (created automatically if absent)
EVIDENCE_DIR = PROJECT_ROOT / "evidence"
EVIDENCE_DIR.mkdir(exist_ok=True)

# Allowed video MIME types and extensions for evidence uploads
ALLOWED_CONTENT_TYPES = {
    "video/webm", "video/mp4", "video/ogg",
    "video/quicktime", "video/x-msvideo",
}
ALLOWED_EXTENSIONS = {".webm", ".mp4", ".ogg", ".mov", ".avi"}

from database import (
    init_db, insert_event, get_all_events, get_event_by_id,
    insert_evidence, get_evidence_for_event, get_evidence_by_id,
    delete_events_by_source,
)
from models import (
    EventCreate, EventResponse, HotspotResponse,
    EvidenceResponse, EventWithEvidenceResponse,
)
import risk_engine
from demo_seed import seed_demo_hotspots

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite DB schema on startup (events + clusters tables)
    init_db()
    # Seed 3 demo hotspots (Mumbai/Pune/Jaipur) if database is empty.
    # Idempotent: does nothing when events already exist.
    seed_demo_hotspots()
    yield

app = FastAPI(
    title="MARG-DRISHTI Road-Risk Intelligence API",
    description="Backend ingestion + risk intelligence engine for vehicle telemetry events",
    version="2.0.0",
    lifespan=lifespan
)

# Enable CORS for all origins (prototype only)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GET / — simple health check
@app.get("/", status_code=status.HTTP_200_OK)
def health_check() -> Dict[str, str]:
    return {
        "status": "ok",
        "service": "MARG-DRISHTI Ingestion + Risk Backend",
        "version": "2.0.0"
    }

# POST /events — validate schema, store in SQLite, trigger risk engine
@app.post("/events", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
def create_event(event: EventCreate):
    try:
        event_dict = event.model_dump()
        stored_event = insert_event(event_dict)

        # Trigger risk_engine: clustering + chain detection + scoring
        risk_engine.process_event_hook(stored_event)

        return stored_event
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest event: {str(e)}"
        )

# GET /events — return all stored events (debugging only)
@app.get("/events", response_model=List[EventResponse], status_code=status.HTTP_200_OK)
def list_events():
    try:
        events = get_all_events()
        return events
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve events: {str(e)}"
        )

# GET /hotspots — return all clustered hotspots with risk scores
@app.get("/hotspots", response_model=List[HotspotResponse], status_code=status.HTTP_200_OK)
def list_hotspots():
    try:
        hotspots = risk_engine.get_hotspots()
        return hotspots
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compute hotspots: {str(e)}"
        )

# GET /phone — serve the phone sensor HTML interface
@app.get("/phone", status_code=status.HTTP_200_OK)
def serve_phone():
    phone_path = PROJECT_ROOT / "phone.html"
    if not phone_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="phone.html not found in project root"
        )
    return FileResponse(phone_path, media_type="text/html")


# ── POST /evidence ─────────────────────────────────────────────────────────────
# Accept a short video clip and link it to an existing event.
# Uses multipart/form-data; the binary is stored locally under evidence/
# and never uploaded to external services.
@app.post("/evidence", response_model=EvidenceResponse, status_code=status.HTTP_201_CREATED)
async def upload_evidence(event_id: int = Form(...), video: UploadFile = File(...)):
    # 1. Validate event exists
    event = get_event_by_id(event_id)
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event {event_id} not found"
        )

    # 2. Validate content type against allowlist (reject scripts, executables, etc.)
    ct = (video.content_type or "").lower()
    suffix = Path(video.filename or "").suffix.lower()
    if ct not in ALLOWED_CONTENT_TYPES and suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{ct}'. Only video files are accepted."
        )

    # 3. Generate a safe server-side filename — never use the client filename
    ext = suffix if suffix in ALLOWED_EXTENSIONS else ".webm"
    safe_name = f"event_{event_id}_{uuid.uuid4().hex}{ext}"
    file_path = EVIDENCE_DIR / safe_name

    # 4. Stream file to disk
    try:
        content = await video.read()
        file_path.write_bytes(content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save evidence file: {e}"
        )

    # 5. Persist evidence record in SQLite
    record = insert_evidence(
        event_id=event_id,
        filename=safe_name,
        file_path=str(file_path),
        content_type=ct or f"video{ext}",
    )

    return EvidenceResponse(
        id=record["id"],
        event_id=record["event_id"],
        content_type=record["content_type"],
        filename=record["filename"],
        created_at=record.get("created_at"),
        url=f"/evidence/{record['id']}",
    )


# ── GET /evidence/{evidence_id} ────────────────────────────────────────────────
# Stream the stored video so a browser can play it inline.
@app.get("/evidence/{evidence_id}")
def get_evidence_file(evidence_id: int):
    record = get_evidence_by_id(evidence_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evidence {evidence_id} not found"
        )
    fp = Path(record["file_path"])
    if not fp.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence file missing from server storage"
        )
    return FileResponse(fp, media_type=record["content_type"])


# ── GET /events/{event_id} ─────────────────────────────────────────────────────
# Return a single event with all linked evidence records.
@app.get("/events/{event_id}", response_model=EventWithEvidenceResponse)
def get_event_detail(event_id: int):
    event = get_event_by_id(event_id)
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event {event_id} not found"
        )
    evidence_rows = get_evidence_for_event(event_id)
    evidence_list = [
        EvidenceResponse(
            id=row["id"],
            event_id=row["event_id"],
            content_type=row["content_type"],
            filename=row["filename"],
            created_at=row.get("created_at"),
            url=f"/evidence/{row['id']}",
        )
        for row in evidence_rows
    ]
    return EventWithEvidenceResponse(**event, evidence=evidence_list)

# DELETE /events/simulator — safe cleanup of simulator-generated events only
@app.delete("/events/simulator", status_code=status.HTTP_200_OK)
def clear_simulator_events():
    """
    Delete all events where source='SIMULATOR'.
    Never deletes PHONE or DEMO_SEED events.
    
    The risk engine recalculates hotspots automatically on the next GET /hotspots
    call based on the remaining events. No manual recomputation needed.
    """
    try:
        deleted_count = delete_events_by_source('SIMULATOR')
        return {
            "status": "success",
            "deleted": deleted_count,
            "message": f"Deleted {deleted_count} simulator event(s). PHONE and DEMO_SEED events preserved."
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete simulator events: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
