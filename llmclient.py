#llmclient file
#Handles all AI interactions for
#Contradiction detection, charge support analysis, grammar and spelling review, and vaugeness or incomplete wording.
#Returns structured JSON results that will show as separate corrections, not make a new file.

import os
import json
from openai import * #lalalalalallalala
#from validators.missing_info import check_missing_info
#from validators.charge_validator import validate_charge
#from llm.llm_client import analyze_report

client = OpenAI(
    api_key=os.environ.get("gen_api_key") #this is a gemini api key cus the idk how to work the unissant one works rn. will look into others
)

System_prompt = f'''
You are an experienced law enforcement report reviewer. You review all types of police reports from all over the United States. 

Your responsibilites:
1. Identify contradictions in reports.
2. Identify grammar and spelling mistakes.
3. Identify unclear pronouns, names, places, and objects.
4. Identify vague or incomplete language.
5. Determine whether report facts support the selected charge given by the report.
6. DO NOT recommend alternatice charges.
7. DO NOT change or suggest different facts that are not already written.
8. Only evalute the charge provided.
9. Return strictly vaild JSON format. 
'''


def analyze_report(report_text, charge, charge_elements): #main review functions that looks at the files you guys made.
    prompt = f'''
    Report : {report_text}
    Officer Selected Charge: {charge}
    Charge Elements: {json.dumps(charge_elements, indent=4)}
    Charge List: #insert virginia laws pdf here?
    TASKS:
    
    A. Contradictions
    -Find conflicting or impossible statements.
    
    B. Vaugueness
    -Find incomplete wording. 
    -Find ambiguous references.
    -Find unsupported conclusions.
    
    C. Grammar and Spelling 
    -Find grammer mistakes.
    -Find spelling errors.
    -Suggest corrected wording.
    
    D. Charge Validation
    -Determine whether each listed element is supported by the facts in the report. 
    
    IMPORTANT:
    DO NOT recommend different charges. 
    
    Return JSON using this format: {{
        "Grammar_issues": [],
        "contradictions": [],
        "Vague_issues": [],
        "Charge_analysis: {{
            "supported": true,
            "missing_elements": []
        }},
        "Overall_comments": []
    }}
'''
    response = client.responses.create(
        model = "gpt-5",
        instructions = System_prompt,
        input = prompt
    )
    return response.output_text

#missing_results = check_missing_info(report)

#charge_results = validate_charge(report)

#ai_results = analyze_report(
    #report.narrative,
    #report.charge_name,
    #charge_results["elements"]
#)
