import unittest
import json
from pipeline.validators.syntax_checker import validate_tool_call, validate_trajectory


class TestDeterministicValidation(unittest.TestCase):

    def test_valid_tool_call(self):
        valid, msg = validate_tool_call("k8s_describe_pod", json.dumps({"namespace": "production", "pod_name": "api-99"}))
        self.assertTrue(valid, msg)

    def test_missing_required_parameter(self):
        valid, msg = validate_tool_call("k8s_describe_pod", json.dumps({"namespace": "production"}))
        self.assertFalse(valid)
        self.assertIn("pod_name", msg)

    def test_invalid_parameter_type(self):
        valid, msg = validate_tool_call("k8s_get_logs", json.dumps({"namespace": "prod", "pod_name": "x", "tail_lines": "not-an-integer"}))
        self.assertFalse(valid)

    def test_malformed_json_args(self):
        valid, msg = validate_tool_call("k8s_describe_pod", "{unclosed json")
        self.assertFalse(valid)
        self.assertIn("Malformed JSON", msg)

    def test_unknown_tool(self):
        valid, msg = validate_tool_call("non_existent_tool", "{}")
        self.assertFalse(valid)
        self.assertIn("Unknown tool", msg)


if __name__ == "__main__":
    unittest.main()
