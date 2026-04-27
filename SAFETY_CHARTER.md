# Project Andrew: Safety Charter

## Executive Summary
Andrew operates on a **Zero-Trust, Human-in-the-Loop (HITL)** framework. He is designed to be a high-leverage proxy for professional and personal tasks while strictly adhering to a **Principle of Least Privilege**. Andrew cannot override human authority, and all high-stakes actions are sandboxed.

## 1. The Human-in-the-Loop (HITL) Thresholds
Andrew categorizes all autonomous actions into three risk tiers:
- **Green Zone (Auto-Pilot):** Low-risk tasks (family replies, calendar blocking, video summarization). These execute autonomously.
- **Yellow Zone (Draft & Notify):** Professional communications (LinkedIn posts, scheduling new clients, GitHub commit messages). Andrew drafts these and holds them in a **10-minute Outbox**. A push notification is sent to the user. If not explicitly cancelled or approved, they either proceed or pause based on specific circle rules.
- **Red Zone (Hard Lock):** Destructive actions (deleting code, spending money, resigning). Andrew is physically blocked at the API level from executing these.

## 2. Semantic Firewalls & Credential Masking
- **Action Isolation:** Andrew only has "Write" access to isolated, specific folders (e.g., `feature-branches` in GitHub). He cannot read or modify `.env` files or master system configurations.
- **Token-Based Access:** Andrew does not possess master passwords. He utilizes encrypted, expiring Session Tokens for platforms like LinkedIn. If anomalous behavior is detected, the token is revoked instantly without compromising the master account.

## 3. The Monitor Agent (Anti-Hallucination)
Before any outbound communication leaves the system, it passes through an isolated **Monitor Agent**:
1. The Core Persona Engine drafts the message.
2. The Monitor Agent reviews the draft against the User Style Guide and Safety Rules (e.g., "Is this offensive?", "Does this leak confidential IP?").
3. If the Monitor Agent flags the draft, it is immediately quarantined, and the user is alerted to take manual control.

## 4. Digital Twin Drift Protection
- **Monthly Audit:** Every 30 days, Andrew generates a "Personality Audit" compiling 10 random interactions for human review to ensure linguistic alignment.
- **The Kill-Switch:** A hardware-level or immediate software interrupt that severs Andrew's connection to all external APIs (n8n, LinkedIn, GitHub) instantly.

## 5. Career Insurance
- **GitHub:** Andrew may push code to `feature-` branches to contribute to the open-source ecosystem, but he is programmatically blocked from merging to `main`.
- **LinkedIn:** Automation utilizes human-timing algorithms (e.g., Browserless/Playwright) to prevent API bans. Posting is restricted to standard waking hours, capped at twice daily.
