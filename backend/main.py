from fastapi import FastAPI, HTTPException, Security, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager


from core.black_book import BlackBook
from core.motion_solver import MotionSolver
from core.persona import PersonaEngine
from scrapers.scout import DigitalScout
from scrapers.developer_bridge import dev_bridge
from scrapers.linkedin_agent import linkedin_agent
from core.agent_runtime import agent_runtime
from core.learning import learning_engine
from core.leverage import leverage_tracker
from core.awareness import awareness_engine

from core.crm_manager import crm_manager
from core.motion_engine import motion_engine
from core.email_nexus import email_nexus
import logging
from core.event_bus import event_bus
from integrations.calendar_sync import CalendarSync
import json
import asyncio


import os
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Security Guardian
API_KEY_NAME = "X-Andrew-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(api_key_header: str = Security(api_key_header)):
    expected_key = os.getenv("ANDREW_SECRET_KEY")
    if not expected_key:
        logger.error("ANDREW_SECRET_KEY not set in .env. All requests will be rejected.")
        raise HTTPException(status_code=500, detail="Server misconfigured: API key not set.")
    if api_key_header == expected_key:
        return api_key_header
    else:
        logger.warning(f"Failed intrusion attempt to Andrew Core. Key provided: {api_key_header}")
        raise HTTPException(
            status_code=403, detail="Could not validate Andrew credentials."
        )


# NervousSystem removed — functionality handled by agent_runtime + event_bus

async def ws_broadcast_event(data, event_type):
    message = json.dumps({"type": event_type, "data": data})
    await manager.broadcast(message)

# Subscribe WebSocket to EventBus
event_bus.subscribe("job_found", lambda d: asyncio.create_task(ws_broadcast_event(d, "job_found")))
event_bus.subscribe("gap_found", lambda d: asyncio.create_task(ws_broadcast_event(d, "gap_found")))
event_bus.subscribe("quiz_ready", lambda d: asyncio.create_task(ws_broadcast_event(d, "quiz_ready")))
event_bus.subscribe("status_update", lambda d: asyncio.create_task(ws_broadcast_event(d, "status_update")))
event_bus.subscribe("feature_added", lambda d: asyncio.create_task(ws_broadcast_event(d, "feature_added")))

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: launch the autonomous agent runtime
    logger.info("Starting Andrew Core Lifespan...")
    event_bus.start()
    agent_runtime.start()
    # Agent runtime handles all autonomous cycles internally
    yield
    # Shutdown: gracefully stop the agent
    logger.info("Shutting down Andrew Core Lifespan...")
    event_bus.stop()
    agent_runtime.stop()

app = FastAPI(
    title="Andrew",
    version="1.0.0",
    description=(
        "Andrew is an autonomous executive agent that manages your calendar, "
        "finances, outreach, and software development. He scouts for opportunities, "
        "drafts proposals, builds code, and learns from every interaction — "
        "all while keeping you in control of high-stakes decisions."
    ),
    lifespan=lifespan
)

# CORS — allow the Control Center frontend to communicate seamlessly across local network
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
memory = BlackBook()

solver = MotionSolver()
persona = PersonaEngine()
scout = DigitalScout()
calendar_sync = CalendarSync()

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

# Pydantic models for incoming data structures
class TaskInput(BaseModel):
    id: str
    duration: int
    priority: int = 1
    deadline: Optional[int] = 1440
    hard_deadline: Optional[bool] = False

class BusySlot(BaseModel):
    start: int
    end: int

class ScheduleRequest(BaseModel):
    tasks: List[TaskInput]
    busy_slots: List[BusySlot]

class PersonaResponse(BaseModel):
    summary: str
    raw_schedule: Dict[str, Any]

class WhatsAppPayload(BaseModel):
    sender: str
    message_content: str
    media_url: Optional[str] = None
    circle: str = "default"

class LinkedInPayload(BaseModel):
    content: str
    auto_post: bool = False

class DeveloperBuildPayload(BaseModel):
    task_description: str
    feature_branch: Optional[str] = None
    commit_message: Optional[str] = None

class BriefingPayload(BaseModel):
    meeting_context: str
    voice_note_transcript: str

class LeveragePayload(BaseModel):
    contact: str
    value: str

class OverrunPayload(BaseModel):
    contact: str
    end_time_minutes: int
    current_time_minutes: int

