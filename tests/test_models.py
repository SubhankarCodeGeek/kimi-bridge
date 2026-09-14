import unittest

from kimibridge.compatibility.models import normalized_models


class ModelTests(unittest.TestCase):
    def test_normalized_models_exposes_kimi_k3(self) -> None:
        result = normalized_models()

        self.assertEqual(result["object"], "list")
        self.assertEqual(result["data"][0]["id"], "kimi-k3")


if __name__ == "__main__":
    unittest.main()
