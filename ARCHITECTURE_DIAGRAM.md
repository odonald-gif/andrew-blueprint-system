# Project Andrew: System Architecture

The following diagram illustrates the data flow, security boundaries, and tool integrations that make up Andrew's Zero-Trust Autonomous ecosystem.

```mermaid
graph TD
    %% Core Users & Interfaces
    User["User (Mobile App / Watch)"]
    Manager["Manager / Clients"]
    OpenSource["GitHub Ecosystem"]
    LinkedInNet["LinkedIn Network"]

    %% Infrastructure Boundaries
    subgraph Oracle Server [Oracle Always Free (ARM Backend)]
        API["FastAPI (Motion Core)"]
        N8N["n8n (Nervous System)"]
        Chroma[("ChromaDB (Style DNA)")]
        Monitor["Monitor Agent (Safety Guardrail)"]
        Persona["Persona Engine (Ollama/Gemini)"]
    end

    subgraph The Sandbox [Local Secure Environment]
        Antigravity["Antigravity CLI (Builder)"]
        Browserless["Playwright / Browserless"]
    end

    %% Communication Flow
    User <-->|WebSocket / HTTP| API
    Manager <-->|WhatsApp / Email| N8N
    N8N <--> API
    
    %% Brain Flow
    API --> Persona
    Persona <--> Chroma
    Persona --> Monitor
    Monitor -- "Fails Safety Check" --> User
    Monitor -- "Passes" --> API

    %% Automation & Actions
    API -->|Commands| Antigravity
    Antigravity -->|Code Commits (Feature Branches)| OpenSource
    API -->|Session Token Commands| Browserless
    Browserless -->|Human-Timed Posts| LinkedInNet
    
    %% Styling
    classDef secure fill:#e8f4f8,stroke:#2b6cb0,stroke-width:2px;
    classDef highRisk fill:#fed7d7,stroke:#c53030,stroke-width:2px;
    classDef memory fill:#fefcbf,stroke:#b7791f,stroke-width:2px;
    
    class Oracle Server secure;
    class Chroma memory;
    class Antigravity highRisk;
    class Browserless highRisk;
```

## Architecture Breakdown

### 1. The Nervous System (n8n)
Acts as the central router. It catches incoming triggers from WhatsApp, Telegram, or GitHub webhooks, and forwards them to the FastAPI brain. It never holds logic, only routing.

### 2. The Brain & Guardrails (FastAPI + Persona + Monitor)
The Python backend processes the context. It fetches your "DNA" from ChromaDB. The Persona Engine drafts a response or action. Before it executes, the **Monitor Agent** acts as a semantic firewall to ensure the draft complies with the Safety Charter.

### 3. The Hands (Browserless & Antigravity)
- **Browserless/Playwright:** Andrew uses this to navigate LinkedIn organically, using session cookies rather than API keys, ensuring actions look human to avoid bans.
- **Antigravity CLI:** When Andrew detects an open-source issue, he commands the local Antigravity CLI to execute code fixes inside an isolated sandbox, pushing to `feature/` branches for human review.
