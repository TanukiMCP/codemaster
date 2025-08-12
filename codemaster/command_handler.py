from typing import Dict, Any, Optional, List
import logging
import json
from abc import ABC, abstractmethod
from datetime import datetime
from .models import Session, Task, BuiltInTool, MCPTool, MemoryTool, EnvironmentCapabilities, InitialToolThoughts, ToolAssignment
from .session_manager import SessionManager
from .schemas import (
    ActionType,
    create_flexible_request, create_flexible_response,
    extract_guidance, clean_guidance
)

logger = logging.getLogger(__name__)


class CodemasterCommand:
    """Represents a command to be executed by the CodemasterCommandHandler."""
    
    def __init__(self, **kwargs):
        if "data" in kwargs:
            merged_data = kwargs["data"].copy()
            merged_data.update({k: v for k, v in kwargs.items() if k != "data"})
            self.data = create_flexible_request(merged_data)
        else:
            self.data = create_flexible_request(kwargs)
        
        self.action = self.data.get("action", "get_status")
        self.task_description = self.data.get("task_description")
        self.session_name = self.data.get("session_name")
        self.builtin_tools = self.data.get("builtin_tools", [])
        self.mcp_tools = self.data.get("mcp_tools", [])
        self.user_resources = self.data.get("user_resources", [])
        self.available_tools = self.data.get("available_tools", [])
        self.success_metrics = self.data.get("success_metrics", [])
        self.coding_standards = self.data.get("coding_standards", [])
        self.tasklist = self.data.get("tasklist", [])
        self.task_mappings = self.data.get("task_mappings", [])
        self.collaboration_context = self.data.get("collaboration_context")
        self.task_id = self.data.get("task_id")
        self.six_hats = self.data.get("six_hats", {})
        self.denoised_plan = self.data.get("denoised_plan", "")
        self.updated_task_data = self.data.get("updated_task_data", {})


class CodemasterResponse:
    """Represents a response from the CodemasterCommandHandler."""
    
    def __init__(self, action: str, **kwargs):
        self.data = create_flexible_response(action, **kwargs)
        self.action = self.data["action"]
        self.session_id = self.data.get("session_id")
        self.status = self.data.get("status", "success")
        self.suggested_next_actions = self.data.get("suggested_next_actions", [])
        self.completion_guidance = self.data.get("completion_guidance", "")
        
        for key, value in kwargs.items():
            if not hasattr(self, key):
                setattr(self, key, value)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary format."""
        return clean_guidance(self.data)


class BaseCommandHandler(ABC):
    """Base class for command handlers."""
    
    def __init__(self, session_manager: SessionManager):
        self.session_manager = session_manager
    
    @abstractmethod
    async def handle(self, command: CodemasterCommand) -> CodemasterResponse:
        """Handle the command and return a response."""
        pass


class CreateSessionHandler(BaseCommandHandler):
    """Handler for create_session command."""
    
    async def handle(self, command: CodemasterCommand) -> CodemasterResponse:
        session = await self.session_manager.create_session(command.session_name)
        guidance = """
✅ **Session created successfully!**

🎯 **NEXT STEP**: Use 'declare_capabilities' to inform Codemaster of the tools you can use.

**CRITICAL**: Codemaster does not scan your environment automatically. You must declare what tools and resources you have access to. This information is essential for creating an effective plan.

