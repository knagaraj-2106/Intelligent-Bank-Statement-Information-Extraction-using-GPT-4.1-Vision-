import pdfplumber

def extract_text(pdf_path):
    complete_text=""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()

            if text:
                complete_text += text
    return complete_text