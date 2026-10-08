# Spec Delta: Quality Filter Judge

## Purpose
Validates syntactic correctness, filters malformed tool calls deterministically, and scores SRE reasoning quality using an LLM-as-a-Judge pipeline to guarantee enterprise grade quality.

## ADDED Requirements

### Requirement: Tier 1 Deterministic Syntactic Validation
The system SHALL validate all tool calls in trajectories against strict JSON parsing and schema validation rules without invoking LLM tokens.

#### Scenario: Malformed Tool Rejection
- **WHEN** an agent trajectory produces invalid JSON or arguments that violate schema constraints
- **THEN** the validator immediately discards the trajectory without spending LLM judge tokens

### Requirement: Tier 2 LLM-as-a-Judge Evaluation
The system SHALL evaluate surviving trajectories across tool selection correctness, realistic environment coherence, and self-healing logic using Qwen 2.5 72B.

#### Scenario: Quality Scoring Threshold
- **WHEN** the judge scores a trajectory on a 1 to 5 rubric
- **THEN** trajectories scoring lower than 4 MUST be pruned from the final commercial release

### Requirement: De-duplication and Diversity Balancing
The system SHALL identify and eliminate redundant incident scenarios to ensure high entropy and scenario diversity across the dataset.

#### Scenario: Semantic De-duplication
- **WHEN** multiple trajectories exhibit near-identical root causes and tool chains
- **THEN** redundant instances are pruned to preserve diversity
