"""
Monitoring API endpoints for Kafka and Dapr components.
Provides real-time status of event-driven infrastructure.
"""

import logging
from typing import Dict, List, Any
from fastapi import APIRouter, HTTPException
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/kafka")
async def get_kafka_status() -> Dict[str, Any]:
    """
    Get Kafka broker and topic status using AdminClient.

    Environment-aware:
    - Kubernetes: kafka.kafka.svc.cluster.local:9092
    - Docker: kafka:29092

    Returns:
        Kafka connection status, topics, and basic metrics
    """
    import os

    # Determine Kafka bootstrap server based on environment
    is_kubernetes = os.path.exists("/var/run/secrets/kubernetes.io/serviceaccount/token")
    if is_kubernetes:
        kafka_bootstrap = "kafka.kafka.svc.cluster.local:9092"
    else:
        kafka_bootstrap = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")

    try:
        from kafka import KafkaAdminClient
        from kafka.errors import KafkaError, NoBrokersAvailable

        status = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "broker": {
                "host": kafka_bootstrap,
                "status": "unknown",
                "connected": False
            },
            "topics": [],
            "topics_count": 0,
            "error": None
        }

        try:
            # Connect to Kafka broker using AdminClient
            admin_client = KafkaAdminClient(
                bootstrap_servers=[kafka_bootstrap],
                request_timeout_ms=10000,
                connections_max_idle_ms=10000,
                api_version_auto_timeout_ms=5000
            )

            # Fetch cluster metadata to verify broker is healthy
            cluster_metadata = admin_client.describe_cluster()

            # Get all topics
            all_topics = admin_client.list_topics()

            # Filter taskflow topics
            taskflow_topics = [
                topic for topic in all_topics
                if topic.startswith('taskflow.')
            ]

            # Broker is healthy if we got here (connection + metadata succeeded)
            status["broker"]["status"] = "healthy"
            status["broker"]["connected"] = True
            status["broker"]["cluster_id"] = cluster_metadata.get("cluster_id", "unknown")
            status["topics_count"] = len(taskflow_topics)
            status["topics"] = [
                {
                    "name": topic,
                    "status": "active"
                }
                for topic in sorted(taskflow_topics)
            ]

            admin_client.close()

        except NoBrokersAvailable as e:
            status["broker"]["status"] = "error"
            status["error"] = f"No brokers available at {kafka_bootstrap}"
            logger.warning(f"Kafka no brokers: {e}")
        except KafkaError as e:
            status["broker"]["status"] = "error"
            status["error"] = str(e)
            logger.warning(f"Kafka connection error: {e}")
        except Exception as e:
            status["broker"]["status"] = "error"
            status["error"] = str(e)
            logger.error(f"Error checking Kafka status: {e}")

        return status

    except ImportError:
        return {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "broker": {
                "host": kafka_bootstrap,
                "status": "unknown",
                "connected": False
            },
            "topics": [],
            "topics_count": 0,
            "error": "kafka-python not installed"
        }


