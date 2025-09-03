from fastapi import FastAPI, UploadFile, File, Form
from pydantic import BaseModel
from typing import List

from services.parser import parse_document
from services.storage import store_document, list_documents, get_doc_chunks
from agents.registry import agent_registry

# ensure agents are loaded
import agents.summarization_agent
import agents.entity_agent
import agents.qa_agent
import agents.validator_agent


app = FastAPI(title="Doc Summarizer & Q&A Platform")


# -------------------------------
# Models
# -------------------------------
class QuestionRequest(BaseModel):
    question: str


# -------------------------------
# Endpoints
# -------------------------------

@app.post("/ingest")
async def ingest_document(doc_id: str = Form(...), file: UploadFile = File(...)):
    """
    Upload + embed + store document in pgvector
    """
    file_path = f"/tmp/{file.filename}"
    with open(file_path, "wb") as f:
        f.write(await file.read())

    text = parse_document(file_path)
    result = store_document(doc_id, text)
    return {"doc_id": doc_id, "chunks_stored": result["chunks"], "status": "ingested"}


@app.get("/docs")
def list_docs():
    """
    List all available documents
    """
    return {"documents": list_documents()}


@app.post("/summarize/{doc_id}")
def summarize_doc(doc_id: str):
    """
    Summarize a specific document chosen by user
    """
    summarizer = agent_registry.get("summarization")
    validator = agent_registry.get("validator")

    chunks = get_doc_chunks(doc_id)
    full_text = " ".join([c["chunk"] for c in chunks])

    summary = summarizer.run("Summarize this text:\n" + full_text)
    valid = validator.run(f"Validate this summary: {summary}")

    return {"doc_id": doc_id, "summary": summary, "valid": valid}


@app.post("/qa/{doc_id}")
def qa_doc(doc_id: str, req: QuestionRequest):
    """
    Ask a Q&A question from a specific document
    """
    qa_agent = agent_registry.get("qa")
    validator = agent_registry.get("validator")

    chunks = get_doc_chunks(doc_id)
    context = " ".join([c["chunk"] for c in chunks])

    answer = qa_agent.run(f"Question: {req.question}\nContext:\n{context}")
    valid = validator.run(f"Validate this answer: {answer}")

    return {"doc_id": doc_id, "question": req.question, "answer": answer, "valid": valid}


@app.post("/entities/{doc_id}")
def extract_entities(doc_id: str):
    """
    Extract entities from a chosen document
    """
    entity_agent = agent_registry.get("entity")
    validator = agent_registry.get("validator")

    chunks = get_doc_chunks(doc_id)
    full_text = " ".join([c["chunk"] for c in chunks])

    entities = entity_agent.run("Extract entities from:\n" + full_text)
    valid = validator.run(f"Validate these entities: {entities}")

    return {"doc_id": doc_id, "entities": entities, "valid": valid}

