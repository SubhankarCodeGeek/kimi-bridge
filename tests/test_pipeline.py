import unittest

from kimibridge.compatibility.pipeline import normalize_request


class PipelineTests(unittest.TestCase):
    def test_compatible_mode_normalizes_roles_and_parameters(self) -> None:
        payload = {
            "model": "kimi-k3",
            "parallel_tool_calls": True,
            "store": True,
            "messages": [{"role": "developer", "content": "Be concise."}],
        }

        result = normalize_request(payload)

        self.assertEqual(result["messages"][0]["role"], "system")
        self.assertNotIn("parallel_tool_calls", result)
        self.assertNotIn("store", result)
        self.assertIn("parallel_tool_calls", payload)

    def test_strict_mode_preserves_request_shape(self) -> None:
        payload = {
            "parallel_tool_calls": True,
            "messages": [{"role": "developer", "content": "Stay strict."}],
        }

        result = normalize_request(payload, mode="strict")

        self.assertEqual(result["messages"][0]["role"], "system")
        self.assertIn("parallel_tool_calls", result)

    def test_passthrough_mode_preserves_request_shape_and_roles(self) -> None:
        payload = {
            "parallel_tool_calls": True,
            "messages": [{"role": "developer", "content": "Stay untouched."}],
        }

        result = normalize_request(payload, mode="passthrough")

        self.assertEqual(result["messages"][0]["role"], "developer")
        self.assertIn("parallel_tool_calls", result)

    def test_unknown_mode_raises(self) -> None:
        with self.assertRaises(ValueError):
            normalize_request({}, mode="mystery")


if __name__ == "__main__":
    unittest.main()
