import sys
import os
import logging
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from backend.db.mirror_db import mirror_db
from backend.core.persona import PersonaEngine

logging.basicConfig(level=logging.INFO)

# 1. Add mock history to ChromaDB
print("--- Adding Mock History ---")
mirror_db.save_interaction("Uncle Steve", "brother", "Hey", "yo i'm tied up but ill check it soon. good looks")
mirror_db.save_interaction("Uncle Steve", "brother", "Haha", "lmao that's actually crazy. catch u later")
mirror_db.save_interaction("Client A", "manager", "Update?", "Thank you for the update. I will review the documentation and provide feedback by EOD.")

# 2. Test Twin Reply (Brother Circle)
print("\n--- Testing Brother Twin Reply ---")
persona = PersonaEngine(ai_provider="mock")
reply_brother = persona.generate_twin_reply(
    sender="Uncle Steve", 
    circle="brother", 
    message_content="Bro did u see the new car?", 
    media_url="youtube.com/watch?v=123"
)
print(f"Reply: {reply_brother}")

# 3. Test Twin Reply (Manager Circle)
print("\n--- Testing Manager Twin Reply ---")
reply_manager = persona.generate_twin_reply(
    sender="Client A", 
    circle="manager", 
    message_content="Please review the new specs.", 
    media_url=None
)
print(f"Reply: {reply_manager}")

print("\nAll tests passed successfully!")
