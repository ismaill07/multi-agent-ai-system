import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from core.orchestrator import MultiAgentOrchestrator
from agents.planner import PlanModel, TaskModel
from agents.reviewer import ReviewResult

@pytest.mark.asyncio
@patch('agents.base.Agent')
@patch('agents.planner.PlannerAgent.generate_plan')
@patch('agents.researcher.ResearcherAgent.chat')
@patch('agents.coder.CoderAgent.chat')
@patch('agents.reviewer.ReviewerAgent.review_code')
async def test_orchestrator_successful_flow(
    mock_review, mock_coder_chat, mock_researcher_chat, mock_generate_plan, mock_agent_class
):
    # Configure the mock Agent instance to avoid connection validation
    mock_agent_instance = MagicMock()
    mock_agent_instance.__aenter__ = AsyncMock(return_value=mock_agent_instance)
    mock_agent_instance.__aexit__ = AsyncMock(return_value=None)
    mock_agent_class.return_value = mock_agent_instance

    # Setup mocks
    mock_generate_plan.return_value = PlanModel(
        tasks=[
            TaskModel(id="t1", description="Research details", assigned_to="researcher", dependencies=[]),
            TaskModel(id="t2", description="Write code", assigned_to="coder", dependencies=["t1"])
        ]
    )
    mock_researcher_chat.return_value = "Research findings summary"
    mock_coder_chat.return_value = "Implemented code content"
    mock_review.return_value = ReviewResult(passed=True, feedback="Looks perfect")

    # Instantiate orchestrator
    orchestrator = MultiAgentOrchestrator()

    # Run execution
    success = await orchestrator.execute_goal("Build a python app")
    
    # Assertions
    assert success is True
    mock_generate_plan.assert_called_once_with("Build a python app")
    mock_researcher_chat.assert_called_once()
    mock_coder_chat.assert_called_once()
    mock_review.assert_called_once_with(
        task_description="Write code",
        files_to_review=["workspace files"],
        test_command=None
    )

@pytest.mark.asyncio
@patch('agents.base.Agent')
@patch('agents.planner.PlannerAgent.generate_plan')
@patch('agents.coder.CoderAgent.chat')
@patch('agents.reviewer.ReviewerAgent.review_code')
async def test_orchestrator_feedback_loop_retry(
    mock_review, mock_coder_chat, mock_generate_plan, mock_agent_class
):
    # Configure the mock Agent instance to avoid connection validation
    mock_agent_instance = MagicMock()
    mock_agent_instance.__aenter__ = AsyncMock(return_value=mock_agent_instance)
    mock_agent_instance.__aexit__ = AsyncMock(return_value=None)
    mock_agent_class.return_value = mock_agent_instance

    # Setup mocks
    mock_generate_plan.return_value = PlanModel(
        tasks=[
            TaskModel(id="t1", description="Write code", assigned_to="coder", dependencies=[])
        ]
    )
    mock_coder_chat.return_value = "Buggy code implementation"
    
    # First review fails, second passes
    mock_review.side_effect = [
        ReviewResult(passed=False, feedback="Syntax error on line 3", test_stdout="", test_stderr="SyntaxError"),
        ReviewResult(passed=True, feedback="Now it is perfect", test_stdout="OK", test_stderr="")
    ]

    orchestrator = MultiAgentOrchestrator(max_reviewer_retries=2)

    # Run execution
    success = await orchestrator.execute_goal("Build simple script")
    
    assert success is True
    assert mock_coder_chat.call_count == 2
    assert mock_review.call_count == 2
