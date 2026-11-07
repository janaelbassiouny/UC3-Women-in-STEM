# llm/extractor.py
# Extracts the Report fields from raw report text.
# Anything that can't be found stays None, so the app keeps working and
# check_missing_info() can list what is missing.

import json
import re
from typing import Optional

from models.report import Report

# Fields that are filled directly from the full text instead of extracted
TEXT_FIELDS = {"facts", "narrative"}

# Everything else on the Report model gets extracted
EXTRACT_FIELDS = [name for name in Report.model_fields if name not in TEXT_FIELDS]

FIELD_HINTS = {
    "officer_id": "badge / employee / officer ID number",
    "report_date": "date of the report or encounter, as written",
    "port_of_entry": "port of entry, station, or location of the encounter",
    "travel_documents": "documents presented by the traveler",
    "passport_number": "passport number only if explicitly written",
    "claimed_status": "immigration/citizenship status the traveler claimed",
    "arrival_method": "how the traveler arrived (vehicle, air, on foot, etc.)",
    "traveler_statements": "what the traveler said",
    "officer_observations": "what the officer personally observed",
    "inspection_findings": "results of the inspection",
    "charge_code": "the charge identifier; must be one of the valid charge IDs provided",
    "ina_section": "INA section cited",
    "inadmissibility_explanation": "why the traveler was found inadmissible",
    "traveler_response": "how the traveler responded to the charge/findings",
    "officer_analysis_of_response": "officer's analysis of the traveler's response",
    "disposition": "final disposition / outcome",
    "forms_used": "forms listed as used or issued",
    "supervisory_review": "supervisory review or approval, if present",
    "service_acknowledgement": "service/acknowledgement of the charge, if present",
    "evidence": "evidence listed or referenced in the report",
}

def _clean(value) -> Optional[str]:
    """Turn the model's output into a string, or None if it's effectively blank."""
    if value is None:
        return None
    if isinstance(value, (list, tuple)):
        value = "; ".join(str(v) for v in value if v)
    elif isinstance(value, dict):
        value = "; ".join(f"{k}: {v}" for k, v in value.items() if v)
    value = str(value).strip()
    if value.lower() in ("", "null", "none", "n/a", "na", "not provided", "unknown"):
        return None
    return value


def extract_data_report(report_text: str, valid_charge_ids: Optional[list] = None) -> Report:
    """
    Build a Report from raw report text.

    - Never raises because of missing data or a failed model call.
    - Missing fields are None (check_missing_info reports them).
    - facts and narrative always hold the full report text.
    """
    values = {name: None for name in EXTRACT_FIELDS}

    if report_text and report_text.strip():
        field_lines = []
        for name in EXTRACT_FIELDS:
            hint = FIELD_HINTS.get(name)
            field_lines.append(f"- {name}" + (f": {hint}" if hint else ""))

        charge_line = ""
        if valid_charge_ids:
            charge_line = "\nValid charge IDs for charge_code: " + ", ".join(valid_charge_ids) + "\n"

        user_prompt = (
            "Extract these fields from the report below:\n"
            + "\n".join(field_lines)
            + "\n"
            + charge_line
            + f'\nREPORT TEXT:\n"""\n{report_text}\n"""'
        )

        try:
            raw = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()
            data = json.loads(raw)
            if isinstance(data, dict):
                for name in EXTRACT_FIELDS:
                    values[name] = _clean(data.get(name))
        except Exception as e:
            print(f"Report extraction failed: {e}")

        # Only keep a charge_code that actually exists in charges.json
        if valid_charge_ids and values.get("charge_code") not in valid_charge_ids:
            values["charge_code"] = None

    return Report(**values, facts=report_text or None, narrative=report_text or None)


def report_from_dict(data, fallback_text: Optional[str] = None):
    """
    Build a Report straight from a JSON dict whose keys match the Report fields.

    Returns (report, matched_count). matched_count is how many Report field names
    were present as keys, so the caller can tell whether the JSON really uses the
    Report layout (and fall back to extract_data_report if it doesn't).
    Missing keys become None; unknown keys are ignored.
    """
    if not isinstance(data, dict):
        return None, 0

    # Unwrap files shaped like {"report": {...}}
    if not any(k in Report.model_fields for k in data):
        for value in data.values():
            if isinstance(value, dict) and any(k in Report.model_fields for k in value):
                data = value
                break

    values = {}
    matched = 0
    for name in Report.model_fields:
        if name in data:
            matched += 1
        values[name] = _clean(data.get(name))

    # facts / narrative fall back to the file's text if the JSON doesn't have them
    if not values.get("facts"):
        values["facts"] = fallback_text
    if not values.get("narrative"):
        values["narrative"] = fallback_text

    return Report(**values), matched