Refer to the guidance in the `declare_capabilities` command for a detailed template and examples.
"""
        return CodemasterResponse(
            action="create_session",
            session_id=session.id,
            suggested_next_actions=["declare_capabilities"],
            completion_guidance=guidance,
        )


class DeclareCapabilitiesHandler(BaseCommandHandler):
    """Handler for declare_capabilities command - unified tool declaration for agentic coding."""
    
    async def handle(self, command: CodemasterCommand) -> CodemasterResponse:
        session = await self.session_manager.get_current_session()
        if not session:
            return CodemasterResponse(action="declare_capabilities", status="guidance", completion_guidance="No active session.")

        available_tools = command.data.get("available_tools", [])
        
        if not available_tools:
            guidance = '''
🛠️ **DECLARE ALL AVAILABLE TOOLS**

Declare ALL tools available in your context packet, regardless of immediate relevance. This creates a comprehensive tool inventory for intelligent task planning.

**CRITICAL**: List EVERY tool from your IDE context packet - built-in tools, MCP tools, and any connected services. Do not filter by relevance at this stage.

**For each tool, provide:**
- `name`: Exact tool name as it appears in your context
- `description`: What the tool does in one clear sentence
- `relevance_assessment`: How relevant this tool is for the current programming task and why

**Template for declare_capabilities:**
```json
{
  "action": "declare_capabilities", 
  "available_tools": [
    {
      "name": "read_file",
      "description": "Reads file contents from the local filesystem",
      "relevance_assessment": "Highly relevant - essential for understanding existing codebase structure and current implementation"
    },
    {
      "name": "search_replace", 
      "description": "Performs exact string replacements in files",
      "relevance_assessment": "Highly relevant - primary tool for modifying existing code files"
    },
    {
      "name": "run_terminal_cmd",
      "description": "Executes terminal commands in the project environment", 
      "relevance_assessment": "Highly relevant - needed for testing, building, and running the application"
    },
    {
      "name": "codebase_search",
      "description": "Semantic search across the entire codebase by meaning",
      "relevance_assessment": "Moderately relevant - useful for finding related code patterns and understanding architecture"
    },
    {
      "name": "mcp_desktop-commander_execute_command",
      "description": "Advanced terminal command execution with enhanced options",
      "relevance_assessment": "Moderately relevant - alternative to run_terminal_cmd with additional capabilities"
    },
    {
      "name": "mcp_puppeteer_navigate_to",
      "description": "Controls browser automation for web testing",
      "relevance_assessment": "Not relevant for this task - current task does not involve web browser testing"
    }
  ]
}
```

**IMPORTANT GUIDANCE FOR TASK DECOMPOSITION:**
When you proceed to create_tasklist, follow these programming-specific decomposition principles:

**Task Planning Strategy:**
- Break complex features into logical implementation phases
- Separate setup/configuration from core implementation  
- Plan for incremental testing and validation
- Consider dependencies between components
- Structure tasks for progressive complexity

**Effective Programming Task Structure:**
1. **Setup Tasks**: Environment preparation, dependency installation, configuration
2. **Foundation Tasks**: Core classes, data models, basic structure
3. **Feature Tasks**: Individual feature implementation, one per task
4. **Integration Tasks**: Connecting components, API integration, data flow
5. **Validation Tasks**: Testing implementation, performance verification, quality checks

**Task Description Best Practices:**
- Use specific, actionable language ("Implement user authentication" not "Add auth")
- Include technical details and constraints
- Specify expected inputs and outputs  
- Reference relevant files or components
- Indicate testing/validation requirements

🎯 **NEXT STEP**: Declare ALL available tools using the format above.
'''
            return CodemasterResponse(
                action="declare_capabilities",
                session_id=session.id,
                status="template", 
                completion_guidance=guidance,
                suggested_next_actions=["declare_capabilities"]
            )

        # Validate and store tool declarations
        try:
            # Store declared tools in session for context persistence
            session.data["declared_tools_context"] = available_tools
            session.capabilities.built_in_tools = [BuiltInTool(name=tool["name"], description=tool["description"]) for tool in available_tools]
        except Exception as e:
            return CodemasterResponse(
                action="declare_capabilities",
                session_id=session.id,
                status="error",
                completion_guidance=f"❌ **VALIDATION ERROR**: {str(e)}\n\nPlease ensure all tools have 'name', 'description', and 'relevance_assessment' fields.",
                suggested_next_actions=["declare_capabilities"]
            )
        
        await self.session_manager.update_session(session)
        
        guidance = f'''
✅ **Tool capabilities declared successfully!**

📊 **TOOL INVENTORY:**
- Total Tools Declared: {len(available_tools)}
- High Relevance: {len([t for t in available_tools if "highly relevant" in t.get("relevance_assessment", "").lower()])}
- Moderate Relevance: {len([t for t in available_tools if "moderately relevant" in t.get("relevance_assessment", "").lower()])}
- Low/No Relevance: {len([t for t in available_tools if "not relevant" in t.get("relevance_assessment", "").lower()])}

🎯 **NEXT STEP**: Use 'define_success_and_standards' to establish success criteria and coding standards.

Your declared tools will be automatically provided as context during tasklist creation and capability mapping for intelligent tool assignment.
'''
        return CodemasterResponse(
            action="declare_capabilities",
            session_id=session.id,
            suggested_next_actions=["define_success_and_standards"],
            completion_guidance=guidance
        )


class DefineSuccessAndStandardsHandler(BaseCommandHandler):
    """Handler for define_success_and_standards command."""
    
    async def handle(self, command: CodemasterCommand) -> CodemasterResponse:
        session = await self.session_manager.get_current_session()
        if not session:
            return CodemasterResponse(action="define_success_and_standards", status="guidance", completion_guidance="No active session.")

        success_metrics = command.data.get("success_metrics", [])
        coding_standards = command.data.get("coding_standards", [])

        if not success_metrics or not coding_standards:
            guidance = '''
🎯 **DEFINE SUCCESS METRICS AND CODING STANDARDS**

Define clear, measurable success criteria and coding standards for this programming task. This context will be persistently available throughout task execution.

**REQUIRED: success_metrics** - Specific, measurable criteria that define successful completion:
- Functional requirements met
- Performance benchmarks achieved  
- User acceptance criteria satisfied
- Integration requirements fulfilled

**REQUIRED: coding_standards** - Quality and style guidelines to follow:
- Naming conventions (camelCase, snake_case, etc.)
- Code organization principles
- Documentation requirements
- Security considerations
- No placeholder/mock code policy
- No hardcoded data policy
- Error handling standards

**Example define_success_and_standards call:**
```json
{
  "action": "define_success_and_standards",
  "success_metrics": [
    "Application successfully processes user input without errors",
    "Response time under 200ms for typical operations", 
    "All edge cases handled with appropriate error messages",
    "Integration tests pass with 100% success rate"
  ],
  "coding_standards": [
    "Use camelCase for JavaScript variables and functions",
    "Follow RESTful API design principles", 
    "Include comprehensive error handling for all user inputs",
    "No hardcoded configuration values - use environment variables",
    "All functions must have JSDoc documentation",
    "Follow security best practices for data validation"
  ]
}
```

🎯 **NEXT STEP**: Provide both success_metrics and coding_standards arrays.
'''
            return CodemasterResponse(
                action="define_success_and_standards",
                session_id=session.id,
                status="template",
                completion_guidance=guidance,
                suggested_next_actions=["define_success_and_standards"]
            )

        # Store success metrics and coding standards in session
        session.data["success_metrics"] = success_metrics
        session.data["coding_standards"] = coding_standards
        await self.session_manager.update_session(session)

        guidance = f'''
✅ **Success metrics and coding standards defined successfully!**

📊 **SUCCESS METRICS ({len(success_metrics)} defined):**
{chr(10).join([f"- {metric}" for metric in success_metrics])}

📋 **CODING STANDARDS ({len(coding_standards)} defined):**
{chr(10).join([f"- {standard}" for standard in coding_standards])}

🎯 **NEXT STEP**: Use 'create_tasklist' to define your programming tasks.

These metrics and standards will be automatically referenced during task execution to ensure quality and completion criteria are met.
'''
        return CodemasterResponse(
            action="define_success_and_standards",
            session_id=session.id,
            suggested_next_actions=["create_tasklist"],
            completion_guidance=guidance
        )







class CreateTasklistHandler(BaseCommandHandler):
    """Handler for create_tasklist command, now enhanced to process a 'denoised_plan'."""
    
    async def handle(self, command: CodemasterCommand) -> CodemasterResponse:
        session = await self.session_manager.get_current_session()
        if not session:
            return CodemasterResponse(action="create_tasklist", status="guidance", completion_guidance="No active session.")

        raw_tasklist = command.tasklist
        denoised_plan = command.data.get("denoised_plan")

        if not raw_tasklist:
            guidance = """
