from typing import Optional
from pydantic import BaseModel, Field
from google.antigravity import BuiltinTools
from agents.base import BaseAgent
from core.logging import log_system_event

class ReviewResult(BaseModel):
    passed: bool = Field(description="True if the code meets all requirements and passes verification, False otherwise")
    feedback: str = Field(description="Constructive review feedback, listing errors, security concerns, or improvements")
    test_stdout: Optional[str] = Field(None, description="Console output of tests or commands run during verification")
    test_stderr: Optional[str] = Field(None, description="Console error output of tests or commands run during verification")

class ReviewerAgent(BaseAgent):
    """Reviewer Agent responsible for auditing code files, running tests, and validating objective completion."""
    
    SYSTEM_INSTRUCTIONS = (
        "You are the Reviewer Agent. Your responsibility is to audit code written by the Coder Agent for best "
        "practices, readability, performance, security, and adherence to requirements.\n"
        "You have the capability to run verification commands (such as running test suites like pytest or python files) "
        "to check functionality. Always execute tests if available before making your final decision.\n"
        "You must output a structured JSON response matching the schema provided, stating clearly if the code "
        "passed review (True) or failed (False), and detailing your feedback."
    )

    def __init__(self):
        # Reviewer needs to run commands (like pytest/scripts) and view/list files.
        enabled_tools = [
            BuiltinTools.RUN_COMMAND,
            BuiltinTools.VIEW_FILE,
            BuiltinTools.LIST_DIR
        ]
        super().__init__(
            name="ReviewerAgent",
            system_instructions=self.SYSTEM_INSTRUCTIONS,
            enabled_tools=enabled_tools,
            response_schema=ReviewResult
        )

    async def review_code(self, task_description: str, files_to_review: list, test_command: Optional[str] = None) -> ReviewResult:
        """Audits the files and runs optional verification tests to evaluate task completion."""
        log_system_event(f"ReviewerAgent starting audit on files: {files_to_review}")
        
        prompt = (
            f"Review the implementation for the following task: '{task_description}'\n"
            f"The files involved are: {files_to_review}\n"
        )
        if test_command:
            prompt += f"Please execute this test command first to verify execution: '{test_command}'\n"
        else:
            prompt += "Please check if any tests are available in the workspace and execute them to verify.\n"
            
        prompt += "Provide a clear pass/fail verdict along with feedback."

        response = await self.agent.chat(prompt)
        
        import asyncio
        log_task = asyncio.create_task(self._process_chunks(response))
        
        structured_review = await response.structured_output()
        
        await log_task
        
        if structured_review is None:
            raise RuntimeError("ReviewerAgent failed to generate a structured review result.")
            
        log_system_event(f"ReviewerAgent review completed. Verdict: {'PASSED' if structured_review.passed else 'FAILED'}")
        return structured_review