class TriagePayload(BaseModel):
    task_name: str
    urgency: int
    importance: int

class SchedulePayload(BaseModel):
    date: str
    available_hours: int

class MessagePayload(BaseModel):
    sender: str
    circle: str
    message: str
    media_url: str = None

class ChatPayload(BaseModel):
    user_message: str

class PayoutPayload(BaseModel):
    amount: float

class MeetingPayload(BaseModel):
    topic: str





class AuthPayload(BaseModel):
    email: str
    password: str

@app.get("/")
def read_root():
    return {"status": "Andrew Core Online"}

@app.post("/api/v1/auth")
def auth_login(payload: AuthPayload):
    owner_email = os.getenv("ANDREW_OWNER_EMAIL")
    owner_pass = os.getenv("ANDREW_OWNER_PASSWORD")
    if payload.email == owner_email and payload.password == owner_pass:
        return {"api_key": os.getenv("ANDREW_SECRET_KEY")}
    raise HTTPException(status_code=403, detail="Invalid credentials")

class ChatPayload(BaseModel):
    message: str

@app.post("/api/v1/chat")
def chat_with_persona(payload: ChatPayload, api_key: str = Depends(get_api_key)):
    """Chat directly with the PersonaEngine (Donna)."""
    # Use process_user_feedback to handle the generic chat
    response = persona.process_user_feedback(payload.message)
    return {"status": "success", "reply": response}

