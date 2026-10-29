import io
import json
import os
import unittest
from unittest.mock import Mock, patch

from synapse_etl.provider import ChatPlanner, NoRedirect, ProviderError


class ProviderTests(unittest.TestCase):
    def planner(self, value):
        planner = ChatPlanner("http://127.0.0.1:11434/v1", "local-test", "test-only-placeholder")
        planner.opener = Mock()
        body = json.dumps({"choices": [{"message": {"content": json.dumps(value)}}]}).encode()
        planner.opener.open.return_value = io.BytesIO(body)
        return planner

    def test_opt_in_transport_and_json(self):
        planner = self.planner({"answer": "synthetic"})
        self.assertEqual(planner.json("Return JSON", "Synthetic input"), {"answer": "synthetic"})
        request = planner.opener.open.call_args.args[0]
        self.assertEqual(request.full_url, "http://127.0.0.1:11434/v1/chat/completions")
        self.assertEqual(request.get_header("Authorization"), "Bearer test-only-placeholder")
        self.assertEqual(json.loads(request.data)["messages"][1]["content"], "Synthetic input")

    def test_rejects_plaintext_remote_and_url_credentials(self):
        for url in [
            "http://remote.example/v1",
            "https://user:password@example.invalid/v1",
            "https://example.invalid/v1?key=secret",
            "file:///tmp/model",
            "https://example.invalid/#fragment",
        ]:
            with self.subTest(url=url), self.assertRaises(ValueError):
                ChatPlanner(url, "test")

    def test_no_model_defaults_or_ambient_credentials(self):
        # Preserve OS configuration: Windows TLS initialization requires SystemRoot.
        model_keys = {"MODEL_BASE_URL", "MODEL_NAME", "MODEL_API_KEY"}
        base_environment = {
            key: value for key, value in os.environ.items() if key not in model_keys
        }
        with patch.dict(os.environ, base_environment, clear=True), self.assertRaises(ProviderError):
            ChatPlanner.from_env()
        with patch.dict(
            os.environ,
            {
                **base_environment,
                "MODEL_BASE_URL": "http://localhost:11434/v1",
                "MODEL_NAME": "local-test",
            },
            clear=True,
        ):
            self.assertEqual(ChatPlanner.from_env().api_key, "")

    def test_rejects_nonobject_or_malformed_content(self):
        with self.assertRaises(ProviderError):
            self.planner(["not-an-object"]).json("JSON", "input")
        planner = self.planner({})
        planner.opener.open.return_value = io.BytesIO(b'{"unexpected":"envelope"}')
        with self.assertRaises(ProviderError):
            planner.json("JSON", "input")

    def test_transport_errors_do_not_leak_credentials(self):
        planner = self.planner({})
        planner.opener.open.side_effect = OSError(
            "test-only-placeholder should never reach the error"
        )
        with self.assertRaises(ProviderError) as error:
            planner.json("JSON", "input")
        self.assertNotIn("test-only-placeholder", str(error.exception))
        self.assertEqual(planner.opener.open.call_count, 1)

    def test_response_and_request_limits(self):
        planner = self.planner({})
        with self.assertRaises(ProviderError):
            planner.json("JSON", "x" * 65000)
        planner.opener.open.return_value = io.BytesIO(b"x" * 1_048_577)
        with self.assertRaises(ProviderError):
            planner.json("JSON", "input")

    def test_redirects_are_not_followed(self):
        self.assertIsNone(
            NoRedirect().redirect_request(None, None, 302, "", {}, "https://other.invalid")
        )


if __name__ == "__main__":
    unittest.main()
