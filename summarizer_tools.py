"""
summarizer_tools.py
-----------------
MCP tools for summarization tasks.
"""

def summarize_section(text: str) -> str:
    """
    Summarize a single section of text.
    Placeholder: returns first 100 characters.
    """
    return text[:100] + "..." if text else "No content"


def summarize_corpus(texts: list[str]) -> str:
    """
    Summarize across multiple documents/sections.
    Placeholder: joins first 50 characters from each.
    """
    if not texts:
        return "No documents provided"
    return " | ".join([t[:50] for t in texts])
