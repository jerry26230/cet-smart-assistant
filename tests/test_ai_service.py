from dataclasses import asdict, replace
from io import BytesIO
import json
import unittest
from unittest.mock import patch, MagicMock
from urllib.error import HTTPError, URLError
import test_profile

from cet_core.ai_service import AIError, AISettings, NoRedirect, build_payload, generate_guide, parse_response
from cet_core.word_guidance import BUILTIN_GUIDES


def response_bytes(guide=None, finish="stop"):
    return json.dumps({"choices": [{"finish_reason": finish, "message": {"content": json.dumps(asdict(guide or BUILTIN_GUIDES["good"]))}}]}).encode()


class AIServiceTests(unittest.TestCase):
    def setUp(self):
        self.settings = AISettings("https://api.example.test/v1/chat/completions", "test-model", "test-secret")

    def test_settings_no_secret_in_repr_and_bad_urls_rejected(self):
        self.assertNotIn("test-secret", repr(self.settings))
        for url in ("http://api.example.test/chat/completions", "https://key@host/chat/completions", "https://host/chat/completions?key=x", "https://host/responses", "https://host:bad/chat/completions"):
            with self.assertRaises(ValueError):
                replace(self.settings, endpoint=url).validate()

    def test_payload_minimization_and_token_modes(self):
        for parameter in ("max_completion_tokens", "max_tokens"):
            payload = build_payload("good", replace(self.settings, token_parameter=parameter))
            self.assertEqual(payload[parameter], 1800)
            self.assertEqual(json.loads(payload["messages"][1]["content"]), {"word": "good"})
            self.assertNotIn("test-secret", json.dumps(payload))
            self.assertNotIn("profile", payload)

    def test_success_request_uses_bearer_and_timeout(self):
        stream = MagicMock()
        stream.__enter__.return_value.read.return_value = response_bytes()
        opener = MagicMock()
        opener.open.return_value = stream
        with patch("cet_core.ai_service.build_opener", return_value=opener):
            self.assertEqual(generate_guide("good", self.settings), BUILTIN_GUIDES["good"])
        request = opener.open.call_args.args[0]
        self.assertEqual(request.headers["Authorization"], "Bearer test-secret")
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(opener.open.call_args.kwargs["timeout"], 30)
        self.assertEqual(stream.__enter__.return_value.read.call_args.args, (131073,))

    def test_http_errors_do_not_leak_response_or_retry(self):
        for status in (400, 401, 403, 429, 500):
            opener = MagicMock()
            opener.open.side_effect = HTTPError(self.settings.endpoint, status, "test-secret", {}, BytesIO(b'test-secret'))
            with patch("cet_core.ai_service.build_opener", return_value=opener), self.assertRaises(AIError) as caught:
                generate_guide("good", self.settings)
            self.assertNotIn("test-secret", str(caught.exception))
            self.assertEqual(opener.open.call_count, 1)

    def test_timeout_and_oversized_response(self):
        opener = MagicMock()
        for error in (TimeoutError("test-secret"), URLError("test-secret")):
            opener.open.side_effect = error
            with patch("cet_core.ai_service.build_opener", return_value=opener), self.assertRaises(AIError) as caught:
                generate_guide("good", self.settings)
            self.assertNotIn("test-secret", str(caught.exception))
        opener.open.side_effect = None
        opener.open.return_value.__enter__.return_value.read.return_value = b"x" * 131073
        with patch("cet_core.ai_service.build_opener", return_value=opener), self.assertRaises(AIError):
            generate_guide("good", self.settings)

    def test_malformed_refused_and_truncated_response(self):
        for raw in (b"not json", b"{}", b'{"choices":[]}', b'{"choices":[{"finish_reason":"stop","message":{"content":null}}]}', response_bytes(finish="length")):
            with self.assertRaises(AIError):
                parse_response(raw)

    def test_redirect_never_forwards_credentials(self):
        with self.assertRaises(AIError):
            NoRedirect().redirect_request(None, None, 307, "redirect", {}, "https://other.test")
