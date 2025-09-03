"""
mcp_server.py
-----------------
FastMCP server exposing summarization, entity extraction,
Q&A, and validation tools for the multi-agent system.
"""

from fastmcp import FastMCP
from pydantic import BaseModel
from typing import List, Dict

# import actual tools
from tools import (
    summarize_section,
    summarize_corpus,
    extract_entities,
    qa_query,
    validate_summary,
    validate_entities,
    validate_answer,
)

# create FastMCP app
app = FastMCP(name="DocSummarizerMCP")


# -------------------------------
# Request Models
# -------------------------------

class SectionSummaryRequest(BaseModel):
    text: str

class CorpusSummaryRequest(BaseModel):
    texts: List[str]

class EntityRequest(BaseModel):
    text: str

class QARequest(BaseModel):
    question: str

class SummaryValidationRequest(BaseModel):
    summary: str

class EntitiesValidationRequest(BaseModel):
    entities: List[Dict]

class AnswerValidationRequest(BaseModel):
    answer: str


# -------------------------------
# Tool Endpoints
# -------------------------------

@app.tool()
def summarize_section_tool(req: SectionSummaryRequest) -> str:
    """Summarize a single document section."""
    return summarize_section(req.text)


@app.tool()
def summarize_corpus_tool(req: CorpusSummaryRequest) -> str:
    """Summarize across multiple documents or sections."""
    return summarize_corpus(req.texts)


@app.tool()
def extract_entities_tool(req: EntityRequest) -> list[dict]:
    """Extract entities (names, dates, orgs, etc.) from text."""
    return extract_entities(req.text)


@app.tool()
def qa_tool(req: QARequest) -> dict:
    """Answer a natural language question over the document corpus."""
    return qa_query(req.question)


@app.tool()
def validate_summary_tool(req: SummaryValidationRequest) -> bool:
    """Validate a summary for length and completeness."""
    return validate_summary(req.summary)


@app.tool()
def validate_entities_tool(req: EntitiesValidationRequest) -> bool:
    """Validate extracted entities are non-empty."""
    return validate_entities(req.entities)


@app.tool()
def validate_answer_tool(req: AnswerValidationRequest) -> bool:
    """Validate a Q&A answer for structure and correctness."""
    return validate_answer(req.answer)


# -------------------------------
# Run Server
# -------------------------------
if __name__ == "__main__":
    app.run()
