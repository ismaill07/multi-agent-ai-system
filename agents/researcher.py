from google.antigravity import BuiltinTools
from agents.base import BaseAgent

class ResearcherAgent(BaseAgent):
    """Researcher Agent responsible for exploring codebases, searching documentation, and summarizing details."""
    
    SYSTEM_INSTRUCTIONS = (
        "You are the Researcher Agent. Your responsibility is to analyze codebase structures, "
        "read files, browse technical documentation, and summarize findings. "
        "Provide thorough, high-quality analysis and research logs to help the Coding Agent understand "
        "requirements, APIs, and project architecture."
    )

    def __init__(self):
        enabled_tools = [
            BuiltinTools.SEARCH_WEB,
            BuiltinTools.VIEW_FILE,
            BuiltinTools.LIST_DIR
        ]
        super().__init__(
            name="ResearcherAgent",
            system_instructions=self.SYSTEM_INSTRUCTIONS,
            enabled_tools=enabled_tools
        )
