"""
Tier 2 LLM-as-a-Judge Evaluator.
Scores SRE / DevOps trajectories on a 1–5 scale based on:
1. Tool Selection Relevance (did the agent select the right diagnostic tool for the alert?)
2. Grounded Interpretation (did the agent read the tool response accurately without hallucination?)
3. Self-Healing & Error Handling (if tool failed, did agent recover logically?)
4. Remediation Effectiveness (did remediation resolve the declared incident?)

Threshold: Scores >= 4 are kept; scores < 4 are pruned.
"""

import os
import sys
import json
import argparse
import urllib.request
from typing import Dict, Any, Tuple, Optional

# Ensure project root in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


JUDGE_SYSTEM_PROMPT = """You are an expert SRE Architect evaluating an autonomous AI agent's multi-turn incident remediation trajectory.
Evaluate the trajectory strictly against the following criteria:
1. Tool Relevance: Were diagnostic tools appropriate for the incident alert?
2. Reasoning & Non-Hallucination: Did the agent accurately interpret tool outputs without making up facts?
3. Error Recovery: If a tool returned an error (504, 404, rate limit), did the agent adapt and recover?
4. Remediation: Was the final remediation step effective and verified?

Respond ONLY with a JSON object in this exact format:
{
  "score": <integer from 1 to 5>,
  "strengths": "<short summary>",
  "weaknesses": "<short summary>",
  "passed": <true if score >= 4 else false>
}
"""


def format_trajectory_for_judge(trajectory: Dict[str, Any]) -> str:
    """Format full trajectory turns into clean text representation for the LLM judge."""
    formatted = [f"### Incident Scenario ID: {trajectory.get('id', 'unknown')}"]
    metadata = trajectory.get("metadata", {})
    if metadata:
        formatted.append(f"Metadata: Category={metadata.get('category')}, Subcategory={metadata.get('subcategory')}, Difficulty={metadata.get('difficulty')}")

    for idx, msg in enumerate(trajectory.get("messages", [])):
        role = msg.get("role", "unknown").upper()
        content = msg.get("content", "")
        tc_info = ""
        if msg.get("tool_calls"):
            calls = [f"{tc['function']['name']}({tc['function']['arguments']})" for tc in msg["tool_calls"]]
            tc_info = f" [TOOL CALLS: {'; '.join(calls)}]"
        elif role == "TOOL":
            tc_info = f" [TOOL RESPONSE to {msg.get('tool_call_id', '')} ({msg.get('name', '')})]"

        formatted.append(f"{role}{tc_info}: {content}")

    return "\n\n".join(formatted)


def evaluate_trajectory_mock(trajectory: Dict[str, Any]) -> Dict[str, Any]:
    """
    Offline heuristic judge for fast testing without GPU tokens.
    Simulates realistic scoring distributions based on trajectory structure.
    """
    messages = trajectory.get("messages", [])
    has_tool_call = any(m.get("role") == "assistant" and m.get("tool_calls") for m in messages)
    has_tool_resp = any(m.get("role") == "tool" for m in messages)
    has_summary = any(m.get("role") == "assistant" and "Incident Remediation Summary" in (m.get("content") or "") for m in messages)
    metadata = trajectory.get("metadata", {})

    if not has_tool_call or not has_tool_resp:
        return {"score": 1, "passed": False, "strengths": "None", "weaknesses": "Missing tool calls or tool responses."}

    if not has_summary:
        return {"score": 3, "passed": False, "strengths": "Tool execution succeeded", "weaknesses": "Missing post-incident summary."}

    # High quality multi-turn trajectory
    if metadata.get("has_error_recovery"):
        return {
            "score": 5,
            "passed": True,
            "strengths": "Demonstrated graceful self-healing on simulated API failure, adapted discovery, and applied remediation.",
            "weaknesses": "None observed."
        }
    else:
        return {
            "score": 4,
            "passed": True,
            "strengths": "Direct diagnostic and targeted patch execution with verified health status.",
            "weaknesses": "Standard happy path."
        }


def query_vllm_judge(endpoint: str, trajectory_text: str) -> Dict[str, Any]:
    """Send evaluation prompt to vLLM Qwen 2.5 72B Instruct instance."""
    url = f"{endpoint.rstrip('/')}/chat/completions"
    payload = {
        "model": "Qwen/Qwen2.5-72B-Instruct",
        "messages": [
            {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
            {"role": "user", "content": f"Please evaluate this SRE trajectory:\n\n{trajectory_text}"}
        ],
        "temperature": 0.1,
        "max_tokens": 512
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})

    with urllib.request.urlopen(req, timeout=60) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        raw_content = res["choices"][0]["message"]["content"]
        # Extract JSON substring
        start = raw_content.find("{")
        end = raw_content.rfind("}") + 1
        if start != -1 and end != 0:
            return json.loads(raw_content[start:end])
        return {"score": 3, "passed": False, "raw": raw_content}


def filter_dataset_with_judge(input_file: str, output_passed_file: str, output_pruned_file: str, endpoint: str = None, use_mock: bool = True) -> Dict[str, Any]:
    """
    Run Tier 2 LLM-as-a-Judge pass over a dataset file.
    Keep rows with score >= 4, prune rows < 4.
    """
    total = 0
    passed = 0
    pruned = 0
    scores = []

    with open(input_file, "r", encoding="utf-8") as in_f, \
         open(output_passed_file, "w", encoding="utf-8") as pass_f, \
         open(output_pruned_file, "w", encoding="utf-8") as prune_f:

        for line in in_f:
            line = line.strip()
            if not line:
                continue

            total += 1
            record = json.loads(line)

            if use_mock:
                eval_res = evaluate_trajectory_mock(record)
            else:
                traj_text = format_trajectory_for_judge(record)
                eval_res = query_vllm_judge(endpoint, traj_text)

            score = eval_res.get("score", 3)
            scores.append(score)
            record["_judge_eval"] = eval_res

            if score >= 4:
                passed += 1
                pass_f.write(json.dumps(record) + "\n")
            else:
                pruned += 1
                prune_f.write(json.dumps(record) + "\n")

    return {
        "total_evaluated": total,
        "passed_enterprise_grade": passed,
        "pruned": pruned,
        "pass_rate_pct": (passed / total * 100) if total > 0 else 0,
        "avg_score": (sum(scores) / len(scores)) if scores else 0
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tier 2 LLM-as-a-Judge Evaluation Filter")
    parser.add_argument("input_file", help="Input .jsonl trajectory file (already Tier 1 validated)")
    parser.add_argument("--passed", default="output/judge_passed.jsonl", help="Output passed trajectories")
    parser.add_argument("--pruned", default="output/judge_pruned.jsonl", help="Output pruned trajectories")
    parser.add_argument("--endpoint", default="http://localhost:8000/v1", help="vLLM endpoint")
    parser.add_argument("--mock", action="store_true", default=True, help="Use mock heuristic judge for dry runs")
    args = parser.parse_args()

    results = filter_dataset_with_judge(args.input_file, args.passed, args.pruned, args.endpoint, use_mock=args.mock)
    print("\n========================================================")
    print(" Tier 2 LLM-as-a-Judge Evaluation Summary")
    print("========================================================")
    print(f"Total Evaluated: {results['total_evaluated']}")
    print(f"Passed (>=4):    {results['passed_enterprise_grade']} ({results['pass_rate_pct']:.1f}%)")
    print(f"Pruned (<4):    {results['pruned']}")
    print(f"Average Score:   {results['avg_score']:.2f} / 5.0")
    print(f"Clean Output:    {args.passed}")
    print("========================================================\n")
