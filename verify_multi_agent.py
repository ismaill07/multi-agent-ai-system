import asyncio
import os
import sys
from unittest.mock import AsyncMock, patch, MagicMock
from core.orchestrator import MultiAgentOrchestrator
from agents.planner import PlanModel, TaskModel
from agents.reviewer import ReviewResult
from google.antigravity.types import Thought, ToolCall, ToolResult

# Pre-defined mock responses for the simulation
PLANNER_PLAN = PlanModel(
    tasks=[
        TaskModel(
            id="task_1", 
            description="Research best practices for a calculator app and basic operations.", 
            assigned_to="researcher", 
            dependencies=[]
        ),
        TaskModel(
            id="task_2", 
            description="Create a calculator.py file with add, subtract, multiply, and divide functions.", 
            assigned_to="coder", 
            dependencies=["task_1"]
        )
    ]
)

RESEARCHER_RESPONSE = (
    "Research Findings:\n"
    "- Calculator should support addition, subtraction, multiplication, division.\n"
    "- Division must be carefully designed to prevent crashing when dividing by zero.\n"
    "- We should write a robust divide function that returns a clear error message or handles the exception."
)

CODER_FIRST_RESPONSE = (
    "Here is my first implementation of calculator.py:\n"
    "```python\n"
    "def add(a, b): return a + b\n"
    "def subtract(a, b): return a - b\n"
    "def multiply(a, b): return a * b\n"
    "def divide(a, b): return a / b  # Simple division\n"
    "```"
)

REVIEWER_FIRST_RESPONSE = ReviewResult(
    passed=False,
    feedback="The divide function raises ZeroDivisionError when b is 0. Please refactor to handle b == 0.",
    test_stdout="1 / 0 failed with ZeroDivisionError",
    test_stderr="ZeroDivisionError: division by zero"
)

CODER_SECOND_RESPONSE = (
    "Here is the corrected implementation of calculator.py:\n"
    "```python\n"
    "def add(a, b): return a + b\n"
    "def subtract(a, b): return a - b\n"
    "def multiply(a, b): return a * b\n"
    "def divide(a, b):\n"
    "    if b == 0:\n"
    "        return 'Error: Division by zero'\n"
    "    return a / b\n"
    "```"
)

REVIEWER_SECOND_RESPONSE = ReviewResult(
    passed=True,
    feedback="The divide function now correctly handles division by zero. All tests pass.",
    test_stdout="Tests Passed",
    test_stderr=""
)

class MockChatResponse:
    """Mocked chat response that implements the async context, thoughts/tool logs, and structured outputs."""
    def __init__(self, text_val, structured_val=None, chunks_list=None):
        self._text_val = text_val
        self._structured_val = structured_val
        self._chunks_list = chunks_list or []

    async def text(self) -> str:
        return self._text_val

    async def structured_output(self) -> any:
        return self._structured_val

    @property
    async def chunks(self):
        # Async generator for chunks
        for chunk in self._chunks_list:
            yield chunk

async def simulated_chat(prompt: str, agent_name: str, call_counts: dict) -> MockChatResponse:
    """Determines what mock response to yield depending on the agent calling it."""
    # Build simulated thoughts and tool calls for logging transparency
    chunks = [
        Thought(step_index=0, text=f"Analyzing prompt as {agent_name}."),
        Thought(step_index=1, text="Determining best action based on role parameters."),
        ToolCall(name="LIST_DIR", args={"path": "."}),
        ToolResult(name="LIST_DIR", result="calculator.py, requirements.txt")
    ]
    
    if "Planner" in agent_name:
        return MockChatResponse(
            text_val="Generating plan schema...", 
            structured_val=PLANNER_PLAN,
            chunks_list=chunks
        )
    elif "Researcher" in agent_name:
        return MockChatResponse(
            text_val=RESEARCHER_RESPONSE,
            chunks_list=chunks
        )
    elif "Coder" in agent_name:
        call_counts["coder"] += 1
        if call_counts["coder"] == 1:
            # First attempt: Coder writes calculator with bug
            # Let's actually create the buggy file in the workspace
            with open("calculator.py", "w") as f:
                f.write("def add(a, b): return a + b\ndef subtract(a, b): return a - b\ndef multiply(a, b): return a * b\ndef divide(a, b): return a / b\n")
            return MockChatResponse(text_val=CODER_FIRST_RESPONSE, chunks_list=chunks)
        else:
            # Second attempt: Coder fixes the division by zero bug
            with open("calculator.py", "w") as f:
                f.write("def add(a, b): return a + b\ndef subtract(a, b): return a - b\ndef multiply(a, b): return a * b\ndef divide(a, b):\n    if b == 0: return 'Error: Division by zero'\n    return a / b\n")
            return MockChatResponse(text_val=CODER_SECOND_RESPONSE, chunks_list=chunks)
    elif "Reviewer" in agent_name:
        call_counts["reviewer"] += 1
        if call_counts["reviewer"] == 1:
            return MockChatResponse(
                text_val="Reviewing... Failed.", 
                structured_val=REVIEWER_FIRST_RESPONSE,
                chunks_list=chunks
            )
        else:
            return MockChatResponse(
                text_val="Reviewing... Passed.", 
                structured_val=REVIEWER_SECOND_RESPONSE,
                chunks_list=chunks
            )
    return MockChatResponse(text_val="Unknown agent prompt.")

async def run_verification():
    # Track the call counts to simulate retry loop state
    call_counts = {"coder": 0, "reviewer": 0}

    # Patch the google-antigravity Agent class
    with patch('agents.base.Agent') as mock_agent_class:
        mock_agent_instance = MagicMock()
        mock_agent_instance.__aenter__ = AsyncMock(return_value=mock_agent_instance)
        mock_agent_instance.__aexit__ = AsyncMock(return_value=None)
        mock_agent_class.return_value = mock_agent_instance

        # Bind the chat method of the mock agent instance to simulated_chat
        async def mock_chat(prompt):
            # Inspect the calling agent using stack frame locals
            import inspect
            caller_name = "Agent"
            frame = inspect.currentframe()
            try:
                while frame:
                    self_obj = frame.f_locals.get("self")
                    if self_obj and hasattr(self_obj, "name"):
                        caller_name = self_obj.name
                        break
                    frame = frame.f_back
            finally:
                del frame
            
            return await simulated_chat(prompt, caller_name, call_counts)

        mock_agent_instance.chat = mock_chat

        print("--- STARTING SIMULATED MULTI-AGENT GOAL ---")
        orchestrator = MultiAgentOrchestrator(max_reviewer_retries=2)
        goal = "Build a calculator app with add, subtract, multiply, and divide functions. Make sure division is safe."
        success = await orchestrator.execute_goal(goal, test_command="python -m unittest tests/test_calculator.py")
        
        print("\n--- GOAL EXECUTION RESULT ---")
        print(f"Orchestration Status: {'SUCCESS' if success else 'FAILURE'}")
        
        print("\n--- GENERATED CODE (calculator.py) ---")
        if os.path.exists("calculator.py"):
            with open("calculator.py", "r") as f:
                print(f.read())
        else:
            print("calculator.py was not created.")

        print("\n--- TAIL OF AGENT EXECUTION LOG ---")
        log_path = os.path.join("logs", "agent_execution.log")
        if os.path.exists(log_path):
            with open(log_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                for line in lines[-35:]:  # Print last 35 lines of log
                    print(line.strip())
        else:
            print("Log file not found.")

if __name__ == "__main__":
    asyncio.run(run_verification())
