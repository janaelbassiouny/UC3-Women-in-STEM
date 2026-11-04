#llmclient file
#Handles all AI interactions for
#Contradiction detection, charge support analysis, grammar and spelling review, and vaugeness or incomplete wording.
#Returns structured JSON results that will show as separate corrections, not make a new file.

import os
import json
from time import sleep
from click import prompt
from google import genai
from pathlib import Path
from models.report import Report
from validators.missing_info import check_missing_info
from validators.charge_validator import validate_charge

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY") 
)

SYSTEM_PROMPT = f'''
You are an experienced law enforcement report reviewer. You review all types of police reports from all over the United States. 

Your responsibilites:
1. Identify contradictions in reports.
2. Identify grammar and spelling mistakes.
3. Identify unclear pronouns, names, places, and objects.
4. Identify vague or incomplete language.
5. Determine whether report facts support the selected charge given by the report.
6. DO NOT recommend alternative charges.
7. DO NOT change or suggest different facts that are not already written.
8. Only evalute the charge provided.
9. Return strictly vaild JSON format. Do not include markdown. Do not include explanations outside JSON.
'''


DATA_DIR = Path(__file__).resolve().parent.parent / "data"

def load_charges():
    with open(
        DATA_DIR / "charges.json",
        "r",
        encoding="utf-8"
    ) as file:
        return json.load(file)

def load_requirements():
    with open(
        DATA_DIR / "charge_requirements.json",
        "r",
        encoding="utf-8"
    ) as file:
        return json.load(file)


def analyze_report(report: Report, charges, charge_elements: list): #main review functions that looks at the files
    """
    Run full AI review on a report.

    Parameters:
    report : Report
        Shared Report object
    
    charge_elements: list
        Legal elements supplied by charge_validator.py
    
    Returns
    dict
        Parsed JSON results
    """

    missing_fields = check_missing_info(report)
    charges = load_charges()
    requirements = load_requirements()
    selected_charge = report.charge_code
    charge_info = next(
        (
            charge
            for charge in charges["charges"]
            if charge["charge_id"] == selected_charge
        ),
        None
    )
    
    charge_validation = validate_charge(report.model_dump())

    prompt = f'''
    PRELIMINARY VALIDATION RESULTS
    Missing Fields: {json.dumps(missing_fields, indent=4)}
    Charge Validation Results: {json.dumps(charge_validation, indent=4)}


    Report Information
    Officer: {report.officer_name}
    Traveler: {report.traveler_name}
    Charge Code: {report.charge_code}

    Narrative: {report.narrative}
    Evidence: {report.evidence}
    Inspection Findings: {report.inspection_findings}
    Charge Elements: {json.dumps(charge_elements, indent=4)}


    TASKS:
    
    A. Contradictions
    -Find conflicting or impossible statements.
    -Compare facts, narative, and evidence
    -Identify conflicting statements.
    -Identity impossible statements.
    -Inconsistent timelines.
    
    B. Vagueness
    -Identify unclear pronouns.
    -Identify missing details.
    -Find incomplete wording. 
    -Find ambiguous references.
    -Find unsupported conclusions.
    -Identify subjective wording.
    
    C. Grammar and Spelling 
    -Find grammer mistakes.
    -Find spelling errors.
    -Find punctuation issues.
    -Suggest corrected wording.
    
    D. Charge Validation
    -Determine whether each listed element is supported by the facts in the report. 
    
    IMPORTANT:
    DO NOT recommend different charges. 
    DO NOT suggest other charges
    
    Return JSON using this format: {{
        "Grammar_issues": [
        {{
            "original": "",
            "suggestion": "",
            "reason": "",
        }}
    ],
        "Contradictions": [
        ""
    ],
        "Vague_issues": [
        {{
            "text": "",
            "reason": "",
        }}
    ],
        "Charge_analysis": {{
            "supported": true,
            "missing_elements": []
        }},
        "Overall_comments": [
        ""
    ]
    }}
'''
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=f"""
                {SYSTEM_PROMPT}
                Return ONLY valid JSON.
                {prompt}
                """
            )
            break
        except Exception as e:
            print(f"Error occurred: {attempt + 1}")
            sleep(5)
    else:
        return {"error": "Failed to generate LLM response"}

    try:
        llm_results = json.loads(response.text)
        return {
            "missing_fields": missing_fields,
            "charge_validation": charge_validation,
            "llm_analysis": llm_results,
        }

    except json.JSONDecodeError:
        return {
            "error": "Invalid JSON response",
            "raw_response": response.text
        }