📝 **CREATE TASKLIST**

You have completed the thinking and denoising process. Now, formalize your plan into a structured tasklist.

**Reminder**: Your tasklist must focus **only on implementation**. Do **NOT** include tasks for testing, validation, or documentation writing.

**Example create_tasklist call:**
```json
{
  "action": "create_tasklist",
  "denoised_plan": "Your synthesized plan from denoise step...",
  "tasklist": [
    {"description": "Set up project structure and initial files"},
    {"description": "Implement CSV reading logic using pandas"},
    {"description": "Implement core data transformation logic"},
    {"description": "Implement JSON output generation"}
  ]
}
```

🎯 **NEXT STEP**: Provide both the `denoised_plan` and `tasklist` parameters.
"""
            return CodemasterResponse(
                action="create_tasklist",
                session_id=session.id,
                status="template",
                completion_guidance=guidance,
                suggested_next_actions=["create_tasklist"]
            )

        enhanced_tasks, validation_issues = self._validate_and_enhance_tasklist(raw_tasklist)
        
        session.tasks = [Task(**task_data) for task_data in enhanced_tasks]
        if denoised_plan:
            session.data["denoised_plan"] = denoised_plan
        await self.session_manager.update_session(session)
        
        guidance = self._build_tasklist_completion_guidance(session.tasks, validation_issues)
        
        # Add context persistence for declared tools
        declared_tools = session.data.get("declared_tools_context", [])
        if declared_tools:
            guidance += f"\n\n**AVAILABLE TOOLS CONTEXT:**\n"
            guidance += "The following tools were declared and are available for mapping:\n"
            for tool in declared_tools:
                relevance = tool.get("relevance_assessment", "No assessment provided")
                guidance += f"- `{tool['name']}`: {tool['description']} ({relevance})\n"
        
        return CodemasterResponse(
            action="create_tasklist",
            session_id=session.id,
            tasks_created=len(session.tasks),
            suggested_next_actions=["map_capabilities"],
            completion_guidance=guidance
        )

    def _validate_and_enhance_tasklist(self, raw_tasklist: List[Dict]) -> tuple[List[Dict], List[str]]:
        """Validates the tasklist and enhances it with default structures."""
        enhanced_tasks = []
        validation_issues = []
        forbidden_keywords = ["test", "validate", "verify", "document", "docs"]

        for i, task_data in enumerate(raw_tasklist):
            description = task_data.get("description", f"Unnamed Task {i+1}")
            
            # Scrub for forbidden keywords
            if any(keyword in description.lower() for keyword in forbidden_keywords):
                validation_issues.append(f"Task {i+1} ('{description}') was removed because it related to testing, validation, or documentation, which is not part of the core implementation workflow.")
                continue

            # Enhance task with default phase structure
            planning_phase = (task_data.get("planning_phase") or {}).copy()
            planning_phase.setdefault("phase_name", "planning")
            planning_phase.setdefault("description", f"Plan for: {description}")

            execution_phase = (task_data.get("execution_phase") or {}).copy()
            execution_phase.setdefault("phase_name", "execution")
            execution_phase.setdefault("description", f"Execution of: {description}")

            enhanced_task = {
                "description": description,
                "planning_phase": planning_phase,
                "execution_phase": execution_phase,
                "initial_tool_thoughts": task_data.get("initial_tool_thoughts", {"reasoning": "No initial thoughts provided."}),
                "complexity_level": self._assess_task_complexity(description),
            }
            enhanced_tasks.append(enhanced_task)
            
        return enhanced_tasks, validation_issues

    def _assess_task_complexity(self, description: str) -> str:
        """Assess task complexity based on its description."""
        desc_lower = description.lower()
        if any(word in desc_lower for word in ["system", "architecture", "framework", "integrate", "refactor"]):
            return "architectural"
        if any(word in desc_lower for word in ["implement", "create", "build", "develop", "add", "modify"]):
            return "complex"
        return "simple"

    def _build_tasklist_completion_guidance(self, tasks: List[Task], issues: List[str]) -> str:
        """Builds the final guidance message after creating a tasklist."""
        message = f"✅ **Tasklist created with {len(tasks)} tasks.**"
        if issues:
            message += "\n\n⚠️ **IMPORTANT NOTICES:**\n" + "\n".join(f"- {issue}" for issue in issues)
        
        message += "\n\n🎯 **NEXT STEP**: Use `map_capabilities` to assign your declared tools to these tasks.\n\n"
        
        message += "## Understanding Tool Mapping\n\n"
        message += "Each task has two phases that need tool assignments:\n"
        message += "- **Planning Phase**: Tools for research, analysis, and understanding\n"
        message += "- **Execution Phase**: Tools for implementation and building\n\n"
        
        message += "## Your Tasks:\n"
        for task in tasks:
            message += f"- **{task.description}** (ID: `{task.id}`)\n"
        message += "\n"
        
        message += "## Tool Assignment Structure:\n\n"
        message += "Each tool assignment needs:\n"
        message += "- `tool_name`: Exact name from your declared capabilities\n"
        message += "- `usage_purpose`: Why this tool is needed for this phase\n"
        message += "- `specific_actions`: (Optional) List of specific actions\n"
        message += "- `expected_outcome`: (Optional) What should be achieved\n"
        message += "- `priority`: (Optional) critical/normal/low\n\n"
        
        message += "**COMPLETE EXAMPLE - Copy and adapt this template:**\n\n"
        message += "```json\n"
        message += "{\n"
        message += '  "action": "map_capabilities",\n'
        message += '  "task_mappings": [\n'
        
        # Generate example for first task
        if tasks:
            task = tasks[0]
            message += '    {\n'
            message += f'      "task_id": "{task.id}",\n'
            message += '      "planning_phase": {\n'
            message += '        "assigned_builtin_tools": [\n'
            message += '          {\n'
            message += '            "tool_name": "codebase_search",\n'
            message += '            "usage_purpose": "Understand existing project structure and identify relevant files",\n'
            message += '            "specific_actions": ["Search for related components", "Understand current architecture"],\n'
            message += '            "expected_outcome": "Clear understanding of how to implement this task",\n'
            message += '            "priority": "critical"\n'
            message += '          },\n'
            message += '          {\n'
            message += '            "tool_name": "read_file",\n'
            message += '            "usage_purpose": "Read configuration files and existing code",\n'
            message += '            "priority": "normal"\n'
            message += '          }\n'
            message += '        ],\n'
            message += '        "assigned_mcp_tools": []\n'
            message += '      },\n'
            message += '      "execution_phase": {\n'
            message += '        "assigned_builtin_tools": [\n'
            message += '          {\n'
            message += '            "tool_name": "edit_file",\n'
            message += '            "usage_purpose": "Create and modify files to implement the functionality",\n'
            message += '            "specific_actions": ["Create new files", "Modify existing code"],\n'
            message += '            "expected_outcome": "Working implementation",\n'
            message += '            "priority": "critical"\n'
            message += '          },\n'
            message += '          {\n'
            message += '            "tool_name": "run_terminal_cmd",\n'
            message += '            "usage_purpose": "Test the implementation and run build commands",\n'
            message += '            "priority": "normal"\n'
            message += '          }\n'
            message += '        ],\n'
            message += '        "assigned_mcp_tools": []\n'
            message += '      }\n'
            message += '    }'
            
            # Add comma and placeholder for additional tasks
            if len(tasks) > 1:
                message += ',\n'
                message += '    {\n'
                message += f'      "task_id": "{tasks[1].id}",\n'
                message += '      "planning_phase": { "assigned_builtin_tools": [...] },\n'
                message += '      "execution_phase": { "assigned_builtin_tools": [...] }\n'
                message += '    }\n'
                message += '    // ... repeat for all tasks\n'
            else:
                message += '\n'
        
        message += '  ]\n'
        message += '}\n'
        message += "```\n\n"
        
        message += "**MAPPING TIPS:**\n"
        message += "- Use planning phase for research and understanding\n"
        message += "- Use execution phase for building and implementation\n"
        message += "- Only assign tools you actually declared in capabilities\n"
        message += "- Be specific about why each tool is needed\n"
        message += "- Critical tools should have priority: 'critical'\n\n"
        
        message += "After mapping capabilities, you'll use 'execute_next' to begin working on tasks."
        
        return message


class MapCapabilitiesHandler(BaseCommandHandler):
    """Handler for map_capabilities command."""
    
    async def handle(self, command: CodemasterCommand) -> CodemasterResponse:
        session = await self.session_manager.get_current_session()
        if not session: 
            return CodemasterResponse(action="map_capabilities", status="guidance", completion_guidance="No active session.")
        if not session.tasks: 
            return CodemasterResponse(action="map_capabilities", status="guidance", completion_guidance="No tasks exist. Use `create_tasklist` first.", suggested_next_actions=["create_tasklist"])
        if not session.capabilities.built_in_tools and not session.capabilities.mcp_tools: 
            return CodemasterResponse(action="map_capabilities", status="guidance", completion_guidance="No capabilities declared. Use `declare_capabilities` first.", suggested_next_actions=["declare_capabilities"])

        task_mappings = command.task_mappings
        if not task_mappings:
            available_tools = {
                "builtin_tools": [(tool.name, tool.description) for tool in session.capabilities.built_in_tools],
                "mcp_tools": [(tool.name, tool.description) for tool in session.capabilities.mcp_tools],
                "user_resources": [(res.name, res.description) for res in session.capabilities.user_resources],
            }
            guidance = f"""
