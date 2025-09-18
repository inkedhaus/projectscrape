from mcp.server.fastmcp import FastMCP

# Simple in-memory storage
memory_store = {}

# Create FastMCP server
mcp_server = FastMCP("Memory Server")


@mcp_server.tool()
def echo(text: str) -> str:
    """Echo back the provided text."""
    return text


@mcp_server.tool()
def memory_upsert(key: str, value: str) -> str:
    """Store a key-value pair in memory."""
    memory_store[key] = value
    return f"Stored '{key}': '{value}'"


@mcp_server.tool()
def memory_get(key: str) -> str:
    """Retrieve a value by key from memory."""
    if key in memory_store:
        return memory_store[key]
    return f"Key '{key}' not found"


@mcp_server.tool()
def memory_list() -> dict:
    """List all stored key-value pairs."""
    return memory_store


@mcp_server.tool()
def memory_delete(key: str) -> str:
    """Delete a key-value pair from memory."""
    if key in memory_store:
        del memory_store[key]
        return f"Deleted key '{key}'"
    return f"Key '{key}' not found"


if __name__ == "__main__":
    mcp_server.run()
