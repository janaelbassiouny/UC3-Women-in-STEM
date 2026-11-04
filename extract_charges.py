
from pathlib import Path
import pdfplumber

BASE_DIR = Path(__file__).resolve().parent
PDF_DIR = BASE_DIR / "legal_sources"
OUTPUT_DIR = BASE_DIR / "data" / "extracted_text"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

pdf_files = sorted(PDF_DIR.glob("*.pdf"))

if not pdf_files:
    print("No PDFs found in legal_sources.")
else:
    for pdf_path in pdf_files:
        pages = []

        with pdfplumber.open(pdf_path) as pdf:
            for page_number, page in enumerate(pdf.pages, start=1):
                text = page.extract_text() or ""
                pages.append(
                    f"--- Page {page_number} ---\n{text}"
                )

        output_path = OUTPUT_DIR / f"{pdf_path.stem}.txt"
        output_path.write_text(
            "\n\n".join(pages),
            encoding="utf-8"
        )

        print(f"Extracted: {pdf_path.name}")

    print("PDF text extraction complete!")