🗺️ **MAP CAPABILITIES TO TASKS**

Assign your available tools to the planning and execution phases of each task. This provides essential context for execution.

**Your Tasks:**
{chr(10).join([f'- {task.description} (ID: {task.id})' for task in session.tasks])}

**Your Tools:**
- **Built-in:** {', '.join([t[0] for t in available_tools['builtin_tools']])}
- **MCP:** {', '.join([t[0] for t in available_tools['mcp_tools']])}
- **Resources:** {', '.join([t[0] for t in available_tools['user_resources']])}

**Example map_capabilities call:**
```json
{{
  "action": "map_capabilities",
  "task_mappings": [
    {{
      "task_id": "{session.tasks[0].id if session.tasks else 'task_id'}",
      "planning_phase": {{
        "assigned_builtin_tools": [
          {{"tool_name": "codebase_search", "usage_purpose": "To understand existing project structure."}}
        ]
      }},
      "execution_phase": {{
        "assigned_builtin_tools": [
          {{"tool_name": "edit_file", "usage_purpose": "To create and modify the script files."}},
          {{"tool_name": "run_terminal_cmd", "usage_purpose": "To run the script and check its output."}}
        ]
      }}
    }}
  ]
}}
```

🎯 **NEXT STEP**: Provide the task_mappings as shown above.
"""
            return CodemasterResponse(
                action="map_capabilities",
                session_id=session.id,
                status="template",
                completion_guidance=guidance,
                suggested_next_actions=["map_capabilities"]
            )

        for mapping in task_mappings:
            task = next((t for t in session.tasks if t.id == mapping.get("task_id")), None)
            if not task: 
                continue

            if "planning_phase" in mapping and task.planning_phase:
                tools = mapping["planning_phase"].get("assigned_builtin_tools", [])
                setattr(task.planning_phase, 'assigned_builtin_tools', [ToolAssignment(**t) for t in tools])
                tools_mcp = mapping["planning_phase"].get("assigned_mcp_tools", [])
                setattr(task.planning_phase, 'assigned_mcp_tools', [ToolAssignment(**t) for t in tools_mcp])
            
            if "execution_phase" in mapping and task.execution_phase:
                tools = mapping["execution_phase"].get("assigned_builtin_tools", [])
                setattr(task.execution_phase, 'assigned_builtin_tools', [ToolAssignment(**t) for t in tools])
                tools_mcp = mapping["execution_phase"].get("assigned_mcp_tools", [])
                setattr(task.execution_phase, 'assigned_mcp_tools', [ToolAssignment(**t) for t in tools_mcp])

        await self.session_manager.update_session(session)
        
        return CodemasterResponse(
            action="map_capabilities",
            session_id=session.id,
            mapping_completed=True,
            suggested_next_actions=["execute_next"],
            completion_guidance="""✅ **Capabilities mapped successfully!** You are ready to begin execution.

