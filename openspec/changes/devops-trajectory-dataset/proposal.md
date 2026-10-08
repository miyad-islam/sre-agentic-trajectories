# Proposal: DevOps / SRE Incident Remediation Trajectory Dataset

## Why
AI agent builders and enterprise labs urgently need high-fidelity, multi-turn agentic trajectories to train and fine-tune lightweight open-weight models (Llama 3.2 3B, Qwen 2.5 7B) on practical tool use. Most existing synthetic datasets focus on generic APIs (weather, calculator) or single-turn happy-path queries, leaving models brittle when facing complex incident triage, multi-step dependencies, and error recovery. 

By leveraging an AMD Instinct MI300X (192GB VRAM) on DigitalOcean running Qwen 2.5 72B Instruct, we can generate a commercially viable 50,000+ row enterprise-grade SRE trajectory dataset with strict JSON tool schemas, deterministic verification, and LLM-as-a-judge filtering within the user's compute credit budget.

## What Changes
- Create a standardized DevOps/SRE tool repository containing OpenAPI/JSON schemas for Kubernetes (`kubectl`), Linux system diagnostics, cloud metrics (CloudWatch/Datadog), and database diagnostics (Postgres).
- Implement a local multi-agent simulation pipeline that pairs incident scenarios with agent reasoning, tool call generation, realistic simulated environment responses (including 20-30% error states), and self-healing turns.
- Provide deployment configurations and scripts for the DigitalOcean AMD MI300X droplet (vLLM ROCm container, saturation batching, automated remote task execution, and automated resource teardown).
- Implement a two-tiered validation and filtering pipeline: Tier 1 deterministic JSON/schema validation and Tier 2 LLM-as-a-Judge evaluation for SRE reasoning fidelity.
- Package the final dataset into standard JSONL format accompanied by a QA audit report, 2,000-row Hugging Face lead magnet, and commercial distribution collateral.

## Capabilities

### New Capabilities
- `synthetic-pipeline`: Core tool definitions, multi-turn dialogue generator, incident scenario seeds, and environment simulation logic.
- `remote-mi300x-runner`: DigitalOcean MI300X vLLM deployment orchestration, batch execution runner, and credit-preserving auto-shutdown script.
- `quality-filter-judge`: Deterministic syntactic schema validator and LLM-as-a-judge scoring filter for filtering out low-quality or hallucinated trajectories.
- `dataset-packaging-sales`: Output JSONL formatting, statistical QA reporting, Hugging Face sample repository preparation, and commercial monetization setup.

### Modified Capabilities
*(None - Greenfield project)*

## Impact
- **Compute Resources**: DigitalOcean GPU Droplet (1x AMD Instinct MI300X 192GB) utilized via official ROCm vLLM Docker image.
- **Local Workspace**: Generation configurations, tool schema registries, prompt templates, and evaluation scripts stored locally in `c:/Users/Dark_Knight/Desktop/AMD_DROPLET`.
- **Target Deliverable**: Commercial enterprise-ready SRE tool-use dataset (JSONL), public 2k sample (Hugging Face), and technical QA documentation.
