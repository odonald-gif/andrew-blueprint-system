import logging
from typing import Callable, Dict, Any, List
import json

logger = logging.getLogger(__name__)

class ToolRegistry:
    """
    Andrew's Hands. 
    Every module registers what it can do here. The Reasoning Engine 
    dynamically composes these tools to solve problems, rather than
    relying on hardcoded switch statements.
    """
    
    def __init__(self):
        # schema: { name: { "description": str, "function": callable, "risk_zone": str, "args_schema": dict } }
        self.tools: Dict[str, Dict[str, Any]] = {}
    
    def register(self, name: str, description: str, function: Callable, risk_zone: str = "yellow", args_schema: Dict[str, str] = None):
        """
        Registers a tool so the LLM knows it exists.
        args_schema: A dict describing expected kwargs, e.g., {"client_name": "string", "budget": "number"}
        """
        self.tools[name] = {
            "description": description,
            "function": function,
            "risk_zone": risk_zone,
            "args_schema": args_schema or {}
        }
        logger.info(f"Tool Registered: {name} [{risk_zone.upper()}]")
        
    def execute_tool(self, name: str, **kwargs) -> Any:
        """
        Executes a registered tool by name with the provided kwargs.
        """
        if name not in self.tools:
            logger.error(f"Attempted to execute unregistered tool: {name}")
            raise ValueError(f"Tool '{name}' is not registered.")
            
        tool = self.tools[name]
        logger.info(f"Executing Tool: {name} (Risk: {tool['risk_zone']})")
        return tool["function"](**kwargs)
        
    def get_tool_descriptions(self) -> str:
        """
        Returns a prompt-friendly JSON schema of all available tools
        for the Reasoning Engine to inject into the LLM prompt.
        """
        tools_list = []
        for name, data in self.tools.items():
            tools_list.append({
                "name": name,
                "description": data["description"],
                "risk_zone": data["risk_zone"],
                "arguments": data["args_schema"]
            })
        return json.dumps(tools_list, indent=2)

tool_registry = ToolRegistry()

# ==========================================
# Core Tool Registration
# ==========================================

# Example of importing and registering existing modules.
# We do this here to avoid circular dependencies, or modules can import tool_registry and register themselves.

# 1. Scout
try:
    from scrapers.scout import DigitalScout
    scout = DigitalScout()
    tool_registry.register(
        name="search_jobs",
        description="Search Upwork and freelance platforms for specific job gigs matching a keyword query.",
        function=scout.perform_routine_scan,
        risk_zone="green",
        args_schema={}
    )
except ImportError:
    pass

# 2. Calendar Sync
try:
    from integrations.calendar_sync import CalendarSync
    cal = CalendarSync()
    tool_registry.register(
        name="block_calendar",
        description="Block time on Google Calendar for deep work or meetings. start_minutes is minutes from midnight (e.g. 540 = 9:00 AM).",
        function=cal.create_time_block,
        risk_zone="green",
        args_schema={"summary": "string", "start_minutes": "integer", "duration_minutes": "integer"}
    )
except ImportError:
    pass

# 3. Email Nexus
try:
    from core.email_nexus import email_nexus
    if email_nexus is not None:
        tool_registry.register(
            name="send_email",
            description="Dispatch an email to a specific address via SMTP.",
            function=email_nexus.send_email,
            risk_zone="yellow",
            args_schema={"to_address": "string", "subject": "string", "body": "string"}
        )
except ImportError:
    pass

# 4. Coinbase Agent
try:
    from core.coinbase_agent import coinbase_wallet
    tool_registry.register(
        name="request_crypto_faucet",
        description="Request testnet funds for a wallet address.",
        function=coinbase_wallet.request_faucet,
        risk_zone="yellow",
        args_schema={"asset_id": "string"}
    )
except ImportError:
    pass

# 5. Developer Bridge
try:
    from scrapers.developer_bridge import dev_bridge
    tool_registry.register(
        name="execute_code",
        description="Trigger the Antigravity CLI to execute code or build architecture within a sandbox.",
        function=dev_bridge.trigger_antigravity_build,
        risk_zone="yellow",
        args_schema={"task_description": "string"}
    )
    tool_registry.register(
        name="push_code",
        description="Push sandbox code to a GitHub feature branch.",
        function=dev_bridge.push_to_github,
        risk_zone="yellow",
        args_schema={"feature_branch": "string", "commit_message": "string"}
    )
    tool_registry.register(
        name="consult_architect",
        description="Ask a technical architecture question and get an expert answer.",
        function=dev_bridge.consult,
        risk_zone="green",
        args_schema={"question": "string"}
    )
    tool_registry.register(
        name="review_code",
        description="Send code for quality review. Returns score, issues, and suggestions.",
        function=dev_bridge.review_code,
        risk_zone="green",
        args_schema={"code": "string", "context": "string"}
    )
except ImportError:
    pass

# 6. Iterative Code Builder
try:
    from core.code_reviewer import code_reviewer
    tool_registry.register(
        name="build_module",
        description="Build a Python module iteratively: generate, test, fix errors, repeat up to 5 times until it passes.",
        function=code_reviewer.iterative_build,
        risk_zone="green",
        args_schema={"task_description": "string", "filename": "string"}
    )
except ImportError:
    pass

# 7. Self-Evolution Meta Coder
try:
    from core.meta_coder import meta_coder
    tool_registry.register(
        name="execute_self_upgrade",
        description="Trigger the MetaCoder to read the roadmap, iteratively build code for the next pending milestone, and merge the self-upgrade.",
        function=meta_coder.process_next_upgrade,
        risk_zone="green",
        args_schema={}
    )
except ImportError:
    pass

# 8. Google Custom Search (Programmable Search Engine)
try:
    from core.google_search import google_search
    tool_registry.register(
        name="web_search",
        description="Search the open web via Google Programmable Search Engine. Returns real-time results with titles, links, and snippets.",
        function=google_search.search,
        risk_zone="green",
        args_schema={"query": "string", "num_results": "integer"}
    )
    tool_registry.register(
        name="web_search_site",
        description="Search within a specific website (e.g. reddit.com, upwork.com). Returns targeted results from that domain.",
        function=google_search.search_site,
        risk_zone="green",
        args_schema={"query": "string", "site": "string", "num_results": "integer"}
    )
except ImportError:
    pass