## What Happens Next

The workflow now enters the execution phase. You'll work through each task in sequence, with each task having two phases:

1. **Planning Phase**: Use your assigned tools to research, analyze, and understand what needs to be done
2. **Execution Phase**: Use your assigned tools to implement and build the solution

## How to Proceed

**NEXT STEP**: Use `execute_next` to get detailed guidance for your first task.

```json
{
  "action": "execute_next"
}
```

This will provide you with:
- Current task and phase information
- Detailed guidance on which tools to use
- Specific actions to take
- Expected outcomes
- Context about the task's objectives

## Execution Flow

1. **Call `execute_next`** - Get guidance for current task/phase
2. **Perform the work** - Use the assigned tools as guided
3. **Call `mark_complete`** - Progress to next phase or task
4. **Repeat** until all tasks are finished

## When You're Stuck

If you encounter issues, need clarification, or require user input:

```json
{
  "action": "collaboration_request",
  "collaboration_context": "Describe what you need help with..."
}
```

This will pause the workflow and request user assistance.

🎯 **Ready to begin!** Call `execute_next` to start working on your first task."""
        )


class ExecuteNextHandler(BaseCommandHandler):
    """Handler for execute_next command."""
    
    async def handle(self, command: CodemasterCommand) -> CodemasterResponse:
        session = await self.session_manager.get_current_session()
        if not session: 
            return CodemasterResponse(action="execute_next", status="guidance", completion_guidance="No active session.")
            
        next_task = next((task for task in session.tasks if task.status == "pending"), None)
        
        if not next_task:
            guidance = "🎉 **All tasks completed!** Use `end_session` to finalize."
            return CodemasterResponse(
                action="execute_next",
                status="completed",
                completion_guidance=guidance,
                suggested_next_actions=["end_session"]
            )

        current_phase_name = next_task.current_phase or "planning"
        phase_obj = getattr(next_task, f"{current_phase_name}_phase", None)
        
        tool_guidance = self._build_tool_guidance(phase_obj) if phase_obj else "No tools assigned for this phase."
        success_context = self._build_success_context(session)

        guidance = f"""
⚡ **EXECUTE TASK: {next_task.description}**

**Phase**: {current_phase_name.upper()}
**Objective**: {phase_obj.description if phase_obj else 'No objective defined.'}

{tool_guidance}

{success_context}