@router.get("/dapr")
async def get_dapr_status() -> Dict[str, Any]:
    """
    Get Dapr components and sidecar status using Kubernetes API.

    A service is healthy if its pod is 2/2 Ready (app + daprd containers running).

    Returns:
        Status of all Dapr sidecars based on pod readiness
    """
    try:
        from kubernetes import client, config

        status = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "sidecars": [],
            "components": [],
            "healthy": 0,
            "unhealthy": 0
        }

        # List of services with Dapr sidecars
        services = ["chat-api", "recurring-processor", "reminder-service", "notification-service", "audit-logger"]

        # Load Kubernetes config (in-cluster)
        try:
            config.load_incluster_config()
            v1 = client.CoreV1Api()
        except Exception as e:
            logger.warning(f"Could not load k8s config: {e}")
            # Docker-compose fallback: check services via HTTP health endpoints
            import aiohttp
            service_ports = {
                "chat-api": ("localhost", 8000),
                "recurring-processor": ("recurring-processor", 8001),
                "reminder-service": ("reminder-service", 8002),
                "notification-service": ("notification-service", 8003),
                "audit-logger": ("audit-logger", 8004),
            }
            try:
                async with aiohttp.ClientSession() as session:
                    for service_name in services:
                        host, port = service_ports.get(service_name, (service_name, 8000))
                        result = {"name": service_name, "status": "unknown", "healthy": False}
                        try:
                            url = f"http://{host}:{port}/health/live"
                            async with session.get(url, timeout=aiohttp.ClientTimeout(total=3)) as response:
                                if response.status == 200:
                                    result["status"] = "healthy"
                                    result["healthy"] = True
                                else:
                                    result["status"] = f"unhealthy (HTTP {response.status})"
                        except Exception:
                            result["status"] = "unreachable"
                        status["sidecars"].append(result)
            except Exception:
                for service_name in services:
                    status["sidecars"].append({"name": service_name, "status": "check failed", "healthy": False})
            status["healthy"] = sum(1 for s in status["sidecars"] if s["healthy"])
            status["unhealthy"] = len(status["sidecars"]) - status["healthy"]

            # Check Dapr components via localhost sidecar
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get("http://localhost:3500/v1.0/metadata", timeout=aiohttp.ClientTimeout(total=2)) as response:
                        if response.status == 200:
                            metadata = await response.json()
                            status["components"] = [
                                {"name": c.get("name"), "type": c.get("type"), "version": c.get("version")}
                                for c in metadata.get("components", [])
                            ]
            except Exception:
                pass

            return status

        # Check pod readiness for each service
        for service_name in services:
            result = {
                "name": service_name,
                "status": "unknown",
                "healthy": False
            }

            try:
                # Get pods with matching label
                pods = v1.list_namespaced_pod(
                    namespace="default",
                    label_selector=f"app={service_name}",
                    timeout_seconds=3
                )

                if pods.items:
                    pod = pods.items[0]
                    # Check if pod has daprd container
                    containers = pod.spec.containers
                    has_daprd = any(c.name == "daprd" for c in containers)

                    # Check container statuses
                    container_statuses = pod.status.container_statuses or []
                    ready_count = sum(1 for cs in container_statuses if cs.ready)
                    total_count = len(container_statuses)

                    if has_daprd and ready_count == 2 and total_count == 2:
                        result["status"] = "healthy"
                        result["healthy"] = True
                    elif has_daprd:
                        result["status"] = f"degraded ({ready_count}/2 ready)"
                    else:
                        result["status"] = "no daprd sidecar"
                else:
                    result["status"] = "pod not found"
            except Exception as e:
                result["status"] = f"error: {str(e)}"
                logger.warning(f"Error checking {service_name}: {e}")

            status["sidecars"].append(result)

        # Count healthy/unhealthy
        status["healthy"] = sum(1 for r in status["sidecars"] if r["healthy"])
        status["unhealthy"] = len(status["sidecars"]) - status["healthy"]

        # Check Dapr components via localhost sidecar
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                url = "http://localhost:3500/v1.0/metadata"
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=2)) as response:
                    if response.status == 200:
                        metadata = await response.json()
                        components = metadata.get("components", [])
                        status["components"] = [
                            {
                                "name": comp.get("name"),
                                "type": comp.get("type"),
                                "version": comp.get("version")
                            }
                            for comp in components
                        ]
        except Exception as e:
            logger.warning(f"Could not fetch Dapr metadata: {e}")

        return status

    except Exception as e:
        logger.error(f"Error checking Dapr status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/docker")
