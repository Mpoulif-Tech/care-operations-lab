"""Run a privacy-safe handover example."""

from .tools import build_shift_handover


def main() -> None:
    print(
        build_shift_handover(
            shift="Evening",
            unit="Sample unit",
            general_notes=["Common areas inspected"],
            follow_ups=[{"resident_id": "R-104", "task": "Confirm activity preference", "owner": "Next shift"}],
            safety_checks=[{"check": "Call bell test", "completed": True}],
        )
    )


if __name__ == "__main__":
    main()
