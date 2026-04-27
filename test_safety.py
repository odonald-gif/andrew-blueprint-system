import sys
import os
import logging
import asyncio

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from backend.core.monitor import MonitorAgent
from backend.scrapers.developer_bridge import dev_bridge
from backend.scrapers.linkedin_agent import linkedin_agent

logging.basicConfig(level=logging.INFO)

print("--- Testing Monitor Agent ---")
monitor = MonitorAgent(ai_provider="mock") # Use mock to avoid API calls during test

# Safe message
safe, reason = monitor.audit_draft("Hello, I am scheduling the meeting for 2 PM.", "message")
print(f"Safe Message Result: {safe} ({reason})")

# Unsafe credential leak
safe, reason = monitor.audit_draft("Here is my api_key for the server: 12345", "message")
print(f"Unsafe Credential Result: {safe} ({reason})")

# Unsafe github commit
safe, reason = monitor.audit_draft("I am going to merge to main branch now.", "github")
print(f"Unsafe GitHub Result: {safe} ({reason})")

print("\n--- Testing Developer Bridge ---")
res = dev_bridge.trigger_antigravity_build("Create a new login feature")
print(f"Build Result: {res}")

res = dev_bridge.push_to_github("main", "Fixed login bug")
print(f"Main Push Result (Should block): {res}")

res = dev_bridge.push_to_github("auth-update", "Fixed login bug")
print(f"Feature Push Result: {res}")

print("\n--- Testing LinkedIn Agent ---")
async def check_linkedin():
    res = await linkedin_agent.draft_and_post("This is a test post.", auto_post=False)
    print(f"LinkedIn Result: {res}")

asyncio.run(check_linkedin())
