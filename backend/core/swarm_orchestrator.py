"""
Async Swarm Orchestrator.

Replaces the thread-based SwarmAgent with asyncio-native tasks.
Persists agent task history to the Black Book for survival across restarts.
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional
from core.black_book import BlackBook

logger = logging.getLogger(__name__)


class SwarmOrchestrator:
    """
    Spawns multiple async agents concurrently to solve problems globally.
    Uses asyncio instead of threads to avoid blocking the FastAPI event loop.
    Persists task history to SQLite so state survives restarts.
    """
    
    def __init__(self, db: Optional[BlackBook] = None):
        self.db = db or BlackBook()
        self._ensure_table()
        self.active_tasks: Dict[str, asyncio.Task] = {}
    
    def _ensure_table(self):
        """Create the AgentTasks table if it doesn't exist."""
        self.db.execute_query('''
            CREATE TABLE IF NOT EXISTS AgentTasks (
                task_id TEXT PRIMARY KEY,
                objective TEXT NOT NULL,
                payload TEXT DEFAULT '{}',
                status TEXT DEFAULT 'pending',
                result TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )
        ''')
    
    async def _execute_objective(self, task_id: str, objective: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single agent objective asynchronously."""
        logger.info(f"[SwarmAgent {task_id}] Initializing: {objective}")
        
        # Update status to running
        self.db.execute_query(
            "UPDATE AgentTasks SET status='running' WHERE task_id=?",
            (task_id,)
        )
        
        # Yield control to the event loop (non-blocking)
        await asyncio.sleep(0)
        
        # Process the objective dynamically using the Tool Registry
        try:
            from core.tool_registry import tool_registry
            import os
            from google import genai
            
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY missing. Swarm Agent cannot think.")
                
            client = genai.Client()
            
            prompt = (
                f"You are a Swarm Agent. Your objective is: '{objective}'.\n"
                f"Payload data: {payload}\n\n"
                f"Available Tools:\n{tool_registry.get_tool_descriptions()}\n\n"
                "Select ONE tool to execute to achieve this objective. Respond strictly in JSON format:\n"
                "{\"tool_name\": \"name\", \"kwargs\": {\"arg1\": \"value\"}}"
            )
            
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )
            
            import json
            # Extract JSON from potential markdown blocks
            text = response.text.strip()
            if text.startswith("```json"):
                text = text.split("```json")[1].split("```")[0].strip()
            elif text.startswith("```"):
                text = text.split("```")[1].strip()
                
            decision = json.loads(text)
            
            tool_name = decision.get("tool_name")
            kwargs = decision.get("kwargs", {})
            
            if tool_name:
                logger.info(f"Swarm Agent selected tool: {tool_name}")
                tool_result = tool_registry.execute_tool(tool_name, **kwargs)
                result = {"status": "success", "action": f"Executed {tool_name}", "tool_result": tool_result}
            else:
                result = {"status": "error", "action": "LLM failed to select a tool."}
                
        except Exception as e:
            logger.error(f"Swarm Agent Execution Error: {e}")
            result = {"status": "error", "action": str(e)}
        
        # Persist completion
        import json
        self.db.execute_query(
            "UPDATE AgentTasks SET status='completed', result=?, completed_at=CURRENT_TIMESTAMP WHERE task_id=?",
            (json.dumps(result), task_id)
        )
        
        logger.info(f"[SwarmAgent {task_id}] Completed. Result: {result}")
        return result
    
    async def dispatch(self, objective: str, payload: Dict[str, Any] = None) -> str:
        """Dispatch a new async agent. Returns the task ID."""
        import json
        
        task_id = f"AGENT_{int(time.time() * 1000)}"
        payload = payload or {}
        
        # Persist to DB
        self.db.execute_query(
            "INSERT INTO AgentTasks (task_id, objective, payload, status) VALUES (?, ?, ?, 'pending')",
            (task_id, objective, json.dumps(payload))
        )
        
        # Launch async task
        task = asyncio.create_task(self._execute_objective(task_id, objective, payload))
        self.active_tasks[task_id] = task
        
        # Cleanup callback
        def _on_done(t, tid=task_id):
            self.active_tasks.pop(tid, None)
        task.add_done_callback(_on_done)
        
        logger.info(f"Dispatched Swarm Agent: {task_id}")
        return task_id
    
    def get_status(self) -> Dict[str, Any]:
        """Get swarm status from persistent storage."""
        total = self.db.execute_query("SELECT COUNT(*) FROM AgentTasks")
        running = self.db.execute_query("SELECT COUNT(*) FROM AgentTasks WHERE status='running'")
        completed = self.db.execute_query("SELECT COUNT(*) FROM AgentTasks WHERE status='completed'")
        
        return {
            "total_dispatched": total[0][0] if total else 0,
            "running": running[0][0] if running else 0,
            "completed": completed[0][0] if completed else 0,
            "active_in_memory": len(self.active_tasks)
        }
    
    def get_recent_tasks(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent task history."""
        import json
        rows = self.db.execute_query(
            "SELECT task_id, objective, status, result, created_at, completed_at FROM AgentTasks ORDER BY created_at DESC LIMIT ?",
            (limit,)
        )
        return [
            {
                "task_id": r[0], "objective": r[1], "status": r[2],
                "result": json.loads(r[3]) if r[3] else None,
                "created_at": r[4], "completed_at": r[5]
            }
            for r in rows
        ]


swarm_orchestrator = SwarmOrchestrator()
