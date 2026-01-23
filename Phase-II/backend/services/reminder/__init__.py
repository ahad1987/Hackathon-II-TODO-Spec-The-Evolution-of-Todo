"""
Reminder Service for Phase V.

Constitutional Compliance:
- Subscribes to task events via Dapr Pub/Sub
- Maintains priority queue of scheduled reminders
- Triggers reminders and publishes reminder.triggered events
- Persists reminder state to database for crash recovery
"""

__version__ = "1.0.0"
