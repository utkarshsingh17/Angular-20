from config.db import SessionLocal
from models.document import DocumentChunk

def list_documents():
    """
    List all unique document IDs in DB
    """
    session = SessionLocal()
    docs = session.query(DocumentChunk.doc_id).distinct().all()
    session.close()
    return [d[0] for d in docs]

def get_doc_chunks(doc_id: str):
    """
    Retrieve all chunks for a given document
    """
    session = SessionLocal()
    chunks = session.query(DocumentChunk).filter(DocumentChunk.doc_id == doc_id).all()
    session.close()
    return [{"id": c.id, "chunk": c.chunk} for c in chunks]