💡 **Stuck? Need Help?**
If you cannot proceed, are stuck in a loop, or need more information from the user, you can pause the workflow at any time by calling the `collaboration_request` command. Provide context on why you are stuck.

**Example collaboration_request call:**
```json
{{
  "action": "collaboration_request",
  "collaboration_context": "I am unable to proceed because the API key for service X is missing. Please provide it."
}}
```

🎯 **NEXT STEP**: Perform the work for this phase and then call `mark_complete`.
"""
        
        return CodemasterResponse(
            action="execute_next",
            session_id=session.id,
            current_task_id=next_task.id,
            current_task_description=next_task.description,
            current_phase=current_phase_name,
            suggested_next_actions=["mark_complete", "collaboration_request"],
            completion_guidance=guidance
        )

    def _build_tool_guidance(self, phase_obj) -> str:
        """Builds a formatted string of tool guidance for the current phase."""
        if not phase_obj: 
            return ""
        
        sections = []
        if hasattr(phase_obj, 'assigned_builtin_tools') and phase_obj.assigned_builtin_tools:
            tools = [f"- `{t.tool_name}`: {t.usage_purpose}" for t in phase_obj.assigned_builtin_tools]
            sections.append(f"**Tools for this phase:**\n" + "\n".join(tools))
        
        if hasattr(phase_obj, 'assigned_mcp_tools') and phase_obj.assigned_mcp_tools:
            tools = [f"- `{t.tool_name}`: {t.usage_purpose}" for t in phase_obj.assigned_mcp_tools]
            sections.append(f"**MCP Tools for this phase:**\n" + "\n".join(tools))

        return "\n\n".join(sections)

    def _build_success_context(self, session) -> str:
        """Build success metrics and coding standards context."""
        success_metrics = session.data.get("success_metrics", [])
        coding_standards = session.data.get("coding_standards", [])
        
        if not success_metrics and not coding_standards:
            return ""
        
        context = "\n**SUCCESS CRITERIA & STANDARDS:**\n"
        
        if success_metrics:
            context += "**Success Metrics to Achieve:**\n"
            context += "\n".join([f"- {metric}" for metric in success_metrics]) + "\n"
        
        if coding_standards:
            context += "\n**Coding Standards to Follow:**\n"
            context += "\n".join([f"- {standard}" for standard in coding_standards]) + "\n"
        
        return context


class MarkCompleteHandler(BaseCommandHandler):
    """Handler for mark_complete command."""
    
    async def handle(self, command: CodemasterCommand) -> CodemasterResponse:
        session = await self.session_manager.get_current_session()
        if not session:
            return CodemasterResponse(action="mark_complete", status="guidance", completion_guidance="No active session.")

        # Find the current task
        current_task = next((task for task in session.tasks if task.status == "pending"), None)
        if not current_task:
            return CodemasterResponse(
                action="mark_complete",
                status="completed",
                completion_guidance="🎉 **All tasks completed!** Use `end_session` to finalize.",
                suggested_next_actions=["end_session"]
            )

        # Progress the task
        if current_task.current_phase == "planning":
            current_task.current_phase = "execution"
            guidance = f"""
✅ **Planning phase completed for: {current_task.description}**

🎯 **NEXT STEP**: Call `execute_next` to begin the execution phase.
"""
            next_actions = ["execute_next"]
        else:
            current_task.status = "completed"
            guidance = f"""
✅ **Task completed: {current_task.description}**

🎯 **NEXT STEP**: Call `execute_next` to move to the next task.
"""
            next_actions = ["execute_next"]

        await self.session_manager.update_session(session)
        
        return CodemasterResponse(
            action="mark_complete",
            session_id=session.id,
            task_id=current_task.id,
            suggested_next_actions=next_actions,
            completion_guidance=guidance
        )


class GetStatusHandler(BaseCommandHandler):
    """Handler for get_status command."""
    
    async def handle(self, command: CodemasterCommand) -> CodemasterResponse:
        session = await self.session_manager.get_current_session()
        if not session:
            return CodemasterResponse(
                action="get_status",
                status="no_session",
                completion_guidance="❌ **No active session.** Use `create_session` to start.",
                suggested_next_actions=["create_session"]
            )

        total_tasks = len(session.tasks)
        completed_tasks = len([t for t in session.tasks if t.status == "completed"])
        current_task = next((t for t in session.tasks if t.status == "pending"), None)
        
        status_info = f"""
📊 **SESSION STATUS**

**Session ID**: {session.id}
**Progress**: {completed_tasks}/{total_tasks} tasks completed
**Current State**: {session.workflow_state}

"""
        
        if current_task:
            status_info += f"""**Current Task**: {current_task.description}
**Current Phase**: {current_task.current_phase or 'planning'}

"""
        
        if session.tasks:
            status_info += "**Tasks:**\n"
            for i, task in enumerate(session.tasks, 1):
                status = "✅" if task.status == "completed" else "⏳"
                phase = f" ({task.current_phase})" if task.status == "pending" else ""
                status_info += f"{i}. {status} {task.description}{phase}\n"
        else:
            status_info += "**No tasks created yet.**\n"

        next_actions = []
        if not session.tasks:
            next_actions = ["six_hat_thinking"]
        elif current_task:
            next_actions = ["execute_next"]
        else:
            next_actions = ["end_session"]

        return CodemasterResponse(
            action="get_status",
            session_id=session.id,
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            current_task_id=current_task.id if current_task else None,
            suggested_next_actions=next_actions,
            completion_guidance=status_info
        )


class CollaborationRequestHandler(BaseCommandHandler):
    """Handler for collaboration_request command."""
    
    async def handle(self, command: CodemasterCommand) -> CodemasterResponse:
        session = await self.session_manager.get_current_session()
        if not session:
            return CodemasterResponse(action="collaboration_request", status="guidance", completion_guidance="No active session.")

        context = command.collaboration_context or "No context provided."
        guidance = f"""
