#!/usr/bin/env python3
"""
Tier 1 Deterministic Dataset Validator CLI.
Fast batch validation for .jsonl trajectory files without spending LLM tokens.
Filters out:
- Malformed JSON / decoding errors.
- Schema parameter mismatches against the 13 SRE tools.
- Missing tool_call_id links or broken multi-turn sequences.
- Security / CSO issues (unmasked tokens, non-documentation IPs).
"""

import os
import sys
import json
import argparse
from typing import Tuple, List, Dict, Any

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from pipeline.validators.syntax_checker import validate_trajectory


def validate_file(input_file: str, output_clean_file: str = None, output_rejected_file: str = None) -> Dict[str, Any]:
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")

    if not output_clean_file:
        base, ext = os.path.splitext(input_file)
        output_clean_file = f"{base}.tier1_valid{ext}"
    if not output_rejected_file:
        base, ext = os.path.splitext(input_file)
        output_rejected_file = f"{base}.tier1_rejected{ext}"

    total_lines = 0
    valid_count = 0
    rejected_count = 0
    rejection_reasons = {}

    with open(input_file, "r", encoding="utf-8") as in_f, \
         open(output_clean_file, "w", encoding="utf-8") as clean_f, \
         open(output_rejected_file, "w", encoding="utf-8") as rej_f:

        for line_num, line in enumerate(in_f, start=1):
            line = line.strip()
            if not line:
                continue

            total_lines += 1

            # 1. JSON decoding test
            try:
                record = json.loads(line)
            except json.JSONDecodeError as e:
                rejected_count += 1
                reason = f"JSONDecodeError: {e}"
                rejection_reasons[reason] = rejection_reasons.get(reason, 0) + 1
                rej_f.write(json.dumps({"line": line_num, "error": reason, "raw": line}) + "\n")
                continue

            # 2. Trajectory & Schema validation
            is_valid, issues = validate_trajectory(record)
            if is_valid:
                valid_count += 1
                clean_f.write(json.dumps(record) + "\n")
            else:
                rejected_count += 1
                primary_issue = issues[0] if issues else "Unknown validation failure"
                rejection_reasons[primary_issue] = rejection_reasons.get(primary_issue, 0) + 1
                record["_rejection_issues"] = issues
                rej_f.write(json.dumps(record) + "\n")

    summary = {
        "input_file": input_file,
        "clean_output": output_clean_file,
        "rejected_output": output_rejected_file,
        "total_records": total_lines,
        "valid_records": valid_count,
        "rejected_records": rejected_count,
        "pass_rate_pct": (valid_count / total_lines * 100) if total_lines > 0 else 0,
        "top_rejection_reasons": rejection_reasons
    }

    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deterministic Tier 1 Trajectory Validator")
    parser.add_argument("input_file", help="Path to input .jsonl file")
    parser.add_argument("--clean", help="Path for cleaned valid records", default=None)
    parser.add_argument("--rejected", help="Path for rejected records", default=None)
    args = parser.parse_args()

    results = validate_file(args.input_file, args.clean, args.rejected)
    print("\n========================================================")
    print(" Tier 1 Deterministic Validation Results")
    print("========================================================")
    print(f"Total Trajectories:    {results['total_records']}")
    print(f"Valid Trajectories:    {results['valid_records']} ({results['pass_rate_pct']:.1f}%)")
    print(f"Rejected Trajectories: {results['rejected_records']}")
    print(f"Clean Output File:     {results['clean_output']}")
    print(f"Rejected Output File:  {results['rejected_output']}")
    if results["top_rejection_reasons"]:
        print("\nRejection Breakdown:")
        for r, count in results["top_rejection_reasons"].items():
            print(f"  - [{count}x] {r}")
    print("========================================================\n")
