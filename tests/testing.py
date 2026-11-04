#testing if the AI connects

from prompts import analyze_report

sample_report = """
The traveler stated he had no luggage. 
During inspection officers discovered three undelcared phones in his backpack.
The subject seemed suspicious. The traveler entered the United states with merchandise. 
"""

charge_name = "Failure to Declare Merchandise"

charge_elements = [
    "entered United states",
    "merchandise present",
    "not declared"
]

results = analyze_report(
    report_text=sample_report,
    charge_name=charge_name,
    charge_elements=charge_elements,
)

print("\nRESULTS")
response = (results)