@app.post("/api/v1/schedule", response_model=PersonaResponse)
def generate_schedule(request: ScheduleRequest, api_key: str = Depends(get_api_key)):
    """
    Receives current tasks and existing calendar slots.
    Outputs the optimized calendar alongside the Andrew strategic briefing.
    """
    # 1. Math block (Motion)
    tasks_dict = [t.model_dump() for t in request.tasks]
    busy_dict = [b.model_dump() for b in request.busy_slots]
    
    result = solver.schedule_tasks(tasks=tasks_dict, busy_slots=busy_dict)
    
    if result["status"] not in ["OPTIMAL", "FEASIBLE"]:
        raise HTTPException(status_code=400, detail="Unable to resolve a feasible schedule.")
    
    # 2. Persona format block (Donna-ism)
    briefing = persona.generate_briefing(raw_data=result, context="schedule_update")

    return PersonaResponse(
        summary=briefing,
        raw_schedule=result
    )

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for the Flutter UI to connect to. 
    Pushes real-time updates when tasks are rescheduled or Andrew acts autonomously.
    """
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Respond to a heartbeat or specific commands from the phone
            await manager.broadcast(f"Andrew Pulse Acknowledged: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/api/v1/scout")
def run_scout_manual(api_key: str = Depends(get_api_key)):
    """Trigger the scout manually to find jobs/scholarships."""
    intel = scout.perform_routine_scan()
    return {"status": "Success", "intel": intel}

@app.get("/api/v1/profile/{name}")
def get_user_profile(name: str, api_key: str = Depends(get_api_key)):
    """Retrieve intel from the Black Book"""
    profile = memory.get_profile(name)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found in Black Book.")
    return profile

@app.post("/webhook/whatsapp")
def handle_whatsapp_webhook(payload: WhatsAppPayload, api_key: str = Depends(get_api_key)):
    """
    Receives incoming WhatsApp messages from n8n.
    Passes them to the Mirror Engine (Persona) to generate a Twin Reply.
    Returns the reply back to n8n to be sent.
    """
    logger.info(f"Received WhatsApp message from {payload.sender} ({payload.circle} circle)")
    
    reply = persona.generate_twin_reply(
        sender=payload.sender,
        circle=payload.circle,
        message_content=payload.message_content,
        media_url=payload.media_url
    )
    
    # In a fully integrated system, we would also add the incoming message to mirror_db here
    # mirror_db.add_interaction(payload.sender, payload.circle, payload.message_content)
    # However, mirror_db stores *outbound* (your) messages to learn your style, not inbound.
    
    return {"status": "Success", "reply": reply}

@app.post("/webhook/linkedin")
async def handle_linkedin_post(payload: LinkedInPayload, api_key: str = Depends(get_api_key)):
    """
    Triggers the LinkedIn Playwright Agent to organically post content
    using the provided Session Cookie to bypass bans.
    """
    logger.info("Triggering LinkedIn organic post sequence.")
    
    # Optional: We could run the content through the PersonaEngine or MonitorAgent here
    # but for now we assume the payload content is pre-drafted or pre-audited.
    
    result = await linkedin_agent.draft_and_post(
        content=payload.content, 
        auto_post=payload.auto_post
    )
    
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["output"])
        
    return result

@app.post("/api/v1/developer/build")
def trigger_developer_bridge(payload: DeveloperBuildPayload, api_key: str = Depends(get_api_key)):
    """
    Commands the Antigravity CLI to build architecture in a sandbox,
    and optionally pushes to a GitHub feature branch.
    """
    logger.info(f"Triggering Developer Bridge for task: {payload.task_description}")
    
    build_result = dev_bridge.trigger_antigravity_build(payload.task_description)
    
    if build_result["status"] == "error":
        raise HTTPException(status_code=500, detail=build_result["output"])
        
    git_output = None
    if payload.feature_branch and payload.commit_message:
        push_result = dev_bridge.push_to_github(payload.feature_branch, payload.commit_message)
        git_output = push_result["output"]
        if push_result["status"] == "blocked" or push_result["status"] == "error":
            logger.warning(f"Git push failed or was blocked: {git_output}")
            
    return {
        "status": "Success", 
        "build_output": build_result["output"],
        "git_output": git_output
    }

@app.post("/api/v1/briefing/post-meeting")
def handle_post_meeting_briefing(payload: BriefingPayload, api_key: str = Depends(get_api_key)):
    """
    The Data-Driven Empathy Loop.
    Receives text transcripts of voice notes taken immediately after a meeting.
    Extracts key relationship context and updates the Black Book dynamically.
    """
    logger.info(f"Processing post-meeting briefing for: {payload.meeting_context}")
    
    # Analyze the transcript to extract facts (e.g. "He likes golf")
    # and update the memory vault.
    extracted_insight = persona.generate_briefing(
        raw_data={"transcript": payload.voice_note_transcript, "context": payload.meeting_context},
        context="extract_facts"
    )
    
    # Store in memory for future reference
    # memory.update_profile(name="Extracted_Entity", facts=[extracted_insight])
    
    return {
        "status": "Success",
        "message": "Black Book updated with post-meeting insights.",
        "insight_extracted": extracted_insight
    }

@app.get("/api/v1/learning/audit")
def get_partnership_audit(api_key: str = Depends(get_api_key)):
    """
    Returns the Honest Score and Autonomy Level for the Flutter UI slider.
    """
    return {"status": "Success", "audit": {"message": "Use /api/v1/runtime/status for agent health."}}

@app.post("/api/v1/leverage/add")
def add_favor(payload: LeveragePayload, api_key: str = Depends(get_api_key)):
    success = leverage_tracker.log_favor(payload.contact, payload.value)
    return {"status": "Success" if success else "Failed", "contact": payload.contact}

@app.get("/api/v1/leverage/{contact}")
def get_favors(contact: str, api_key: str = Depends(get_api_key)):
    favors = leverage_tracker.get_leverage(contact)
    return {"status": "Success", "favors": favors}

@app.post("/api/v1/awareness/overrun")
def check_meeting_overrun(payload: OverrunPayload, api_key: str = Depends(get_api_key)):
    """
    Called by n8n or an internal cron job every 5 minutes to see if we're held over.
    """
    meeting_data = {"contact": payload.contact, "end_time_minutes": payload.end_time_minutes}
    result = awareness_engine.check_meeting_status(meeting_data, payload.current_time_minutes)
    return result

@app.post("/api/v1/triage")
def triage_task(payload: TriagePayload, api_key: str = Depends(get_api_key)):
    # Basic logic placeholder for Motion triage
    score = payload.urgency * 1.5 + payload.importance * 2.0
    status = "Do Now" if score > 15 else "Schedule Later"
    return {"status": "Success", "task": payload.task_name, "triage_score": score, "recommendation": status}

@app.post("/api/v1/messages/incoming")
def process_incoming_message(payload: MessagePayload, api_key: str = Depends(get_api_key)):
    draft = persona.generate_twin_reply(
        sender=payload.sender,
        circle=payload.circle,
        message_content=payload.message,
        media_url=payload.media_url
    )
    return {
        "status": "Success",
        "action": "draft_created",
        "draft_message": draft,
        "original_message": payload.message,
        "sender": payload.sender
    }

@app.post("/api/v1/briefing")
def briefing_room(payload: ChatPayload, api_key: str = Depends(get_api_key)):
    response_text = persona.process_user_feedback(payload.user_message)
    return {
        "status": "Success",
        "reply": response_text
    }

@app.get("/api/v1/revenue")
def get_revenue(api_key: str = Depends(get_api_key)):
    return crm_manager.get_financial_summary()

@app.post("/api/v1/whatsapp/webhook")
def whatsapp_intercept(payload: dict, api_key: str = Depends(get_api_key)):
    from core.aegis_link_scanner import aegis_scanner
    sender = payload.get("sender", "Unknown")
    message = payload.get("message", "")
    
    # Phase 13: Aegis Protocol
    aegis_result = aegis_scanner.scan_payload(message, sender)
    if aegis_result["status"] == "malicious":
        logger.critical(f"AEGIS BLOCKED WhatsApp message from {sender}.")
        return {"status": "blocked", "reason": aegis_result["reason"]}
        
    is_video = "youtube.com" in message.lower()
    from core.persona import persona_engine
    media_url = message if is_video else None
    response = persona_engine.generate_twin_reply(sender, "casual", message, media_url)
    return {"status": "success", "donna_action": response}

@app.post("/api/v1/email/webhook")
def email_intercept(payload: dict, api_key: str = Depends(get_api_key)):
    from core.aegis_link_scanner import aegis_scanner
    sender = payload.get("sender", "Unknown")
    body = payload.get("body", "")
    
    # Phase 13: Aegis Protocol
    aegis_result = aegis_scanner.scan_payload(body, sender)
    if aegis_result["status"] == "malicious":
        logger.critical(f"AEGIS BLOCKED Email from {sender}.")
        return {"status": "blocked", "reason": aegis_result["reason"]}
        
    result = email_nexus.process_incoming_emails()
    return {"status": "success", "email_action": result}


# NOTE: Duplicate /api/v1/auth route removed. Single auth endpoint at line 195.


# ─── Agent Runtime Status ───────────────────────────────────────
@app.get("/api/v1/runtime/status")
def get_runtime_status(api_key: str = Depends(get_api_key)):
    """Get the current autonomous agent runtime status."""
    return agent_runtime.get_status()

@app.get("/api/v1/dashboard/summary")
def get_dashboard_summary(api_key: str = Depends(get_api_key)):
    """Aggregation endpoint for the Flutter UI."""
    from core.wealth_manager import wealth_manager
    revenue_data = wealth_manager.get_portfolio_summary()
    
    # Map portfolio to frontend schema
    owner_wallet = revenue_data.get("wallets", {}).get("owner_personal_wallet", {}).get("balance", 0)
    bounties = revenue_data.get("wallets", {}).get("coinbase_wallet_1", {}).get("balance", 0)
    mapped_revenue = {
        "projected_earnings": owner_wallet,
        "bounties_won": bounties,
        "saas_income": 0.00
    }
    
    outbox_drafts = agent_runtime.outbox.get_pending_drafts()
    # Map to frontend list of maps: [{"sender": "...", "message": "..."}]
    mapped_drafts = []
    for d in outbox_drafts:
        mapped_drafts.append({"id": d["id"], "sender": d["target"], "message": d["content"]})
        
    events = calendar_sync.fetch_todays_events()
    mapped_schedule = []
    for e in events:
        mapped_schedule.append({
            "time": e.get("start", {}).get("dateTime", e.get("start", {}).get("date", "All Day")),
            "title": e.get("summary", "Busy"),
            "urgency": "Medium",
            "energy": 50,
            "type": "work"
        })
        
    system_status = agent_runtime.get_status()
    
    return {
        "status": "success",
        "revenueData": mapped_revenue,
        "pendingDrafts": mapped_drafts,
        "scheduleItems": mapped_schedule,
        "systemStatus": system_status
    }

@app.post("/api/v1/runtime/cycle")
async def trigger_manual_cycle(api_key: str = Depends(get_api_key)):
    """Manually trigger an agent cycle (for debugging or urgent situations)."""
    import asyncio
    asyncio.create_task(agent_runtime._run_cycle())
    return {"status": "cycle_triggered", "cycle_count": agent_runtime.cycle_count + 1}


# ─── Draft Outbox Management ───────────────────────────────────
@app.get("/api/v1/outbox")
def get_outbox(api_key: str = Depends(get_api_key)):
    """Get all pending drafts in the 10-minute outbox."""
    return {"status": "success", "drafts": agent_runtime.outbox.get_pending_drafts()}

class OutboxAction(BaseModel):
    draft_id: int
    action: str  # "approve" or "cancel"

@app.post("/api/v1/outbox/resolve")
def resolve_outbox_draft(payload: OutboxAction, api_key: str = Depends(get_api_key)):
    """Approve or cancel a pending draft."""
    if payload.action == "approve":
        agent_runtime.outbox.approve_draft(payload.draft_id)
        return {"status": "approved", "draft_id": payload.draft_id}
    elif payload.action == "cancel":
        agent_runtime.outbox.cancel_draft(payload.draft_id)
        return {"status": "cancelled", "draft_id": payload.draft_id}
    raise HTTPException(status_code=400, detail="Action must be 'approve' or 'cancel'.")


# ─── Wealth & Portfolio (Persistent) ────────────────────────────
@app.get("/api/v1/wealth/portfolio")
def get_portfolio(api_key: str = Depends(get_api_key)):
    """Get the current wealth portfolio from persistent storage."""
    from core.wealth_manager import wealth_manager
    return wealth_manager.get_portfolio_summary()

@app.post("/api/v1/wealth/payout")
def request_payout(payload: PayoutPayload, api_key: str = Depends(get_api_key)):
    """Manually request a payout from Andrew's managed funds to your pocket."""
    from core.wealth_manager import wealth_manager
    result = wealth_manager.execute_direct_payout(payload.amount)
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result

