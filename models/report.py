from pydantic import BaseModel
from typing import Optional


class Report(BaseModel):
    officer_id: str
    officer_name: str

    report_date: str
    encounter_time: str
    port_of_entry: str

    traveler_name: str
    nationality: str
    citizenship: str

    passport_number: str | None = None
    claimed_status: str

    travel_documents: str
    purpose_of_travel: str
    arrival_method: str

    traveler_statements: str
    officer_observations: str
    inspection_findings: str

    charge_code: str
    ina_section: str
    inadmissibility_explanation: str

    traveler_response: str
    officer_analysis_of_response: str

    disposition: str
    forms_used: str
    supervisory_review: str
    service_acknowledgement: str

    narrative: str
    evidence: str

