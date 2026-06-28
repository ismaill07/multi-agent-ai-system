import os
import sys
import logging
from datetime import datetime

# Define log directory and file path
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
LOG_FILE = os.path.join(LOG_DIR, 'agent_execution.log')

# Ensure log directory exists
os.makedirs(LOG_DIR, exist_ok=True)

# Custom formatter for clean, timestamped logs
class AgentFormatter(logging.Formatter):
    def format(self, record):
        timestamp = datetime.now().isoformat()
        return f"[{timestamp}] {record.levelname:<8} | {record.getMessage()}"

# Configure logging
logger = logging.getLogger("MultiAgentSystem")
logger.setLevel(logging.INFO)

# File Handler
file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
file_handler.setFormatter(AgentFormatter())
logger.addHandler(file_handler)

# Console Handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(AgentFormatter())
logger.addHandler(console_handler)

def log_agent_thought(agent_name: str, thought: str):
    """Log an agent's internal thought process."""
    logger.info(f"[{agent_name}] THINKING: {thought}")

def log_agent_tool_call(agent_name: str, tool_name: str, args: dict):
    """Log a tool call by an agent."""
    logger.info(f"[{agent_name}] TOOL CALL: Executing '{tool_name}' with args: {args}")

def log_agent_tool_result(agent_name: str, tool_name: str, result: str):
    """Log the result of a tool call."""
    logger.info(f"[{agent_name}] TOOL RESULT: '{tool_name}' completed. Result: {result}")

def log_agent_communication(sender: str, recipient: str, message: str):
    """Log communication message between agents."""
    logger.info(f"[COMMUNICATION] {sender} -> {recipient} | Message: {message}")

def log_agent_response(agent_name: str, response: str):
    """Log the final response/answer of an agent."""
    logger.info(f"[{agent_name}] RESPONSE: {response}")

def log_system_event(event_description: str):
    """Log general system orchestration event."""
    logger.info(f"[SYSTEM] {event_description}")
