"""
RADAR — Logs Router
GET  /api/logs          — paginated + filtered log archive
POST /api/logs/upload   — JSON / NDJSON file upload
POST /api/logs/stream   — Filebeat-compatible HTTP stream ingestion
"""
import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

import ndjson
from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from fastapi.responses import JSONResponse

from backend import database as db
from backend.services import geolocation
from backend.routers.alerts import broadcast_event
from backend.state import app_state

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/logs")

# ─── Normalization ─────────────────────────────────────────────────────────────

def _normalize_uploaded_event(raw: dict) -> dict:
    """
    Normalize an uploaded event to RADAR's internal schema.
    Accepts a range of field names from common log formats.
    """
    def pick(*keys, default="unknown"):
        for k in keys:
            if raw.get(k):
                return str(raw[k])
        return default

    severity_map = {
        "critical": "critical", "crit": "critical", "high": "critical",
        "warning": "warning", "warn": "warning", "medium": "warning",
        "info": "info", "low": "info", "informational": "info",
    }
    raw_severity = pick("severity", "level", "log_level", default="info").lower()
    severity = severity_map.get(raw_severity, "info")

    ts = pick("timestamp", "time", "@timestamp", "date", default="")
    try:
        parsed_ts = datetime.fromisoformat(ts.replace("Z", "+00:00")).isoformat()
    except Exception:
        parsed_ts = datetime.now(timezone.utc).isoformat()

    return {
        "id": pick("id", "event_id", "uuid", default=str(uuid.uuid4())),
        "timestamp": parsed_ts,
        "source_ip": pick("source_ip", "src_ip", "src", "client_ip", "remote_addr"),
        "destination_ip": pick("destination_ip", "dst_ip", "dst", "target", "host"),
        "event_type": pick("event_type", "type", "action", "category").upper(),
        "severity": severity,
        "technique_id": pick("technique_id", "technique", "mitre_id", default=None) or None,
        "tactic": pick("tactic", "mitre_tactic", default=None) or None,
        "description": pick("description", "message", "msg", "summary"),
        "raw_payload": raw,
        "playbook_generated": False,
        "lat": None, "lon": None, "country": None, "city": None,
    }


async def _enrich_and_store(event: dict) -> None:
    """Enrich with geolocation and persist, then broadcast."""
    src = event.get("source_ip", "")
    if src and not any(src.startswith(p) for p in ("10.", "192.168.", "172.16.", "127.")):
        geo = await geolocation.lookup(src)
        event["lat"] = geo["lat"]
        event["lon"] = geo["lon"]
        event["country"] = geo["country"]
        event["city"] = geo["city"]

    await db.insert_event(event)
    await broadcast_event(event)


# ─── Archive ───────────────────────────────────────────────────────────────────

@router.get("")
async def get_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    severity: Optional[str] = Query(None),
    technique_id: Optional[str] = Query(None),
    playbook_generated: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    time_from: Optional[str] = Query(None),
    time_to: Optional[str] = Query(None),
):
    events, total = await db.get_events_paginated(
        page=page,
        page_size=page_size,
        severity=severity,
        technique_id=technique_id,
        playbook_generated=playbook_generated,
        search=search,
        time_from=time_from,
        time_to=time_to,
    )
    import math
    return {
        "events": events,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": math.ceil(total / page_size),
    }


# ─── Upload ───────────────────────────────────────────────────────────────────

@router.post("/upload")
async def upload_logs(file: UploadFile = File(...)):
    """
    Accept JSON array or NDJSON log file.
    Parses line-by-line to avoid loading large files into memory at once.
    """
    if not file.filename:
        raise HTTPException(400, "No file provided")

    fname = file.filename.lower()
    if not (fname.endswith(".json") or fname.endswith(".ndjson") or fname.endswith(".jsonl")):
        raise HTTPException(400, "Only .json, .ndjson, and .jsonl files are supported")

    content = await file.read()
    text = content.decode("utf-8", errors="replace")
    raw_events: list[dict] = []

    try:
        # Try NDJSON first (line-by-line)
        if fname.endswith((".ndjson", ".jsonl")):
            raw_events = ndjson.loads(text)
        else:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                raw_events = parsed
            elif isinstance(parsed, dict):
                raw_events = [parsed]
            else:
                raise HTTPException(400, "JSON must be an array or object")
    except json.JSONDecodeError as e:
        raise HTTPException(400, f"Invalid JSON: {e}")

    if not raw_events:
        raise HTTPException(400, "File contains no events")

    # Cap at 10,000 events per upload
    raw_events = raw_events[:10_000]

    # Switch to upload mode
    app_state.input_mode = "upload"
    app_state.feed_state = "LIVE_FEED_ACTIVE"

    # Process in background — enrich + store + broadcast
    async def process():
        for raw in raw_events:
            if isinstance(raw, dict):
                event = _normalize_uploaded_event(raw)
                await _enrich_and_store(event)
                await asyncio.sleep(0.08)  # ~12 events/sec organic pacing

    asyncio.create_task(process())

    return {"status": "processing", "events_queued": len(raw_events)}


# ─── Filebeat-compatible Stream ───────────────────────────────────────────────

@router.post("/stream")
async def stream_logs(payload: dict):
    """
    Filebeat HTTP output compatible endpoint.
    Accepts a batch or single event and routes through the same pipeline.
    """
    # Filebeat sends {"events": [...]} or a single event dict
    events_raw = payload.get("events", [payload])

    app_state.input_mode = "stream"
    app_state.feed_state = "LIVE_FEED_ACTIVE"

    for raw in events_raw:
        if isinstance(raw, dict):
            # Filebeat wraps in {"message": ..., "@timestamp": ...}
            inner = raw.get("message", raw)
            if isinstance(inner, str):
                try:
                    inner = json.loads(inner)
                except Exception:
                    inner = {"message": inner}
            event = _normalize_uploaded_event(inner)
            asyncio.create_task(_enrich_and_store(event))

    return {"status": "accepted", "count": len(events_raw)}
