import unittest

from kimibridge.compatibility.errors import normalize_error


class ErrorTests(unittest.TestCase):
    def test_normalizes_openai_like_error(self) -> None:
        result = normalize_error(
            401,
            b'{"error":{"message":"Bad key","type":"auth","code":"invalid_key"}}',
        )

        self.assertEqual(result["error"]["message"], "Bad key")
        self.assertEqual(result["error"]["type"], "auth")
        self.assertEqual(result["error"]["code"], "invalid_key")

    def test_normalizes_plain_message_error(self) -> None:
        result = normalize_error(429, b'{"message":"Rate limited"}')

        self.assertEqual(result["error"]["message"], "Rate limited")
        self.assertEqual(result["error"]["code"], "upstream_http_429")

    def test_handles_non_json_body(self) -> None:
        result = normalize_error(500, b"internal server error")

        self.assertEqual(result["error"]["message"], "Upstream error")
        self.assertEqual(result["error"]["code"], "upstream_http_500")


if __name__ == "__main__":
    unittest.main()
