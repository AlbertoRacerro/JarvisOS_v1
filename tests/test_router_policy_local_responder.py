import copy
import json
import math
import sys
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import Mock, patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import router_policy_decision_probe as decision_probe  # noqa: E402
import router_policy_local_responder as responder  # noqa: E402
import router_policy_local_route_probe as local_route  # noqa: E402


FIXTURE_PATH = ROOT / "tests/fixtures/router_policy/base_router_policy_fixture.json"
NOW = "2026-06-24T12:00:00+00:00"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class RecordingClient:
    def __init__(self, response=None, exc=None):
        self.calls = []
        self.response = {"response": "mock local response"} if response is None else response
        self.exc = exc

    def __call__(self, endpoint: str, payload: dict, timeout_s: float) -> dict:
        self.calls.append({"endpoint": endpoint, "payload": payload, "timeout_s": timeout_s})
        if self.exc is not None:
            raise self.exc
        return self.response


class RouterPolicyLocalResponderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = load_json(FIXTURE_PATH)

    def base_input(self):
        return copy.deepcopy(self.fixture["input"])

    def make_high_complexity_public(self):
        input_obj = self.base_input()
        input_obj["user_policy"]["external_routing_enabled"] = True
        input_obj["user_policy"]["external_requires_confirmation"] = True
        input_obj["provider_policy"] = {
            "allowed_provider_tiers": ["LOCAL_ONLY", "LOCAL_FAST", "SCIENTIFIC_MEDIUM"],
            "blocked_provider_tiers": ["FRONTIER"],
        }
        input_obj["budget_policy"]["max_tier"] = "SCIENTIFIC_MEDIUM"
        input_obj["phase_a_signals"]["external_provider_allowed"] = True
        input_obj["phase_a_signals"]["sensitivity_bucket_proposal"] = "public"
        input_obj["router_hint"].update(
            {
                "task_type": "analysis",
                "complexity": "high",
                "domain": "scientific",
                "needs_scientific_depth": True,
                "needs_reasoning": True,
            }
        )
        return input_obj

    def test_a4_001_build_local_responder_returns_callable_without_client_call(self):
        client = RecordingClient()
        local = responder.build_local_responder(client=client)
        self.assertTrue(callable(local))
        self.assertEqual([], client.calls)
        self.assertEqual("mock local response", local("hello"))
        self.assertEqual(1, len(client.calls))

    def test_a4_002_localhost_endpoints_allowed(self):
        for endpoint in (
            "http://127.0.0.1:11434/api/generate",
            "http://localhost:11434/api/generate",
            "http://[::1]:11434/api/generate",
        ):
            with self.subTest(endpoint=endpoint):
                local = responder.build_local_responder(endpoint=endpoint, client=RecordingClient())
                self.assertTrue(callable(local))

    def test_a4_003_non_localhost_endpoints_rejected(self):
        endpoints = [
            "https://api.openai.com/v1/chat/completions",
            "http://192.168.1.10:11434/api/generate",
            "http://10.0.0.5:11434/api/generate",
            "http://example.com:11434/api/generate",
            "http://localhost.evil.com:11434/api/generate",
            "http://evil.com/api/generate?x=localhost",
            "http://127.0.0.1:11434/api/generate/",
            "http://user:pass@localhost:11434/api/generate",
        ]
        for endpoint in endpoints:
            with self.subTest(endpoint=endpoint):
                with self.assertRaises(responder.LocalResponderPolicyError):
                    responder.build_local_responder(endpoint=endpoint, client=RecordingClient())

    def test_a4_004_deterministic_bounded_payload(self):
        client = RecordingClient()
        text = responder.call_local_ollama_generate(
            "exact prompt",
            model="gemma3:4b",
            endpoint=responder.DEFAULT_ENDPOINT,
            timeout_s=3,
            temperature=0.0,
            max_prompt_chars=100,
            max_output_chars=100,
            client=client,
        )
        self.assertEqual("mock local response", text)
        payload = client.calls[0]["payload"]
        self.assertEqual("gemma3:4b", payload["model"])
        self.assertEqual("exact prompt", payload["prompt"])
        self.assertFalse(payload["stream"])
        self.assertEqual({"temperature": 0}, payload["options"])
        self.assertNotIn("tools", payload)
        self.assertNotIn("messages", payload)
        self.assertNotIn("decision", payload)
        self.assertNotIn("memory", payload)
        self.assertNotIn("retrieval", payload)

    def test_a4_005_prompt_too_long_fails_before_client_call(self):
        client = RecordingClient()
        with self.assertRaises(responder.LocalResponderPolicyError):
            responder.call_local_ollama_generate(
                "too long",
                model="gemma3:4b",
                endpoint=responder.DEFAULT_ENDPOINT,
                timeout_s=3,
                temperature=0.0,
                max_prompt_chars=3,
                max_output_chars=100,
                client=client,
            )
        self.assertEqual([], client.calls)

    def test_a4_006_output_text_bounded(self):
        client = RecordingClient(response={"response": "abcdef"})
        text = responder.call_local_ollama_generate(
            "prompt",
            model="gemma3:4b",
            endpoint=responder.DEFAULT_ENDPOINT,
            timeout_s=3,
            temperature=0.0,
            max_prompt_chars=100,
            max_output_chars=3,
            client=client,
        )
        self.assertEqual("abc", text)

    def test_a4_007_malformed_response_fails_safely(self):
        for response in ({}, {"response": 123}, []):
            with self.subTest(response=response):
                client = RecordingClient(response=response)
                with self.assertRaises(responder.LocalResponderResponseError):
                    responder.call_local_ollama_generate(
                        "prompt",
                        model="gemma3:4b",
                        endpoint=responder.DEFAULT_ENDPOINT,
                        timeout_s=3,
                        temperature=0.0,
                        max_prompt_chars=100,
                        max_output_chars=100,
                        client=client,
                    )

    def test_a4_008_transport_non_json_non_2xx_failures_fail_safely(self):
        client = RecordingClient(exc=responder.LocalResponderTransportError("boom"))
        with self.assertRaises(responder.LocalResponderTransportError):
            responder.call_local_ollama_generate(
                "prompt",
                model="gemma3:4b",
                endpoint=responder.DEFAULT_ENDPOINT,
                timeout_s=3,
                temperature=0.0,
                max_prompt_chars=100,
                max_output_chars=100,
                client=client,
            )

        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("down")):
            with self.assertRaises(responder.LocalResponderTransportError):
                responder._stdlib_json_post_client(responder.DEFAULT_ENDPOINT, {}, 1)

        class BadJsonResponse:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def read(self):
                return b"{not json"

            def getcode(self):
                return self.status

        with patch("urllib.request.urlopen", return_value=BadJsonResponse()):
            with self.assertRaises(responder.LocalResponderResponseError):
                responder._stdlib_json_post_client(responder.DEFAULT_ENDPOINT, {}, 1)

        class Non2xxResponse(BadJsonResponse):
            status = 500

            def read(self):
                return b'{"response": "bad"}'

        with patch("urllib.request.urlopen", return_value=Non2xxResponse()):
            with self.assertRaises(responder.LocalResponderTransportError):
                responder._stdlib_json_post_client(responder.DEFAULT_ENDPOINT, {}, 1)

    def test_a4_009_local_route_probe_default_remains_offline_safe(self):
        result = local_route.run_local_route(self.base_input(), responder=None, now=NOW)
        self.assertFalse(result["executed"])
        self.assertIsNone(result["response"])
        self.assertEqual("local_responder_missing", result["reason"])

    def test_a4_010_run_local_wiring_does_not_bypass_router_policy(self):
        fake_responder = Mock(return_value="should not run")
        with patch.object(local_route, "_BUILD_LOCAL_RESPONDER", return_value=fake_responder) as builder:
            with patch("builtins.print") as printed:
                exit_code = local_route.main(
                    [
                        "--fixture",
                        str(FIXTURE_PATH),
                        "--run-local",
                        "--now",
                        NOW,
                    ]
                )
        self.assertEqual(0, exit_code)
        builder.assert_called_once()
        fake_responder.assert_called_once_with(self.base_input()["message_text"])
        printed.assert_called_once()

        external_input = self.make_high_complexity_public()
        fake_responder = Mock(return_value="should not run")
        with patch.object(local_route, "_BUILD_LOCAL_RESPONDER", return_value=fake_responder) as builder:
            with patch.object(local_route, "_load_fixture", return_value=external_input):
                with patch("builtins.print") as printed:
                    exit_code = local_route.main(
                        [
                            "--fixture",
                            str(FIXTURE_PATH),
                            "--run-local",
                            "--now",
                            NOW,
                        ]
                    )
        decision = decision_probe.decide_router_policy(external_input, now=NOW)
        printed_result = json.loads(printed.call_args.args[0])
        self.assertEqual(0, exit_code)
        builder.assert_called_once()
        self.assertEqual("USER_CONFIRM", decision["route_tier"])
        self.assertEqual("external:scientific_medium", decision["proposed_external_target"])
        self.assertFalse(printed_result["executed"])
        fake_responder.assert_not_called()

    def test_a4_011_safe_local_route_with_injected_a4_responder_calls_fake_client_once(self):
        client = RecordingClient(response={"response": "adapter response"})
        local = responder.build_local_responder(client=client)
        result = local_route.run_local_route(self.base_input(), responder=local, now=NOW)
        self.assertTrue(result["executed"])
        self.assertEqual("adapter response", result["response"])
        self.assertEqual(1, len(client.calls))
        self.assertEqual(self.base_input()["message_text"], client.calls[0]["payload"]["prompt"])

    def test_a4_012_tests_use_fake_clients_only(self):
        client = RecordingClient()
        local = responder.build_local_responder(client=client)
        self.assertEqual("mock local response", local("prompt"))
        self.assertEqual(1, len(client.calls))

    def test_a4_013_invalid_parameters_fail_before_client_call(self):
        invalid_cases = [
            {"prompt": 123},
            {"model": ""},
            {"model": 123},
            {"endpoint": 123},
            {"timeout_s": 0},
            {"timeout_s": -1},
            {"timeout_s": math.nan},
            {"max_prompt_chars": 0},
            {"max_output_chars": 0},
            {"temperature": 0.1},
            {"client": object()},
        ]
        for invalid in invalid_cases:
            with self.subTest(invalid=invalid):
                client = invalid.get("client", RecordingClient())
                kwargs = {
                    "model": invalid.get("model", "gemma3:4b"),
                    "endpoint": invalid.get("endpoint", responder.DEFAULT_ENDPOINT),
                    "timeout_s": invalid.get("timeout_s", 3),
                    "temperature": invalid.get("temperature", 0.0),
                    "max_prompt_chars": invalid.get("max_prompt_chars", 100),
                    "max_output_chars": invalid.get("max_output_chars", 100),
                    "client": client,
                }
                with self.assertRaises(responder.LocalResponderPolicyError):
                    responder.call_local_ollama_generate(invalid.get("prompt", "prompt"), **kwargs)
                if isinstance(client, RecordingClient):
                    self.assertEqual([], client.calls)


if __name__ == "__main__":
    unittest.main()
