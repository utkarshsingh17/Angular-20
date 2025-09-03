from fastapi import FastAPI, UploadFile, File, Form
from services.parser import parse_document
from services.storage import store_document
from services.summarizer import summarize_context

app = FastAPI(title="Document Summarizer API (pgvector)")

@app.post("/ingest")
async def ingest_document(doc_id: str = Form(...), file: UploadFile = File(...)):
    """
    Upload a document, parse, chunk, embed and store in pgvector DB.
    """
    file_path = f"/tmp/{file.filename}"
    with open(file_path, "wb") as f:
        f.write(await file.read())

    text = parse_document(file_path)
    return store_document(doc_id, text)

@app.get("/summary")
async def fetch_summary(question: str):
    """
    Summarize context from stored documents for a question.
    """
    return summarize_context(question)

@app.get("/qa")
async def qa_query(question: str):
    """
    Answer a natural language question using stored document context.
    (Alias of summary for now)
    """
    return summarize_context(question)
