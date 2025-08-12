#!/usr/bin/env python3
"""
Minimal test server to verify FastMCP works in container.
"""
import os
from fastmcp import FastMCP

# Create minimal FastMCP server
mcp = FastMCP("CodeMaster-Test")

# FastMCP handles HTTP endpoints through its built-in system
# Traditional health checks aren't needed for MCP servers

# Add minimal tool for testing
@mcp.tool()
async def test_tool(message: str = "Hello") -> dict:
    """Test tool for verification."""
    return {"response": f"Test successful: {message}"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 9090))
    print(f"🧪 Starting minimal test server on port {port}")
    
    # Run the server
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0", 
        port=port,
        log_level="info"
    )