🤝 **WORKFLOW PAUSED FOR USER COLLABORATION**

The agent has requested help with the following context:
> {context}

**To Resume Workflow**:
The user must provide feedback. The agent should then use the `edit_task` command to update the plan based on the user's response and then continue with `execute_next`.
"""
        return CodemasterResponse(
            action="collaboration_request",
            session_id=session.id,
            status="paused",
            completion_guidance=guidance,
            suggested_next_actions=["edit_task"]
        )


class EditTaskHandler(BaseCommandHandler):
    """Handler for edit_task command."""
    
    async def handle(self, command: CodemasterCommand) -> CodemasterResponse:
        session = await self.session_manager.get_current_session()
        if not session:
            return CodemasterResponse(action="edit_task", status="guidance", completion_guidance="No active session.")

        task_id = command.task_id
        updated_data = command.updated_task_data

        if not task_id or not updated_data:
            return CodemasterResponse(
                action="edit_task",
                status="template",
                completion_guidance="""
🛠️ **EDIT TASK**

Update a task based on user feedback or new requirements.

**Example edit_task call:**
```json
{
  "action": "edit_task",
  "task_id": "task_123",
  "updated_task_data": {
    "description": "Updated task description",
    "complexity_level": "complex"
  }
}
```
""",
                suggested_next_actions=["edit_task"]
            )

        # Find and update the task
        task = next((t for t in session.tasks if t.id == task_id), None)
        if not task:
            return CodemasterResponse(
                action="edit_task",
                status="error",
                completion_guidance=f"❌ **Task not found**: {task_id}",
                suggested_next_actions=["get_status"]
            )

        # Update task fields
        for key, value in updated_data.items():
            if hasattr(task, key):
                setattr(task, key, value)

        await self.session_manager.update_session(session)

        return CodemasterResponse(
            action="edit_task",
            session_id=session.id,
            task_id=task_id,
            completion_guidance=f"✅ **Task updated successfully**: {task.description}",
            suggested_next_actions=["execute_next"]
        )


class EndSessionHandler(BaseCommandHandler):
    """Handler for end_session command."""
    
    async def handle(self, command: CodemasterCommand) -> CodemasterResponse:
        session = await self.session_manager.get_current_session()
        if not session:
            return CodemasterResponse(action="end_session", status="guidance", completion_guidance="No active session to end.")

        total_tasks = len(session.tasks)
        completed_tasks = len([t for t in session.tasks if t.status == "completed"])
        
        guidance = f"""
🎉 **SESSION COMPLETED**

