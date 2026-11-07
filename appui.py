#interface for app
import io
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
from llm.extractor import extract_data_report, report_from_dict
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
if "report_data" not in st.session_state:
    st.session_state.report_data = None  # parsed JSON upload, if any

#Sidebar

with st.sidebar:
    st.title("Reports")

    if st.button("New Report"):
        st.session_state.report_text = ""
        st.session_state.report_data = None
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
            st.session_state.report_data = None
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
        type=["txt", "pdf", "docx", "json"]
    )
    SAVE_DIR = Path("saved_reports")
    SAVE_DIR.mkdir(exist_ok=True)

    pdf_path = None
    if upload_file:
        file_bytes = upload_file.getvalue()
        text = ""
        st.session_state.report_data = None

        if upload_file.type == "application/pdf":
            pdf_path = (SAVE_DIR / upload_file.name)
            with open(pdf_path, "wb") as f:
                f.write(file_bytes)
            pdf = PyPDF2.PdfReader(io.BytesIO(file_bytes))

            for page in pdf.pages:
                text += (page.extract_text() or "") + "\n"

            if not text.strip():
                st.warning(
                    "No readable text was found in this PDF (it may be a scan). "
                    "All fields will be reported as missing."
                )

        elif upload_file.name.lower().endswith(".docx"):
            try:
                from docx import Document  # pip install python-docx
                doc = Document(io.BytesIO(file_bytes))
                text = "\n".join(p.text for p in doc.paragraphs)
            except Exception:
                st.warning("Could not read this .docx file.")

        elif upload_file.name.lower().endswith(".json"):
            try:
                parsed = json.loads(file_bytes.decode("utf-8-sig"))
                st.session_state.report_data = parsed
                text = json.dumps(parsed, indent=2)
            except Exception:
                st.error("Could not read this JSON file. Check that it is valid JSON.")

        else:
            text = file_bytes.decode("utf-8", errors="ignore")
        
        st.session_state.report_text = text

    if st.button("Analyze Report"):
        if not st.session_state.report_text.strip():
            st.warning("Upload a report with readable text first.")
        else:
            with st.spinner("Analyzing Report..."):
                valid_charge_ids = [c["charge_id"] for c in charges["charges"]]

                report = None

                # JSON that already uses the Report field names is loaded directly.
                if st.session_state.report_data is not None:
                    report, matched = report_from_dict(
                        st.session_state.report_data,
                        st.session_state.report_text,
                    )
                    if matched < 3:  # unfamiliar layout, so extract from the text instead
                        report = None

                # Otherwise pull the fields out of the report text. Anything not found is None.
                if report is None:
                    report = extract_data_report(
                        st.session_state.report_text,
                        valid_charge_ids,
                    )

                missing = check_missing_info(report)
                charge_results = validate_charge(report.model_dump())
                ai_results = analyze_report(report, charge_results, [])
                st.session_state.results = {
                    "report": report.model_dump(),
                    "missing": missing,
                    "charge": charge_results,
                    "ai": ai_results
                }

    results = st.session_state.results

    # charge code of the analyzed report (stored in results so it survives reruns
    # and saved-report loads; older saved reports won't have it)
    current_charge_code = None
    if results:
        current_charge_code = results.get("report", {}).get("charge_code")

    if results:
        charge_info = next(
            (charge for charge in charges["charges"]
             if charge["charge_id"] == current_charge_code),
            {},
        )
        st.divider()

        ai = results["ai"]

        #Extracted data
        extracted = results.get("report")
        if extracted:
            with st.expander("Extracted Report Data"):
                st.json({
                    k: v for k, v in extracted.items()
                    if k not in ("facts", "narrative")
                })

        st.header("Issues Found")

        #Missing Info
        st.subheader("Missing Information")
        if not results["missing"]:
            st.success("No missing information found.")
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
    if st.session_state.results and current_charge_code:
        charge_info = get_charge_description(current_charge_code)

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
        elif upload_file.name.lower().endswith(".json") and st.session_state.report_data is not None:
            st.json(st.session_state.report_data)
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
