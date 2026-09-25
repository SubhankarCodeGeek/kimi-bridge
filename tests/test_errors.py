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

    def test_normalizes_deepseek_422_detail_error(self) -> None:
        body = (
            b'{"detail":"Failed to deserialize the JSON body into the target type: '
            b'messages[0].role: unknown variant developer, expected one of system, user, assistant, tool, latest_reminder"}'
        )
        result = normalize_error(422, body)

        self.assertEqual(result["error"]["type"], "invalid_request_error")
        self.assertEqual(result["error"]["code"], "invalid_parameters")
        self.assertIn("unknown variant developer", result["error"]["message"])

    def test_normalizes_pydantic_validation_error(self) -> None:
        body = (
            b'{"detail":[{"loc":["messages",0,"role"],"msg":"unknown variant developer","type":"value_error"}]}'
        )
        result = normalize_error(422, body)

        self.assertEqual(result["error"]["type"], "invalid_request_error")
        self.assertEqual(result["error"]["code"], "invalid_parameters")
        self.assertIn("messages.0.role: unknown variant developer", result["error"]["message"])


if __name__ == "__main__":
    unittest.main()
