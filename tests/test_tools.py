import pytest

from care_operations_lab import (
    anonymize_incident_log,
    audit_medication_schedule,
    build_shift_handover,
    plan_resident_activities,
)


def test_shift_handover_uses_identifiers_and_statuses():
    result = build_shift_handover(
        shift="Night",
        unit="Demo",
        general_notes=["Hallway clear"],
        follow_ups=[{"resident_id": "R-101", "task": "Confirm transport time", "owner": "Day shift"}],
        safety_checks=[{"check": "Emergency exits", "completed": True}, {"check": "Supply count", "completed": False}],
    )
    assert "R-101" in result
    assert "Emergency exits: **completed**" in result
    assert "Supply count: **requires follow-up**" in result


def test_shift_handover_rejects_personal_details_as_identifier():
    with pytest.raises(ValueError):
        build_shift_handover(
            shift="Night",
            unit="Demo",
            general_notes=[],
            follow_ups=[{"resident_id": "First Last, room 9", "task": "Follow up"}],
            safety_checks=[],
        )


def test_incident_anonymizer_redacts_direct_identifiers():
    result = anonymize_incident_log(
        "Contact test@example.com or 514-555-0123. Postal code J6T 1A1. DOB: 1940-05-04."
    )
    assert "test@example.com" not in result["text"]
    assert "514-555-0123" not in result["text"]
    assert result["redaction_count"] == 4


def test_medication_schedule_audit_checks_documentation_only():
    result = audit_medication_schedule(
        [
            {
                "resident_id": "R-1",
                "medication": "Medication A",
                "date": "2026-08-15",
                "time": "08:00",
                "status": "administered",
                "initials": "HM",
            },
            {
                "resident_id": "R-2",
                "medication": "Medication B",
                "date": "2026-08-15",
                "time": "09:00",
                "status": "administered",
                "initials": "",
            },
        ]
    )
    assert result["complete"] is False
    assert result["issues"] == [{"row": 2, "code": "missing_initials", "field": "initials"}]
    assert "Administrative completeness" in result["disclaimer"]


def test_medication_schedule_audit_flags_duplicates():
    entry = {
        "resident_id": "R-1",
        "medication": "Medication A",
        "date": "2026-08-15",
        "time": "08:00",
        "status": "scheduled",
    }
    result = audit_medication_schedule([entry, entry])
    assert any(issue["code"] == "duplicate_schedule" for issue in result["issues"])


def test_activity_planner_respects_interests_accessibility_and_capacity():
    result = plan_resident_activities(
        [
            {"resident_id": "R-1", "interests": ["music"], "accessibility_needs": ["seated"]},
            {"resident_id": "R-2", "interests": ["gardening"], "accessibility_needs": ["large-print"]},
        ],
        [
            {"name": "Music circle", "tags": ["music"], "supports": ["seated"]},
            {"name": "Garden club", "tags": ["gardening"], "supports": []},
        ],
    )
    assert result["groups"]["Music circle"] == ["R-1"]
    assert result["unassigned"] == [{"resident_id": "R-2", "reason": "no compatible supplied activity"}]
