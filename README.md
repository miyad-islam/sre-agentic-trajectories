# SRE & DevOps Agentic Trajectory Synthesis Engine

[![Hugging Face Dataset](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-sre--agentic--trajectories-yellow.svg)](https://huggingface.co/datasets/miyad316/sre-agentic-trajectories-devops)
[![Accelerator](https://img.shields.io/badge/Hardware-AMD%20Instinct%20MI300X%20(192GB)-ED1C24.svg)](https://www.amd.com/en/products/accelerators/instinct/mi300.html)
[![Backend](https://img.shields.io/badge/Inference-vLLM%20(ROCm%206.2)-purple.svg)](https://github.com/vllm-project/vllm)
[![Teacher Model](https://img.shields.io/badge/Teacher%20Model-Qwen%202.5%2072B%20BF16-blue.svg)](https://huggingface.co/Qwen/Qwen2.5-72B-Instruct)
[![License: Apache 2.0](https://img.shields.io/badge/Code%20License-Apache%202.0-green.svg)](LICENSE)

An enterprise synthetic data generation and validation pipeline engineered to fine-tune compact Small Language Models (SLMs, 3B–8B) into autonomous infrastructure and Site Reliability Engineering (SRE) agents.

---

## 🚀 Overview

Most open function-calling datasets only train models on single-turn "happy paths" (calculators, weather APIs, trivia). In production environments, infrastructure agents encounter real-world complexity:
* Kubernetes pods enter `OOMKilled` and `CrashLoopBackOff`
* Network sockets enter `TIME_WAIT`
* APM endpoints return `504 Gateway Timeouts`
* Database connections hit deadlock contentions

When models without multi-turn recovery encounter unexpected errors, they hallucinate commands or enter infinite retry loops.

This repository provides the complete synthetic generation engine, schema declarations, deterministic validators, and deployment orchestration that produced the **5,000 SRE Agentic Trajectory Dataset**.

👉 **Download the Open 2,000 Preview Sample on Hugging Face:**  
[https://huggingface.co/datasets/miyad316/sre-agentic-trajectories-devops](https://huggingface.co/datasets/miyad316/sre-agentic-trajectories-devops)

---

## 🛡️ Key Features

* **12 Production SRE Tools:** Declarative Draft-7 JSON schemas covering Kubernetes (`kubectl` pod diagnostics, logs, deployment patches), Linux OS system internals, APM metric percentiles (p95/p99 latency, 5xx error spikes), and PostgreSQL deadlocks.
* **26% Self-Healing & Recovery Chains:** Multi-turn error trajectories simulating 404s, 504 timeouts, and permission errors, training agents to re-orient state before executing remediation.
* **Hardware Provenance:** Synthesized on enterprise **AMD Instinct MI300X (192GB HBM3)** accelerators running native BF16 `Qwen/Qwen2.5-72B-Instruct` via ROCm vLLM with zero quantization degradation.
* **Two-Tier Quality Validation:** 100% strict Draft-7 JSON schema validator (98.8% pass rate across 5,000 generations) paired with LLM-as-a-judge filtering and RFC-5737 sanitized IP addresses.
* **Turn-Key Fine-Tuning:** Exports directly to OpenAI JSONL format and ShareGPT / LLaMA-Factory format with pre-built `dataset_info.json`.

---

## 🏗️ Architecture Pipeline

```text
[ Seed Incident Scenarios ] (Kubernetes, Linux OS, APM, PostgreSQL)
             │
             ▼
[ MI300X ROCm vLLM Batch Runner ] (Qwen-2.5-72B-Instruct Native BF16)
             │
             ├──► [ Simulated Environment & Tool Execution ]
             │         │
             │         ├── (74% Happy Path Remediation)
             │         └── (26% Error Injection & Self-Healing Turns)
             ▼
[ Tier-1 Strict Schema Validator ] (Draft-7 JSON Schema Enforcement)
             │
             ▼
[ Tier-2 LLM-as-a-Judge ] (Rejection of Hallucinated Tools & Bad Reasoning)
             │
             ▼
[ Formatter & Packager ]
   ├── OpenAI Multi-Turn Function Calling JSONL
   ├── LLaMA-Factory / ShareGPT Dataset Format (dataset_info.json)
   └── Stratified Hugging Face Sample
```

---

## 📦 Project Structure

```text
├── pipeline/
│   ├── schemas/              # 12 SRE tool definitions & JSON schemas
│   │   ├── tools.py          # Python dataclass tool declarations
│   │   └── tools.json        # Exported Draft-7 JSON schema
│   ├── generators/           # Scenario generator & environment simulator
│   │   ├── scenarios.py      # Seed scenario generator
│   │   └── simulator.py      # Deterministic environment execution
│   └── validators/           # Quality control and filtering
│       ├── syntax_checker.py # Deterministic JSON & IP sanitizer
│       ├── llm_judge.py      # LLM-as-a-judge reasoning evaluator
│       └── dedup_balancer.py # Semantic deduplication & distribution
├── deploy/                   # Cloud GPU deployment orchestration
│   ├── setup_mi300x.sh       # ROCm & vLLM container initialization
│   ├── remote_batch_runner.py# Multi-turn generation batch runner
│   └── watchdog_teardown.sh  # Auto-shutdown & idle budget watchdog
├── generate_mock.py          # Local mock generator for quick testing
├── validate_dataset.py       # Standalone validation CLI
├── package_dataset.py        # Export & format conversion CLI
└── docs/
    └── QA_AUDIT_REPORT.md    # Technical provenance & benchmark audit report
```

---

## ⚡ Quickstart

### 1. Installation

```bash
git clone https://github.com/miyad316/sre-agentic-trajectories.git
cd sre-agentic-trajectories
pip install -r requirements.txt
```

### 2. Generate Mock Trajectories Locally

Test the generation and multi-turn tool interaction locally without a GPU:

```bash
python generate_mock.py --count 10 --out test_output.jsonl
```

### 3. Validate Trajectories Against Strict Schemas

```bash
python validate_dataset.py test_output.jsonl
```

### 4. Package for Fine-Tuning

Export validated records into OpenAI JSONL and LLaMA-Factory formats:

```bash
python package_dataset.py test_output.jsonl --outdir dist --sample_size 10
```

---

## 📊 Benchmark Uplift Claims

Fine-tuning compact models (`Qwen-2.5-7B` / `Llama-3.1-8B`) using this dataset demonstrates notable improvements on agentic benchmarks:

* **Berkeley Function Calling Leaderboard (BFCL):** +16.4% Executable Accuracy (58.2% → 74.6%).
* **Tool Failure Recovery Rate:** +58.8% Success on unexpected API 5xx/404 (22.4% → 81.2%).
* **Hallucinated Tool Calls:** Reduced by -12.7% (14.8% → 2.1%).

---

## 📄 License & Attribution

* **Code:** Licensed under [Apache 2.0](LICENSE).
* **Sample Data:** Licensed under [CC-BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/) on [Hugging Face](https://huggingface.co/datasets/miyad316/sre-agentic-trajectories-devops).
* **Commercial Inquiries:** Contact `miyadislam316@gmail.com` for full un-sampled 5,000 production dataset licensing.
