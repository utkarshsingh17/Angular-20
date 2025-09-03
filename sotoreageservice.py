"""
storage.py
-----------------
Handles storing and retrieving documents in Postgres + pgvector.
- Store documents as chunks with embeddings
- List all ingested documents
- Retrieve chunks by document ID
"""

from config.db import SessionLocal, engine, Base
from models.document import DocumentChunk
from services.embeddings import embed_text
from services.parser import chunk_text

# Ensure DB tables exist
Base.metadata.create_all(bind=engine)


def store_document(doc_id: str, text: str):
    """
    Parse text into chunks, embed them, and store into pgvector DB.

    Args:
        doc_id (str): Unique document identifier
        text (str): Full document text

    Returns:
        dict: status + number of chunks stored
    """
    session = SessionLocal()
    chunks = chunk_text(text)

    for chunk in chunks:
        embedding = embed_text(chunk)
        entry = DocumentChunk(
            doc_id=doc_id,
            chunk=chunk,
            embedding=embedding
        )
        session.add(entry)

    session.commit()
    session.close()

    return {"status": "stored", "chunks": len(chunks)}


def list_documents():
    """
    List all unique document IDs that have been ingested.

    Returns:
        list[str]: List of doc_ids
    """
    session = SessionLocal()
    docs = session.query(DocumentChunk.doc_id).distinct().all()
    session.close()
    return [d[0] for d in docs]


def get_doc_chunks(doc_id: str):
    """
    Retrieve all chunks for a specific document.

    Args:
        doc_id (str): The document identifier

    Returns:
        list[dict]: List of chunk records {id, chunk}
    """
    session = SessionLocal()
    chunks = session.query(DocumentChunk).filter(DocumentChunk.doc_id == doc_id).all()
    session.close()
    return [{"id": c.id, "chunk": c.chunk} for c in chunks]
