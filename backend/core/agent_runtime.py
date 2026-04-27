"""
Agent Runtime: The Autonomous Sense→Think→Act Loop.

This is Andrew's brain stem — the unified agent loop that makes Andrew
an actual autonomous agent instead of a collection of passive API endpoints.

Architecture:
    Every cycle (default 15 min), Andrew:
    1. SENSE  — Poll inputs (calendar, email, Upwork, system health)
    2. THINK  — Triage, prioritize, draft responses via Persona + Monitor
    3. ACT    — Execute Green Zone actions, queue Yellow Zone drafts in Outbox
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional

from core.black_book import BlackBook
from core.persona import PersonaEngine
from core.monitor import MonitorAgent
from core.survival_engine import SurvivalEngine

logger = logging.getLogger(__name__)


# ─── Risk Zone Classification ───────────────────────────────────────
RISK_ZONES = {
    "green": [
        "calendar_block", "family_reply", "video_summary",
        "scout_scan", "skill_quiz", "heartbeat_cycle", 
        "execute_self_upgrade", "build_module"
    ],
    "yellow": [
        "linkedin_post", "upwork_proposal", "github_commit",
        "client_email", "cold_outreach", "whatsapp_professional"
    ],
    "red": [
        "delete_code", "spend_money", "merge_main",
        "resign", "send_legal", "modify_env"
    ]
}


def classify_risk(action_type: str) -> str:
    """Classify an action into Green/Yellow/Red risk zone."""
    for zone, actions in RISK_ZONES.items():
        if action_type in actions:
            return zone
    return "yellow"  # Default to yellow (cautious) for unknown actions


class DraftOutbox:
    """
    The 10-Minute Outbox for Yellow Zone actions.
    
    When Andrew drafts something in the Yellow Zone, it goes here.
    After 10 minutes with no explicit cancel from the user,
    the draft auto-sends (for approved circles) or auto-expires.
    """
    
    def __init__(self, db: BlackBook):
        self.db = db
        self._ensure_table()
    
    def _ensure_table(self):
        """Create the DraftOutbox table if it doesn't exist."""
        self.db.execute_query('''
            CREATE TABLE IF NOT EXISTS DraftOutbox (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action_type TEXT NOT NULL,
                target TEXT NOT NULL,
                content TEXT NOT NULL,
                circle TEXT DEFAULT 'default',
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                resolved_at TIMESTAMP,
                resolved_by TEXT
            )
        ''')
    
    def queue_draft(self, action_type: str, target: str, content: str, circle: str = "default", ttl_minutes: int = 10) -> int:
        """Queue a draft in the outbox. Returns the draft ID."""
        expires_at = (datetime.now(timezone.utc) + timedelta(minutes=ttl_minutes)).isoformat()
        
        result = self.db.execute_query(
            'INSERT INTO DraftOutbox (action_type, target, content, circle, expires_at) VALUES (?, ?, ?, ?, ?) RETURNING id',
            (action_type, target, content, circle, expires_at)
        )
        draft_id = result[0][0] if result else -1
        logger.info(f"[Outbox] Queued draft #{draft_id}: {action_type} → {target} (expires in {ttl_minutes}m)")
        return draft_id
    
    def approve_draft(self, draft_id: int) -> bool:
        """User explicitly approves a draft for immediate send."""
        self.db.execute_query(
            "UPDATE DraftOutbox SET status='approved', resolved_at=CURRENT_TIMESTAMP, resolved_by='user' WHERE id=? AND status='pending'",
            (draft_id,)
        )
        logger.info(f"[Outbox] Draft #{draft_id} approved by user.")
        return True
    
    def cancel_draft(self, draft_id: int) -> bool:
        """User explicitly cancels a draft."""
        self.db.execute_query(
            "UPDATE DraftOutbox SET status='cancelled', resolved_at=CURRENT_TIMESTAMP, resolved_by='user' WHERE id=? AND status='pending'",
            (draft_id,)
        )
        logger.info(f"[Outbox] Draft #{draft_id} cancelled by user.")
        return True
    
    def get_pending_drafts(self) -> List[Dict[str, Any]]:
        """Get all pending drafts."""
        rows = self.db.execute_query(
            "SELECT id, action_type, target, content, circle, status, created_at, expires_at FROM DraftOutbox WHERE status='pending' ORDER BY created_at DESC"
        )
        return [
            {"id": r[0], "action_type": r[1], "target": r[2], "content": r[3],
             "circle": r[4], "status": r[5], "created_at": r[6], "expires_at": r[7]}
            for r in rows
        ]
    
    def process_expired_drafts(self) -> List[Dict[str, Any]]:
        """
        Check for expired drafts. Auto-send approved-circle drafts, 
        auto-expire restricted ones.
        """
        now = datetime.now(timezone.utc).isoformat()
        expired = self.db.execute_query(
            "SELECT id, action_type, target, content, circle FROM DraftOutbox WHERE status='pending' AND expires_at <= ?",
            (now,)
        )
        
        auto_send_circles = {"family", "brother", "friend"}
        results = []
        
        for row in expired:
            draft_id, action_type, target, content, circle = row
            if circle.lower() in auto_send_circles:
                self.db.execute_query(
                    "UPDATE DraftOutbox SET status='auto_sent', resolved_at=CURRENT_TIMESTAMP, resolved_by='timer' WHERE id=?",
                    (draft_id,)
                )
                results.append({"id": draft_id, "action": "auto_sent", "reason": f"Circle '{circle}' allows auto-send"})
                logger.info(f"[Outbox] Draft #{draft_id} auto-sent (circle: {circle})")
            else:
                self.db.execute_query(
                    "UPDATE DraftOutbox SET status='expired', resolved_at=CURRENT_TIMESTAMP, resolved_by='timer' WHERE id=?",
                    (draft_id,)
                )
                results.append({"id": draft_id, "action": "expired", "reason": f"Circle '{circle}' requires explicit approval"})
                logger.info(f"[Outbox] Draft #{draft_id} expired (circle: {circle})")
        
        return results


