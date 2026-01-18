import pdfplumber
import os

def extract_text_from_pdf(file_path):
    text_content = []
    with pdfplumber.open(file_path) as pdf:
        for i, page in enumerate(pdf.pages):
            page_text = page.extract_text()
            if page_text:
                text_content.append({
                    "text": page_text,
                    "page_number": i + 1,
                    "source_name": os.path.basename(file_path)
                })
    return text_content

def extract_text_from_txt(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()
    return [{
        "text": text,
        "page_number": 1,
        "source_name": os.path.basename(file_path)
    }]

def extract_text(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    elif ext == ".txt":
        return extract_text_from_txt(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")

def chunk_text(extracted_data, chunk_size=300, overlap=50):
    chunks = []
    chunk_id_counter = 0
    for item in extracted_data:
        text = item["text"]
        words = text.split()
        if len(words) <= chunk_size:
            chunks.append({
                "chunk_id": chunk_id_counter,
                "text": text,
                "page_number": item["page_number"],
                "source_name": item["source_name"]
            })
            chunk_id_counter += 1
            continue
        for i in range(0, len(words), chunk_size - overlap):
            chunk_words = words[i : i + chunk_size]
            chunk_text_str = " ".join(chunk_words)
            chunks.append({
                "chunk_id": chunk_id_counter,
                "text": chunk_text_str,
                "page_number": item["page_number"],
                "source_name": item["source_name"]
            })
            chunk_id_counter += 1
            if i + chunk_size >= len(words):
                break
    return chunks
