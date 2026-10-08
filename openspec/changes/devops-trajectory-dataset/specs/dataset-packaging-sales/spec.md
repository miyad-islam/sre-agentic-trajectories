# Spec Delta: Dataset Packaging and Sales

## Purpose
Formats filtered trajectories into standard conversational tool-use JSONL, compiles the technical QA report, and prepares distribution assets for Hugging Face and commercial storefronts.

## ADDED Requirements

### Requirement: Standardized Conversational JSONL Formatting
The system SHALL export the validated dataset in OpenAI/ShareGPT tool-use conversational format with separate role definitions (system, user, assistant tool_calls, tool role responses).

#### Scenario: Industry Standard Schema Export
- **WHEN** the final dataset is written to disk
- **THEN** every record validates against the standard conversational function calling schema accepted by popular fine-tuning frameworks (Axolotl, LLaMA-Factory, Unsloth)

### Requirement: Technical QA Audit Report
The system SHALL generate an enterprise audit document detailing methodology, model specifications, rejection rates, schema dictionaries, and benchmark metrics.

#### Scenario: QA Documentation Generation
- **WHEN** packaging is finalized
- **THEN** a comprehensive summary report is compiled to serve as technical proof for enterprise buyers

### Requirement: Lead Magnet and Sales Collateral Preparation
The system SHALL generate a stratified 2,000-row public preview sample for Hugging Face under non-commercial licensing alongside commercial licensing metadata.

#### Scenario: Distribution Asset Generation
- **WHEN** the distribution package is generated
- **THEN** both the 2,000-row public sample repository and the commercial release package are ready for deployment
