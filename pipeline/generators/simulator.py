"""
Multi-Turn Conversational Trajectory Simulator.
Generates multi-turn SRE dialogues in standard OpenAI/ShareGPT function-calling schema.
Features:
- Step-by-step diagnostic reasoning.
- Tool call generation (`tool_calls` array).
- Realistic environment responses.
- 25% Error-Injection & Self-Healing turns.
- RFC-5737 sanitized documentation IPs.
"""

import json
import random
import uuid
from typing import Dict, Any, List
from pipeline.schemas.tools import DEVOPS_TOOLS
from pipeline.generators.scenarios import generate_scenario_seed


SYSTEM_PROMPT = (
    "You are an autonomous Senior Site Reliability Engineer (SRE) agent responsible for "
    "incident triage, root-cause diagnosis, and automated remediation. You have access to "
    "specialized diagnostic tools covering Kubernetes clusters, Linux host diagnostics, "
    "cloud metrics, and PostgreSQL databases. Analyze incoming alerts systematically, inspect "
    "telemetry before taking disruptive actions, handle tool errors gracefully, and provide a clear "
    "post-incident summary once stability is restored."
)


def _gen_tool_id() -> str:
    return f"call_{uuid.uuid4().hex[:10]}"


def simulate_environment_response(tool_name: str, args: Dict[str, Any], inject_error: bool = False) -> str:
    """
    Simulate realistic tool output.
    If inject_error is True, return realistic API/infrastructure error response.
    """
    if inject_error:
        error_types = [
            {"error": "ResourceNotFound", "code": 404, "message": f"Resource not found in target namespace or cluster for {tool_name}."},
            {"error": "RateLimitExceeded", "code": 429, "message": "APM telemetry rate limit exceeded. Retry after 2 seconds."},
            {"error": "InvalidFieldSelector", "code": 400, "message": "Field selector syntax invalid or unsupported on Kubernetes 1.30 API."},
            {"error": "ConnectionTimeout", "code": 504, "message": "Host did not respond within 3000ms socket timeout."}
        ]
        return json.dumps(random.choice(error_types))

    # Realistic mock successes by tool
    if tool_name == "k8s_get_pods":
        ns = args.get("namespace", "production")
        return json.dumps({
            "namespace": ns,
            "items": [
                {"name": "checkout-service-7c4d-x92", "status": "CrashLoopBackOff", "restarts": 14, "ip": "10.244.2.14"},
                {"name": "checkout-service-7c4d-p11", "status": "Running", "restarts": 0, "ip": "10.244.3.82"}
            ]
        })

    elif tool_name == "k8s_describe_pod":
        return json.dumps({
            "pod": args.get("pod_name", "pod-unknown"),
            "namespace": args.get("namespace", "production"),
            "last_state": {"terminated": {"exit_code": 137, "reason": "OOMKilled"}},
            "limits": {"cpu": "500m", "memory": "256Mi"},
            "requests": {"cpu": "200m", "memory": "128Mi"},
            "events": [
                {"type": "Warning", "reason": "OOMKilling", "message": "Memory cgroup out of memory: Killed process 418 (node)."}
            ]
        })

    elif tool_name == "k8s_get_logs":
        return json.dumps({
            "pod": args.get("pod_name"),
            "lines": [
                "2026-10-06T15:20:01Z [INFO] Initializing service listener on :8080",
                "2026-10-06T15:20:14Z [WARN] Heap memory allocation approaching 92% ceiling",
                "2026-10-06T15:20:19Z [FATAL] JavaScript heap out of memory / SIGKILL received from kernel"
            ]
        })

    elif tool_name == "k8s_patch_deployment":
        return json.dumps({
            "status": "success",
            "deployment": args.get("deployment_name"),
            "namespace": args.get("namespace"),
            "applied_patch": args.get("patch_body"),
            "observed_generation": 4
        })

    elif tool_name == "k8s_rollout_restart":
        return json.dumps({
            "status": "success",
            "resource": args.get("resource_name"),
            "message": "Restarted deployment successfully; rolling replacement triggered."
        })

    elif tool_name == "linux_check_system_resources":
        return json.dumps({
            "host_id": args.get("host_id"),
            "cpu_utilization_pct": 89.4,
            "memory_used_gb": 30.2,
            "memory_total_gb": 32.0,
            "swap_used_gb": 4.0,
            "swap_total_gb": 4.0,
            "disk_mounts": [{"mount": "/", "used_pct": 74}, {"mount": "/var/log", "used_pct": 98}]
        })

    elif tool_name == "linux_inspect_process":
        return json.dumps({
            "host_id": args.get("host_id"),
            "top_processes": [
                {"pid": 1042, "user": "app", "cpu_pct": 78.1, "mem_pct": 84.2, "cmd": "/opt/app/bin/worker --concurrency=32"},
                {"pid": 891, "user": "root", "cpu_pct": 4.2, "mem_pct": 1.1, "cmd": "/usr/sbin/systemd-journald"}
            ]
        })

    elif tool_name == "linux_check_network_connections":
        return json.dumps({
            "host_id": args.get("host_id"),
            "total_sockets": 48210,
            "time_wait": 43100,
            "established": 4820,
            "close_wait": 290
        })

    elif tool_name == "metrics_query_latency_percentiles":
        return json.dumps({
            "service": args.get("service_name"),
            "window": f"{args.get('time_window_minutes')}m",
            "p50_ms": 112,
            "p90_ms": 480,
            "p95_ms": 1420,
            "p99_ms": 4920
        })

    elif tool_name == "metrics_query_error_rates":
        return json.dumps({
            "service": args.get("service_name"),
            "total_requests": 148200,
            "http_5xx_count": 8940,
            "error_rate_pct": 6.03
        })

    elif tool_name == "db_query_active_sessions":
        return json.dumps({
            "database": args.get("database_name"),
            "total_connections": 492,
            "max_connections": 500,
            "active": 310,
            "idle_in_transaction": 182
        })

    elif tool_name == "db_check_locks_and_deadlocks":
        return json.dumps({
            "database": args.get("database_name"),
            "blocked_sessions": [
                {"blocked_pid": 2841, "blocking_pid": 1942, "wait_event": "transactionid", "relation": "orders"}
            ]
        })

    elif tool_name == "db_terminate_backend":
        return json.dumps({
            "database": args.get("database_name"),
            "pid": args.get("pid"),
            "result": "success",
            "message": f"Terminated backend process {args.get('pid')}."
        })

    return json.dumps({"status": "executed", "tool": tool_name})


