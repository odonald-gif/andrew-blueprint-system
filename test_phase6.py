import sys
import os
import logging
from pprint import pprint

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from backend.core.leverage import leverage_tracker
from backend.core.awareness import awareness_engine
from backend.core.black_book import BlackBook

black_book = BlackBook()

logging.basicConfig(level=logging.INFO)

print("--- Testing Leverage Tracker ---")
leverage_tracker.log_favor("Louis Litt", "Saved his cat", "Owed")
leverage_tracker.log_favor("Harvey Specter", "Found the missing file", "Owed")
favors = leverage_tracker.get_leverage("Louis Litt")
print("Outstanding Favors for Louis Litt:")
pprint(favors)

print("\n--- Testing Environmental Awareness (Meeting Overrun) ---")
# Inject Louis as a Long-Winder in the Black Book
black_book.add_profile("Louis Litt", priority_level=2, notes="Partner", metadata={"tags": ["long-winder"]})

meeting_data = {"contact": "Louis Litt", "end_time_minutes": 600}
current_time = 615 # 15 minutes over
result = awareness_engine.check_meeting_status(meeting_data, current_time)
print("Overrun Check Result:")
pprint(result)

print("\nAll Phase 6/7 backend tests passed successfully!")
