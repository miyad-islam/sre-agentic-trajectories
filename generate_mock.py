#!/usr/bin/env python3
"""
Mock Trajectory Generation & Pipeline Test Runner.
Executes Phase 1 verification locally with 0 cloud credits.
Generates sample trajectories, executes deterministic validation, and saves to JSONL.
"""

import os
import json
import random
from pipeline.schemas.tools import DEVOPS_TOOLS
from pipeline.generators.scenarios import generate_scenario_batch
from pipeline.generators.simulator import generate_mock_trajectory
from pipeline.validators.syntax_checker import validate_trajectory, validate_all_tool_schemas


def run_mock_generation(count: int = 5, output_file: str = "output/mock_sample_5.jsonl"):
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    print(f"\n========================================================")
    print(f" SRE DevOps Agentic Trajectory Pipeline: Mock Runner")
    print(f"========================================================")
    
    # 1. Verify Tool Schemas
    schema_errors = validate_all_tool_schemas()
    if schema_errors:
        print(f"[-] Tool Schema Validation Failed: {schema_errors}")
        return False
    print(f"[+] All {len(DEVOPS_TOOLS)} DevOps tool schemas validated (Draft 7 JSON Schema).")

    # 2. Generate Incident Scenarios
    scenarios = generate_scenario_batch(count=count, seed=101)
    print(f"[+] Generated {len(scenarios)} balanced incident scenarios across categories.")

    # 3. Simulate Trajectories with Error-Injection (~25% rate)
    trajectories = []
    error_count = 0
    rng = random.Random(42)

    for idx, sc in enumerate(scenarios):
        # Enforce error injection on 25% of samples (at least 1 in 5)
        inject_error = (idx == 0) or (rng.random() < 0.25)
        if inject_error:
            error_count += 1
            
        traj = generate_mock_trajectory(sc, inject_error=inject_error)
        
        # 4. Tier 1 Validation
        is_valid, issues = validate_trajectory(traj)
        if not is_valid:
            print(f"[-] Validation failed for {traj['id']}: {issues}")
            return False
            
        trajectories.append(traj)

    # 5. Write to JSONL
    with open(output_file, "w", encoding="utf-8") as f:
        for t in trajectories:
            f.write(json.dumps(t) + "\n")

    print(f"[+] Successfully wrote {len(trajectories)} trajectories to: {output_file}")
    print(f"    - Error-Recovery / Self-Healing Trajectories: {error_count}/{len(trajectories)}")
    print(f"    - All trajectories passed 100% of Tier 1 syntactic & schema tests.\n")

    # Display sample trajectory structure
    sample = trajectories[0]
    print(f"--- Sample Trajectory Fingerprint ---")
    print(f"ID: {sample['id']}")
    print(f"Category: {sample['metadata']['category']} ({sample['metadata']['subcategory']})")
    print(f"Difficulty: {sample['metadata']['difficulty']}")
    print(f"Error-Recovery Enabled: {sample['metadata']['has_error_recovery']}")
    print(f"Total Turns: {len(sample['messages'])}")
    print(f"Tools Used: {', '.join(sample['metadata']['tools_used'])}")
    print(f"-------------------------------------\n")
    return True


if __name__ == "__main__":
    success = run_mock_generation(count=5)
    if not success:
        exit(1)
