import pdfplumber
import docx

class DocumentParser:
    @staticmethod
    def extract_text_from_pdf(file_bytes_or_path) -> str:
        text = ''
        with pdfplumber.open(file_bytes_or_path) as pdf:
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + '\n'
        return text.strip()

    @staticmethod
    def extract_text_from_docx(file_bytes_or_path) -> str:
        doc = docx.Document(file_bytes_or_path)
        full_text = [para.text for para in doc.paragraphs if para.text]
        return '\n'.join(full_text).strip()

    @classmethod
    def parse_document(cls, uploaded_file) -> str:
        if hasattr(uploaded_file, 'seek'):
            uploaded_file.seek(0)
        name = uploaded_file.name.lower()
        if name.endswith('.pdf'):
            return cls.extract_text_from_pdf(uploaded_file)
        elif name.endswith('.docx'):
            return cls.extract_text_from_docx(uploaded_file)
        elif name.endswith('.txt'):
            raw_bytes = uploaded_file.read()
            try:
                return raw_bytes.decode('utf-8')
            except UnicodeDecodeError:
                return raw_bytes.decode('latin-1', errors='replace')
        else:
            raise ValueError(f'Unsupported file format: {name}')