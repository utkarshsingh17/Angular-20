"""
mcp_tools_client.py
-----------------
Utility to connect to FastMCP server and fetch tool handles
for use inside AssistantAgents.
"""

from fastmcp import MCPClient

# point to your MCP server
MCP_URL = "http://127.0.0.1:8000"

client = MCPClient(MCP_URL)

def get_tool(name: str):
    """
    Get a handle to a tool exposed by the MCP server.
    Example: get_tool("summarize_section_tool")
    """
    return client.get_tool(name)
