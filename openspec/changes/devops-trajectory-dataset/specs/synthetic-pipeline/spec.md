# Spec Delta: Synthetic Pipeline

## Purpose
Provides the scenario generators, structured tool schema registry, and multi-turn conversational simulator for generating realistic SRE and DevOps incident remediation dialogues.

## ADDED Requirements

### Requirement: Structured DevOps Tool Registry
The system SHALL provide a validated schema catalog covering Kubernetes (`kubectl`), Linux OS diagnostics, CloudWatch/Datadog metrics, and Postgres diagnostics.

#### Scenario: Tool Schema Validation
- **WHEN** tool definitions are registered into the pipeline
- **THEN** every tool must strictly comply with valid JSON Schema / OpenAPI 3.0 specifications including parameter types, required fields, and descriptions

### Requirement: Incident Scenario Generation
The system SHALL generate diverse incident seed scenarios spanning pod crashes, memory leaks, high latency spikes, and database deadlocks.

#### Scenario: Seed Generation Diversity
- **WHEN** the generator produces incident scenarios
- **THEN** it generates a balanced distribution of infrastructure failure types across container, OS, network, and database layers

### Requirement: Multi-Turn Trajectory Simulation with Error Injection
The system SHALL simulate agent reasoning, tool call generation, environment response execution, and self-healing turns with 20% to 30% realistic error conditions.

#### Scenario: Self-Healing on Tool Failure
- **WHEN** a simulated tool execution returns an error (e.g., 404, PodNotFound, or PermissionDenied)
- **THEN** the simulated agent trajectory MUST inspect the failure reason and execute an alternative remediation turn rather than halting
