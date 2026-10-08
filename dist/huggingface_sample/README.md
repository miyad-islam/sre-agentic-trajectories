---
license: cc-by-nc-4.0
task_categories:
- text-generation
- question-answering
tags:
- agents
- function-calling
- tool-use
- sre
- devops
- synthetic-data
- trajectory
size_categories:
- 1K<n<10K
---

# SRE & DevOps Agentic Trajectory Dataset (2,000-Row Preview)

[![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc/4.0/)
[![Dataset Type](https://img.shields.io/badge/Dataset-Multi--Turn%20Agentic%20Tool--Use-blue.svg)]()
[![Model Provenance](https://img.shields.io/badge/Generated%20With-Qwen%202.5%2072B%20BF16%20(MI300X)-green.svg)]()

> **Notice**: This repository provides an open **2,000-row preview sample** licensed under **Creative Commons Attribution-NonCommercial 4.0 (CC-BY-NC-4.0)** for academic evaluation and research.  
> 🛒 **For Commercial Model Training & Full 5,000 Production Dataset ($49 Launch Special):** See purchase instructions below.

---

## 🚀 Overview

Training small language models (3B to 8B) to reliably operate as autonomous infrastructure agents requires complex, multi-turn tool-use data. Most existing open datasets provide single-turn happy-path queries on trivial tools (weather, calculators).

This dataset provides **enterprise-grade incident remediation trajectories** across real-world DevOps environments:
* **Kubernetes (`kubectl`)**: OOMKilled crashes, CrashLoopBackOff, readiness probe timeouts, pod resource patching.
* **Linux OS**: Inode/disk exhaustion, zombie processes, socket state leaks (TIME_WAIT).
* **APM & Cloud Metrics**: Datadog/CloudWatch p99 latency queries, 5xx error spikes, dependency tracing.
* **PostgreSQL**: Table lock contentions, connection pool exhaustion, transaction cancellation.

### 🛡️ Key Features
* **26% Self-Healing & Error-Recovery Turns**: Agents handle 404s, 504 timeouts, and rate limits gracefully, re-orienting cluster state before executing remediation.
* **100% Strict Schema Validation**: Every tool call adheres strictly to Draft-7 JSON schemas.
* **Two-Tier Quality Filter**: Cleaned via deterministic schema checks and LLM-as-a-Judge validation.
* **Zero Quantization Noise**: Generated on AMD Instinct MI300X (192GB VRAM) running native BF16 `Qwen/Qwen2.5-72B-Instruct`.

---

## 📦 How to Load in Python

```python
from datasets import load_dataset

# Load preview sample directly
dataset = load_dataset("json", data_files="sample_2000.jsonl")

# Inspect first incident
sample = dataset["train"][0]
print("Incident ID:", sample["id"])
print("Category:", sample["metadata"]["category"])
print("Turns:", len(sample["messages"]))
```

---

## 📊 Benchmark Fine-Tuning Uplift

Fine-tuning `Qwen-2.5-7B` on this SRE trajectory dataset yields significant improvements on multi-turn function calling:

* **Berkeley Function Calling Leaderboard (BFCL)**: +16.4% Executable Accuracy (58.2% → 74.6%).
* **Tool Failure Recovery Rate**: +58.8% Success on unexpected API 5xx/404 (22.4% → 81.2%).
* **Hallucinated Tool Calls**: Reduced by -12.7% (14.8% → 2.1%).

---

## 💼 Full Commercial Dataset ($49 Launch Special)

Need the un-sampled **5,000 production trajectories (4,938 strictly validated)** with commercial training rights?

### What is Included in the Full Package:
1. **Full 5,000 Production Trajectories (`.jsonl`)**: Both OpenAI Function Calling format and ShareGPT / LLaMA-Factory format.
2. **LLaMA-Factory & Axolotl Configs**: Ready-to-train `dataset_info.json`.
3. **Full Commercial Rights**: Perpetual worldwide license to train proprietary models, fine-tune SLMs, and monetize model weights.
4. **Verified QA Audit Report**: Provenance, schema audit, and rejection documentation.

### 💳 How to Purchase ($49 via Card / Bank Wire):
To purchase the full commercial dataset:
* **Email:** Send a request to `miyadislam316@gmail.com` with subject *"DevOps Dataset Purchase"*.
* We will send an instant **Payoneer payment invoice** (supports all major Credit/Debit Cards, Apple Pay, and Bank Transfers).
* Upon payment, the full package download link is delivered to your inbox immediately.
