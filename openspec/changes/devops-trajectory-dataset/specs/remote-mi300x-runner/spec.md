# Spec Delta: Remote MI300X Runner

## Purpose
Orchestrates high-throughput vLLM serving on DigitalOcean AMD Instinct MI300X droplets, runs saturation batching for Qwen 2.5 72B Instruct, and safeguards credits with automated teardown.

## ADDED Requirements

### Requirement: ROCm vLLM Serving on AMD MI300X
The system SHALL deploy the official AMD ROCm vLLM container exposing an OpenAI-compatible API on the remote MI300X GPU instance.

#### Scenario: vLLM Server Readiness
- **WHEN** the container is launched with ROCm devices mapped
- **THEN** vLLM initializes Qwen 2.5 72B Instruct across 192GB VRAM and returns HTTP 200 on health checks

### Requirement: High-Concurrency Batch Generation Runner
The system SHALL execute concurrent async generation queries against the vLLM server to maximize GPU memory utilization and token throughput.

#### Scenario: Throughput Saturation
- **WHEN** batch trajectories are generated
- **THEN** the runner maintains continuous concurrent requests and streams intermediate outputs to disk at defined checkpoint intervals

### Requirement: Credit Safeguard and Automated Teardown
The system SHALL trigger automated workload termination and instance destruction upon generation completion or fatal error.

#### Scenario: Automated Teardown on Completion
- **WHEN** all target trajectories are generated and synced
- **THEN** the system executes the termination routine to prevent idle droplet billing
