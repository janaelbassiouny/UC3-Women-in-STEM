from pydantic import BaseModel
from typing import Optional


class Report(BaseModel):
    officer_id: str
    officer_name: str

    report_date: str
    incident_date: str

    port_of_entry: str

    subject_name: str
    passport_number: Optional[str] = None
    nationality: Optional[str] = None

    arrival_method: str

    charge_code: str

    facts: str
    narrative: str
    evidence: str

    seized_items: Optional[str] = None

