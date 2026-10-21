#LLM client code for report checker

from openai import *

client = OpenAI()

response = client.responses.create(
    model='gpt-5',
    input=prompts
)