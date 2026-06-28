import pytest
from google.antigravity import BuiltinTools
from agents.base import BaseAgent
from agents.planner import PlannerAgent
from agents.researcher import ResearcherAgent
from agents.coder import CoderAgent
from agents.reviewer import ReviewerAgent

def test_base_agent_init():
    agent = BaseAgent(
        name="TestAgent",
        system_instructions="You are a test agent.",
        enabled_tools=[BuiltinTools.LIST_DIR]
    )
    assert agent.name == "TestAgent"
    assert agent.system_instructions == "You are a test agent."
    assert agent.config.system_instructions == "You are a test agent."
    assert agent.config.capabilities.enabled_tools == [BuiltinTools.LIST_DIR]

def test_planner_agent_init():
    planner = PlannerAgent()
    assert planner.name == "PlannerAgent"
    assert BuiltinTools.VIEW_FILE in planner.enabled_tools
    assert BuiltinTools.LIST_DIR in planner.enabled_tools
    assert planner.config.response_schema is not None

def test_researcher_agent_init():
    researcher = ResearcherAgent()
    assert researcher.name == "ResearcherAgent"
    assert BuiltinTools.SEARCH_WEB in researcher.enabled_tools
    assert BuiltinTools.VIEW_FILE in researcher.enabled_tools

def test_coder_agent_init():
    coder = CoderAgent()
    assert coder.name == "CoderAgent"
    assert BuiltinTools.CREATE_FILE in coder.enabled_tools
    assert BuiltinTools.EDIT_FILE in coder.enabled_tools

def test_reviewer_agent_init():
    reviewer = ReviewerAgent()
    assert reviewer.name == "ReviewerAgent"
    assert BuiltinTools.RUN_COMMAND in reviewer.enabled_tools
    assert BuiltinTools.VIEW_FILE in reviewer.enabled_tools
    assert reviewer.config.response_schema is not None
