import argparse
import asyncio
import sys
from core.orchestrator import MultiAgentOrchestrator
from core.logging import log_system_event

async def main():
    parser = argparse.ArgumentParser(description="Multi-Agent AI System for Software R&D")
    parser.add_argument(
        "goal", 
        type=str, 
        help="The high-level goal you want the multi-agent team to accomplish"
    )
    parser.add_argument(
        "--test-command", 
        type=str, 
        default=None,
        help="Optional test command for the Reviewer Agent to execute to verify the solution (e.g. 'pytest tests/')"
    )
    parser.add_argument(
        "--retries", 
        type=int, 
        default=3,
        help="Max retries for Reviewer Agent feedback loops (default: 3)"
    )
    
    args = parser.parse_args()
    
    orchestrator = MultiAgentOrchestrator(max_reviewer_retries=args.retries)
    
    log_system_event("=== STARTING MULTI-AGENT EXECUTION ===")
    try:
        success = await orchestrator.execute_goal(args.goal, test_command=args.test_command)
        if success:
            log_system_event("=== MULTI-AGENT EXECUTION SUCCESSFUL ===")
            sys.exit(0)
        else:
            log_system_event("=== MULTI-AGENT EXECUTION FAILED ===")
            sys.exit(1)
    except Exception as e:
        log_system_event(f"Unhandled pipeline exception: {e}")
        sys.exit(2)

if __name__ == "__main__":
    asyncio.run(main())
