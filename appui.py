#interface for app
import json
from datetime import datetime
from pathlib import Path
import streamlit as st
from streamlit_pdf_viewer import pdf_viewer
import PyPDF2

from models.report import Report
from validators.missing_info import check_missing_info
from validators.charge_validator import validate_charge

from llm.llmclient import analyze_report
from database import save_report, get_reports, load_report
from export_pdf import export_results

BASE_DIR = Path(__file__).resolve().parent
with open(BASE_DIR / "data" / "charges.json", "r", encoding="utf-8") as f:
    charges = json.load(f)

def get_charge_description(charge_code):
    for charge in charges["charges"]:
        if charge["charge_id"] == charge_code:
            return charge
    return None

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

html, body, [class*="css"] {font-family:"Inter", sans-serif;}

.issue-card{background:white; border-radius:14px; padding:15px; margin-bottom:10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);}
.result-card {
    background-color: white;
    border: 1px solid #d1d5db;
    border-radius: 12px;
    padding: 15px;
    margin-bottom: 12px;
    box-shadow:
        0 2px 6px rgba(0,0,0,.08);
}.grammar {border-left:5px solid #3b82f6; padding:8px;}
.contradiction{border-left:5px solid #ef4444; padding:8px;}

.success{border-left:5px solid #22c55e; padding:8px;}
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
if "selected_issue" not in st.session_state:
    st.session_state.selected_issue = ""

#Sidebar

with st.sidebar:
    st.title("Reports")

    if st.button("New Report"):
        st.session_state.report_text = ""
        st.session_state.results = None
        st.rerun()

    st.divider()

    st.subheader("Saved Reports")

    history = get_reports()
    for row in history:
        report_id = row[0]
        report_name = row[1]

        if st.button(f"{report_name}", key=f"report_{report_id}"):
            loaded = load_report(report_id)
            st.session_state.report_text = loaded[0]
            st.session_state.results = json.loads(loaded[1])
            pdf_path = loaded[2]
            if pdf_path:
                with open(pdf_path, "rb") as file:
                    pdf_viewer(file.read())

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
    st.header("Report Review") #app explaination
    st.info("The AI will analyze the report for contradictions, grammar issues, vague language, and charge validation.\n")
    st.info("Please ensure the report is clear and complete before submission. The AI will not suggest alternative charges or modify facts.\n")
   
    st.subheader("Report Results")

    upload_file = st.file_uploader(
        "Upload Police Report",
        type=["txt", "pdf", "docx"]
    )
    SAVE_DIR = Path("saved_reports")
    SAVE_DIR.mkdir(exist_ok=True)

    pdf_path = None
    if upload_file:
        if upload_file.type == "application/pdf":
            pdf_path = (SAVE_DIR / upload_file.name)
            with open(pdf_path, "wb") as f:
                f.write(upload_file.getvalue())
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
        charge_info = next(
            (charge for charge in charges["charges"]
             if charge["charge_id"] == "8_USC_1325"),
            {},
        )
        st.divider()

        ai = results["ai"]
        st.header("Issues Found")

        #Missing Info
        st.subheader("Missing Information")
        for item in results["missing"]:
            st.markdown(f"""
                <div class="issue-card missing">
                <h5>Missing Information</h5>
                <b>{item}</b>
                </div>
                """, unsafe_allow_html=True)

        #Contradictions
        st.subheader("Contradictions")
        for item in results["ai"].get("contradictions", []):
            st.session_state.selected_issue = item
            st.markdown(f"""
                <div class="issue-card contradiction">
                    <h5>Contradiction</h5>
                    <p>{item}</p>
                </div>
                """, unsafe_allow_html=True)

        #Grammar
        st.subheader("Grammar")
        for item in results["ai"].get("grammar_issues", []):
            st.session_state.selected_issue = item
            st.markdown(f"""
                <div class="issue-card grammar">
                    <h5>Grammar Issue</h5>
                    <b>Original:</b>
                    {item['original']}
                    <br>
                    <b>Suggestion:</b>
                    {item['suggestion']}
                </div>
                """, unsafe_allow_html=True)

        #Vague Language 
        st.subheader("Vague Language")
        for item in results["ai"].get("vague_issues", []):
            st.session_state.selected_issue = item
            st.markdown(f"""
                <div class="issue-card vague">
                    <h5>Vague Language</h5>
                    <b>{item['text']}</b>
                    <br>
                    <b>Reason:</b>
                    {item['reason']}
                </div>
                """, unsafe_allow_html=True
                )
            
        charge_elements = []
        missing_elements = []

        charge_analysis = ai.get("llm_analysis", {}).get("Charge_analysis", {})
        if isinstance(charge_analysis, dict):
            missing_elements = charge_analysis.get("missing_elements", [])
            charge_elements = charge_analysis.get("supported_elements", [])

        st.subheader("Charge Elements")
        st.markdown(f"""
        <div class="result-card">
        <h5>Supported Elements:</h5>
        attempted entry
        <br><br>

        <b>Relevant Statute:</b>
        {charge_info.get("statute", "Not available")}
        </div>
        """, unsafe_allow_html=True)
        for element in charge_elements:
            if element not in missing_elements:
                st.markdown(f"- {element}")
            else:
                st.markdown(f"- {element} (Missing)")

        st.subheader("Charge Requirements")
        requirements_html = ""
        for req in charge_info.get("requirements",[]):
            requirements_html += f"""
            <li>{req}</li>
            """
        st.markdown(f"""
            <div class="result-card">
            <h5>Charge Requirements</h5>
            <ul>{requirements_html}</ul>
            </div> 
            """,
            unsafe_allow_html=True
            )

    st.divider()
#Law References

    st.divider()
    st.subheader("Legal Reference")

    charge_info = None
    if st.session_state.results:
        try:
            charge_info = next(
            (charge for charge in charges["charges"] 
            if charge["charge_id"] == "8_USC_1325"),
            None )
        except Exception:
            charge_info = None

    if charge_info:
        st.markdown( f"""
        <div class="result-card">
        <h4>{charge_info["statute"]}</h4>
        <p>{charge_info["description"]}</p>
        </div>""",
        unsafe_allow_html=True
        )

        source_file = charge_info.get("source_file")

        if source_file:
            law_file = (BASE_DIR / "data" / "extracted_text" / source_file)

            if law_file.exists():
                with st.expander("View Source Law"):
                    law_text = (law_file.read_text(encoding="utf-8"))
                    st.text_area("Referenced Statute",value=law_text,height=350)
            else:
                st.warning(f"Source file not found: {source_file}")

    else:
        st.info("No legal reference available.")


#Right Side Column: Report Display

with right_col:
    st.subheader("Police Report")
    if upload_file is not None:
        if upload_file.type == "application/pdf":
            st.markdown("""
            <div style="
                background:white; 
                padding:15px;
                border-radius:8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                margin-bottom: 20px;
                ">
                <h4>Uploaded PDF Report</h4>
            </div>
            """, unsafe_allow_html=True)
            pdf_viewer(upload_file.getvalue(), width=900)
        else:
            st.markdown("""
            <div style="
                background:white; 
                padding:15px;
                border-radius:8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                margin-bottom: 20px;
                ">
            """,unsafe_allow_html=True)
            st.text(st.session_state.report_text)
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("Upload a report to begin analysis.")
        
    st.divider()

    col1, col2 = st.columns(2)

    #Save Report

    with col1:
        if st.button("Save Report"):
            save_report(
                report_name = f"Report {datetime.now().strftime('%H:%M:%S')}",
                report_text = st.session_state.report_text,
                analysis_json = st.session_state.results,
                pdf_path = str(pdf_path) if pdf_path else None
            )
            st.success("Report Saved")
            st.write(get_reports())
    
    with col2:
        if st.button("Export Results"):
            pdf_file = export_results(st.session_state.results)
            with open(pdf_file, "rb") as f:
                st.download_button("Download PDF", f, file_name="PR_Results.pdf")

            st.success(
                "Export coming soon"
            )


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
