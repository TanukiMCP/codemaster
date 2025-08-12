# server.py
import asyncio
import logging
import os
import json
from fastmcp import FastMCP
from typing import Optional, List, Dict, Any, Union

# Import project-specific components
from codemaster.container import get_container, CodemasterContainer
from codemaster.command_handler import CodemasterCommandHandler, CodemasterCommand
from codemaster.schemas import create_flexible_response, validate_request, extract_guidance
from codemaster.exceptions import CodemasterError

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the FastMCP server
# CORS is enabled by default for streamable-http transport
mcp = FastMCP("Codemaster")

# Global container - initialize once
container: Optional[CodemasterContainer] = None

def preprocess_mcp_parameters(**kwargs) -> Dict[str, Any]:
    """
    Preprocess MCP parameters to handle serialization issues.
    
    The MCP protocol sometimes serializes array parameters as JSON strings.
    This function detects and converts them back to proper data types.
    """
    processed = {}
    
    # List of parameters that should be arrays
    array_parameters = [
        'builtin_tools', 'mcp_tools', 'user_resources', 'available_tools',
        'success_metrics', 'coding_standards', 'tasklist', 'task_mappings'
    ]
    
    # Parameters that should be dictionaries
    dict_parameters = ['six_hats', 'updated_task_data']
    
    for key, value in kwargs.items():
        if value is None:
            processed[key] = value
            continue
            
        # Handle array parameters
        if key in array_parameters:
            if isinstance(value, str):
                try:
                    # Try to parse as JSON
                    parsed_value = json.loads(value)
                    if isinstance(parsed_value, list):
                        processed[key] = parsed_value
                        logger.info(f"Converted {key} from JSON string to array")
                    else:
                        processed[key] = value
                except (json.JSONDecodeError, TypeError):
                    # If parsing fails, keep original value
                    processed[key] = value
            else:
                processed[key] = value
                
        # Handle dictionary parameters
        elif key in dict_parameters:
            if isinstance(value, str):
                try:
                    # Try to parse as JSON
                    parsed_value = json.loads(value)
                    if isinstance(parsed_value, dict):
                        processed[key] = parsed_value
                        logger.info(f"Converted {key} from JSON string to dict")
                    else:
                        processed[key] = value
                except (json.JSONDecodeError, TypeError):
                    # If parsing fails, keep original value
                    processed[key] = value
            else:
                processed[key] = value
        else:
            processed[key] = value
    
    return processed

async def get_command_handler():
    """Get the command handler, initializing container if needed."""
    global container
    if container is None:
        logger.info("Initializing container...")
        container = get_container()
        logger.info("Container initialized.")
    return container.resolve(CodemasterCommandHandler)

async def execute_codemaster_logic(data: dict) -> dict:
    """Execute codemaster command - simplified."""
    try:
        command_handler = await get_command_handler()
        
        # Process the request
        enhanced_request = validate_request(data)
        command = CodemasterCommand(**enhanced_request)
        response = await command_handler.execute(command)
        
        return response.to_dict()
        
    except Exception as e:
        logger.error(f"Error during codemaster execution: {e}", exc_info=True)
        return create_flexible_response(
            action=data.get("action", "error"),
            status="error",
            completion_guidance=f"Error: {str(e)}",
            error_details=str(e),
            next_action_needed=True
        )

@mcp.tool()
async def codemaster(
    action: str,
    session_name: Optional[str] = None,
    available_tools: Optional[Union[List[Dict[str, Any]], str]] = None,
    success_metrics: Optional[Union[List[str], str]] = None,
    coding_standards: Optional[Union[List[str], str]] = None,
    tasklist: Optional[Union[List[Dict[str, Any]], str]] = None,
    task_mappings: Optional[Union[List[Dict[str, Any]], str]] = None,
    collaboration_context: Optional[str] = None,
    task_id: Optional[str] = None,
    updated_task_data: Optional[Union[Dict[str, Any], str]] = None,
) -> dict:
    """
    🚀 CODEMASTER - LLM AGENTIC CODING FRAMEWORK 🚀

    Structured workflow for agentic coding assistants:
    1. create_session - Create a new coding session
    2. declare_capabilities - Declare all available tools  
    3. define_success_and_standards - Define success metrics and coding standards
    4. create_tasklist - Define programming tasks
    5. map_capabilities - Assign tools to tasks
    6. execute_next - Execute tasks with success context
    7. mark_complete - Complete tasks and phases  
    8. end_session - End session
    """
    # Preprocess parameters to handle MCP serialization issues
    raw_params = {
        "action": action,
        "session_name": session_name,
        "available_tools": available_tools,
        "success_metrics": success_metrics,
        "coding_standards": coding_standards,
        "tasklist": tasklist,
        "task_mappings": task_mappings,
        "collaboration_context": collaboration_context,
        "task_id": task_id,
        "updated_task_data": updated_task_data,
    }
    
    # Apply preprocessing to convert JSON strings back to proper types
    processed_params = preprocess_mcp_parameters(**raw_params)
    
    # Convert to the data dict format with proper defaults
    data = {
        "action": processed_params["action"],
        "session_name": processed_params["session_name"] or "",
        "available_tools": processed_params["available_tools"] or [],
        "success_metrics": processed_params["success_metrics"] or [],
        "coding_standards": processed_params["coding_standards"] or [],
        "tasklist": processed_params["tasklist"] or [],
        "task_mappings": processed_params["task_mappings"] or [],
        "collaboration_context": processed_params["collaboration_context"] or "",
        "task_id": processed_params["task_id"] or "",
        "updated_task_data": processed_params["updated_task_data"] or {},
    }
    
    return await execute_codemaster_logic(data)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 9090))
    print(f"🌐 Starting Codemaster FastMCP Server on port {port}")
    print(f"🔧 Using streamable-http transport with /mcp endpoint")
    print(f"🌍 CORS is enabled by default for cross-origin requests")
    print(f"🛠️ Enhanced parameter preprocessing enabled")
    
    # Run the FastMCP server with streamable-http transport
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=port,
        log_level="info"
    ) 