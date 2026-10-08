# Tasks

## 1. Local Schema & Simulation Pipeline

- [x] 1.1 Define structured JSON/OpenAPI tool schemas for Kubernetes (`kubectl`), Linux OS diagnostics, Cloud Metrics, and Postgres, and verify valid syntax with `jsonschema`
- [x] 1.2 Implement the incident scenario generator covering pod crashes, memory leaks, latency spikes, and DB deadlocks, and verify balanced scenario distribution
- [x] 1.3 Build the multi-turn conversational simulator with 25% error-injection / self-healing turns and verify locally on 5 mock samples

## 2. Remote MI300X Infrastructure & vLLM Orchestration

- [x] 2.1 Prepare DigitalOcean droplet setup script running official `rocm/vllm` Docker image for Qwen 2.5 72B Instruct and verify health check endpoint
- [x] 2.2 Implement the high-concurrency batch runner script with streaming checkpoints to local disk / cloud storage and verify batch saturation
- [x] 2.3 Build the automated watchdog and teardown routine using the DigitalOcean API (`doctl` or REST) to guarantee zero credit bleed upon completion

## 3. Two-Tier Quality Filtering & LLM-as-a-Judge

- [x] 3.1 Implement Tier 1 deterministic JSON parser and schema validator, and verify rejection of malformed tool calls without spending LLM tokens
- [x] 3.2 Implement Tier 2 LLM-as-a-Judge evaluation script with 1–5 scoring rubric, filtering out rows scoring below 4, and verify scoring outputs
- [x] 3.3 Implement semantic de-duplication and scenario balancing, and verify dataset entropy metrics

## 4. Packaging, QA Audit Report & Commercial Launch

- [x] 4.1 Export filtered trajectories into standard conversational function-calling JSONL compatible with Axolotl and LLaMA-Factory
- [x] 4.2 Compile the 2-page technical QA audit report documenting rejection rate, model provenance, schema dictionary, and benchmark claims
- [x] 4.3 Package the 2,000-row public sample repository for Hugging Face (CC-BY-NC) and prepare commercial listing collateral for Gumroad/LemonSqueezy
