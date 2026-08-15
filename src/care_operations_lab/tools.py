"""Non-clinical workflow tools for privacy, continuity and documentation.

These functions organize supplied administrative data. They do not diagnose,
recommend treatment, calculate doses or replace professional judgment and
approved policies.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime
from typing import Any, Iterable, Mapping
import re


def build_shift_handover(
    *,
    shift: str,
    unit: str,
    general_notes: Iterable[str],
    follow_ups: Iterable[Mapping[str, str]],
    safety_checks: Iterable[Mapping[str, Any]],
) -> str:
    """Build a structured handover using identifiers instead of names."""
    lines = [
        f"# Shift handover — {shift.strip()}",
        "",
        f"**Unit:** {unit.strip()}",
        "",
        "## General observations",
    ]
    notes = [note.strip() for note in general_notes if note.strip()]
    lines.extend([f"- {note}" for note in notes] or ["- No general observation recorded."])
    lines += ["", "## Follow-ups"]
    follow_up_lines = []
    for item in follow_ups:
        identifier = _safe_identifier(item.get("resident_id", ""))
        task = item.get("task", "").strip()
        owner = item.get("owner", "Next shift").strip() or "Next shift"
        if task:
            follow_up_lines.append(f"- [ ] {identifier}: {task} — {owner}")
    lines.extend(follow_up_lines or ["- No follow-up recorded."])
    lines += ["", "## Safety checks"]
    check_lines = []
    for check in safety_checks:
        label = str(check.get("check", "Unnamed check")).strip()
        status = "completed" if check.get("completed") is True else "requires follow-up"
        check_lines.append(f"- {label}: **{status}**")
    lines.extend(check_lines or ["- No safety check recorded."])
    lines += ["", "_Administrative handover only. Follow employer policies and authorized clinical instructions._"]
    return "\n".join(lines).strip() + "\n"


def anonymize_incident_log(text: str) -> dict[str, Any]:
    """Redact common direct identifiers from an incident narrative."""
    patterns = [
        ("email", re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)),
        ("phone", re.compile(r"(?<!\d)(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}(?!\d)")),
        ("health_id", re.compile(r"\b[A-Z]{4}\s?\d{4}\s?\d{2}\b", re.I)),
        ("postal_code", re.compile(r"\b[A-Z]\d[A-Z][ -]?\d[A-Z]\d\b", re.I)),
        ("date_of_birth", re.compile(r"\b(?:DOB|date of birth|date de naissance)\s*[:=-]\s*\d{4}[-/]\d{2}[-/]\d{2}\b", re.I)),
    ]
    redacted = text
    counts = Counter()
    for label, pattern in patterns:
        redacted, count = pattern.subn(f"[REDACTED_{label.upper()}]", redacted)
        counts[label] += count
    return {"text": redacted, "redactions": dict(counts), "redaction_count": sum(counts.values())}


def audit_medication_schedule(entries: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Find administrative completeness issues without evaluating medication choices.

    The audit checks only record structure: resident identifier, medication
    label, scheduled time, status, initials when administered, and duplicate
    records. It never changes instructions or assesses clinical appropriateness.
    """
    rows = list(entries)
    issues: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, str]] = set()
    allowed_statuses = {"scheduled", "administered", "held", "refused", "not_available"}
    for row_number, entry in enumerate(rows, start=1):
        resident = str(entry.get("resident_id", "")).strip()
        medication = str(entry.get("medication", "")).strip()
        date = str(entry.get("date", "")).strip()
        time = str(entry.get("time", "")).strip()
        status = str(entry.get("status", "")).strip().lower()
        initials = str(entry.get("initials", "")).strip()
        required = {"resident_id": resident, "medication": medication, "date": date, "time": time, "status": status}
        for field, value in required.items():
            if not value:
                issues.append({"row": row_number, "code": "required", "field": field})
        if date:
            try:
                datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                issues.append({"row": row_number, "code": "invalid_date", "field": "date"})
        if time:
            try:
                datetime.strptime(time, "%H:%M")
            except ValueError:
                issues.append({"row": row_number, "code": "invalid_time", "field": "time"})
        if status and status not in allowed_statuses:
            issues.append({"row": row_number, "code": "invalid_status", "field": "status"})
        if status == "administered" and not initials:
            issues.append({"row": row_number, "code": "missing_initials", "field": "initials"})
        key = (resident.casefold(), medication.casefold(), date, time)
        if all(key):
            if key in seen:
                issues.append({"row": row_number, "code": "duplicate_schedule", "field": "record"})
            seen.add(key)
    return {
        "entry_count": len(rows),
        "complete": bool(rows) and not issues,
        "issues": issues,
        "disclaimer": "Administrative completeness check only; follow authorized medication records and employer policy.",
    }


def plan_resident_activities(
    participants: Iterable[Mapping[str, Any]], activities: Iterable[Mapping[str, Any]], max_group_size: int = 6
) -> dict[str, Any]:
    """Match stated preferences and accessibility needs to supplied activities."""
    available = list(activities)
    groups: dict[str, list[str]] = {str(activity["name"]): [] for activity in available}
    unassigned: list[dict[str, str]] = []
    for participant in participants:
        identifier = _safe_identifier(participant.get("resident_id", ""))
        interests = {str(value).casefold() for value in participant.get("interests", [])}
        needs = {str(value).casefold() for value in participant.get("accessibility_needs", [])}
        candidates = []
        for activity in available:
            name = str(activity["name"])
            tags = {str(value).casefold() for value in activity.get("tags", [])}
            supports = {str(value).casefold() for value in activity.get("supports", [])}
            if len(groups[name]) >= max_group_size or not interests.intersection(tags) or not needs.issubset(supports):
                continue
            candidates.append((len(interests.intersection(tags)), -len(groups[name]), name))
        if not candidates:
            unassigned.append({"resident_id": identifier, "reason": "no compatible supplied activity"})
            continue
        selected = max(candidates)[2]
        groups[selected].append(identifier)
    return {"groups": groups, "unassigned": unassigned}


def _safe_identifier(value: Any) -> str:
    identifier = str(value).strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,20}", identifier):
        raise ValueError("use a short resident identifier, not a name or personal detail")
    return identifier