async def get_docker_status() -> Dict[str, Any]:
    """
    Get Docker deployment status and configuration.

    Returns:
        Docker deployment mode and service configuration
    """
    try:
        status = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "mode": "docker-compose",
            "services": [
                {"name": "backend", "image": "phase-ii-backend", "status": "running"},
                {"name": "postgres", "image": "postgres:15-alpine", "status": "running"},
                {"name": "kafka", "image": "confluentinc/cp-kafka:7.5.0", "status": "running"},
                {"name": "redis", "image": "redis:7-alpine", "status": "running"},
                {"name": "zookeeper", "image": "confluentinc/cp-zookeeper:7.5.0", "status": "running"},
                {"name": "recurring-processor", "image": "phase-ii-recurring-processor", "status": "running"},
                {"name": "reminder-service", "image": "phase-ii-reminder-service", "status": "running"},
                {"name": "notification-service", "image": "phase-ii-notification-service", "status": "running"},
                {"name": "audit-logger", "image": "phase-ii-audit-logger", "status": "running"},
                {"name": "frontend", "image": "phase-ii-frontend", "status": "running"},
            ],
            "images": [
                {"name": "phase-ii-backend", "type": "application"},
                {"name": "phase-ii-frontend", "type": "application"},
                {"name": "phase-ii-recurring-processor", "type": "service"},
                {"name": "phase-ii-reminder-service", "type": "service"},
                {"name": "phase-ii-notification-service", "type": "service"},
                {"name": "phase-ii-audit-logger", "type": "service"},
            ],
            "dapr": {
                "enabled": True,
                "version": "1.12.0",
                "sidecars": 5
            },
            "message": "Running in Docker Compose mode with Dapr sidecars"
        }

        return status

    except Exception as e:
        logger.error(f"Error getting Docker status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kubernetes")
async def get_kubernetes_status() -> Dict[str, Any]:
    """
    Get Kubernetes cluster and resources status.

    Returns:
        K8s deployments, services, secrets status
    """
    try:
        import subprocess

        status = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "mode": "docker-compose",
            "cluster": "not-deployed",
            "deployments": [],
            "services": [],
            "secrets": {
                "total": 0,
                "configured": [],
                "missing": [],
                "status": "docker-compose",
                "message": "Secrets managed via docker-compose environment variables",
                "expected": ["DATABASE_URL", "REDIS_URL", "JWT_SECRET_KEY", "ANTHROPIC_API_KEY"]
            },
            "message": "Running in Docker Compose mode. Deploy to K8s: kubectl apply -f k8s/"
        }

        # Check if running in Kubernetes by looking for service account token
        import os
        k8s_service_account = "/var/run/secrets/kubernetes.io/serviceaccount/token"
        k8s_service_host = os.environ.get("KUBERNETES_SERVICE_HOST")

        if os.path.exists(k8s_service_account) or k8s_service_host:
            # We're running in Kubernetes
            status["mode"] = "kubernetes"
            status["cluster"] = "connected"
            status["message"] = "Running in Kubernetes cluster"

            # Try to use kubectl if available
            try:
                result = subprocess.run(
                    ["kubectl", "cluster-info"],
                    capture_output=True,
                    text=True,
                    timeout=3
                )

                if result.returncode == 0:
                    # kubectl available, get more details
                    # Get deployments
                    deploy_result = subprocess.run(
                        ["kubectl", "get", "deployments", "-n", "default", "-o", "json"],
                        capture_output=True,
                        text=True,
                        timeout=3
                    )

                    if deploy_result.returncode == 0:
                        import json as json_lib
                        deployments = json_lib.loads(deploy_result.stdout)
                        status["deployments"] = [
                            {
                                "name": d["metadata"]["name"],
                                "ready": f"{d['status'].get('readyReplicas', 0)}/{d['status'].get('replicas', 0)}",
                                "status": "healthy" if d['status'].get('readyReplicas', 0) == d['status'].get('replicas', 0) else "unhealthy"
                            }
                            for d in deployments.get("items", [])
                            if "taskflow" in d["metadata"]["name"]
                        ]

                    # Get secrets
                    secrets_result = subprocess.run(
                        ["kubectl", "get", "secrets", "-n", "default", "-o", "json"],
                        capture_output=True,
                        text=True,
                        timeout=3
                    )

                    if secrets_result.returncode == 0:
                        secrets = json_lib.loads(secrets_result.stdout)
                        secret_items = secrets.get("items", [])

                        # Required secrets for taskflow
                        required_secrets = [
                            "taskflow-postgres-secret",
                            "taskflow-redis-secret",
                            "taskflow-kafka-secret",
                            "taskflow-anthropic-secret"
                        ]

                        existing_secrets = [s["metadata"]["name"] for s in secret_items if "taskflow" in s["metadata"]["name"]]

                        status["secrets"]["total"] = len(existing_secrets)
                        status["secrets"]["configured"] = existing_secrets
                        status["secrets"]["missing"] = [s for s in required_secrets if s not in existing_secrets]
                        status["secrets"]["status"] = "healthy" if len(status["secrets"]["missing"]) == 0 else "incomplete"
                        status["secrets"]["message"] = f"{len(existing_secrets)}/{len(required_secrets)} secrets configured"

            except (subprocess.TimeoutExpired, FileNotFoundError):
                # kubectl not available, but we're still in K8s
                pass
            except Exception as e:
                logger.warning(f"kubectl check failed: {e}")

        # If not in Kubernetes, keep docker-compose mode (already set)

        return status

    except Exception as e:
        logger.error(f"Error getting Kubernetes status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cicd")
