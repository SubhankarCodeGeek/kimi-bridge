import unittest

from kimibridge.compatibility.profiles import (
    DEEPSEEK_PROFILE,
    KIMI_PROFILE,
    OPENAI_PROFILE,
    detect_provider,
    get_provider_profile,
)


class ProfileTests(unittest.TestCase):
    def test_kimi_profile_configuration(self) -> None:
        self.assertEqual(KIMI_PROFILE.name, "kimi")
        self.assertFalse(KIMI_PROFILE.supports_developer_role)
        self.assertEqual(KIMI_PROFILE.developer_role_target, "system")
        self.assertIn("parallel_tool_calls", KIMI_PROFILE.unsupported_parameters)
        self.assertIn("store", KIMI_PROFILE.unsupported_parameters)

    def test_deepseek_profile_configuration(self) -> None:
        self.assertEqual(DEEPSEEK_PROFILE.name, "deepseek")
        self.assertFalse(DEEPSEEK_PROFILE.supports_developer_role)
        self.assertEqual(DEEPSEEK_PROFILE.developer_role_target, "system")
        self.assertIn("latest_reminder", DEEPSEEK_PROFILE.supported_roles)
        self.assertTrue(any(m["id"] == "deepseek-chat" for m in DEEPSEEK_PROFILE.default_models))

    def test_openai_profile_configuration(self) -> None:
        self.assertEqual(OPENAI_PROFILE.name, "openai")
        self.assertTrue(OPENAI_PROFILE.supports_developer_role)
        self.assertEqual(OPENAI_PROFILE.developer_role_target, "developer")

    def test_detect_provider_by_model(self) -> None:
        self.assertEqual(detect_provider(model="deepseek-chat").name, "deepseek")
        self.assertEqual(detect_provider(model="deepseek-reasoner").name, "deepseek")
        self.assertEqual(detect_provider(model="kimi-k3").name, "kimi")
        self.assertEqual(detect_provider(model="moonshot-v1-8k").name, "kimi")
        self.assertEqual(detect_provider(model="gpt-4o").name, "openai")
        self.assertEqual(detect_provider(model="o1-preview").name, "openai")

    def test_detect_provider_by_base_url(self) -> None:
        self.assertEqual(detect_provider(base_url="https://api.deepseek.com").name, "deepseek")
        self.assertEqual(detect_provider(base_url="https://api.moonshot.ai/v1").name, "kimi")
        self.assertEqual(detect_provider(base_url="https://api.openai.com/v1").name, "openai")

    def test_detect_provider_by_header(self) -> None:
        self.assertEqual(
            detect_provider(headers={"x-bridge-provider": "deepseek"}).name,
            "deepseek",
        )
        self.assertEqual(
            detect_provider(headers={"x-provider": "kimi"}).name,
            "kimi",
        )

    def test_detect_provider_by_config(self) -> None:
        self.assertEqual(
            detect_provider(configured_provider="deepseek").name,
            "deepseek",
        )
        self.assertEqual(
            detect_provider(configured_provider="kimi").name,
            "kimi",
        )

    def test_detect_provider_prioritizes_deepseek_base_url_over_default_kimi_config(self) -> None:
        self.assertEqual(
            detect_provider(base_url="https://api.deepseek.com", configured_provider="kimi").name,
            "deepseek",
        )

    def test_detect_provider_prioritizes_deepseek_model_over_default_kimi_config(self) -> None:
        self.assertEqual(
            detect_provider(model="deepseek-v3-pro", configured_provider="kimi").name,
            "deepseek",
        )

    def test_get_provider_profile_fallback(self) -> None:
        self.assertEqual(get_provider_profile("unknown-provider").name, "generic")
        self.assertEqual(get_provider_profile(None).name, "kimi")


if __name__ == "__main__":
    unittest.main()