def generate_mock_trajectory(scenario: Dict[str, Any], inject_error: bool = False) -> Dict[str, Any]:
    """
    Assemble a full, multi-turn synthetic conversation for the given scenario.
    If inject_error=True, turn 1 tool call returns an error, followed by self-healing recovery turns.
    """
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": scenario["alert"]}
    ]

    target_tools = scenario.get("expected_tools", ["k8s_describe_pod", "k8s_patch_deployment"])
    first_tool_name = target_tools[0]
    first_tool_args = {
        "namespace": scenario["namespace"],
        "pod_name": scenario["pod_name"]
    } if "k8s" in first_tool_name else {
        "host_id": scenario["host_id"]
    } if "linux" in first_tool_name else {
        "service_name": scenario["service"],
        "time_window_minutes": 15
    } if "metrics" in first_tool_name else {
        "database_name": scenario["database"]
    }

    # Turn 1: Assistant proposes diagnostic tool call
    tc_id_1 = _gen_tool_id()
    turn_1_thought = (
        f"Alert received indicating instability in {scenario['service'] or scenario['host_id']}. "
        f"I will first inspect telemetry using '{first_tool_name}' to verify root cause: {scenario['root_cause']}."
    )
    messages.append({
        "role": "assistant",
        "content": turn_1_thought,
        "tool_calls": [
            {
                "id": tc_id_1,
                "type": "function",
                "function": {
                    "name": first_tool_name,
                    "arguments": json.dumps(first_tool_args)
                }
            }
        ]
    })

    # Turn 1: Tool execution output
    tool_resp_1 = simulate_environment_response(first_tool_name, first_tool_args, inject_error=inject_error)
    messages.append({
        "role": "tool",
        "tool_call_id": tc_id_1,
        "name": first_tool_name,
        "content": tool_resp_1
    })

    # If error was injected, add an error-recovery / self-healing turn
    if inject_error:
        tc_id_recovery = _gen_tool_id()
        recovery_tool_name = "k8s_get_pods" if "k8s" in first_tool_name else "linux_check_system_resources"
        recovery_args = {"namespace": scenario["namespace"]} if "k8s" in first_tool_name else {"host_id": scenario["host_id"]}

        turn_error_recovery_thought = (
            f"The initial call to '{first_tool_name}' returned an error ({json.loads(tool_resp_1).get('error', 'Failed')}). "
            f"Adapting strategy: running fallback discovery with '{recovery_tool_name}' to re-orient cluster state."
        )
        messages.append({
            "role": "assistant",
            "content": turn_error_recovery_thought,
            "tool_calls": [
                {
                    "id": tc_id_recovery,
                    "type": "function",
                    "function": {
                        "name": recovery_tool_name,
                        "arguments": json.dumps(recovery_args)
                    }
                }
            ]
        })

        # Recovery response succeeds
        tool_resp_recovery = simulate_environment_response(recovery_tool_name, recovery_args, inject_error=False)
        messages.append({
            "role": "tool",
            "tool_call_id": tc_id_recovery,
            "name": recovery_tool_name,
            "content": tool_resp_recovery
        })

    # Turn 2 / 3: Remediation action
    remediation_tool_name = target_tools[-1]
    if remediation_tool_name == first_tool_name and len(target_tools) > 1:
        remediation_tool_name = target_tools[1]

    if "patch" in remediation_tool_name:
        remediation_args = {
            "namespace": scenario["namespace"],
            "deployment_name": scenario["service"],
            "patch_body": {"spec": {"template": {"spec": {"containers": [{"name": scenario["service"], "resources": {"limits": {"memory": "512Mi"}}}]}}}}
        }
    elif "restart" in remediation_tool_name:
        remediation_args = {
            "namespace": scenario["namespace"],
            "resource_type": "deployment",
            "resource_name": scenario["service"]
        }
    elif "terminate" in remediation_tool_name:
        remediation_args = {
            "database_name": scenario["database"],
            "pid": 1942,
            "graceful": True
        }
    else:
        remediation_args = first_tool_args

    tc_id_2 = _gen_tool_id()
    remediation_thought = (
        f"Diagnosis confirmed: {scenario['root_cause']}. Proceeding with targeted remediation "
        f"via '{remediation_tool_name}'."
    )
    messages.append({
        "role": "assistant",
        "content": remediation_thought,
        "tool_calls": [
            {
                "id": tc_id_2,
                "type": "function",
                "function": {
                    "name": remediation_tool_name,
                    "arguments": json.dumps(remediation_args)
                }
            }
        ]
    })

    # Remediation response
    tool_resp_2 = simulate_environment_response(remediation_tool_name, remediation_args, inject_error=False)
    messages.append({
        "role": "tool",
        "tool_call_id": tc_id_2,
        "name": remediation_tool_name,
        "content": tool_resp_2
    })

    # Final Assistant Resolution Turn
    final_resolution = (
        f"### Incident Remediation Summary\n"
        f"- **Service Affected**: `{scenario['service']}` ({scenario['namespace']})\n"
        f"- **Root Cause**: {scenario['root_cause']}\n"
        f"- **Remediation Executed**: Executed `{remediation_tool_name}` successfully. Verified pods healthy and metrics returning to normal baseline.\n"
        f"- **Self-Healing Flag**: {'Yes (Handled initial API error and recovered)' if inject_error else 'No (Direct path)'}\n"
        f"- **Prevention Recommendation**: Implement automated canary health-checks and adjust alerts threshold."
    )
    messages.append({
        "role": "assistant",
        "content": final_resolution
    })

    return {
        "id": scenario["scenario_id"],
        "metadata": {
            "category": scenario["category"],
            "subcategory": scenario["subcategory"],
            "difficulty": scenario["difficulty"],
            "has_error_recovery": inject_error,
            "tools_used": list(set([first_tool_name, remediation_tool_name]))
        },
        "tools": DEVOPS_TOOLS,
        "messages": messages
    }
