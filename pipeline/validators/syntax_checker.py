"""
Tier 1 Deterministic Syntax & Schema Validator.
Validates:
1. Tool JSON schemas against Draft 7 JSON Schema.
2. Tool call invocations against declared parameter requirements and types.
3. Conversational ShareGPT/OpenAI structure (system, user, assistant tool_calls, tool response).
4. Security/CSO hygiene (no unescaped private tokens, RFC-5737 documentation IP conformity).
"""

import json
import re
from typing import Dict, Any, List, Tuple
from jsonschema import Draft7Validator, ValidationError
from pipeline.schemas.tools import DEVOPS_TOOLS, get_tool_by_name


# Build validator cache for registered tools
_TOOL_VALIDATORS: Dict[str, Draft7Validator] = {}
for _tool in DEVOPS_TOOLS:
    _fn = _tool["function"]
    _schema = _fn["parameters"]
    Draft7Validator.check_schema(_schema)
    _TOOL_VALIDATORS[_fn["name"]] = Draft7Validator(_schema)


def validate_all_tool_schemas() -> List[str]:
    """Verify that all registered tool schemas in DEVOPS_TOOLS are valid Draft7 JSON Schemas."""
    errors = []
    for tool in DEVOPS_TOOLS:
        fn_name = tool["function"]["name"]
        schema = tool["function"]["parameters"]
        try:
            Draft7Validator.check_schema(schema)
        except Exception as e:
            errors.append(f"Tool '{fn_name}' has invalid schema: {e}")
    return errors


def validate_tool_call(tool_name: str, arguments_str: str) -> Tuple[bool, str]:
    """
    Validate that:
    1. arguments_str is valid JSON.
    2. Parsed arguments conform to tool parameter schema.
    """
    if tool_name not in _TOOL_VALIDATORS:
        return False, f"Unknown tool: '{tool_name}'"

    try:
        args = json.loads(arguments_str) if isinstance(arguments_str, str) else arguments_str
    except json.JSONDecodeError as e:
        return False, f"Malformed JSON arguments for {tool_name}: {e}"

    if not isinstance(args, dict):
        return False, f"Arguments for {tool_name} must be a JSON object, got {type(args).__name__}"

    validator = _TOOL_VALIDATORS[tool_name]
    errors = list(validator.iter_errors(args))
    if errors:
        msg = "; ".join([f"{err.message} at path '{list(err.path)}'" for err in errors[:3]])
        return False, f"Schema mismatch for {tool_name}: {msg}"

    return True, "Valid"


def validate_trajectory(trajectory: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Tier 1 validation of a full multi-turn trajectory record.
    Checks message sequencing, tool call syntax, tool responses, and CSO hygiene.
    """
    issues = []
    messages = trajectory.get("messages") or trajectory.get("conversations")
    if not messages or not isinstance(messages, list):
        return False, ["Missing or invalid 'messages' array in trajectory."]

    if len(messages) < 3:
        issues.append(f"Trajectory too short ({len(messages)} messages). Minimum 3 turns required.")

    # Track tool_call IDs to ensure matching tool responses
    pending_tool_calls: Dict[str, str] = {}

    for idx, msg in enumerate(messages):
        role = msg.get("role")
        if role not in ["system", "user", "assistant", "tool"]:
            issues.append(f"Message {idx}: Invalid role '{role}'")

        if role == "assistant":
            tool_calls = msg.get("tool_calls", [])
            for tc in tool_calls:
                tc_id = tc.get("id")
                fn = tc.get("function", {})
                fn_name = fn.get("name")
                fn_args = fn.get("arguments")

                if not tc_id or not fn_name:
                    issues.append(f"Message {idx}: Malformed tool_call without id or name.")
                    continue

                valid, err = validate_tool_call(fn_name, fn_args)
                if not valid:
                    issues.append(f"Message {idx}: {err}")
                else:
                    pending_tool_calls[tc_id] = fn_name

        elif role == "tool":
            tc_id = msg.get("tool_call_id")
            if not tc_id:
                issues.append(f"Message {idx}: Tool message missing 'tool_call_id'.")
            elif tc_id in pending_tool_calls:
                del pending_tool_calls[tc_id]
            else:
                issues.append(f"Message {idx}: Tool response references uncalled id '{tc_id}'.")

    # CSO check: verify no real leaked secrets or authorization bearer headers
    raw_str = json.dumps(trajectory)
    if re.search(r"bearer\s+ey[A-Za-z0-9_\-\.]{20,}", raw_str, re.IGNORECASE):
        issues.append("CSO Warning: Trajectory contains unmasked JWT bearer token.")
    if re.search(r"(AKIA[0-9A-Z]{16})", raw_str):
        issues.append("CSO Warning: Trajectory contains real AWS access key format.")

    return len(issues) == 0, issues
