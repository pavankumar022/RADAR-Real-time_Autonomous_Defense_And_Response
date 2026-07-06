"""
RADAR — Playbook Router
POST /api/playbook/generate — generates AI IR playbook for a given alert ID
GET  /api/playbook/{alert_id} — retrieves existing playbook for an alert
"""
import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks

from backend import database as db
from backend.services import playbook_gen, report_gen
from backend.services.ws_manager import manager

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/playbook")


@router.post("/generate")
async def generate_playbook(request: dict, background_tasks: BackgroundTasks):
    """
    Generate an AI IR playbook for a given alert.
    Body: {"alert_id": "<uuid>", "provider": "gemini|claude|mock" (optional)}
    Returns the generated playbook immediately.
    """
    alert_id = request.get("alert_id")
    if not alert_id:
        raise HTTPException(400, "alert_id is required")

    # Check if already generated
    existing = await db.get_playbook_by_alert(alert_id)
    if existing:
        return existing

    # Load the event
    event = await db.get_event_by_id(alert_id)
    if not event:
        raise HTTPException(404, f"Alert {alert_id} not found")

    # Generate playbook
    provider = request.get("provider")
    session_key = request.get("key")

    # Check key presence
    from backend.config import settings as cfg
    has_key = False
    resolved_provider = provider or cfg.effective_ai_provider
    if session_key and session_key.strip():
        has_key = True
    else:
        if resolved_provider == "gemini" and cfg.has_gemini:
            has_key = True
        elif resolved_provider == "claude" and cfg.has_anthropic:
            has_key = True

    if not has_key:
        raise HTTPException(
            status_code=400,
            detail="Add your Gemini or Claude API key in Settings to enable AI-generated playbooks"
        )

    playbook = await playbook_gen.generate_playbook(event, provider=resolved_provider, session_key=session_key)

    # Persist
    await db.save_playbook(playbook)
    await db.mark_event_playbook_generated(alert_id)

    # Notify WS clients
    background_tasks.add_task(
        manager.broadcast,
        {"type": "playbook_generated", "payload": {"alert_id": alert_id, "playbook_id": playbook["id"]}},
    )

    return playbook


@router.get("/{alert_id}")
async def get_playbook(alert_id: str):
    """Retrieve existing playbook for an alert, or 404 if not generated yet."""
    playbook = await db.get_playbook_by_alert(alert_id)
    if not playbook:
        raise HTTPException(404, "Playbook not generated for this alert")
    return playbook


@router.post("/report")
async def generate_report_endpoint(request: dict):
    """
    Generate an AI incident report for a given alert.
    Body: {"alert_id": "<uuid>", "provider": "gemini|claude|mock" (optional), "key": "session_key" (optional)}
    """
    alert_id = request.get("alert_id")
    if not alert_id:
        raise HTTPException(400, "alert_id is required")

    # Check if already generated
    existing = await db.get_report_by_alert(alert_id)
    if existing:
        return existing

    # Load the event
    event = await db.get_event_by_id(alert_id)
    if not event:
        raise HTTPException(404, f"Alert {alert_id} not found")

    provider = request.get("provider")
    session_key = request.get("key")

    from backend.config import settings as cfg
    has_key = False
    resolved_provider = provider or cfg.effective_ai_provider
    if session_key and session_key.strip():
        has_key = True
    else:
        if resolved_provider == "gemini" and cfg.has_gemini:
            has_key = True
        elif resolved_provider == "claude" and cfg.has_anthropic:
            has_key = True

    if not has_key:
        raise HTTPException(
            status_code=400,
            detail="Add your Gemini or Claude API key in Settings to enable AI-generated reports"
        )

    report = await report_gen.generate_report(event, provider=resolved_provider, session_key=session_key)

    # Persist
    await db.save_report(report)

    return report


@router.get("/report/{alert_id}")
async def get_report_endpoint(alert_id: str):
    """Retrieve existing report for an alert, or 404 if not generated yet."""
    report = await db.get_report_by_alert(alert_id)
    if not report:
        raise HTTPException(404, "Report not generated for this alert")
    return report
