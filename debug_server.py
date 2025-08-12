#!/usr/bin/env python3
"""
Debug version of the server to identify build issues.
"""
import sys
import os

print("=== Debug Server Starting ===")
print(f"Python version: {sys.version}")
print(f"Working directory: {os.getcwd()}")
print(f"PORT environment: {os.environ.get('PORT', 'Not set')}")

try:
    print("Importing fastmcp...")
    from fastmcp import FastMCP
    print("✓ FastMCP imported successfully")
except Exception as e:
    print(f"✗ FastMCP import failed: {e}")
    sys.exit(1)

try:
    print("Creating FastMCP instance...")
    mcp = FastMCP("CodeMaster-Debug")
    print("✓ FastMCP instance created")
except Exception as e:
    print(f"✗ FastMCP instance creation failed: {e}")
    sys.exit(1)

@mcp.app.get("/health")
async def health_check():
    return {"status": "healthy", "debug": True}

@mcp.tool()
async def debug_tool(test: str = "hello") -> dict:
    return {"debug": "working", "input": test}

if __name__ == "__main__":
    try:
        port = int(os.environ.get("PORT", 9090))
        print(f"Starting server on port {port}...")
        
        mcp.run(
            transport="streamable-http",
            host="0.0.0.0",
            port=port,
            log_level="debug"
        )
    except Exception as e:
        print(f"Server failed to start: {e}")
        sys.exit(1)
