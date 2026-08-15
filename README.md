# Care Operations Lab

Four privacy-first Python tools that demonstrate structured handovers, confidentiality, documentation checks and inclusive activity planning in care environments.

## Projects

| # | Project | Practical outcome |
|---|---|---|
| 14 | **Shift Handover Builder** | Creates structured, identifier-only shift notes and follow-ups. |
| 15 | **Incident Log Anonymizer** | Redacts common direct identifiers from incident narratives. |
| 16 | **Medication Schedule Audit** | Finds administrative completeness issues without assessing treatment. |
| 17 | **Resident Activity Planner** | Matches stated interests and accessibility needs to supplied activities. |

## Safety boundary

These projects are administrative portfolio demonstrations. They do **not** provide medical advice, diagnosis, dosage calculations, treatment recommendations or authorization to act. Real work must follow the employer's policies, authorized records, privacy rules and professional supervision.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest -q
python -m care_operations_lab
```

## Engineering choices

- Synthetic identifiers and examples only
- Explicit redaction and data-minimization controls
- Documentation checks separated from clinical judgment
- Type hints, validation and pytest coverage
- GitHub Actions CI with read-only repository permissions

These are personal portfolio projects, not client or employer systems.

## License

MIT © Henri Mpouli
