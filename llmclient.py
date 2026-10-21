#LLM client code for report checker

from openai import *

client = OpenAI()

response = client.responses.create(
    model='gpt-5', #need to check if this is the ai we're using
    input=prompts #link to prompts file?
)