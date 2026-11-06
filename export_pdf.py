from reportlab.platypus import *
from reportlab.lib.styles import getSampleStyleSheet

def export_results(results, filename="report_review.pdf"):
    doc = SimpleDocTemplate(filename)
    styles = getSampleStyleSheet()
    elements = []
    
    elements.append(Paragraph("Police Report Analysis", styles["Title"]))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(str(results), styles["BodyText"]))

    doc.build(elements)

    return filename
