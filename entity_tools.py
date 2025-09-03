"""
entity_tools.py
-----------------
MCP tools for entity extraction.
"""

def extract_entities(text: str) -> list[dict]:
    """
    Extract entities from text.
    Placeholder: returns dummy entities.
    """
    if not text:
        return []
    return [
        {"text": "Alice", "label": "PERSON"},
        {"text": "2025", "label": "DATE"},
    ]
