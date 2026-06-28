from google.antigravity import BuiltinTools
from agents.base import BaseAgent

class CoderAgent(BaseAgent):
    """Coder Agent responsible for writing, refactoring, and debugging Python files based on plans and research."""
    
    SYSTEM_INSTRUCTIONS = (
        "You are the Coder Agent. Your responsibility is to write, modify, refactoring, and debug modular "
        "Python code files in the workspace. You should adhere strictly to clean coding principles, "
        "modularity, and security guidelines. Follow the technical architecture specified by the Planner "
        "and coordinate with the Researcher's notes. Do not write placeholder code; make all implementations "
        "fully functional."
    )

    def __init__(self):
        enabled_tools = [
            BuiltinTools.CREATE_FILE,
            BuiltinTools.EDIT_FILE,
            BuiltinTools.LIST_DIR,
            BuiltinTools.VIEW_FILE
        ]
        super().__init__(
            name="CoderAgent",
            system_instructions=self.SYSTEM_INSTRUCTIONS,
            enabled_tools=enabled_tools
        )
