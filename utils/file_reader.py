import os
from typing import Optional
import docx
import PyPDF2
import csv

def extract_text_from_file(filepath: str) -> Optional[str]:
    ext = os.path.splitext(filepath)[-1].lower()
    
    if ext == ".txt":
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    
    elif ext == ".docx":
        doc = docx.Document(filepath)
        return "\n".join([para.text for para in doc.paragraphs])
    
    elif ext == ".pdf":
        text = ""
        with open(filepath, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() or ""
        return text
    
    else:
        raise ValueError(f"Unsupported file format: {ext}")


def parse_csv_records(filepath: str) -> list[dict]:
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)