**Final Summary:**
- Session ID: {session.id}
- Tasks Completed: {completed_tasks}/{total_tasks}
- Session ended at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**Thank you for using Codemaster!**
"""
        
        # Session cleanup would happen here if needed
        
        return CodemasterResponse(
            action="end_session",
            session_id=session.id,
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            completion_guidance=guidance
        )


class CodemasterCommandHandler:
    """Main command handler that orchestrates all codemaster operations."""
    
    def __init__(self, session_manager: SessionManager):
        self.session_manager = session_manager
        
        # Get workflow state machine from session manager
        self.workflow_state_machine = getattr(session_manager, 'workflow_state_machine', None)
        
        self.handlers = {
            "create_session": CreateSessionHandler(session_manager),
            "declare_capabilities": DeclareCapabilitiesHandler(session_manager),
            "define_success_and_standards": DefineSuccessAndStandardsHandler(session_manager),
            "create_tasklist": CreateTasklistHandler(session_manager),
            "map_capabilities": MapCapabilitiesHandler(session_manager),
            "execute_next": ExecuteNextHandler(session_manager),
            "mark_complete": MarkCompleteHandler(session_manager),
            "get_status": GetStatusHandler(session_manager),
            "collaboration_request": CollaborationRequestHandler(session_manager),
            "edit_task": EditTaskHandler(session_manager),
            "end_session": EndSessionHandler(session_manager),
        }
        
        # Map actions to workflow events for state machine integration
        self.action_to_event = {
            "create_session": "CREATE_SESSION",
            "declare_capabilities": "DECLARE_CAPABILITIES", 
            "define_success_and_standards": "DEFINE_SUCCESS_STANDARDS",
            "create_tasklist": "CREATE_TASKLIST",
            "map_capabilities": "MAP_CAPABILITIES",
            "execute_next": "START_TASK",  # Will be handled contextually
            "mark_complete": "COMPLETE_TASK",
            "collaboration_request": "REQUEST_COLLABORATION",
            "edit_task": "EDIT_TASK",
            "end_session": "END_SESSION"
        }
    
    async def execute(self, command: CodemasterCommand) -> CodemasterResponse:
        """Execute a command using the appropriate handler with workflow state enforcement."""
        handler = self.handlers.get(command.action)
        if not handler:
            return CodemasterResponse(
                action=command.action,
                status="guidance",
                completion_guidance=f"❌ **ERROR**: Action '{command.action}' is not recognized.\n\nAvailable actions: {', '.join(self.handlers.keys())}"
            )

        # Allow status checks and session creation without a session
        if command.action in ["get_status", "create_session"]:
            return await handler.handle(command)

        session = await self.session_manager.get_current_session()
        if not session:
            return CodemasterResponse(action=command.action, status="guidance", completion_guidance="❌ **ERROR**: No active session. Please start with 'create_session'.")

        # --- Enhanced Workflow State Machine Integration ---
        if self.workflow_state_machine:
            # Synchronize workflow state machine with session state
            await self._synchronize_workflow_state(session)
            
            # Special handling for execute_next command - context-aware event triggering
            if command.action == "execute_next":
                event_name = self._get_execute_next_event(self.workflow_state_machine.current_state, session)
                if not event_name:
                    # No state transition needed, just execute the handler
                    return await handler.handle(command)
            # Special handling for mark_complete command - context-aware event triggering
            elif command.action == "mark_complete":
                event_name = self._get_mark_complete_event(session)
            else:
                event_name = self.action_to_event.get(command.action)
            
            if event_name:
                from .workflow_state_machine import WorkflowEvent
                try:
                    event = WorkflowEvent[event_name]
                    
                    # Prepare context data for the workflow state machine
                    context_data = {
                        "task_count": len(session.tasks),
                        "completed_tasks": len([t for t in session.tasks if t.status == "completed"]),
                        "session_id": session.id,
                        **command.data
                    }
                    
                    if not self.workflow_state_machine.trigger_event(event, **context_data):
                        # Find the expected transition for the current state to provide better guidance
                        possible_transitions = self.workflow_state_machine.get_possible_transitions(self.workflow_state_machine.current_state)
                        possible_events = [t.event.value for t in possible_transitions]
                        
                        return CodemasterResponse(
                            action="workflow_gate",
                            status="guidance",
                            completion_guidance=f"🚦 **WORKFLOW ALERT**: Action '{command.action}' is not allowed in the current state '{self.workflow_state_machine.current_state.value}'.\n\n"
                                               f"Possible next actions are: {', '.join(possible_events)}",
                            suggested_next_actions=possible_events
                        )
                    
                    # Persist the new state back to session
                    session.workflow_state = self.workflow_state_machine.current_state.value
                    await self.session_manager.update_session(session)
                    
                except (KeyError, ValueError) as e:
                    logger.warning(f"Could not find a corresponding WorkflowEvent for action '{command.action}': {e}")

        # Execute the handler
        return await handler.handle(command)

    def _get_execute_next_event(self, current_state, session: Session) -> Optional[str]:
        """Get the appropriate event for execute_next based on current workflow state."""
        from .workflow_state_machine import WorkflowState
        
        if current_state == WorkflowState.CAPABILITIES_MAPPED:
            return "START_TASK"  # Move to TASK_PLANNING
        elif current_state == WorkflowState.TASK_PLANNING:
            # For TASK_PLANNING, execute_next should just provide guidance, not trigger transitions.
            # The 'mark_complete' action for the planning phase triggers the state change to execution.
            return None
        elif current_state == WorkflowState.TASK_EXECUTING:
            # For TASK_EXECUTING, execute_next should just provide guidance, not trigger transitions
            return None  
        elif current_state == WorkflowState.TASK_COMPLETED:
            # If a task was just completed, check if more are pending before starting a new one.
            next_task = next((task for task in session.tasks if task.status == "pending"), None)
            if next_task:
                return "START_TASK"  # Move to the next task's planning phase
            else:
                # No more tasks, so no state change. Let the handler return the final completion message.
                return None
        else:
            return "START_TASK"  # Default fallback

    def _get_mark_complete_event(self, session) -> Optional[str]:
        """Get the appropriate event for mark_complete based on current task phase."""
        # Find the current task
        current_task = next((task for task in session.tasks if task.status == "pending"), None)
        if not current_task:
            return None  # No current task, let handler deal with it
        
        # If completing planning phase, trigger PLAN_TASK to move to execution
        if current_task.current_phase == "planning":
            return "PLAN_TASK"
        # If completing execution phase, trigger COMPLETE_TASK to complete the task
        else:
            return "COMPLETE_TASK"

    async def _synchronize_workflow_state(self, session: Session) -> None:
        """Synchronize workflow state machine with session state."""
        if not self.workflow_state_machine:
            return
            
        try:
            from .workflow_state_machine import WorkflowState
            current_session_state = WorkflowState(session.workflow_state)
            
            # Only sync if states are different
            if self.workflow_state_machine.current_state != current_session_state:
                self.workflow_state_machine.current_state = current_session_state
                
                # Update context with session information
                self.workflow_state_machine.context.session_id = session.id
                self.workflow_state_machine.context.task_count = len(session.tasks)
                self.workflow_state_machine.context.completed_tasks = len([t for t in session.tasks if t.status == "completed"])
                self.workflow_state_machine.context.metadata["session"] = session
                
                logger.info(f"Synchronized workflow state machine to {current_session_state.value}")
                
        except (ValueError, AttributeError) as e:
            logger.warning(f"Could not synchronize workflow state: {e}")

    def add_handler(self, action: str, handler: BaseCommandHandler) -> None:
        """Add a new command handler."""
        self.handlers[action] = handler
    
    def get_available_actions(self) -> List[str]:
        """Get list of available actions."""
        return list(self.handlers.keys())