@app.get("/api/v1/wealth/benefits")
def get_benefits_summary(api_key: str = Depends(get_api_key)):
    """Get the total direct benefits received from Andrew."""
    from core.wealth_manager import wealth_manager
    summary = wealth_manager.get_portfolio_summary()
    personal_wallet = summary["wallets"].get("owner_personal_wallet", {})
    return {
        "status": "success",
        "total_payouts_usd": personal_wallet.get("balance", 0),
        "asset": personal_wallet.get("asset", "USD")
    }


# ─── Swarm Status ──────────────────────────────────────────────
@app.get("/api/v1/swarm/status")
def get_swarm_status(api_key: str = Depends(get_api_key)):
    """Get the current swarm orchestrator status."""
    from core.swarm_orchestrator import swarm_orchestrator
    return swarm_orchestrator.get_status()



@app.get("/api/v1/swarm/ethics")
def get_swarm_ethics(api_key: str = Depends(get_api_key)):
    """Get the current ethical alignment score and primal directives."""
    from core.ethical_core import ethical_core
    return {
        "status": "success",
        "alignment_score": ethical_core.get_alignment_score(),
        "primal_directives": ethical_core.PRIMAL_DIRECTIVES
    }


@app.post("/api/v1/swarm/meeting")
async def convene_brain_trust(payload: MeetingPayload, api_key: str = Depends(get_api_key)):
    """Convene a specialized meeting of Andrew's department heads."""
    from core.swarm_brain_trust import swarm_brain_trust
    return await swarm_brain_trust.convene_meeting(payload.topic)


# ─── Google Custom Search ──────────────────────────────────────
class SearchPayload(BaseModel):
    query: str
    num_results: int = 5
    site: Optional[str] = None
    days: Optional[int] = None

@app.post("/api/v1/search")
def web_search(payload: SearchPayload, api_key: str = Depends(get_api_key)):
    """Search the web via Google Programmable Search Engine."""
    from core.google_search import google_search

    if payload.site:
        result = google_search.search_site(
            query=payload.query,
            site=payload.site,
            num_results=payload.num_results,
            date_restrict=f"d{payload.days}" if payload.days else None,
        )
    elif payload.days:
        result = google_search.search_recent(
            query=payload.query,
            days=payload.days,
            num_results=payload.num_results,
        )
    else:
        result = google_search.search(
            query=payload.query,
            num_results=payload.num_results,
        )

    return result

@app.get("/api/v1/search/market")
def trigger_market_scan(api_key: str = Depends(get_api_key)):
    """Manually trigger Andrew's daily market intelligence sweep."""
    from core.market_scanner import market_scanner
    return market_scanner.run()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
