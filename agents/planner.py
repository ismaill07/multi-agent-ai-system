from typing import List
from pydantic import BaseModel, Field
from google.antigravity import BuiltinTools
from agents.base import BaseAgent
from core.logging import log_system_event

# Pydantic schema for structured task definitions
class TaskModel(BaseModel):
    id: str = Field(description="Unique task identifier, e.g. task_1, task_2")
    description: str = Field(description="Detailed actionable task description")
    assigned_to: str = Field(description="Agent role to assign the task to: either 'researcher' or 'coder'")
    dependencies: List[str] = Field(default_factory=list, description="List of task IDs that this task depends on")

class PlanModel(BaseModel):
    tasks: List[TaskModel] = Field(description="List of tasks in the order they should be executed")

class PlannerAgent(BaseAgent):
    """Planner Agent responsible for analyzing high-level requirements and breaking them down into structured tasks."""
    
    SYSTEM_INSTRUCTIONS = (
        "You are the Planner Agent. Your job is to analyze high-level user requirements and break "
        "them down into a sequence of actionable subtasks for other specialized agents.\n"
        "There are two roles available for tasks:\n"
        "1. 'researcher': Responsible for exploring files, checking context, or collecting info.\n"
        "2. 'coder': Responsible for writing, refactoring, or editing python code files.\n\n"
        "Always structure your response exactly as the requested JSON schema. Make sure the tasks "
        "are granular, modular, and have correct dependencies so that the orchestration pipeline "
        "runs them in the right order."
    )

    def __init__(self):
        # Planner only needs to view files and directories to plan properly, and write simple artifacts.
        enabled_tools = [
            BuiltinTools.VIEW_FILE,
            BuiltinTools.LIST_DIR,
            BuiltinTools.CREATE_FILE,
            BuiltinTools.EDIT_FILE
        ]
        super().__init__(
            name="PlannerAgent",
            system_instructions=self.SYSTEM_INSTRUCTIONS,
            enabled_tools=enabled_tools,
            response_schema=PlanModel
        )

    async def generate_plan(self, goal: str) -> PlanModel:
        """Asks the agent to generate a plan based on the user's high-level goal."""
        log_system_event("PlannerAgent is generating task roadmap...")
        prompt = f"Deconstruct the following goal into a sequence of tasks: {goal}"
        
        # Call base chat. Base class handles logging thoughts and tool calls in real time.
        # But since we configured response_schema, the response has structured output.
        # So we chat first to trigger the agent call:
        response = await self.agent.chat(prompt)
        
        # Start logging task for thoughts/tools
        import asyncio
        log_task = asyncio.create_task(self._process_chunks(response))
        
        # Retrieve parsed response
        structured_plan = await response.structured_output()
        
        await log_task
        
        if structured_plan is None:
            raise RuntimeError("PlannerAgent failed to generate a structured plan.")
            
        log_system_event(f"PlannerAgent successfully generated plan with {len(structured_plan.tasks)} tasks.")
        return structured_plan
