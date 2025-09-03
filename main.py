"""
main.py
-----------------
FastAPI backend exposing endpoints that use AutoGen agents
for summarization, entity extraction, Q&A, and validation.
"""

from fastapi import FastAPI
from pydantic import BaseModel

from agents.registry import agent_registry

# ensure agent modules are imported so they self-register
import agents.summarization_agent
import agents.entity_agent
import agents.qa_agent
import agents.validator_agent


# -------------------------------
# FastAPI app
# -------------------------------
app = FastAPI(title="Intelligent Document Summarization & Q&A Agents")

# -------------------------------
# Request Models
# -------------------------------
class TextRequest(BaseModel):
    text: str

class QuestionRequest(BaseModel):
    text: str
    question: str

class ValidationRequest(BaseModel):
    content: str
    type: str  # "summary" | "entities" | "answer"


# -------------------------------
# Endpoints
# -------------------------------
@app.post("/summarize")
def summarize(req: TextRequest):
    """
    Run the SummarizationAgent on given text.
    """
    summarizer = agent_registry.get("summarization")
    output = summarizer.run("Summarize this text:\n" + req.text)
    return {"summary": output}


@app.post("/entities")
def extract_entities(req: TextRequest):
    """
    Run the EntityExtractionAgent on given text.
    """
    entity_agent = agent_registry.get("entity")
    output = entity_agent.run("Extract entities from:\n" + req.text)
    return {"entities": output}


@app.post("/qa")
def qa(req: QuestionRequest):
    """
    Run the QAAgent on text + question.
    """
    qa_agent = agent_registry.get("qa")
    prompt = f"Question: {req.question}\nContext:\n{req.text}"
    output = qa_agent.run(prompt)
    return {"question": req.question, "answer": output}


@app.post("/validate")
def validate(req: ValidationRequest):
    """
    Run the ValidatorAgent to validate outputs.
    """
    validator = agent_registry.get("validator")

    if req.type == "summary":
        output = validator.run(f"Validate this summary: {req.content}")
    elif req.type == "entities":
        output = validator.run(f"Validate these entities: {req.content}")
    elif req.type == "answer":
        output = validator.run(f"Validate this answer: {req.content}")
    else:
        return {"error": "Invalid type. Use summary | entities | answer"}

    return {"valid": output}


# -------------------------------
# Root Endpoint
# -------------------------------
@app.get("/")
def root():
    return {
        "message": "Welcome to Intelligent Document Summarization & Q&A Agents API",
        "available_agents": agent_registry.list_agents(),
        "endpoints": ["/summarize", "/entities", "/qa", "/validate"],
    }
