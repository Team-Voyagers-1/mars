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



def parse_csv_records(csv_file_path: str):
    records = []

    with open(csv_file_path, mode="r", encoding="utf-8-sig") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            record = {
                "summary": row.get("summary", "").strip(),
                "project": row.get("project", "").strip(),
                "description": row.get("description", "").strip(),
                "issuetype": row.get("issuetype", "Story").strip(),
                "sprint": row.get("sprint", "").strip(),
                "story_points": row.get("story_points", 0),
                "assignee": row.get("assignee", "").strip(),
                "labels": [label.strip() for label in row.get("labels", "").split(",") if label.strip()],
                "parent": row.get("parent", "").strip()
            }
            records.append(record)

    return records
