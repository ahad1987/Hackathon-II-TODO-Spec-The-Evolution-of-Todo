"""
Recurring Task Processor Service for Phase V.

Constitutional Compliance:
- Consumes task.created and task.updated events via Dapr
- Generates recurring task instances automatically
- Uses Chat API for task instance creation (service invocation)
"""

__version__ = "1.0.0"
