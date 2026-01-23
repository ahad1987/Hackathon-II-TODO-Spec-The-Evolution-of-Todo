"""
Notification Service for Phase V.

Constitutional Compliance:
- Subscribes to all task events via Dapr Pub/Sub
- Manages SSE connections for real-time notifications
- Rate limiting and connection limits enforced
- Heartbeat mechanism and stale connection cleanup
"""

__version__ = "1.0.0"
