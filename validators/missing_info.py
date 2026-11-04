# Check a report for missing information

required_fields = [
    "officer_id",
    "officer_name",
    "report_date",
    "incident_date",
    "port_of_entry",
    "subject_name",
    "arrival_method",
    "charge_code",
    "facts",
    "narrative",
    "evidence",
]
def check_missing_info(report):

    if hasattr(report, "model_dump"):
        report = report.model_dump()
    elif not isinstance(report, dict):
        return ["Invalid report: expected a dictionary or report model"]

    missing_fields = []

    for field in required_fields:
        value = report.get(field)

        if value is None:
            missing_fields.append(field)
        elif isinstance(value, str) and not value.strip():
            missing_fields.append(field)
        elif isinstance(value, (list, dict)) and not value:
            missing_fields.append(field)

    return missing_fields