class AgentRuntime:
    """
    Andrew's Autonomous Brain Stem.
    
    Runs a continuous Sense→Think→Act loop that makes Andrew
    a proactive agent rather than a passive API.
    """
    
    def __init__(self, cycle_interval_minutes: int = 15):
        self.cycle_interval = cycle_interval_minutes * 60
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        
        # Core systems
        self.memory = BlackBook()
        self.persona = PersonaEngine()
        self.monitor = MonitorAgent()
        self.survival = SurvivalEngine()
        self.outbox = DraftOutbox(self.memory)
        
        # Revenue & Intelligence systems
        from core.market_scanner import market_scanner
        from core.revenue_lab import revenue_lab
        from core.people_intel import people_intel
        self.market_scanner = market_scanner
        self.revenue_lab = revenue_lab
        self.people_intel = people_intel
        self.revenue_lab.seed_experiments()  # Ensure experiments are always running
        
        # Cycle tracking
        self.cycle_count = 0
        self.last_cycle_at: Optional[str] = None
        self.modes = ["evolution", "planning", "planning", "planning", "planning"]
        
        # Restore mode index from persistence
        saved_mode = self.memory.get_preference("heartbeat_mode", "0")
        self.current_mode_index = int(saved_mode) if saved_mode.isdigit() else 0
        
        logger.info("Agent Runtime initialized.")
    
    # ─── SENSE PHASE ────────────────────────────────────────────
    async def _sense(self) -> Dict[str, Any]:
        """
        Poll all input sources and return a unified context snapshot.
        """
        context = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "mode": self.modes[self.current_mode_index],
            "inputs": {}
        }
        
        # 1. System health check
        health = self.survival.check_system_health()
        context["inputs"]["system_health"] = health
        
        # 2. Check for expired outbox drafts
        expired_actions = self.outbox.process_expired_drafts()
        context["inputs"]["outbox_expired"] = expired_actions
        
        # 2.5 Inject Memory Cortex (S2)
        try:
            from db.memory_cortex import memory_cortex
            context["inputs"]["semantic_memory"] = memory_cortex.retrieve_relevant_knowledge("current priorities")
            context["inputs"]["recent_episodes"] = memory_cortex.get_recent_episodes(limit=5)
        except Exception as e:
            logger.error(f"[Sense] Failed to connect to Memory Cortex: {e}")
        
        # 3. Mode-specific sensing
        current_mode = self.modes[self.current_mode_index]
        
        if current_mode == "scouting":
            from core.bounty_hunter import bounty_hunter
            from core.phantom_network import phantom_network
            
            logger.info("[Sense] Scouting mode — executing Bounty Hunter, Phantom Network & People Intel.")
            res = bounty_hunter.scan_and_execute()
            scout_jobs = [res] if res.get("status") != "no_bounties" and res.get("status") != "api_error" else []
            
            pn_res = phantom_network.scan_and_deploy()
            leads = []
            if pn_res.get("status") == "ready_for_review":
                leads.append(pn_res)
                self.outbox.queue_draft(
                    action_type="phantom_network_outreach",
                    target=pn_res.get("business_type", "Target Business"),
                    content=pn_res.get("email_draft", "Draft content missing"),
                    circle="default"
                )
            
            # People Intel: mine forums for buyer language & psychology
            forum_result = self.people_intel.scan_forums()
            people_briefing = self.people_intel.get_people_briefing()
            
            context["inputs"]["scout_results"] = {
                "new_jobs": scout_jobs, "status": "scanned",
                "leads_found": len(leads),
                "people_intel": forum_result,
                "human_experience_count": self.people_intel.get_interaction_count(),
            }
            context["inputs"]["people_briefing"] = people_briefing
            
        elif current_mode == "researching":
            from core.omni_presence import omnipresence
            logger.info("[Sense] Researching mode — OmniPresence + Market Scanner.")
            
            trends = omnipresence.scan_forums()
            market_result = self.market_scanner.run()
            recent_insights = self.market_scanner.get_recent_insights(days=3)
            
            context["inputs"]["research"] = {
                "articles_found": len(trends),
                "status": "scanned",
                "market_scan": market_result,
                "recent_market_insights": recent_insights,
                "top_opportunity": self.memory.get_preference("todays_top_opportunity", "None identified yet"),
            }
            
        elif current_mode == "maintenance":
            from core.wealth_manager import wealth_manager
            logger.info("[Sense] Maintenance mode — wealth audit + revenue experiment evaluation.")
            
            wealth_manager.monitor_market_dips()
            # NOTE: issue_autonomous_dividend() removed from auto-cycle.
            # Dividends require explicit user command — never run autonomously.
            experiment_verdicts = self.revenue_lab.evaluate_experiments()
            
            context["inputs"]["maintenance"] = {
                "status": "wealth_audited",
                "experiment_verdicts": experiment_verdicts,
                "active_experiments": self.revenue_lab.get_active_summary(),
            }
            
        elif current_mode == "synthesis":
            from core.hype_man import hype_man
            logger.info("[Sense] Synthesis mode — generating PR and LinkedIn posts.")
            
            post = hype_man.generate_daily_update()
            context["inputs"]["synthesis"] = {"post_generated": True, "status": "ready"}
            
        elif current_mode == "planning":
            from core.swarm_brain_trust import swarm_brain_trust
            from core.roadmap_manager import roadmap_manager
            
            logger.info("[Sense] Planning mode — Brain Trust convening to architect next upgrade.")
            status = roadmap_manager.get_roadmap_status()
            pending = next((m for m in status.get("milestones", []) if m.get("status") == "pending"), None)
            
            topic = pending.get("title") if pending else "Determine next strategic evolution objective"
            meeting_result = await swarm_brain_trust.convene_meeting(f"How to implement: {topic}")
            
            context["inputs"]["planning"] = {
                "topic": topic,
                "consensus_plan": meeting_result.get("consensus"),
                "status": "plan_ready"
            }
            
        elif current_mode == "evolution":
            from core.roadmap_manager import roadmap_manager
            logger.info("[Sense] Evolution mode — checking roadmap for pending self-upgrades.")
            status = roadmap_manager.get_roadmap_status()
            pending_milestone = next((m for m in status.get("milestones", []) if m.get("status") == "pending"), None)
            
            context["inputs"]["evolution"] = {
                "roadmap_progress": status.get("progress_percentage", 0),
                "pending_milestone": pending_milestone,
                "status": "ready_for_upgrade" if pending_milestone else "all_caught_up"
            }
        
        return context
    
    # ─── THINK PHASE ────────────────────────────────────────────
    async def _think(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Analyze sensed inputs and decide on actions dynamically via LLM Reasoning.
        Returns a list of action plans with risk classifications.
        """
        logger.info("[Think] Initiating Reasoning Engine...")
        action_plans = []
        
        try:
            from core.tool_registry import tool_registry
            import json
            
            # 1. Context Assembler
            # We convert the raw inputs (health, scout, etc.) into a prompt.
            reasoning_prompt = (
                "You are the central strategic brain of Project Andrew, an autonomous executive assistant.\n"
                f"Current system context and sensor inputs:\n{json.dumps(context['inputs'], indent=2)}\n\n"
                f"Available Tools (Hands):\n{tool_registry.get_tool_descriptions()}\n\n"
                "Based on the context, decide what actions (if any) you need to take right now to serve the user's best interests. "
                "For each action, select a valid tool from the Available Tools list. "
                "Return a strict JSON array of objects. Each object must have:\n"
                "- 'type': the name of the tool from the registry.\n"
                "- 'data': a dictionary of arguments matching the tool's schema.\n"
                "- 'reason': a brief explanation of why this action is necessary.\n"
                "- 'risk_zone': 'green', 'yellow', or 'red'.\n\n"
                "If no action is necessary, return an empty array []."
            )
            
            # 2. The Brain
            response = self.persona.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=reasoning_prompt,
            )
            
            # 3. Parse Action Plans
            text = response.text.strip()
            if text.startswith("```json"):
                text = text.split("```json")[1].split("```")[0].strip()
            elif text.startswith("```"):
                text = text.split("```")[1].strip()
                
            parsed_plans = json.loads(text)
            if isinstance(parsed_plans, list):
                action_plans = parsed_plans
            else:
                logger.warning("Reasoning Engine did not return a JSON array.")
                
        except Exception as e:
            logger.error(f"[Think] Reasoning Engine Error: {e}")
            # Fallback for critical system survival
            health = context["inputs"].get("system_health", {})
            if health.get("status") == "critical":
                action_plans.append({
                    "type": "system_migration_request",
                    "risk_zone": "red",
                    "data": self.survival.request_migration_permission(),
                    "reason": f"System health critical: {health.get('reason')}"
                })
        
        # 4. AEC: Mandatory Ethical Validation (Safety Sandbox)
        from core.ethical_core import ethical_core
        for plan in action_plans:
            objective = plan.get("reason", plan.get("type", "Unknown Action"))
            audit = ethical_core.validate_intent(objective)
            if not audit["is_valid"]:
                logger.critical(f"ETHICAL CORE BLOCK: Violations detected in plan '{objective}'")
                plan["action"] = "HALTED: Ethical Violation"
                plan["risk_zone"] = "red"
            else:
                ethical_core.reward_alignment(f"Formulated positive plan: {objective[:30]}...")

        return action_plans
    
    # ─── ACT PHASE ──────────────────────────────────────────────
    async def _act(self, action_plans: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Execute actions based on risk zone classification.
        - Green: Execute immediately
        - Yellow: Queue in 10-minute outbox
        - Red: Block and alert user
        """
        results = []
        
        for plan in action_plans:
            zone = plan["risk_zone"]
            action_type = plan["type"]
            
            if zone == "green":
                # Auto-execute
                logger.info(f"[Act] ✅ Green Zone: Executing '{action_type}' autonomously.")
                try:
                    from core.outcome_tracker import outcome_tracker
                    action_id = outcome_tracker.log_action(action_type, target="Autonomous System", context=str(plan))
                    # Note: We would actually execute it here via ToolRegistry if we had dynamic args, 
                    # but tool execution currently happens in SwarmOrchestrator or Think phase logic.
                    # Since Think phase just plans it, we should actually execute it.
                    from core.tool_registry import tool_registry
                    if "type" in plan and "data" in plan:
                        tool_registry.execute_tool(action_type, **plan.get("data", {}))
                    outcome_tracker.log_outcome(action_id, "success", 1.0)
                except Exception as e:
                    logger.error(f"[Act] Execution failed: {e}")
                    try:
                        from core.outcome_tracker import outcome_tracker
                        outcome_tracker.log_outcome(action_id, "failure", 0.0, notes=str(e))
                    except Exception as logging_err:
                        logger.error(f"[Act] Outcome tracking failed: {logging_err}")

                results.append({
                    "action": action_type,
                    "zone": "green",
                    "status": "executed",
                    "detail": plan.get("reason", "")
                })
                
            elif zone == "yellow":
                # Queue in outbox for human review
                content = str(plan.get("data", {}).get("briefing", plan.get("reason", "")))
                target = str(plan.get("data", {}).get("job", {}).get("title", "Unknown"))
                
                draft_id = self.outbox.queue_draft(
                    action_type=action_type,
                    target=target,
                    content=content,
                    circle=plan.get("data", {}).get("circle", "default")
                )
                
                try:
                    from core.outcome_tracker import outcome_tracker
                    action_id = outcome_tracker.log_action(action_type, target=target, context=f"Draft #{draft_id}")
                    outcome_tracker.log_outcome(action_id, "pending", 0.0, notes="Queued for user review")
                except Exception as e:
                    logger.error(f"[Act] Failed to log yellow zone outcome: {e}")

                logger.info(f"[Act] ⏳ Yellow Zone: Queued '{action_type}' as Draft #{draft_id}. User has 10 min to review.")
                results.append({
                    "action": action_type,
                    "zone": "yellow",
                    "status": "queued",
                    "draft_id": draft_id,
                    "detail": plan.get("reason", "")
                })
                
            elif zone == "red":
                # Hard block
                try:
                    from core.outcome_tracker import outcome_tracker
                    action_id = outcome_tracker.log_action(action_type, target="Blocked", context=plan.get("reason", ""))
                    outcome_tracker.log_outcome(action_id, "failure", 0.0, notes="Blocked by Safety Rules")
                except Exception as e:
                    logger.error(f"[Act] Failed to log red zone outcome: {e}")

                logger.warning(f"[Act] 🚫 Red Zone: BLOCKED '{action_type}'. Reason: {plan.get('reason', 'Safety override')}")
                results.append({
                    "action": action_type,
                    "zone": "red",
                    "status": "blocked",
                    "detail": f"BLOCKED: {plan.get('reason', 'Requires manual override')}"
                })
        
        return results
    
    # ─── MAIN LOOP ──────────────────────────────────────────────
    async def _run_cycle(self):
        """Execute one full Sense→Think→Act cycle."""
        self.cycle_count += 1
        cycle_start = time.time()
        current_mode = self.modes[self.current_mode_index]
        
        logger.info(f"═══ Agent Cycle #{self.cycle_count} | Mode: {current_mode.upper()} ═══")
        
        try:
            # Phase 1: Sense
            context = await self._sense()
            
            # Phase 2: Think
            action_plans = await self._think(context)
            
            # Phase 3: Act
            results = await self._act(action_plans)
            
            # Log cycle summary
            elapsed = time.time() - cycle_start
            self.last_cycle_at = datetime.now(timezone.utc).isoformat()
            
            logger.info(
                f"═══ Cycle #{self.cycle_count} Complete | "
                f"Actions: {len(results)} | "
                f"Duration: {elapsed:.2f}s ═══"
            )
            
            # S3: Schedule Daily Retrospective
            current_hour = datetime.utcnow().hour
            # Run at roughly 23:00 UTC, once per day
            if current_hour == 23 and self.cycle_count % 4 == 0:
                try:
                    from core.retrospective import retrospective_engine
                    logger.info("Triggering Daily Retrospective...")
                    retrospective_engine.run_daily_retrospective()
                except Exception as e:
                    logger.error(f"Daily Retrospective failed: {e}")

            # Rotate mode for next cycle
            self.current_mode_index = (self.current_mode_index + 1) % len(self.modes)
            self.memory.set_preference("heartbeat_mode", str(self.current_mode_index))
            
        except Exception as e:
            logger.error(f"Agent cycle #{self.cycle_count} failed: {e}", exc_info=True)
    
    async def _run_loop(self):
        """Continuous autonomous loop."""
        while self.is_running:
            await self._run_cycle()
            await asyncio.sleep(self.cycle_interval)
    
    # ─── LIFECYCLE ──────────────────────────────────────────────
    def start(self):
        """Start the autonomous agent runtime."""
        if not self.is_running:
            self.is_running = True
            self._task = asyncio.create_task(self._run_loop())
            logger.info(
                f"🚀 Agent Runtime ONLINE. "
                f"Cycle interval: {self.cycle_interval}s. "
                f"Starting in '{self.modes[self.current_mode_index]}' mode."
            )
    
    def stop(self):
        """Gracefully stop the agent runtime."""
        self.is_running = False
        if self._task:
            self._task.cancel()
        logger.info("Agent Runtime OFFLINE.")
    
    def get_status(self) -> Dict[str, Any]:
        """Return current runtime status for the Control Center."""
        return {
            "is_running": self.is_running,
            "cycle_count": self.cycle_count,
            "last_cycle_at": self.last_cycle_at,
            "current_mode": self.modes[self.current_mode_index],
            "pending_drafts": len(self.outbox.get_pending_drafts()),
            "cycle_interval_seconds": self.cycle_interval
        }


# Singleton instance
agent_runtime = AgentRuntime()
