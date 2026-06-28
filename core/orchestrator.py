import os
import asyncio
from typing import Dict, List, Any
from agents.planner import PlannerAgent, PlanModel, TaskModel
from agents.researcher import ResearcherAgent
from agents.coder import CoderAgent
from agents.reviewer import ReviewerAgent
from core.logging import log_system_event, log_agent_communication

class MultiAgentOrchestrator:
    """Orchestrator that manages the flow of tasks between Planner, Researcher, Coder, and Reviewer agents."""
    
    def __init__(self, max_reviewer_retries: int = 3):
        self.max_reviewer_retries = max_reviewer_retries
        self.planner = PlannerAgent()
        self.researcher = ResearcherAgent()
        self.coder = CoderAgent()
        self.reviewer = ReviewerAgent()
        
        # Shared knowledge base to pass between agents
        self.research_notes: List[str] = []
        self.completed_tasks: Dict[str, Any] = {}

    async def execute_goal(self, goal: str, test_command: str = None) -> bool:
        """Runs the multi-agent workflow to accomplish the high-level goal."""
        log_system_event(f"Starting orchestration pipeline for goal: '{goal}'")
        
        # Initialize contexts of all agents concurrently
        async with self.planner, self.researcher, self.coder, self.reviewer:
            # Step 1: Generate the plan
            try:
                log_agent_communication("System", "PlannerAgent", f"Generate plan for: {goal}")
                plan: PlanModel = await self.planner.generate_plan(goal)
            except Exception as e:
                log_system_event(f"Failed to generate plan: {e}")
                return False
            
            # Print and log the planned roadmap
            log_system_event(f"Planned roadmap generated:")
            for t in plan.tasks:
                log_system_event(f" - [{t.id}] ({t.assigned_to}): {t.description} (depends on: {t.dependencies})")
                
            # Step 2: Execute tasks in dependency order
            tasks_queue = list(plan.tasks)
            executing = True
            
            while executing and tasks_queue:
                # Find tasks ready to execute (all dependencies completed)
                ready_tasks = [
                    t for t in tasks_queue 
                    if all(dep in self.completed_tasks for dep in t.dependencies)
                ]
                
                if not ready_tasks:
                    log_system_event("CRITICAL ERROR: Circular dependency detected in tasks, or tasks cannot proceed.")
                    return False
                
                # Execute the first ready task
                task = ready_tasks[0]
                tasks_queue.remove(task)
                
                success = await self._execute_task(task, test_command)
                if not success:
                    log_system_event(f"Task {task.id} execution failed. Aborting pipeline.")
                    return False
                    
                self.completed_tasks[task.id] = task.description
                
            log_system_event("Multi-agent orchestration successfully completed the goal!")
            return True

    async def _execute_task(self, task: TaskModel, test_command: str = None) -> bool:
        """Executes a single task based on its assigned agent."""
        log_system_event(f"Executing Task [{task.id}] Assigned to: '{task.assigned_to}'")
        
        if task.assigned_to == "researcher":
            # Formulate researcher prompt
            research_context = "\n".join([f"- Previous Note: {n}" for n in self.research_notes])
            prompt = (
                f"Your task is: {task.description}\n"
                f"Previous research findings (if any):\n{research_context}\n"
                "Please research this requirement and provide a detailed summary of your findings and recommendations."
            )
            
            log_agent_communication("Orchestrator", "ResearcherAgent", prompt)
            research_result = await self.researcher.chat(prompt)
            
            # Store notes for coding agents
            self.research_notes.append(f"Task [{task.id}] Findings: {research_result}")
            log_system_event(f"Researcher findings saved for Task [{task.id}].")
            return True
            
        elif task.assigned_to == "coder":
            # Formulate coder prompt including all research context
            research_context = "\n\n".join(self.research_notes)
            coder_prompt = (
                f"Your task is: {task.description}\n"
                f"Use the following research context to implement the code:\n{research_context}\n"
                "Write the functional python implementation directly in the workspace."
            )
            
            # Coder and Reviewer validation loop
            retries = 0
            while retries <= self.max_reviewer_retries:
                log_agent_communication("Orchestrator", "CoderAgent", coder_prompt)
                coder_result = await self.coder.chat(coder_prompt)
                
                # Audit the code using the ReviewerAgent
                reviewer_prompt = (
                    f"Validate the coder's implementation against task objective: '{task.description}'\n"
                    f"Coder's response output: {coder_result}"
                )
                log_agent_communication("Orchestrator", "ReviewerAgent", reviewer_prompt)
                
                # We review the files created in the workspace. Let's ask Reviewer to check the workspace.
                # Since Reviewer has access to RUN_COMMAND, it can check and run tests.
                review_result = await self.reviewer.review_code(
                    task_description=task.description,
                    files_to_review=["workspace files"],
                    test_command=test_command
                )
                
                if review_result.passed:
                    log_system_event(f"Task [{task.id}] PASSED reviewer audit on attempt {retries + 1}.")
                    return True
                else:
                    log_system_event(f"Task [{task.id}] FAILED reviewer audit on attempt {retries + 1}. Feedback: {review_result.feedback}")
                    # Feed feedback back to the coder for the next retry
                    coder_prompt = (
                        f"Your previous implementation for task '{task.description}' failed review.\n"
                        f"Reviewer Feedback:\n{review_result.feedback}\n"
                        f"Test stdout:\n{review_result.test_stdout}\n"
                        f"Test stderr:\n{review_result.test_stderr}\n"
                        "Please correct the implementation, resolve all errors/feedback, and update the workspace files."
                    )
                    retries += 1
            
            log_system_event(f"Task [{task.id}] exceeded maximum review retries ({self.max_reviewer_retries}).")
            return False
            
        else:
            log_system_event(f"Unknown agent assignment: {task.assigned_to}")
            return False
