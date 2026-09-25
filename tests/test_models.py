import unittest

from kimibridge.compatibility.models import normalized_models


class ModelTests(unittest.TestCase):
    def test_normalized_models_exposes_kimi_k3(self) -> None:
        result = normalized_models()

        self.assertEqual(result["object"], "list")
        self.assertEqual(result["data"][0]["id"], "kimi-k3")

    def test_normalized_models_exposes_all_kimi_models(self) -> None:
        result = normalized_models(provider="kimi")
        model_ids = {m["id"] for m in result["data"]}  # type: ignore[union-attr]

        expected_kimi_models = {
            "kimi-k3",
            "kimi-latest",
            "kimi-k1.5",
            "kimi-k2",
            "moonshot-v1-auto",
            "moonshot-v1-8k",
            "moonshot-v1-32k",
            "moonshot-v1-128k",
            "moonshot-v1-8k-vision-preview",
            "moonshot-v1-32k-vision-preview",
            "moonshot-v1-128k-vision-preview",
        }
        self.assertTrue(expected_kimi_models.issubset(model_ids))

    def test_normalized_models_for_deepseek_exposes_deepseek_chat(self) -> None:
        result = normalized_models(provider="deepseek")
        model_ids = {m["id"] for m in result["data"]}  # type: ignore[union-attr]

        self.assertIn("deepseek-chat", model_ids)
        self.assertIn("deepseek-reasoner", model_ids)
        self.assertIn("deepseek-v3-pro", model_ids)
        self.assertIn("deepseek-flash", model_ids)

    def test_normalized_models_for_openai_exposes_gpt_models(self) -> None:
        result = normalized_models(provider="openai")

        self.assertEqual(result["object"], "list")
        self.assertTrue(any(m["id"] == "gpt-4o" for m in result["data"]))  # type: ignore[union-attr]

    def test_normalized_models_for_all_combines_providers(self) -> None:
        result = normalized_models(provider="all")
        model_ids = {m["id"] for m in result["data"]}  # type: ignore[union-attr]

        self.assertIn("kimi-k3", model_ids)
        self.assertIn("deepseek-chat", model_ids)
        self.assertIn("gpt-4o", model_ids)


if __name__ == "__main__":
    unittest.main()
