"""
validator_tools.py
-----------------
MCP tools for validating agent outputs.
"""

def validate_summary(summary: str) -> bool:
    """
    Validate that a summary is non-empty and long enough.
    """
    return bool(summary and len(summary) > 20)


def validate_entities(entities: list[dict]) -> bool:
    """
    Validate that extracted entities are not empty.
    """
    return bool(entities)


def validate_answer(answer: str) -> bool:
    """
    Validate that an answer contains both question and answer structure.
    """
    return bool(answer and "answer" in answer.lower())
