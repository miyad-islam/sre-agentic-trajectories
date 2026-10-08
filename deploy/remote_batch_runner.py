#!/usr/bin/env python3
"""
High-Concurrency SRE Trajectory Batch Runner.
Pumps incident scenarios through the vLLM endpoint (Qwen 2.5 72B Instruct),
performs on-the-fly Tier 1 deterministic validation, and streams checkpoints to disk.
Uses standard library concurrent.futures for zero-dependency execution.
"""

import os
import sys
import json
import time
import argparse
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List, Optional

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pipeline.schemas.tools import DEVOPS_TOOLS
from pipeline.generators.scenarios import generate_scenario_batch
from pipeline.generators.simulator import simulate_environment_response, SYSTEM_PROMPT
from pipeline.validators.syntax_checker import validate_trajectory


def query_vllm_chat(endpoint: str, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None, temperature: float = 0.7, max_tokens: int = 1024) -> Dict[str, Any]:
    """Send a chat completion request to an OpenAI-compatible vLLM endpoint."""
    url = f"{endpoint.rstrip('/')}/chat/completions"
    payload = {
        "model": "Qwen/Qwen2.5-72B-Instruct",
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            res_body = response.read().decode("utf-8")
            return json.loads(res_body)
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8", errors="replace")
        print(f"\n[HTTPError {e.code}]: {err_msg}")
        raise


def process_single_scenario(scenario: Dict[str, Any], endpoint: str, inject_error: bool = False, use_mock_llm: bool = False) -> Optional[Dict[str, Any]]:
    """
    Execute a full multi-turn generation workflow for one scenario seed.
    If use_mock_llm is True, simulates generation locally without calling vLLM.
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

    try:
        if use_mock_llm:
            # Local mock fallback for fast dry-run verification
            from pipeline.generators.simulator import generate_mock_trajectory
            return generate_mock_trajectory(scenario, inject_error=inject_error)

        # -------------------------------------------------------------
        # Turn 1: Call Model for diagnostic reasoning and tool call
        # -------------------------------------------------------------
        resp1 = query_vllm_chat(endpoint, messages, tools=DEVOPS_TOOLS)
        choice1 = resp1["choices"][0]["message"]
        messages.append(choice1)

        tool_calls1 = choice1.get("tool_calls", [])
        if not tool_calls1:
            return None  # Model failed to invoke tool

        # -------------------------------------------------------------
        # Turn 1 Response: Environment feedback
        # -------------------------------------------------------------
        for tc in tool_calls1:
            fn_name = tc["function"]["name"]
            fn_args = json.loads(tc["function"]["arguments"])
            tool_content = simulate_environment_response(fn_name, fn_args, inject_error=inject_error)
            messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "name": fn_name,
                "content": tool_content
            })

        # -------------------------------------------------------------
        # Turn 2: Model adapts (Self-healing or Remediation)
        # -------------------------------------------------------------
        resp2 = query_vllm_chat(endpoint, messages, tools=DEVOPS_TOOLS)
        choice2 = resp2["choices"][0]["message"]
        messages.append(choice2)

        tool_calls2 = choice2.get("tool_calls", [])
        if tool_calls2:
            for tc in tool_calls2:
                fn_name = tc["function"]["name"]
                fn_args = json.loads(tc["function"]["arguments"])
                tool_content = simulate_environment_response(fn_name, fn_args, inject_error=False)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "name": fn_name,
                    "content": tool_content
                })

            # Final resolution summary
            resp3 = query_vllm_chat(endpoint, messages, tools=None)
            messages.append(resp3["choices"][0]["message"])

        # -------------------------------------------------------------
        # Assemble Trajectory Record
        # -------------------------------------------------------------
        trajectory = {
            "id": scenario["scenario_id"],
            "metadata": {
                "category": scenario["category"],
                "subcategory": scenario["subcategory"],
                "difficulty": scenario["difficulty"],
                "has_error_recovery": inject_error,
                "tools_used": [tc["function"]["name"] for m in messages if m.get("tool_calls") for tc in m["tool_calls"]]
            },
            "tools": DEVOPS_TOOLS,
            "messages": messages
        }

        # Deterministic validation
        is_valid, _ = validate_trajectory(trajectory)
        return trajectory if is_valid else None

    except Exception as e:
        import traceback
        print(f"\n[Worker Error on {scenario.get('scenario_id', 'unknown')}]: {e}")
        traceback.print_exc()
        return None


def run_batch(total_samples: int = 100, concurrency: int = 16, endpoint: str = "http://localhost:8000/v1", output_dir: str = "output/batches", checkpoint_interval: int = 500, use_mock: bool = False):
    """Execute high-concurrency batch generation loop with checkpointing."""
    os.makedirs(output_dir, exist_ok=True)
    checkpoint_file = os.path.join(output_dir, f"trajectories_batch_{int(time.time())}.jsonl")
    
    print(f"\n==========================================================")
    print(f" Starting Batch Generation Runner")
    print(f" Target Samples: {total_samples} | Concurrency: {concurrency}")
    print(f" Endpoint: {endpoint} | Mode: {'Mock Dry-Run' if use_mock else 'vLLM ROCm'}")
    print(f" Checkpoint Output: {checkpoint_file}")
    print(f"==========================================================\n")

    scenarios = generate_scenario_batch(count=total_samples, seed=int(time.time()) % 100000)
    completed_count = 0
    valid_count = 0
    start_time = time.time()

    with open(checkpoint_file, "a", encoding="utf-8") as out_f:
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            # Map scenarios with 25% error-injection
            future_to_idx = {
                executor.submit(process_single_scenario, sc, endpoint, inject_error=(i % 4 == 0), use_mock_llm=use_mock): i
                for i, sc in enumerate(scenarios)
            }

            for future in as_completed(future_to_idx):
                completed_count += 1
                result = future.result()
                if result:
                    valid_count += 1
                    out_f.write(json.dumps(result) + "\n")
                    if valid_count % 50 == 0:
                        out_f.flush()

                # Progress report
                elapsed = time.time() - start_time
                rate = completed_count / elapsed if elapsed > 0 else 0
                sys.stdout.write(
                    f"\rProgress: [{completed_count}/{total_samples}] | "
                    f"Valid: {valid_count} ({valid_count/completed_count*100:.1f}%) | "
                    f"Speed: {rate:.1f} traj/sec | Elapsed: {elapsed:.0f}s"
                )
                sys.stdout.flush()

    total_time = time.time() - start_time
    print(f"\n\n[+] Batch Run Completed in {total_time:.1f} seconds.")
    print(f"[+] Total Valid Trajectories Written: {valid_count}/{total_samples}")
    print(f"[+] Output File: {checkpoint_file}")
    return checkpoint_file


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SRE Trajectory Batch Runner")
    parser.add_argument("--count", type=int, default=20, help="Number of trajectories to generate")
    parser.add_argument("--concurrency", type=int, default=4, help="Concurrent workers")
    parser.add_argument("--endpoint", type=str, default="http://localhost:8000/v1", help="vLLM endpoint URL")
    parser.add_argument("--mock", action="store_true", help="Run in mock mode without calling remote LLM")
    args = parser.parse_args()

    run_batch(total_samples=args.count, concurrency=args.concurrency, endpoint=args.endpoint, use_mock=args.mock)
