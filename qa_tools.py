"""
qa_tools.py
-----------------
MCP tools for Q&A over the document corpus.
"""

from services.retriever import query_chunks

def qa_query(question: str) -> dict:
    """
    Query the vector DB for relevant chunks and return an answer.
    Placeholder: returns chunks with dummy answer.
    """
    if not question:
        return {"error": "No question provided"}
    
    results = query_chunks(question, top_k=3)
    return {
        "question": question,
        "context_chunks": results,
        "answer": f"(Placeholder) Answer generated from {len(results)} chunks"
    }
