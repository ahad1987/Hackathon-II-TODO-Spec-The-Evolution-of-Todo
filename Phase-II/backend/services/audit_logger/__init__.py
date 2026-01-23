"""
Audit Logger Service Package for Phase V (T058-T066)

A standalone FastAPI service that subscribes to task events via Dapr Pub/Sub
and stores them in an immutable audit log (task_events table).

Features:
- Batch write optimization (buffer 100 events, flush every 1 second)
- Duplicate detection via event_id
- Monthly partitioning support
- Chronological query endpoint
- Health endpoints for Kubernetes probes

Constitutional Compliance:
- NO direct Kafka client usage (Dapr Pub/Sub only)
- Immutable audit trail (ON CONFLICT DO NOTHING)
- Efficient batch writes with background flush task
"""

__version__ = "1.0.0"
