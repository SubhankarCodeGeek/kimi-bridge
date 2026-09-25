import unittest

from kimibridge.compatibility.profiles import DEEPSEEK_PROFILE, KIMI_PROFILE, OPENAI_PROFILE
from kimibridge.compatibility.roles import normalize_roles


class RoleTests(unittest.TestCase):
    def test_developer_role_becomes_system_in_compatible_mode(self) -> None:
        payload = {
            "messages": [
                {"role": "developer", "content": "Follow project rules."},
                {"role": "user", "content": "Hello"},
            ]
        }

        result = normalize_roles(payload)

        self.assertEqual(result["messages"][0]["role"], "system")
        self.assertEqual(payload["messages"][0]["role"], "developer")

    def test_developer_role_normalized_for_deepseek(self) -> None:
        payload = {
            "messages": [
                {"role": "developer", "content": "You are an Android expert."},
                {"role": "user", "content": "Explain this code."},
            ]
        }

        result = normalize_roles(payload, profile=DEEPSEEK_PROFILE)

        self.assertEqual(result["messages"][0]["role"], "system")
        self.assertEqual(payload["messages"][0]["role"], "developer")

    def test_developer_role_preserved_for_openai(self) -> None:
        payload = {
            "messages": [
                {"role": "developer", "content": "You are OpenAI o1."},
                {"role": "user", "content": "Solve problem."},
            ]
        }

        result = normalize_roles(payload, profile=OPENAI_PROFILE)

        self.assertEqual(result["messages"][0]["role"], "developer")

    def test_passthrough_mode_keeps_developer_role(self) -> None:
        payload = {"messages": [{"role": "developer", "content": "Stay unchanged."}]}

        result = normalize_roles(payload, mode="passthrough")

        self.assertEqual(result["messages"][0]["role"], "developer")


if __name__ == "__main__":
    unittest.main()
