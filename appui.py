#interface for app
import json
from datetime import datetime
import streamlit as st
import PyPDF2

from models.report import Report
from validators.missing_info import check_missing_info
from validators.charge_validator import validate_charge

from llm.llmclient import analyze_report
from database import save_report, get_reports, load_report


#Page configuration
st.set_page_config(
    page_title= "Police Report Analyzer",
    page_icon= "🚨",
    layout= "wide",
)

st.title("Police Report Analyzer")

#Custom css
st.markdown("""
<style>
.main {background-color:#f4f7c;}

.issue-red{border-left:5px solid #ef4444; padding:8px;}
.issue-yellow:{border-left:5px solid #f59e0b; padding:8px;}
.issue-green:{border-left:5px solid #22c55e; padding:8px;}

html, body, [class*="css"] {font-family:"Inter", sans-serif;}

</style>
""",
unsafe_allow_html=True)

#Session state variables
if "report_text" not in st.session_state:
    st.session_state.report_text = ""
if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = None
if "saved_reports" not in st.session_state:
    st.session_state.saved_reports = []
if "results" not in st.session_state:
    st.session_state.results = None

#Sidebar

with st.sidebar:
    st.title("Reports")

    if st.button("New Report"):
        st.session_state.report_text = ""
        st.session_state.results = None

    st.divider()

    st.subheader("Saved Reports")

    #history = get_reports()
    #for row in history:
        #report_id = row[0]
        #report_name = row[1]

        #if st.button(report_name, key=report_id):
            #loaded = load_report(report_id)
            #st.session_state.report_text = loaded[0]
            #st.session_state.results = json.loads(loaded[1])

#Score bar

score = 100
results = st.session_state.results
if st.session_state.results:
    score -= len(st.session_state.results["missing"]) * 5
    score -= len(
        st.session_state.results["ai"]
        .get("contradictions", [])
    ) * 10
    score -= len(
        st.session_state.results["ai"]
        .get("grammar_issues", [])
    ) * 2

score = max(score, 0)

st.metric(
    "Report Quality Score",
    f"{score}%"
)

st.progress(score / 100)


#Two columns layout

left_col, right_col = st.columns([1,2])

# Left column: Input/Review area
with left_col:
    st.subheader("Report Results")

    upload_file = st.file_uploader(
        "Upload Police Report",
        type=["txt", "pdf", "docx"]
    )
        
    if upload_file:
        if upload_file.type == "application/pdf":
            pdf = PyPDF2.PdfReader(upload_file)
            text = ""

            for page in pdf.pages:
                text += (page.extract_text() or "")

        else:
            text = upload_file.read().decode("utf-8")
        
        st.session_state.report_text = text

    if st.button("Analyze Report"):
        report = Report(
        officer_id = "123",
        officer_name = "John Doe",
        report_date = "2026-01-01",
        port_of_entry= "Entry Point", 
        traveler_name= "Traveler Name",
        travel_documents= "Documents",
        citizenship= "Citizenship",
        nationality= "Nationality",
        passport_number= None,
        claimed_status= "Status",
        purpose_of_travel= "Purpose",
        arrival_method= None,
        traveler_statements= "Statements",
        officer_observations= "Observations",
        inspection_findings= "Findings",
        charge_code= "8_USC_1325",
        ina_section= "Section",
        inadmissibility_explanation= "Explanation",
        traveler_response= "Response",
        officer_analysis_of_response= "Analysis",
        disposition= "Disposition",
        forms_used= "Forms Used",
        supervisory_review= "Review",
        service_acknowledgement="Acknowledgement",
        facts = st.session_state.report_text,
        narrative = st.session_state.report_text,
        evidence = " "
        )

        with st.spinner("Analyzing Report..."):
            missing = check_missing_info(report)
            charge_results = validate_charge(report.model_dump())
            ai_results = analyze_report(report, charge_results, [])
            st.session_state.results = {
                "missing": missing,
                "charge": charge_results,
                "ai": ai_results
            }

    results = st.session_state.results
    if results:
        st.divider()

        ai = results["ai"]
        st.subheader("Issues Found")

        #Missing Info
        st.subheader("Missing Information")
        for item in results["missing"]:
            with st.expander(f"Missing: {item}"):
                st.error(item)

        #Contradictions
        st.subheader("Contradictions")
        for item in results["ai"].get("contradictions", []):
            with st.expander("Potential Contradiction"):
                st.warning(item)

        #Grammar
        st.subheader("Grammar")
        for item in results["ai"].get("grammar_issues", []):
            with st.expander(item.get("original", "Grammar Issue")):
                st.error(item.get("reason", " "))
                st.success(item.get("suggestion", " "))

        #Vague Language 
        st.subheader("Vauge Language")
        for item in results["ai"].get("vauge_issues", []):
            with st.expander(item.get("text", "issue")):
                st.warning(item.get("reason", " "))

        st.subheader("Charge Elements")
        charge_analysis = ai.get("charge_analysis", {})
        missing_elements = (charge_analysis.get("missing_elements", []))

    st.divider()

    st.markdown("### Report Review") #app explaination
    st.info("The AI will analyze the report for contradictions, grammar issues, vague language, and charge validation.\n")
    st.info("Please ensure the report is clear and complete before submission. The AI will not suggest alternative charges or modify facts.\n")
   
    #chat box start
    st.markdown("### Review Chat")
    user_input = st.text_area("Enter your questions or comments about the report:", height=150)
    if st.button("Submit Review"):
        st.info("Thank you for your review. Your comments have been submitted.")
        if user_input:
            st.write("Your comments:")
            st.write(user_input)


