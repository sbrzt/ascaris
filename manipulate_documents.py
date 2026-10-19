from PyPDF2 import PdfReader
from docx import Document as DocxDocument

ALLOWED_EXTENSIONS = {'docx', 'pdf', 'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def read_docx(uploaded_file):
    try:
        doc = DocxDocument(uploaded_file)
        text_content = ""
        for paragraph in doc.paragraphs:
            text_content += paragraph.text + "\n"
        return text_content
    except Exception as e:
        print(f"Error reading DOCX file: {e}")
        return None

def read_pdf(uploaded_file):
    try:
        pdf = PdfReader(uploaded_file)
        text_content = ""
        for page_num in range(len(pdf.pages)):
            page = pdf.pages[page_num]
            text_content += page.extract_text() + "\n"
        return text_content
    except Exception as e:
        print(f"Error reading PDF file: {e}")
        return None

def read_txt(uploaded_file):
    try:
        text_content = uploaded_file.read().decode('utf-8')
        return text_content
    except Exception as e:
        print(f"Error reading TXT file: {e}")
        return None