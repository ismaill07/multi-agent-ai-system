import asyncio
from typing import List, Optional
from google.antigravity import Agent, LocalAgentConfig, CapabilitiesConfig, BuiltinTools
from google.antigravity.types import Thought, Text, ToolCall, ToolResult
from core.logging import (
    log_agent_thought,
    log_agent_tool_call,
    log_agent_tool_result,
    log_agent_response,
    log_system_event
)

class BaseAgent:
    """Base Agent class wrapping the google-antigravity Agent.
    
    Manages lifecycle, safety/capability configuration, and logs thoughts, tool calls, and tool results.
    """
    def __init__(self, name: str, system_instructions: str, enabled_tools: Optional[List[BuiltinTools]] = None, **kwargs):
        self.name = name
        self.system_instructions = system_instructions
        self.enabled_tools = enabled_tools
        self.config = LocalAgentConfig(
            system_instructions=self.system_instructions,
            capabilities=CapabilitiesConfig(
                enabled_tools=self.enabled_tools,
                enable_subagents=True
            ),
            **kwargs
        )
        self.agent = None

    async def __aenter__(self):
        self.agent = Agent(self.config)
        await self.agent.__aenter__()
        log_system_event(f"Agent '{self.name}' context entered.")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.agent:
            await self.agent.__aexit__(exc_type, exc_val, exc_tb)
            log_system_event(f"Agent '{self.name}' context exited.")

    async def chat(self, prompt: str) -> str:
        """Sends a prompt to the agent and returns the final text response.
        
        Logs the thoughts, tool calls, results, and response details.
        """
        log_system_event(f"Sending prompt to '{self.name}': {prompt[:100]}...")
        response = await self.agent.chat(prompt)
        
        # Spawn background processing of chunks to log thoughts and tool calls in real time
        log_task = asyncio.create_task(self._process_chunks(response))
        
        # Await final text content
        text = await response.text()
        
        # Ensure log processing finishes
        await log_task
        
        log_agent_response(self.name, text)
        return text

    async def _process_chunks(self, response):
        """Processes chunks from the chat response to log thoughts and tool interactions."""
        try:
            async for chunk in response.chunks:
                if isinstance(chunk, Thought):
                    log_agent_thought(self.name, chunk.text)
                elif isinstance(chunk, ToolCall):
                    log_agent_tool_call(self.name, str(chunk.name), chunk.args)
                elif isinstance(chunk, ToolResult):
                    # Format log for tool result
                    res_str = f"Success: {chunk.result}" if chunk.error is None else f"Error: {chunk.error}"
                    log_agent_tool_result(self.name, str(chunk.name), res_str)
        except Exception as e:
            log_system_event(f"Logging error in '{self.name}': {e}")
