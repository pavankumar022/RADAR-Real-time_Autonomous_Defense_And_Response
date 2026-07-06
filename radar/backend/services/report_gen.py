import logging
import uuid
import json
from datetime import datetime, timezone
from typing import Optional

from backend.config import settings
from backend.services.playbook_gen import _generate_gemini, _generate_claude

log = logging.getLogger(__name__)

def _build_report_prompt(event: dict) -> str:
    # Format a human-readable timestamp from the ISO format
    ts_raw = event.get("timestamp", "unknown")
    try:
        dt = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
        # format like "May 2nd, 2026 at 09:18"
        day = dt.day
        if 4 <= day <= 20 or 24 <= day <= 30:
            suffix = "th"
        else:
            suffix = ["st", "nd", "rd"][day % 10 - 1]
        formatted_ts = dt.strftime(f"%B {day}{suffix}, %Y at %H:%M")
    except Exception:
        formatted_ts = ts_raw

    return f"""You are a senior SOC analyst. Generate a structured Incident Report for the following security alert.

ALERT DETAILS:
- Event Type: {event.get("event_type", "UNKNOWN")}
- Severity: {event.get("severity", "unknown").upper()}
- Source IP: {event.get("source_ip", "unknown")}
- Destination IP: {event.get("destination_ip", "unknown")}
- MITRE Technique: {event.get("technique_id", "unknown")} — {event.get("tactic", "unknown")}
- Description: {event.get("description", "No description")}
- Timestamp: {event.get("timestamp", "unknown")}

Respond ONLY with valid JSON in this exact structure (no markdown, no extra text):
{{
  "time_of_activity": "{formatted_ts}",
  "detected": "A brief sentence summarizing when and how the threat was first detected (e.g., {formatted_ts} via automated sniffer/SIEM)",
  "affected_entities": "List of affected entities (e.g., host machines, IP addresses, systems, user accounts)",
  "classification_reason": "Explain the reason for classifying this as a True Positive (TP) or False Positive (FP) based on the alert telemetry",
  "escalation_reason": "Explain why this alert warrants escalation to the Incident Response (IR) team (severity, impact, MITRE technique danger)",
  "remediation_actions": "List of recommended remediation actions (e.g., blocking IP, patching port, isolating host)",
  "attack_indicators": "List of specific attack indicators / IoCs (e.g., suspicious source IP, probed ports, payload details)"
}}

Be specific, technical, and professional. Reference the actual IP addresses and technique IDs from the alert."""

async def _generate_mock_report(event: dict) -> tuple[dict, str]:
    ts_raw = event.get("timestamp", "unknown")
    try:
        dt = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
        day = dt.day
        if 4 <= day <= 20 or 24 <= day <= 30:
            suffix = "th"
        else:
            suffix = ["st", "nd", "rd"][day % 10 - 1]
        formatted_ts = dt.strftime(f"%B {day}{suffix}, %Y at %H:%M")
    except Exception:
        formatted_ts = ts_raw

    result = {
        "time_of_activity": formatted_ts,
        "detected": f"Detected on {formatted_ts} via real-time network sniffer telemetry stream.",
        "affected_entities": f"Monitored host/destination host at {event.get('destination_ip', 'unknown')}.",
        "classification_reason": f"Classified as True Positive due to anomalous TCP probe burst matching signature patterns for {event.get('event_type', 'anomaly')}.",
        "escalation_reason": f"Escalated due to critical severity alert ({event.get('severity', 'unknown').upper()}) targeting internal systems, carrying potential for lateral movement (MITRE {event.get('technique_id', 'T1046')}).",
        "remediation_actions": f"1. Quarantine destination host {event.get('destination_ip', 'unknown')}\n2. Block attacker IP {event.get('source_ip', 'unknown')} at firewall\n3. Review auth logs.",
        "attack_indicators": f"Probes from source IP {event.get('source_ip', 'unknown')} targeting critical ports; event technique ID {event.get('technique_id', 'unknown')}."
    }
    return result, "MOCK_PROVIDER"

async def generate_report(event: dict, provider: Optional[str] = None, session_key: Optional[str] = None) -> dict:
    resolved_provider = provider or settings.effective_ai_provider
    prompt = _build_report_prompt(event)
    raw_text = ""

    try:
        if resolved_provider == "gemini" and (session_key or settings.has_gemini):
            parsed, raw_text = await _generate_gemini(prompt, api_key=session_key)
            actual_provider = "gemini"
        elif resolved_provider == "claude" and (session_key or settings.has_anthropic):
            parsed, raw_text = await _generate_claude(prompt, api_key=session_key)
            actual_provider = "claude"
        else:
            parsed, raw_text = await _generate_mock_report(event)
            actual_provider = "mock"
    except Exception as e:
        log.warning(f"AI report provider '{resolved_provider}' failed: {e}. Falling back to mock report.")
        parsed, raw_text = await _generate_mock_report(event)
        actual_provider = "mock"

    return {
        "id": str(uuid.uuid4()),
        "alert_id": event.get("id", ""),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "provider": actual_provider,
        "time_of_activity": parsed.get("time_of_activity", ""),
        "detected": parsed.get("detected", ""),
        "affected_entities": parsed.get("affected_entities", ""),
        "classification_reason": parsed.get("classification_reason", ""),
        "escalation_reason": parsed.get("escalation_reason", ""),
        "remediation_actions": parsed.get("remediation_actions", ""),
        "attack_indicators": parsed.get("attack_indicators", ""),
        "raw_response": raw_text,
    }
