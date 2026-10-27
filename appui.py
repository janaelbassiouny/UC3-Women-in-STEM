#interface for app

import streamlit as st

#Page configuration
st.set_page_config(
    page_title= "Police Report Analyzer",
    page_icon= "🚨"
    layout= "wide",
)

st.title("Police Report Analyzer")

#Session state variables
if "report_text" not in st.session_state:
    st.session_state.report_text = ""

#Two columns layout

left_col, right_col = st.columns([1,2])

# Left column: Input/Review area
with left_col:
    st.subheader("Report Input")

    upload_file = st.file_uploader("Upload a police report (PDF or text)", type=["pdf", "txt"])

    if upload_file is not None: #file upload and get the text 
        if upload_file.type == "application/pdf":
            import PyPDF2
            pdf_reader = PyPDF2.PdfReader(upload_file)
            report_text = ""
            for page in pdf_reader.pages:
                report_text += page.extract_text()
        else:
            report_text = upload_file.read().decode("utf-8")

        st.session_state.report_text = report_text

    st.divider()

    st.markdown("### Report Review") #app explaination
    st.info("The AI will analyze the report for contradictions, grammar issues, vague language, and charge validation.\n")
    st.info("Please ensure the report is clear and complete before submission. The AI will not suggest alternative charges or modify facts.\n")
    st.info("The AI will return a JSON output with the following structure:\n"
            "```json\n"
            "{\n"
            '    "Grammar_issues": [],\n'
            '    "contradictions": [],\n'
            '    "Vague_issues": [],\n'
            '    "Charge_analysis": {\n'
            '        "supported": true,\n'
            '        "missing_elements": []\n'
            '    },\n'
            '    "Overall_comments": []\n'
            "}\n"
            "```\n"
        )
    
    #checker thingys
    st.markdown("### Grammar and Spelling Issues")
    st.info("No grammar or spelling issues found in the report.")  #replace with grammer file

    st.markdown("### Contradictions")
    st.info("No contradictions found in the report.") #replace with contradiction file

    st.markdown("### Vague or Incomplete Language")
    st.info("No vague or incomplete language found in the report.") #replace with imcomplete file

    st.markdown("### Charge Validation")
    st.info("The report supports the selected charge. All required elements are present.") #replace with charge file

    st.markdown("### Overall Comments")
    st.info("The report is clear, complete, and supports the selected charge. No issues were found during the analysis.")

    st.divider()

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
    report_text = st.text_area("Report Content", value=st.session_state.report_text, height=400)
    st.session_state.report_text = report_text

    if st.session_state.report_text:
        st.text_area("Report Content", value=st.session_state.report_text, height=400)
    else:
        st.info("Please upload a report to display its content.")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Check Report"):
            st.success(
                "Analysis started."
            )
    
    with col2:
        if st.button("Save Draft"):
            st.success(
                "Draft saved"
            )

    with col3:
        if st.button("Export Results"):
            st.succuess(
                "Export complete"
            )

#End Metrics

st.divider()
m1, m2, m3, m4 = st.columns(4)

m1.metrics("Issues Found", "0") 
m2.metrics("Charge Support", "100%")
m3.metrics("Grammar Score", "100%")
m4.metrics("Report Quality", "100%")

