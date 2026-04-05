"""
run_agent.py

Entry point to execute the Auto-PPT Agent.
"""

import asyncio
from agent.core.executor import run_agent
import sys

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
if __name__ == "__main__":
    user_input = input("Enter topic: ")

    asyncio.run(run_agent(user_input))