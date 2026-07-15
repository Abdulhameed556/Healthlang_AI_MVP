"""Extract text from DOCX files using python-docx."""
import io

from docx import Document


class DocxParser:
    def parse(self, content: bytes, file_type: str) -> str:
        doc = Document(io.BytesIO(content))
        return "\n".join(para.text for para in doc.paragraphs if para.text.strip())
