import sqlite3
import math
import os
from typing import List, Dict, Any, Optional

DB_FILE = os.path.join(os.path.dirname(__file__), "events.db")

def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db() -> None:
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # ── events ──────────────────────────────────────────────────────────
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vehicle_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                speed REAL NOT NULL,
                acceleration REAL NOT NULL,
                heading REAL NOT NULL,
                event_type TEXT NOT NULL,
                confidence REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                source TEXT DEFAULT 'PHONE'
            );
        """)
        
        # Migrate existing events table to add source column if it doesn't exist
        try:
            cursor.execute("ALTER TABLE events ADD COLUMN source TEXT DEFAULT 'PHONE'")
        except Exception:
            pass  # column already exists

        # ── logical spatial hotspots (persistent road-risk locations) ────────
        # One row per unique physical road location across all time windows.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hotspots (
                id TEXT PRIMARY KEY,
                centroid_lat REAL NOT NULL,
                centroid_lon REAL NOT NULL,
                cluster_count INTEGER NOT NULL DEFAULT 0
            );
        """)

        # ── temporal clusters (one burst of events in ≤5min, ≤50m, ≤30°) ───
        # Each cluster is linked to exactly one logical hotspot via hotspot_id.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clusters (
                id TEXT PRIMARY KEY,
                hotspot_id TEXT,
                centroid_lat REAL NOT NULL,
                centroid_lon REAL NOT NULL,
                avg_heading REAL NOT NULL,
                last_timestamp TEXT NOT NULL,
                first_timestamp TEXT NOT NULL,
                event_ids TEXT NOT NULL DEFAULT '',
                possible_chain INTEGER NOT NULL DEFAULT 0,
                risk_score INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'LOW',
                FOREIGN KEY (hotspot_id) REFERENCES hotspots(id)
            );
        """)

        # Migrate existing `clusters` rows that lack a hotspot_id column.
        # SQLite's ALTER TABLE only supports ADD COLUMN; ignore if already present.
        try:
            cursor.execute("ALTER TABLE clusters ADD COLUMN hotspot_id TEXT")
        except Exception:
            pass  # column already exists

        # ── evidence files (video clips linked to events) ──────────────────
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS evidence (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                content_type TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (event_id) REFERENCES events(id)
            );
        """)

        conn.commit()

# ─── Events ──────────────────────────────────────────────────────────────────

