# Design: DevOps / SRE Incident Remediation Trajectory Dataset

## Context
See `proposal.md` for background motivation. Development occurs locally on Windows (PowerShell), orchestrating execution on a remote DigitalOcean Droplet equipped with 1x AMD Instinct MI300X GPU (192GB VRAM). The user has a finite $300 credit balance, making compute efficiency, throughput saturation, and automated lifecycle management critical.

## Goals / Non-Goals

**Goals:**
- Provide a robust local simulation architecture (schema definitions, seed generators, dialogue templates) tested with 0 GPU credit cost.
- Deploy an optimized vLLM server on DigitalOcean MI300X using official ROCm containers.
- Generate 50,000+ multi-turn incident remediation trajectories featuring multi-step tool calls, realistic failure injection, and self-healing turns.
- Implement Tier 1 deterministic schema validation and Tier 2 LLM-as-a-Judge scoring to ensure enterprise quality.
- Package the dataset into industry-standard function-calling JSONL accompanied by technical QA documentation and distribution collateral.

**Non-Goals:**
- Training or fine-tuning foundation models in this change (focus is strictly dataset generation, filtering, and packaging).
- Real-time interaction with physical production cloud infrastructure (all environment outputs are strictly simulated within sandbox parameters).
- Multi-node distributed training.

## Decisions

### Decision 1: Base Generation Model — Qwen 2.5 72B Instruct
- **Choice**: `Qwen/Qwen2.5-72B-Instruct` in native BF16 precision.
- **Rationale**: Weighs ~144GB in BF16, leaving ~48GB for vLLM KV-cache on the MI300X (192GB). It has state-of-the-art open-weights coding, JSON generation, and tool-use simulation performance.
- **Alternatives Considered**: 
  - *DeepSeek-V3*: 671B MoE model requires 8x MI300X or 8x H100s (>650GB VRAM); impossible on a single droplet.
  - *Llama 3.3 70B*: High quality, but Qwen 2.5 72B shows superior native function-calling adherence and structured JSON generation.

### Decision 2: Serving Engine — Official ROCm vLLM Docker
- **Choice**: `rocm/vllm:latest` via Docker with `--network=host` and `--device=/dev/kfd --device=/dev/dri`.
- **Rationale**: Pre-compiled with ROCm kernels and PagedAttention optimizations for AMD Instinct architectures, avoiding fragile manual ROCm dependency compilation.
- **Alternatives Considered**: 
  - *Hugging Face TGI*: Slower batching saturation on ROCm compared to vLLM.
  - *Native PyTorch script*: Lacks continuous batching and PagedAttention, resulting in ~5x lower token throughput.

### Decision 3: Two-Tier Filtering Architecture
- **Choice**: Tier 1 Deterministic Validator (`json.loads` + `jsonschema` + regex) followed by Tier 2 LLM-as-a-Judge.
- **Rationale**: Approximately 15–20% of synthetic tool calls produce minor syntax errors or invalid argument types. Weeding these out locally or deterministically saves millions of tokens from the LLM judge pass.
- **Alternatives Considered**: 
  - *Pure LLM Judge*: Unnecessarily burns GPU tokens reading malformed JSON.
  - *Pure Heuristics*: Misses nuanced hallucinated logic or implausible SRE explanations.

### Decision 4: Safe Teardown and Credit Protection
- **Choice**: Trajectory streaming with per-batch checkpointing to local disk / cloud object store, followed by automated droplet termination via DigitalOcean API / CLI (`doctl compute droplet delete <id> --force`).
- **Rationale**: DigitalOcean charges for reserved droplets even when powered off. Complete droplet deletion is required to stop credit consumption immediately.

## Risks / Trade-offs

- **[Risk: Droplet Idle Credit Bleed]** → **Mitigation**: Dedicated watchdog timer script and API-based auto-destruction on completion or prolonged idle (>30 minutes).
- **[Risk: Repetitive Trajectory Patterns]** → **Mitigation**: Stratified seed generation spanning 4 infrastructure domains (Kubernetes, Linux OS, Cloud Metrics, Postgres) with randomized error permutations.
- **[Risk: ROCm Driver/Image Incompatibility]** → **Mitigation**: Use tested DigitalOcean GPU droplet base image with verified ROCm 6.x compatibility and official AMD vLLM container tags.
- **[Risk: Network Disconnection during Generation]** → **Mitigation**: Run remote generation jobs inside detached sessions (`tmux` or background systemd service) with periodic checkpoint saves.
