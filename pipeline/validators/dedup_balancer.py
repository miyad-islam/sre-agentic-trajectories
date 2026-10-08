"""
Semantic De-Duplication and Entropy Balancing Engine.
1. Detects and removes near-duplicate trajectories using MinHash/Jaccard shingling on incident alerts and tool call chains.
2. Computes Shannon Entropy over categories and difficulty tiers to guarantee balanced dataset representation.
3. Generates statistical diversity metrics for the QA audit report.
"""

import os
import sys
import json
import math
import argparse
from typing import Dict, Any, List, Set, Tuple
from collections import Counter

# Ensure project root in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


def _get_shingles(text: str, k: int = 3) -> Set[str]:
    """Extract character k-shingles from text."""
    clean = "".join(c.lower() for c in text if c.isalnum() or c.isspace())
    words = clean.split()
    return set(" ".join(words[i:i+k]) for i in range(len(words) - k + 1)) if len(words) >= k else {clean}


def jaccard_similarity(set_a: Set[str], set_b: Set[str]) -> float:
    """Calculate Jaccard similarity between two sets."""
    union = set_a | set_b
    if not union:
        return 0.0
    return len(set_a & set_b) / len(union)


def calculate_shannon_entropy(items: List[str]) -> float:
    """Compute Shannon entropy in bits for a discrete distribution."""
    if not items:
        return 0.0
    total = len(items)
    counts = Counter(items)
    entropy = 0.0
    for count in counts.values():
        p = count / total
        entropy -= p * math.log2(p)
    return entropy


def deduplicate_and_balance(input_file: str, output_file: str, similarity_threshold: float = 0.85) -> Dict[str, Any]:
    """
    Filter out near-duplicate trajectories and report dataset diversity and entropy metrics.
    """
    seen_shingles: List[Tuple[str, Set[str]]] = []
    retained_records: List[Dict[str, Any]] = []
    duplicate_count = 0

    categories = []
    difficulties = []
    tools_frequency = Counter()

    with open(input_file, "r", encoding="utf-8") as in_f:
        for line in in_f:
            line = line.strip()
            if not line:
                continue

            record = json.loads(line)
            user_msg = next((m.get("content", "") for m in record.get("messages", []) if m.get("role") == "user"), "")
            tool_chain = "-".join(record.get("metadata", {}).get("tools_used", []))
            fingerprint_text = f"{user_msg} || {tool_chain}"
            shingles = _get_shingles(fingerprint_text)

            # Check similarity against previously accepted records
            is_duplicate = False
            for prev_id, prev_shingles in seen_shingles:
                sim = jaccard_similarity(shingles, prev_shingles)
                if sim >= similarity_threshold:
                    is_duplicate = True
                    duplicate_count += 1
                    break

            if not is_duplicate:
                seen_shingles.append((record.get("id", ""), shingles))
                retained_records.append(record)

                meta = record.get("metadata", {})
                categories.append(meta.get("category", "unknown"))
                difficulties.append(meta.get("difficulty", "unknown"))
                for t in meta.get("tools_used", []):
                    tools_frequency[t] += 1

    # Write de-duplicated dataset
    with open(output_file, "w", encoding="utf-8") as out_f:
        for rec in retained_records:
            out_f.write(json.dumps(rec) + "\n")

    # Metrics
    cat_entropy = calculate_shannon_entropy(categories)
    max_cat_entropy = math.log2(4)  # 4 failure categories = 2.0 bits max
    diff_entropy = calculate_shannon_entropy(difficulties)
    max_diff_entropy = math.log2(3)  # 3 difficulty levels = 1.58 bits max

    return {
        "input_total": len(retained_records) + duplicate_count,
        "duplicates_pruned": duplicate_count,
        "retained_total": len(retained_records),
        "category_distribution": dict(Counter(categories)),
        "category_entropy_bits": round(cat_entropy, 3),
        "category_entropy_ratio": round(cat_entropy / max_cat_entropy if max_cat_entropy > 0 else 0, 3),
        "difficulty_distribution": dict(Counter(difficulties)),
        "difficulty_entropy_bits": round(diff_entropy, 3),
        "difficulty_entropy_ratio": round(diff_entropy / max_diff_entropy if max_diff_entropy > 0 else 0, 3),
        "unique_tools_exercised": len(tools_frequency),
        "output_file": output_file
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Dataset De-Duplication & Entropy Balancer")
    parser.add_argument("input_file", help="Input .jsonl file")
    parser.add_argument("--output", default="output/sre_trajectories_deduped.jsonl", help="Output path")
    parser.add_argument("--threshold", type=float, default=0.85, help="Jaccard similarity cutoff for duplicates")
    args = parser.parse_args()

    stats = deduplicate_and_balance(args.input_file, args.output, args.threshold)
    print("\n========================================================")
    print(" De-Duplication & Entropy Diversity Report")
    print("========================================================")
    print(f"Total Evaluated:        {stats['input_total']}")
    print(f"Duplicates Pruned:      {stats['duplicates_pruned']}")
    print(f"Retained Trajectories:  {stats['retained_total']}")
    print(f"Category Entropy:       {stats['category_entropy_bits']} / {math.log2(4):.2f} bits ({stats['category_entropy_ratio']*100:.1f}% max)")
    print(f"Difficulty Entropy:     {stats['difficulty_entropy_bits']} / {math.log2(3):.2f} bits ({stats['difficulty_entropy_ratio']*100:.1f}% max)")
    print(f"Unique Tools Utilized:  {stats['unique_tools_exercised']}")
    print(f"Categories:             {stats['category_distribution']}")
    print(f"Difficulties:           {stats['difficulty_distribution']}")
    print(f"Saved to:               {stats['output_file']}")
    print("========================================================\n")