def insert_event(event_data: Dict[str, Any]) -> Dict[str, Any]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Get source from event_data, default to 'PHONE' if not provided
        source = event_data.get("source", "PHONE")
        cursor.execute("""
            INSERT INTO events (
                vehicle_id, timestamp, latitude, longitude,
                speed, acceleration, heading, event_type, confidence, source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event_data["vehicle_id"],
            event_data["timestamp"],
            event_data["latitude"],
            event_data["longitude"],
            event_data["speed"],
            event_data["acceleration"],
            event_data["heading"],
            event_data["event_type"],
            event_data["confidence"],
            source
        ))
        conn.commit()
        event_id = cursor.lastrowid
        inserted_record = dict(event_data)
        inserted_record["id"] = event_id
        inserted_record["source"] = source
        return inserted_record

def get_all_events() -> List[Dict[str, Any]]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, vehicle_id, timestamp, latitude, longitude, "
            "speed, acceleration, heading, event_type, confidence, created_at, source "
            "FROM events ORDER BY id ASC"
        )
        return [dict(row) for row in cursor.fetchall()]

def get_events_by_ids(event_ids: List[int]) -> List[Dict[str, Any]]:
    """Return full event rows for a list of event primary-key integers."""
    if not event_ids:
        return []
    placeholders = ",".join("?" * len(event_ids))
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT * FROM events WHERE id IN ({placeholders}) ORDER BY timestamp ASC",
            event_ids,
        )
        return [dict(row) for row in cursor.fetchall()]

def get_event_by_id(event_id: int) -> Optional[Dict[str, Any]]:
    """Return a single event row by primary key, or None if not found."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, vehicle_id, timestamp, latitude, longitude, "
            "speed, acceleration, heading, event_type, confidence, created_at, source "
            "FROM events WHERE id = ?",
            (event_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

# ─── Temporal Cluster helpers ─────────────────────────────────────────────────

def get_all_clusters() -> List[Dict[str, Any]]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM clusters")
        return [dict(row) for row in cursor.fetchall()]

def save_cluster(cluster: Dict[str, Any]) -> None:
    """Insert or replace a cluster row (keyed by id)."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO clusters
                (id, hotspot_id, centroid_lat, centroid_lon, avg_heading,
                 last_timestamp, first_timestamp, event_ids,
                 possible_chain, risk_score, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            cluster["id"],
            cluster.get("hotspot_id"),
            cluster["centroid_lat"],
            cluster["centroid_lon"],
            cluster["avg_heading"],
            cluster["last_timestamp"],
            cluster["first_timestamp"],
            cluster["event_ids"],
            int(cluster["possible_chain"]),
            cluster["risk_score"],
            cluster["status"],
        ))
        conn.commit()

def get_clusters_for_hotspot(hotspot_id: str) -> List[Dict[str, Any]]:
    """Return all temporal clusters that belong to the given logical hotspot."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM clusters WHERE hotspot_id = ?", (hotspot_id,)
        )
        return [dict(row) for row in cursor.fetchall()]

# ─── Logical Hotspot helpers ──────────────────────────────────────────────────

def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6_371_000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi  = math.radians(lat2 - lat1)
    dlam  = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))

def find_hotspot_near(lat: float, lon: float, radius_m: float) -> Optional[Dict[str, Any]]:
    """Return the nearest hotspot within radius_m, or None."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM hotspots")
        rows = cursor.fetchall()
    best, best_dist = None, float("inf")
    for row in rows:
        d = _haversine_m(lat, lon, row["centroid_lat"], row["centroid_lon"])
        if d < radius_m and d < best_dist:
            best, best_dist = dict(row), d
    return best

def save_hotspot(hotspot: Dict[str, Any]) -> None:
    """Insert or replace a logical hotspot row."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO hotspots
                (id, centroid_lat, centroid_lon, cluster_count)
            VALUES (?, ?, ?, ?)
        """, (
            hotspot["id"],
            hotspot["centroid_lat"],
            hotspot["centroid_lon"],
            hotspot["cluster_count"],
        ))
        conn.commit()

def get_all_hotspots() -> List[Dict[str, Any]]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM hotspots")
        return [dict(row) for row in cursor.fetchall()]

# ─── Evidence helpers ─────────────────────────────────────────────────────────

def insert_evidence(event_id: int, filename: str, file_path: str, content_type: str) -> Dict[str, Any]:
    """Store a new evidence record linked to an event and return the created row."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO evidence (event_id, filename, file_path, content_type)
            VALUES (?, ?, ?, ?)
        """, (event_id, filename, file_path, content_type))
        conn.commit()
        evidence_id = cursor.lastrowid
        cursor.execute("SELECT * FROM evidence WHERE id = ?", (evidence_id,))
        return dict(cursor.fetchone())

def get_evidence_for_event(event_id: int) -> List[Dict[str, Any]]:
    """Return all evidence rows linked to a given event_id."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM evidence WHERE event_id = ? ORDER BY id ASC",
            (event_id,)
        )
        return [dict(row) for row in cursor.fetchall()]

def get_evidence_by_id(evidence_id: int) -> Optional[Dict[str, Any]]:
    """Return a single evidence row by primary key, or None."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM evidence WHERE id = ?", (evidence_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

# ─── Event cleanup by source ──────────────────────────────────────────────────

def delete_events_by_source(source: str) -> int:
    """Delete all events with the specified source. Returns count of deleted rows."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM events WHERE source = ?", (source,))
        conn.commit()
        return cursor.rowcount