#Right Side Column: Report Display

with right_col:
    st.subheader("Police Report Display")
    report_text = st.text_area(" ", value=st.session_state.report_text, height=700)
    st.session_state.report_text = report_text

    st.divider()

    if st.session_state.report_text:
        st.text_area("Report Content", value=st.session_state.report_text, height=400)
    else:
        st.info("Please upload a report to display its content.")

    col1, col2 = st.columns(2)

    st.subheader("Report Viewer")

    highlighted_text = (st.session_state.get("report_text", ""))
    if st.session_state.results:
        ai = (st.session_state.results["ai"])

        #grammar highlights
        for issue in ai.get("grammar_issues", []):
            original = issue.get("original", "")
            highlighted_text = (highlighted_text.replace(original, f"""
            <span style="background-color:#7dd3fc; padding:2px; "> {original} </span>
            """))

        #vague wording higlights
        for issue in ai.get("vague_issues", []):
            text = issue.get("text", "")
            highlighted_text = (highlighted_text.replace(text, f"""
            <span style="background-color:#fde68a; padding:2px;"> {text} </span> 
            """))

    st.markdown(highlighted_text, unsafe_allow_html=True)

    #Save Report

    with col1:
        if st.button("Save Report"):
            st.session_state.saved_reports.append(
                {
                "Name": f"Report {datetime.now().strftime('%H:%M:%S')}",
                "text": st.session_state.report_text,
                "results": st.session_state.results,
                }
            )
            st.success("Report Saved")
    
    with col2:
        if st.button("Export Results"):
            st.success(
                "Export coming soon"
            )

#Law References

if st.session_state.results:
    st.divider
    st.subheader("Legal References")

    charge_result = (st.session_state.results["charge"])
    st.json(charge_result)

#End Metrics

if st.session_state.results:
    results = st.session_state.results
    st.divider()

    m1, m2, m3, m4 = st.columns(4)

    m1.metric("Missing Fields", len(results["missing"]))
    m2.metric("Contradictions", len(results["ai"].get("contradictions", [])))
    m3.metric("Grammar Issues", len(results["ai"].get("grammar_issues", [])))
    charge_analysis = (results["ai"].get("charge_analysis", {}))
    m4.metric("Charge Supported", "✅"
              if charge_analysis.get(
                  "supported",
                  False
              )
              else "❌"
            )

#JSON Debug view
if st.session_state.results:
    with st.expander("Raw JSON Results"):
        st.json(st.session_state.results)
