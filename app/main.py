from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import List
import shutil
import os
from .document_processor import extract_text, chunk_text
from .retriever import TFIDFRetriever
from .generator import PhiGenerator

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

retriever = TFIDFRetriever()
generator = None
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.on_event("startup")
async def startup_event():
    global generator
    generator = PhiGenerator()

@app.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    all_chunks = []
    for file in files:
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        extracted_data = extract_text(file_path)
        chunks = chunk_text(extracted_data)
        all_chunks.extend(chunks)
    retriever.index_chunks(all_chunks)
    return {"message": f"Successfully indexed {len(all_chunks)} chunks from {len(files)} files."}

@app.post("/chat")
async def chat(query: str = Form(...), mode: str = Form("normal")):
    results = retriever.search(query)
    answer = generator.generate_grounded_answer(mode, query, results)
    sources = []
    for r in results:
        sources.append({
            "source": r["chunk"]["source_name"],
            "page": r["chunk"]["page_number"]
        })
    return {"answer": answer, "sources": sources}

@app.post("/summary")
async def summary(query: str = Form("Provide a summary")):
    results = retriever.search(query, top_k=10)
    answer = generator.generate_grounded_answer("summary", query, results)
    return {"answer": answer}

app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
