import asyncio
import logging
from typing import Callable, Dict, List, Any

logger = logging.getLogger("EventBus")

class EventBus:
    """
    The Nervous System of Andrew.
    Allows isolated organs (modules) to communicate autonomously.
    """
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}
        self.queue = asyncio.Queue()
        self._running = False

    def subscribe(self, event_type: str, callback: Callable):
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)
        logger.info(f"Subscribed to event: {event_type}")

    async def publish(self, event_type: str, data: Any = None):
        """Puts an event onto the bus."""
        event = {"type": event_type, "data": data}
        await self.queue.put(event)
        logger.debug(f"Event published: {event_type}")

    async def _process_events(self):
        """Background loop to route events to subscribers."""
        self._running = True
        logger.info("Event Bus (Nervous System) is online and processing events.")
        while self._running:
            event = await self.queue.get()
            event_type = event["type"]
            data = event["data"]
            
            if event_type in self.subscribers:
                for callback in self.subscribers[event_type]:
                    try:
                        # Allow both async and sync callbacks
                        if asyncio.iscoroutinefunction(callback):
                            await callback(data)
                        else:
                            callback(data)
                    except Exception as e:
                        logger.error(f"Error in subscriber for {event_type}: {e}")
            
            self.queue.task_done()

    def start(self):
        """Starts the event bus loop in the background."""
        asyncio.create_task(self._process_events())

    def stop(self):
        self._running = False

# Global Singleton Event Bus
event_bus = EventBus()
