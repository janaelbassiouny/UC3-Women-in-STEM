#prompt file for report checker

from llmclient import response


def main(self):
    self.detect_contradition_prompt
    self.detect_uncertain_prompt
    self.detect_charge_prompt


def detect_contradiction_prompt(report): #prompt to check errors
    Contradiction_prompt = f'''
    Review the report given. Identify any contradictions only. Do not suggest any changes or add anything that was not mentioned. 
    Identify factual contradictions only.
    Return JSON format. 
    Report: {report}
    '''

    response = client.responses.create(
        model = "gpt-5"
        input = Contradiction_prompt
    )

    return response.output.json()

def detect_uncertain_prompt(report): #prompt to check clairity
    Uncertain_prompt = f'''
    Review the report given. Identify vague or incomplete language. Identify unclear pronouns, names, places, and objects.
    Return JSON format. 
    Report: {report}
    '''
    response = client.responses.create(
        model = "gpt-5"
        input = Uncertain_prompt
    )

    return response.output.json()

def detect_charge_prompt(report): #prompt to check charges
    Charge_prompt = f'''
    Review the report given. The officer selected Charge X. Determine whether the facts support each legal element. Do not recommed other charges.
    Return JSON format. 
    
    Charge X: {charge_name}
    Elements: {elements}
    Report: {report}
    '''
    response = client.responses.create(
        model = "gpt-5"
        input = Charge_prompt
    )
    return response.output.json()

#def detect_grammer_spelling(report):