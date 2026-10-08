#!/usr/bin/env python3
"""
Packaging and Format Conversion CLI.
Exports validated and judge-filtered SRE trajectories into:
1. Standard OpenAI / ShareGPT JSONL format.
2. LLaMA-Factory dataset format with dataset_info.json configuration.
3. Stratified 2,000-row preview sample for Hugging Face (CC-BY-NC 4.0).
"""

import os
import sys
import json
import random
import argparse
from typing import Dict, Any, List

# Ensure project root in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from pipeline.schemas.tools import DEVOPS_TOOLS


def package_datasets(input_file: str, output_base_dir: str = "dist", sample_size: int = 2000):
    os.makedirs(os.path.join(output_base_dir, "openai_format"), exist_ok=True)
    os.makedirs(os.path.join(output_base_dir, "llama_factory"), exist_ok=True)
    os.makedirs(os.path.join(output_base_dir, "huggingface_sample"), exist_ok=True)
    os.makedirs(os.path.join(output_base_dir, "commercial"), exist_ok=True)

    print(f"\n========================================================")
    print(f" Packaging SRE Trajectory Datasets for Distribution")
    print(f" Source: {input_file}")
    print(f"========================================================\n")

    records = []
    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    total_records = len(records)
    print(f"[+] Loaded {total_records} validated trajectories.")

    # 1. Export Standard OpenAI Format
    openai_path = os.path.join(output_base_dir, "openai_format", "sre_trajectories_enterprise.jsonl")
    with open(openai_path, "w", encoding="utf-8") as f:
        for r in records:
            # Clean internal review annotations for final buyer export
            clean_rec = {
                "id": r["id"],
                "metadata": r.get("metadata", {}),
                "tools": r.get("tools", DEVOPS_TOOLS),
                "messages": r.get("messages", [])
            }
            f.write(json.dumps(clean_rec) + "\n")
    print(f"[+] Exported OpenAI format ({total_records} rows): {openai_path}")

    # 2. Export LLaMA-Factory Format
    llama_path = os.path.join(output_base_dir, "llama_factory", "sre_trajectories_llama_factory.jsonl")
    with open(llama_path, "w", encoding="utf-8") as f:
        for r in records:
            llama_rec = {
                "id": r["id"],
                "tools": json.dumps(r.get("tools", DEVOPS_TOOLS)),
                "conversations": r.get("messages", [])
            }
            f.write(json.dumps(llama_rec) + "\n")

    # Generate LLaMA-Factory dataset_info.json configuration
    dataset_info = {
        "sre_agent_trajectories": {
            "file_name": "sre_trajectories_llama_factory.jsonl",
            "formatting": "sharegpt",
            "columns": {
                "messages": "conversations",
                "tools": "tools"
            }
        }
    }
    with open(os.path.join(output_base_dir, "llama_factory", "dataset_info.json"), "w", encoding="utf-8") as f:
        json.dump(dataset_info, f, indent=2)
    print(f"[+] Exported LLaMA-Factory format & dataset_info.json: {llama_path}")

    # 3. Export Stratified Hugging Face Sample
    actual_sample_size = min(sample_size, total_records)
    random.seed(42)
    sample_records = random.sample(records, actual_sample_size) if total_records > actual_sample_size else records

    hf_sample_path = os.path.join(output_base_dir, "huggingface_sample", "sample_2000.jsonl")
    with open(hf_sample_path, "w", encoding="utf-8") as f:
        for r in sample_records:
            clean_rec = {
                "id": r["id"],
                "metadata": r.get("metadata", {}),
                "tools": r.get("tools", DEVOPS_TOOLS),
                "messages": r.get("messages", [])
            }
            f.write(json.dumps(clean_rec) + "\n")
    print(f"[+] Exported Stratified Sample ({len(sample_records)} rows): {hf_sample_path}")

    return {
        "total_records": total_records,
        "sample_size": len(sample_records),
        "openai_path": openai_path,
        "llama_path": llama_path,
        "hf_sample_path": hf_sample_path
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Dataset Packaging & Format Converter")
    parser.add_argument("input_file", help="Path to validated .jsonl file")
    parser.add_argument("--outdir", default="dist", help="Output directory")
    parser.add_argument("--sample_size", type=int, default=2000, help="Hugging Face sample size")
    args = parser.parse_args()

    package_datasets(args.input_file, args.outdir, args.sample_size)