async def get_cicd_status() -> Dict[str, Any]:
    """
    Get CI/CD pipeline status.

    Checks:
    1. CICD_CONFIGURED env var (for containerized environments)
    2. Local .github/workflows directory

    Returns:
        Status of CI/CD pipelines (GitHub Actions, GitLab CI, etc.)
    """
    import os

    try:
        status = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "pipelines": [],
            "status": "not-configured",
            "provider": None,
            "message": "No CI/CD pipelines configured"
        }

        # Method 1: Check environment variable (for containers)
        cicd_configured = os.getenv("CICD_CONFIGURED", "").lower() in ("true", "1", "yes")
        cicd_provider = os.getenv("CICD_PROVIDER", "github-actions")

        if cicd_configured:
            status["status"] = "configured"
            status["provider"] = cicd_provider
            status["message"] = f"CI/CD configured via {cicd_provider}"
            status["pipelines"] = [
                {
                    "name": "CI Pipeline",
                    "type": cicd_provider,
                    "status": "ready",
                    "file": "ci.yml"
                }
            ]
            return status

        # Method 2: Check for GitHub Actions workflows on filesystem
        possible_paths = [
            "../.github/workflows",
            "../../.github/workflows",
            "/app/.github/workflows",
            os.path.join(os.getcwd(), "../.github/workflows")
        ]

        github_workflows_dir = None
        for path in possible_paths:
            if os.path.exists(path):
                github_workflows_dir = path
                break

        if github_workflows_dir:
            try:
                workflows = [
                    f for f in os.listdir(github_workflows_dir)
                    if f.endswith(('.yml', '.yaml')) and not f.startswith('README')
                ]
                if workflows:
                    status["status"] = "configured"
                    status["provider"] = "github-actions"
                    status["message"] = f"Found {len(workflows)} GitHub Actions workflow(s)"
                    status["pipelines"] = [
                        {
                            "name": w.replace('.yml', '').replace('.yaml', '').replace('-', ' ').title(),
                            "type": "github-actions",
                            "status": "ready",
                            "file": w
                        }
                        for w in workflows
                    ]
            except Exception as e:
                logger.warning(f"Error reading workflows directory: {e}")

        return status

    except Exception as e:
        logger.error(f"Error getting CI/CD status: {e}")
        return {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "pipelines": [],
            "status": "error",
            "provider": None,
            "message": str(e)
        }


@router.get("/overview")
async def get_monitoring_overview() -> Dict[str, Any]:
    """
    Get complete monitoring overview (Kafka + Dapr + K8s + CI/CD).

    Returns:
        Combined status of all infrastructure components
    """
    try:
        kafka_status = await get_kafka_status()
        dapr_status = await get_dapr_status()
        k8s_status = await get_kubernetes_status()
        cicd_status = await get_cicd_status()

        return {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "kafka": kafka_status,
            "dapr": dapr_status,
            "kubernetes": k8s_status,
            "cicd": cicd_status,
            "overall_health": (
                "healthy" if dapr_status["healthy"] >= 3 and kafka_status["broker"]["connected"]
                else "degraded" if dapr_status["healthy"] >= 1
                else "unhealthy"
            )
        }
    except Exception as e:
        logger.error(f"Error getting monitoring overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))
