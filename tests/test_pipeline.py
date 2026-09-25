import unittest

from kimibridge.compatibility.pipeline import normalize_request
from kimibridge.compatibility.profiles import DEEPSEEK_PROFILE, OPENAI_PROFILE


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

    def test_pipeline_auto_detects_deepseek_and_normalizes_roles(self) -> None:
        payload = {
            "model": "deepseek-chat",
            "messages": [{"role": "developer", "content": "You are an Android expert."}],
        }

        result = normalize_request(payload)

        self.assertEqual(result["messages"][0]["role"], "system")

    def test_pipeline_preserves_developer_role_for_openai(self) -> None:
        payload = {
            "model": "gpt-4o",
            "messages": [{"role": "developer", "content": "You are OpenAI model."}],
        }

        result = normalize_request(payload)

        self.assertEqual(result["messages"][0]["role"], "developer")

    def test_pipeline_with_explicit_provider_argument(self) -> None:
        payload = {
            "model": "custom-model",
            "messages": [{"role": "developer", "content": "Custom assistant."}],
        }

        result_deepseek = normalize_request(payload, provider=DEEPSEEK_PROFILE)
        self.assertEqual(result_deepseek["messages"][0]["role"], "system")

        result_openai = normalize_request(payload, provider=OPENAI_PROFILE)
        self.assertEqual(result_openai["messages"][0]["role"], "developer")

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
