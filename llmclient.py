#llmclient file
#Handles all AI interactions for
#Contradiction detection, charge support analysis, grammar and spelling review, and vaugeness or incomplete wording.
#Returns structured JSON results that will show as separate corrections, not make a new file.

import os
import json
from openai import OpenAI 
from models.report import Report
from validators.missing_info import check_missing_info
from validators.charge_validator import validate_charge

client = OpenAI(
    api_key=os.environ.get("OPEN_API_KEY") 
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

report = Report()


def analyze_report(report: Report, charge, charge_elements: list): #main review functions that looks at the files
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
    charge_validation = validate_charge(report.model_dump())

    prompt = f'''
    PRELIMINARY VALIDATION RESULTS
    Missing Fields: {json.dumps(missing_fields, indent=4)}
    Charge Validation Results: {json.dumps(charge_validation, indent=4)}


    Report Information
    Officer: {report.officer_name}
    Subject: {report.subject_name}
    Charge Code: {report.charge_code}

    Facts: {report.facts}
    Narrative: {report.narrative}
    Evidence: {report.evidence}
    Seized items: {report.seized_items}
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
    response = client.responses.create(
        model = "gpt-5",
        instructions = SYSTEM_PROMPT,
        input = prompt
    )
    try:
        llm_results = json.loads(response.output_text)
        return {
            "missing_fields": missing_fields,
            "charge_validation": charge_validation,
            "llm_analysis": llm_results,
        }

    except json.JSONDecodeError:
        return {
            "error": "Invaild JSON response",
            "raw_response": response.output_text
        }
