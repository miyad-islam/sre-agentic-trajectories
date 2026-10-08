"""
DevOps / SRE Incident Scenario Generator.
Generates balanced, entropy-rich incident seeds across Kubernetes, Linux OS, Cloud Metrics, and Database failure domains.
Includes difficulty stratification (Easy, Medium, Hard) as advised by GStack CEO review.
"""

import random
from typing import Dict, Any, List


INCIDENT_CATEGORIES = ["kubernetes", "linux_system", "cloud_metrics", "database"]
DIFFICULTY_LEVELS = ["easy", "medium", "hard"]

# Seed components for combinatorial generation
SERVICES = [
    "checkout-service", "auth-gateway", "payment-processor", 
    "order-fulfillment", "inventory-api", "search-indexer", 
    "user-profile-svc", "notification-worker"
]

NAMESPACES = ["production", "prod-us-east", "prod-eu-west", "staging"]
HOST_NODES = ["node-worker-01", "node-worker-04", "node-ingress-02", "db-primary-01"]
DATABASES = ["orders_prod_db", "users_auth_db", "payments_ledger_db", "inventory_db"]


# Detailed scenario templates with ground-truth root causes and target remediation strategies
SCENARIO_TEMPLATES = {
    "kubernetes": [
        {
            "subcategory": "oom_crash",
            "alert_template": "CRITICAL Alert: Pod {pod_name} in namespace '{namespace}' is restarting with exit code 137 (OOMKilled).",
            "root_cause": "Container memory limit is configured at 256Mi, while peak payload processing demands ~380Mi.",
            "target_tools": ["k8s_get_pods", "k8s_describe_pod", "k8s_get_logs", "k8s_patch_deployment"],
            "difficulty": "medium"
        },
        {
            "subcategory": "crashloop_config",
            "alert_template": "Warning: Deployment '{service}' in namespace '{namespace}' has 0/3 replicas ready. Pods are in CrashLoopBackOff.",
            "root_cause": "Application panics on startup because mandatory environment variable 'DATABASE_URL' is missing.",
            "target_tools": ["k8s_get_pods", "k8s_get_logs", "k8s_patch_deployment", "k8s_rollout_restart"],
            "difficulty": "medium"
        },
        {
            "subcategory": "readiness_probe_fail",
            "alert_template": "PagerDuty Incident: Readiness probe failed for service '{service}' in '{namespace}'. Endpoint removed from ingress routing.",
            "root_cause": "Health check timeout threshold (1s) is too aggressive during heavy GC pauses.",
            "target_tools": ["k8s_describe_pod", "k8s_get_logs", "k8s_patch_deployment"],
            "difficulty": "easy"
        }
    ],
    "linux_system": [
        {
            "subcategory": "disk_exhaustion",
            "alert_template": "Alert: Node '{host_id}' filesystem mount '/var/log' is at 98% disk capacity. New container creation failing.",
            "root_cause": "Unrotated application stdout debug logs consuming 140GB in /var/log/containers/.",
            "target_tools": ["linux_check_system_resources", "linux_inspect_process"],
            "difficulty": "easy"
        },
        {
            "subcategory": "cpu_throttling",
            "alert_template": "SRE Alert: Host '{host_id}' reporting load average 48.2 (8 vCPUs). High iowait detected.",
            "root_cause": "Orphaned backup daemon process hogging disk I/O and CPU cycles.",
            "target_tools": ["linux_check_system_resources", "linux_inspect_process"],
            "difficulty": "medium"
        },
        {
            "subcategory": "port_exhaustion",
            "alert_template": "Network Warning: Host '{host_id}' cannot establish outbound TCP connections (EADDRNOTAVAIL).",
            "root_cause": "High volume of outbound HTTP calls without keep-alive leading to 45,000 sockets in TIME_WAIT.",
            "target_tools": ["linux_check_network_connections", "linux_inspect_process"],
            "difficulty": "hard"
        }
    ],
    "cloud_metrics": [
        {
            "subcategory": "p99_latency_spike",
            "alert_template": "Datadog Monitor: '{service}' p99 latency spiked from 180ms to 4850ms in the last 15 minutes.",
            "root_cause": "Downstream payment provider API endpoint timing out under high batch request load.",
            "target_tools": ["metrics_query_latency_percentiles", "metrics_query_error_rates", "k8s_get_logs"],
            "difficulty": "medium"
        },
        {
            "subcategory": "5xx_error_surge",
            "alert_template": "Alert: HTTP 500 error rate for '{service}' exceeded 5% threshold (currently 14.8%).",
            "root_cause": "NullPointerException thrown during deserialization of new order payload schema.",
            "target_tools": ["metrics_query_error_rates", "k8s_get_logs", "k8s_patch_deployment"],
            "difficulty": "easy"
        }
    ],
    "database": [
        {
            "subcategory": "deadlock_contention",
            "alert_template": "PostgreSQL Alert: '{database}' reports multiple transactions rolled back due to 'deadlock detected'.",
            "root_cause": "Concurrent checkout and inventory hold transactions acquiring row locks in reverse order.",
            "target_tools": ["db_query_active_sessions", "db_check_locks_and_deadlocks", "db_terminate_backend"],
            "difficulty": "hard"
        },
        {
            "subcategory": "connection_pool_exhaustion",
            "alert_template": "Alert: Database '{database}' reached 98% of max_connections (490/500 active sessions).",
            "root_cause": "Leaked database connections in worker pods not closing sessions in exception handlers.",
            "target_tools": ["db_query_active_sessions", "db_terminate_backend"],
            "difficulty": "medium"
        }
    ]
}


def generate_scenario_seed(category: str = None, seed_index: int = 0) -> Dict[str, Any]:
    """
    Generate a single, deterministic yet diversified incident seed.
    """
    rng = random.Random(seed_index)
    if not category or category not in INCIDENT_CATEGORIES:
        category = rng.choice(INCIDENT_CATEGORIES)

    template = rng.choice(SCENARIO_TEMPLATES[category])
    service = rng.choice(SERVICES)
    namespace = rng.choice(NAMESPACES)
    host_id = rng.choice(HOST_NODES)
    database = rng.choice(DATABASES)
    pod_hash = f"{rng.randint(1000, 9999)}-{rng.choice(['x9z', 'k8b', 'p2m', 'w4c'])}"
    pod_name = f"{service}-{pod_hash}"

    alert_text = template["alert_template"].format(
        service=service,
        namespace=namespace,
        pod_name=pod_name,
        host_id=host_id,
        database=database
    )

    return {
        "scenario_id": f"sre-{category[:3]}-{template['subcategory']}-{seed_index:05d}",
        "category": category,
        "subcategory": template["subcategory"],
        "difficulty": template["difficulty"],
        "alert": alert_text,
        "service": service,
        "namespace": namespace,
        "pod_name": pod_name,
        "host_id": host_id,
        "database": database,
        "root_cause": template["root_cause"],
        "expected_tools": template["target_tools"]
    }


def generate_scenario_batch(count: int, seed: int = 42) -> List[Dict[str, Any]]:
    """
    Generate a batch of scenarios with balanced category representation.
    """
    scenarios = []
    cat_cycle = INCIDENT_CATEGORIES * (count // len(INCIDENT_CATEGORIES) + 1)

    for i in range(count):
        cat = cat_cycle[i]
        scenarios.append(generate_scenario_seed(category=cat, seed_index=seed + i))

    return scenarios[:count]
