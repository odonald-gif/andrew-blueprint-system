from core.black_book import BlackBook
from core.agent_runtime import DraftOutbox

memory = BlackBook()
outbox = DraftOutbox(memory)

draft_id = outbox.queue_draft(
    action_type="phantom_network_outreach",
    target="Elite Auto Repair",
    content="Hey there, I noticed your website is taking 8 seconds to load on mobile. I built a much faster React prototype for you here: https://auto-repair-fast.vercel.app. Let me know if you want to jump on a quick 5-min call to discuss deploying it.",
    circle="default"
)
print(f"Injected test draft ID: {draft_id}")
